from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class VisionConfig:
    width: int = 32
    height: int = 18
    frame_stack: int = 3
    capture_interval_s: float = 0.05
    wait_for_boot_screen: bool = False
    boot_timeout_s: int = 20

    def __post_init__(self) -> None:
        self.width = max(1, self.width)
        self.height = max(1, self.height)
        self.frame_stack = max(1, self.frame_stack)
        self.capture_interval_s = max(0.0, self.capture_interval_s)
        self.boot_timeout_s = max(1, self.boot_timeout_s)


@dataclass(slots=True)
class RewardConfig:
    brightness_weight: float = 0.6
    contrast_weight: float = 0.9
    motion_weight: float = 1.4
    entropy_weight: float = 0.25


@dataclass(slots=True)
class NoveltyConfig:
    weight: float = 0.35
    archive_size: int = 250
    k_nearest: int = 8


@dataclass(slots=True)
class ExplorationConfig:
    epsilon_start: float = 0.25
    epsilon_end: float = 0.03
    epsilon_decay: float = 0.985
    temperature_start: float = 1.0
    temperature_end: float = 0.4
    temperature_decay: float = 0.992


@dataclass(slots=True)
class AgentConfig:
    input_size: int
    hidden_size: int = 256
    output_size: int = 12
    mutation_std: float = 0.08
    crossover_rate: float = 0.60
    action_repeat: int = 2


@dataclass(slots=True)
class EvolutionConfig:
    population_size: int = 48
    elite_count: int = 8
    generations: int = 200
    episode_seconds: int = 90
    evaluation_repeats: int = 2
    tournament_size: int = 5
    mutation_decay: float = 0.992
    min_mutation_std: float = 0.01
    max_mutation_std: float = 0.5
    mutation_boost: float = 1.3
    stagnation_generations: int = 10
    immigrants_per_generation: int = 2
    random_seed: int = 7


@dataclass(slots=True)
class RuntimeConfig:
    checkpoint_dir: Path = Path("checkpoints")
    report_dir: Path = Path("reports")
    checkpoint_every: int = 1
    resume_from: Path | None = None
    dry_run: bool = False
    verbose: bool = True


def build_agent_config(
    vision_cfg: VisionConfig,
    output_size: int,
    action_repeat: int,
    hidden_size: int = 256,
    mutation_std: float = 0.08,
    crossover_rate: float = 0.60,
) -> AgentConfig:
    input_size = vision_cfg.width * vision_cfg.height * vision_cfg.frame_stack
    return AgentConfig(
        input_size=input_size,
        output_size=output_size,
        action_repeat=action_repeat,
        hidden_size=hidden_size,
        mutation_std=mutation_std,
        crossover_rate=crossover_rate,
    )
