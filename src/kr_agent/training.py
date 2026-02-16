from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import time

import numpy as np

from .actions import ActionExecutor
from .checkpoint import load_genome, save_genome
from .config import (
    AgentConfig,
    EvolutionConfig,
    ExplorationConfig,
    NoveltyConfig,
    RuntimeConfig,
    RewardConfig,
    VisionConfig,
)
from .environment import KingdomRushEnvironment
from .evolution import Evolver
from .model import Genome, PolicyNetwork
from .vision import ScreenRegion, VisionEncoder


@dataclass(slots=True)
class TrainingBundle:
    agent: AgentConfig
    evolution: EvolutionConfig
    exploration: ExplorationConfig
    runtime: RuntimeConfig
    vision: VisionConfig
    reward: RewardConfig
    novelty: NoveltyConfig


@dataclass(slots=True)
class GenerationStats:
    generation: int
    best: float
    mean: float
    std: float
    epsilon: float
    temperature: float
    mutation_std: float
    note: str


class EvolutionTrainer:
    def __init__(
        self,
        config: TrainingBundle,
        region: ScreenRegion,
        executor: ActionExecutor,
    ) -> None:
        self.cfg = config
        self.encoder = VisionEncoder(region=region, config=config.vision)
        self.environment = KingdomRushEnvironment.from_configs(
            encoder=self.encoder,
            executor=executor,
            reward_cfg=config.reward,
            vision_cfg=config.vision,
            action_repeat=config.agent.action_repeat,
        )
        self.evolver = Evolver(config.agent, config.evolution)
        self._novelty_archive: list[np.ndarray] = []

    def run(self) -> None:
        if self.cfg.vision.wait_for_boot_screen:
            detected = self.encoder.wait_for_boot_screen(self.cfg.vision.boot_timeout_s)
            if self.cfg.runtime.verbose:
                print(f"boot_screen_detected={detected}")

        start_generation = 0
        population = self.evolver.initial_population()
        best_seen = float("-inf")
        stagnation = 0
        history: list[GenerationStats] = []

        if self.cfg.runtime.resume_from is not None:
            start_generation, genome = load_genome(self.cfg.runtime.resume_from)
            if self.cfg.runtime.verbose:
                print(f"resumed_from_generation={start_generation} fitness={genome.fitness:.3f}")
            population[0] = genome

        for generation in range(start_generation, self.cfg.evolution.generations):
            epsilon, temperature = self._exploration_params(generation)
            for genome in population:
                genome.fitness = self._evaluate_genome(genome, epsilon=epsilon, temperature=temperature)

            best = max(population, key=lambda g: g.fitness)
            fitnesses = [g.fitness for g in population]
            mean_fitness = float(np.mean(fitnesses))
            std_fitness = float(np.std(fitnesses))

            note = self._progress_note(best_seen, best.fitness, stagnation)
            history.append(
                GenerationStats(
                    generation=generation,
                    best=best.fitness,
                    mean=mean_fitness,
                    std=std_fitness,
                    epsilon=epsilon,
                    temperature=temperature,
                    mutation_std=self.evolver.current_mutation_std,
                    note=note,
                )
            )

            if best.fitness > best_seen:
                best_seen = best.fitness
                stagnation = 0
            else:
                stagnation += 1
                if stagnation >= self.cfg.evolution.stagnation_generations:
                    boosted = min(
                        self.cfg.evolution.max_mutation_std,
                        self.evolver.current_mutation_std * self.cfg.evolution.mutation_boost,
                    )
                    self.evolver.current_mutation_std = boosted
                    stagnation = 0

            if generation % self.cfg.runtime.checkpoint_every == 0:
                ckpt = self.cfg.runtime.checkpoint_dir / f"best_gen_{generation:04d}.npz"
                save_genome(ckpt, best, generation)

            population = self.evolver.next_generation(population)

        report_path = self._write_training_report(history)
        if self.cfg.runtime.verbose:
            print(f"training_report={report_path}")

    def _evaluate_genome(self, genome: Genome, epsilon: float, temperature: float) -> float:
        scores: list[float] = []
        behaviors: list[np.ndarray] = []

        for _ in range(self.cfg.evolution.evaluation_repeats):
            policy = PolicyNetwork(genome, rng=self.evolver.rng)
            state = self.environment.reset()
            score = 0.0
            start = time.time()

            metric_totals = {"brightness": 0.0, "contrast": 0.0, "motion": 0.0, "entropy": 0.0}
            steps = 0
            action_counts = np.zeros(genome.b2.shape[0], dtype=np.float32)

            while (time.time() - start) < self.cfg.evolution.episode_seconds:
                action = policy.act_explore(state, epsilon=epsilon, temperature=temperature)
                action_counts[action] += 1
                state, reward, metrics = self.environment.step(action)
                score += reward
                for key in metric_totals:
                    metric_totals[key] += metrics.get(key, 0.0)
                steps += 1

            scores.append(score)
            behaviors.append(self._behavior_vector(metric_totals, action_counts, steps))

        novelty = self._novelty_score(behaviors)
        base = float(np.median(scores))
        return base + self.cfg.novelty.weight * novelty

    def _behavior_vector(
        self, metric_totals: dict[str, float], action_counts: np.ndarray, steps: int
    ) -> np.ndarray:
        steps = max(1, steps)
        metrics = np.array(
            [
                metric_totals["brightness"] / steps,
                metric_totals["contrast"] / steps,
                metric_totals["motion"] / steps,
                metric_totals["entropy"] / steps,
            ],
            dtype=np.float32,
        )
        action_probs = action_counts / max(1.0, float(action_counts.sum()))
        action_entropy = -float(np.sum(action_probs * np.log(action_probs + 1e-8)))
        return np.concatenate([metrics, np.array([action_entropy], dtype=np.float32)])

    def _novelty_score(self, behaviors: list[np.ndarray]) -> float:
        if not behaviors:
            return 0.0
        behavior = np.mean(np.stack(behaviors, axis=0), axis=0)
        if not self._novelty_archive:
            self._novelty_archive.append(behavior)
            return 0.0

        distances = [float(np.linalg.norm(behavior - prev)) for prev in self._novelty_archive]
        k = min(self.cfg.novelty.k_nearest, len(distances))
        nearest = sorted(distances)[:k]
        novelty = float(np.mean(nearest)) if nearest else 0.0

        self._novelty_archive.append(behavior)
        if len(self._novelty_archive) > self.cfg.novelty.archive_size:
            self._novelty_archive.pop(0)
        return novelty

    def _exploration_params(self, generation: int) -> tuple[float, float]:
        e_cfg = self.cfg.exploration
        eps = max(e_cfg.epsilon_end, e_cfg.epsilon_start * (e_cfg.epsilon_decay**generation))
        temp = max(e_cfg.temperature_end, e_cfg.temperature_start * (e_cfg.temperature_decay**generation))
        return eps, temp

    @staticmethod
    def _progress_note(best_seen: float, current_best: float, stagnation: int) -> str:
        if current_best > best_seen:
            return "new_best"
        if stagnation == 0:
            return "matching_best"
        return f"stagnant_{stagnation}"

    def _write_training_report(self, history: list[GenerationStats]) -> Path:
        self.cfg.runtime.report_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.cfg.runtime.report_dir / f"run_report_{stamp}.txt"

        if not history:
            path.write_text("No generations were run.\n", encoding="utf-8")
            return path

        best_entry = max(history, key=lambda x: x.best)
        last = history[-1]

        next_focus: list[str] = []
        if last.note.startswith("stagnant"):
            next_focus.append("Improve exploration: raise novelty weight or reduce epsilon decay.")
        if last.std < 0.05:
            next_focus.append("Population collapsed: increase immigrants or mutation std.")
        if last.best - last.mean < 0.2:
            next_focus.append("Top genome edge is small: increase population or episode length.")
        if not next_focus:
            next_focus.append("Continue current settings and resume from latest checkpoint.")

        lines = [
            "Kingdom Rush Training Report",
            "============================",
            f"Generations run: {len(history)}",
            f"Best fitness overall: {best_entry.best:.4f} (generation {best_entry.generation})",
            f"Last generation best/mean/std: {last.best:.4f} / {last.mean:.4f} / {last.std:.4f}",
            f"Last epsilon/temperature: {last.epsilon:.4f} / {last.temperature:.4f}",
            f"Last mutation std: {last.mutation_std:.6f}",
            f"Last status note: {last.note}",
            "",
            "What to work on at resume:",
        ]
        for item in next_focus:
            lines.append(f"- {item}")

        lines.append("")
        lines.append("Per-generation summary:")
        for entry in history:
            lines.append(
                f"gen={entry.generation:04d} best={entry.best:.4f} mean={entry.mean:.4f} "
                f"std={entry.std:.4f} eps={entry.epsilon:.4f} temp={entry.temperature:.4f} "
                f"mut={entry.mutation_std:.6f} note={entry.note}"
            )

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path
