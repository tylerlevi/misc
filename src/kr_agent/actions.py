from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random
import time

import numpy as np

from .ui import KRUIAnalyzer, UITargets


@dataclass(slots=True)
class Action:
    name: str
    x: int
    y: int
    hotkey: str | None = None


class ActionExecutor:
    """Maps policy output index to adaptive game UI actions."""

    def __init__(
        self,
        actions: list[Action],
        click_delay: float = 0.03,
        click_jitter_px: int = 2,
        dry_run: bool = False,
    ) -> None:
        self.actions = actions
        self.click_delay = click_delay
        self.click_jitter_px = click_jitter_px
        self.dry_run = dry_run
        self._ui = KRUIAnalyzer()
        self._targets = UITargets(build_spots=[], start_wave=None, continue_button=None)
        self._build_index = 0

    @property
    def size(self) -> int:
        return len(self.actions)

    def update_targets(self, frame_bgr: np.ndarray) -> None:
        self._targets = self._ui.detect(frame_bgr)

    def bootstrap_opening(self) -> None:
        """Deterministic opening so training starts waves/towers quickly."""
        opening = [
            self._find_action("build_archer"),
            self._find_action("build_mage"),
            self._find_action("start_wave"),
        ]
        for idx in opening:
            if idx is not None:
                self.execute(idx)

    def execute(self, index: int) -> None:
        action = self.actions[index % len(self.actions)]
        x, y = self._resolve_target(action)

        if self.dry_run:
            time.sleep(self.click_delay)
            return

        import pyautogui  # lazy import for headless/test compatibility

        x += random.randint(-self.click_jitter_px, self.click_jitter_px)
        y += random.randint(-self.click_jitter_px, self.click_jitter_px)
        if action.hotkey:
            pyautogui.press(action.hotkey)
        pyautogui.click(x, y)
        time.sleep(self.click_delay)

    def _resolve_target(self, action: Action) -> tuple[int, int]:
        if action.name.startswith("build_") and self._targets.build_spots:
            spot = self._targets.build_spots[self._build_index % len(self._targets.build_spots)]
            self._build_index += 1
            return spot

        if action.name == "start_wave":
            if self._targets.start_wave is not None:
                return self._targets.start_wave
            if self._targets.continue_button is not None:
                return self._targets.continue_button

        return action.x, action.y

    def _find_action(self, name: str) -> int | None:
        for i, action in enumerate(self.actions):
            if action.name == name:
                return i
        return None


def default_actions() -> list[Action]:
    return [
        Action("build_archer", 250, 900, "1"),
        Action("build_mage", 315, 900, "2"),
        Action("build_barracks", 380, 900, "3"),
        Action("build_artillery", 450, 900, "4"),
        Action("rally_near_spawn", 540, 350),
        Action("rally_mid", 760, 480),
        Action("rally_end", 1090, 580),
        Action("hero_ability", 1300, 920, "space"),
        Action("reinforcements", 1220, 920, "r"),
        Action("meteor", 1150, 920, "f"),
        Action("start_wave", 1480, 960),
        Action("idle_observe", 50, 50),
    ]


def load_actions(path: Path | None) -> list[Action]:
    if path is None:
        return default_actions()
    raw = json.loads(path.read_text())
    return [Action(**item) for item in raw]
