from __future__ import annotations

from dataclasses import dataclass
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


class EvolutionTrainer:
    def __init__(self, config: TrainingBundle, region: ScreenRegion, executor: ActionExecutor) -> None:
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
            print(
                f"generation={generation} best={best.fitness:.3f} mean={mean_fitness:.3f} "
                f"std={std_fitness:.3f} epsilon={epsilon:.3f} temp={temperature:.3f} "
                f"mutation_std={self.evolver.current_mutation_std:.4f} archive={len(self._novelty_archive)}"
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
