from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random
import time


@dataclass(slots=True)
class Action:
    name: str
    x: int
    y: int
    hotkey: str | None = None


class ActionExecutor:
    """Maps policy output index to clicks/hotkeys for the game UI."""

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

    @property
    def size(self) -> int:
        return len(self.actions)

    def execute(self, index: int) -> None:
        action = self.actions[index % len(self.actions)]
        if self.dry_run:
            time.sleep(self.click_delay)
            return

        import pyautogui  # lazy import for headless/test compatibility

        x = action.x + random.randint(-self.click_jitter_px, self.click_jitter_px)
        y = action.y + random.randint(-self.click_jitter_px, self.click_jitter_px)
        if action.hotkey:
            pyautogui.press(action.hotkey)
        pyautogui.click(x, y)
        time.sleep(self.click_delay)


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
