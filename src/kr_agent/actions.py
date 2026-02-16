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
    x: float
    y: float
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
        self._targets = UITargets(
            build_spots=[],
            start_wave=None,
            continue_button=None,
            kr_confidence=0.0,
            menu_buttons={},
        )
        self._build_index = 0
        self._frame_shape: tuple[int, int] | None = None

    @property
    def size(self) -> int:
        return len(self.actions)

    def update_targets(self, frame_bgr: np.ndarray) -> None:
        self._targets = self._ui.detect(frame_bgr)
        h, w = frame_bgr.shape[:2]
        self._frame_shape = (w, h)

    def bootstrap_opening(self) -> None:
        """Deterministic bootstrapping for Steam menu + early battle flow."""
        if self._targets.kr_confidence < 0.30:
            return

        # If in meta/menu screens, click obvious buttons first.
        for name in ("close_panel", "enemy_encyclopedia", "upgrades", "start_game"):
            if name in self._targets.menu_buttons:
                self._click_point(self._targets.menu_buttons[name])
                time.sleep(self.click_delay)

        # If in battle, run fast opening setup.
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
        self._click_point((x, y), hotkey=action.hotkey)

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

        if action.name in self._targets.menu_buttons:
            return self._targets.menu_buttons[action.name]

        return self._to_screen_point(action.x, action.y)

    def _to_screen_point(self, x: float, y: float) -> tuple[int, int]:
        if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and self._frame_shape is not None:
            width, height = self._frame_shape
            return int(x * width), int(y * height)
        return int(x), int(y)

    def _click_point(self, point: tuple[int, int], hotkey: str | None = None) -> None:
        x, y = point
        if self.dry_run:
            time.sleep(self.click_delay)
            return

        import pyautogui

        x += random.randint(-self.click_jitter_px, self.click_jitter_px)
        y += random.randint(-self.click_jitter_px, self.click_jitter_px)
        if hotkey:
            pyautogui.press(hotkey)
        pyautogui.click(int(x), int(y))
        time.sleep(self.click_delay)

    def _find_action(self, name: str) -> int | None:
        for i, action in enumerate(self.actions):
            if action.name == name:
                return i
        return None


def default_actions() -> list[Action]:
    # Normalized coordinates so fallback remains resolution-independent.
    return [
        Action("build_archer", 0.156, 0.900, "1"),
        Action("build_mage", 0.197, 0.900, "2"),
        Action("build_barracks", 0.238, 0.900, "3"),
        Action("build_artillery", 0.281, 0.900, "4"),
        Action("rally_near_spawn", 0.337, 0.350),
        Action("rally_mid", 0.475, 0.480),
        Action("rally_end", 0.681, 0.580),
        Action("hero_ability", 0.812, 0.920, "space"),
        Action("reinforcements", 0.762, 0.920, "r"),
        Action("meteor", 0.719, 0.920, "f"),
        Action("start_wave", 0.925, 0.960),
        Action("start_game", 0.820, 0.835),
        Action("upgrades", 0.810, 0.455),
        Action("enemy_encyclopedia", 0.810, 0.260),
        Action("close_panel", 0.915, 0.095),
        Action("idle_observe", 0.031, 0.050),
    ]


def load_actions(path: Path | None) -> list[Action]:
    if path is None:
        return default_actions()
    raw = json.loads(path.read_text())
    return [Action(**item) for item in raw]
