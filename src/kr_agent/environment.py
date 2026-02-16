from __future__ import annotations

from dataclasses import dataclass
import time

import numpy as np

from .actions import ActionExecutor
from .config import RewardConfig, VisionConfig
from .vision import VisionEncoder


@dataclass(slots=True)
class EpisodeStats:
    survival_seconds: float
    actions_taken: int
    heuristic_score: float


class RewardShaper:
    def __init__(self, config: RewardConfig) -> None:
        self.config = config

    def score(self, state: np.ndarray, prev_state: np.ndarray | None) -> float:
        metrics = self.metrics(state, prev_state)
        return (
            self.config.brightness_weight * metrics["brightness"]
            + self.config.contrast_weight * metrics["contrast"]
            + self.config.motion_weight * metrics["motion"]
            + self.config.entropy_weight * metrics["entropy"]
        )

    def metrics(self, state: np.ndarray, prev_state: np.ndarray | None) -> dict[str, float]:
        brightness = float(np.mean(state))
        contrast = float(np.std(state))
        motion = float(np.mean(np.abs(state - prev_state))) if prev_state is not None else 0.0
        entropy = self._entropy(state)
        return {
            "brightness": brightness,
            "contrast": contrast,
            "motion": motion,
            "entropy": entropy,
        }

    @staticmethod
    def _entropy(state: np.ndarray) -> float:
        bins = np.histogram(state, bins=16, range=(0.0, 1.0))[0].astype(np.float32)
        p = bins / (bins.sum() + 1e-8)
        return float(-(p * np.log(p + 1e-8)).sum())


class KingdomRushEnvironment:
    """Online interaction wrapper using screen pixels and UI actions."""

    def __init__(
        self,
        encoder: VisionEncoder,
        executor: ActionExecutor,
        reward_shaper: RewardShaper,
        action_repeat: int = 2,
        capture_interval_s: float = 0.05,
    ) -> None:
        self.encoder = encoder
        self.executor = executor
        self.reward_shaper = reward_shaper
        self.action_repeat = max(1, action_repeat)
        self.capture_interval_s = capture_interval_s
        self._last_state: np.ndarray | None = None

    @classmethod
    def from_configs(
        cls,
        encoder: VisionEncoder,
        executor: ActionExecutor,
        reward_cfg: RewardConfig,
        vision_cfg: VisionConfig,
        action_repeat: int,
    ) -> "KingdomRushEnvironment":
        return cls(
            encoder=encoder,
            executor=executor,
            reward_shaper=RewardShaper(reward_cfg),
            action_repeat=action_repeat,
            capture_interval_s=vision_cfg.capture_interval_s,
        )

    def reset(self) -> np.ndarray:
        frame = self.encoder.capture_raw_bgr()
        self.executor.update_targets(frame)
        self.executor.bootstrap_opening()
        state = self.encoder.reset_stack()
        self._last_state = state
        return state

    def step(self, action_index: int) -> tuple[np.ndarray, float, dict[str, float]]:
        total_reward = 0.0
        latest_metrics: dict[str, float] = {}
        state = self._last_state if self._last_state is not None else self.encoder.capture()
        for _ in range(self.action_repeat):
            self.executor.execute(action_index)
            time.sleep(self.capture_interval_s)
            self.executor.update_targets(self.encoder.capture_raw_bgr())
            state = self.encoder.capture()
            latest_metrics = self.reward_shaper.metrics(state, self._last_state)
            total_reward += self.reward_shaper.score(state, self._last_state)
            self._last_state = state
        return state, total_reward, latest_metrics
