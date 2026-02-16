from __future__ import annotations

import argparse
from pathlib import Path

from .actions import ActionExecutor, load_actions
from .config import (
    EvolutionConfig,
    ExplorationConfig,
    NoveltyConfig,
    RewardConfig,
    RuntimeConfig,
    VisionConfig,
    build_agent_config,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train an evolutionary RL agent for Kingdom Rush")

    # Screen region
    parser.add_argument("--left", type=int, default=0)
    parser.add_argument("--top", type=int, default=0)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)

    # Vision and state
    parser.add_argument("--state-width", type=int, default=32)
    parser.add_argument("--state-height", type=int, default=18)
    parser.add_argument("--frame-stack", type=int, default=3)
    parser.add_argument("--capture-interval", type=float, default=0.05)
    parser.add_argument("--wait-for-boot-screen", action="store_true")
    parser.add_argument("--boot-timeout", type=int, default=20)

    # Agent model
    parser.add_argument("--hidden-size", type=int, default=256)
    parser.add_argument("--mutation-std", type=float, default=0.08)
    parser.add_argument("--crossover-rate", type=float, default=0.60)

    # Evolution
    parser.add_argument("--generations", type=int, default=60)
    parser.add_argument("--population", type=int, default=24)
    parser.add_argument("--elite-count", type=int, default=6)
    parser.add_argument("--episode-seconds", type=int, default=90)
    parser.add_argument("--evaluation-repeats", type=int, default=2)
    parser.add_argument("--action-repeat", type=int, default=2)
    parser.add_argument("--tournament-size", type=int, default=5)
    parser.add_argument("--mutation-decay", type=float, default=0.992)
    parser.add_argument("--min-mutation-std", type=float, default=0.01)
    parser.add_argument("--max-mutation-std", type=float, default=0.5)
    parser.add_argument("--mutation-boost", type=float, default=1.3)
    parser.add_argument("--stagnation-gens", type=int, default=10)
    parser.add_argument("--immigrants", type=int, default=2)

    # Exploration
    parser.add_argument("--epsilon-start", type=float, default=0.25)
    parser.add_argument("--epsilon-end", type=float, default=0.03)
    parser.add_argument("--epsilon-decay", type=float, default=0.985)
    parser.add_argument("--temperature-start", type=float, default=1.0)
    parser.add_argument("--temperature-end", type=float, default=0.4)
    parser.add_argument("--temperature-decay", type=float, default=0.992)

    # Novelty
    parser.add_argument("--novelty-weight", type=float, default=0.35)
    parser.add_argument("--novelty-archive", type=int, default=250)
    parser.add_argument("--novelty-k", type=int, default=8)

    # Reward shaping
    parser.add_argument("--reward-brightness", type=float, default=0.6)
    parser.add_argument("--reward-contrast", type=float, default=0.9)
    parser.add_argument("--reward-motion", type=float, default=1.4)
    parser.add_argument("--reward-entropy", type=float, default=0.25)

    # Runtime
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("checkpoints"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports"))
    parser.add_argument("--checkpoint-every", type=int, default=1)
    parser.add_argument("--resume-from", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--actions-file", type=Path, help="JSON file with action list")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    actions = load_actions(args.actions_file)

    vision_cfg = VisionConfig(
        width=args.state_width,
        height=args.state_height,
        frame_stack=args.frame_stack,
        capture_interval_s=args.capture_interval,
        wait_for_boot_screen=args.wait_for_boot_screen,
        boot_timeout_s=args.boot_timeout,
    )
    agent_cfg = build_agent_config(
        vision_cfg,
        output_size=len(actions),
        action_repeat=args.action_repeat,
        hidden_size=args.hidden_size,
        mutation_std=args.mutation_std,
        crossover_rate=args.crossover_rate,
    )
    evo_cfg = EvolutionConfig(
        generations=args.generations,
        population_size=args.population,
        elite_count=args.elite_count,
        episode_seconds=args.episode_seconds,
        evaluation_repeats=args.evaluation_repeats,
        tournament_size=args.tournament_size,
        mutation_decay=args.mutation_decay,
        min_mutation_std=args.min_mutation_std,
        max_mutation_std=args.max_mutation_std,
        mutation_boost=args.mutation_boost,
        stagnation_generations=args.stagnation_gens,
        immigrants_per_generation=args.immigrants,
    )
    exploration_cfg = ExplorationConfig(
        epsilon_start=args.epsilon_start,
        epsilon_end=args.epsilon_end,
        epsilon_decay=args.epsilon_decay,
        temperature_start=args.temperature_start,
        temperature_end=args.temperature_end,
        temperature_decay=args.temperature_decay,
    )
    novelty_cfg = NoveltyConfig(
        weight=args.novelty_weight,
        archive_size=args.novelty_archive,
        k_nearest=args.novelty_k,
    )
    runtime_cfg = RuntimeConfig(
        checkpoint_dir=args.checkpoint_dir,
        report_dir=args.report_dir,
        checkpoint_every=args.checkpoint_every,
        resume_from=args.resume_from,
        dry_run=args.dry_run,
    )
    reward_cfg = RewardConfig(
        brightness_weight=args.reward_brightness,
        contrast_weight=args.reward_contrast,
        motion_weight=args.reward_motion,
        entropy_weight=args.reward_entropy,
    )

    from .training import EvolutionTrainer, TrainingBundle
    from .vision import ScreenRegion

    bundle = TrainingBundle(
        agent=agent_cfg,
        evolution=evo_cfg,
        exploration=exploration_cfg,
        runtime=runtime_cfg,
        vision=vision_cfg,
        reward=reward_cfg,
        novelty=novelty_cfg,
    )

    trainer = EvolutionTrainer(
        config=bundle,
        region=ScreenRegion(args.left, args.top, args.width, args.height),
        executor=ActionExecutor(actions, dry_run=args.dry_run),
    )
    trainer.run()


if __name__ == "__main__":
    main()
