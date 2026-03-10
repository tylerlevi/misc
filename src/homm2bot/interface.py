from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    def center(self) -> Point:
        return Point((self.left + self.right) // 2, (self.top + self.bottom) // 2)


@dataclass(frozen=True)
class UiLayout:
    """Fixed-window fheroes2 layout coordinates (calibrated for 1680x945 windowed view)."""

    width: int = 1680
    height: int = 945

    # Right panel quick buttons.
    btn_hero: Rect = Rect(1423, 516, 1469, 562)
    btn_castle: Rect = Rect(1475, 516, 1521, 562)
    btn_spellbook: Rect = Rect(1527, 516, 1573, 562)
    btn_kingdom: Rect = Rect(1422, 567, 1470, 615)
    btn_puzzle: Rect = Rect(1474, 567, 1522, 615)
    btn_end_turn: Rect = Rect(1578, 567, 1626, 615)

    # Playfield and minimap.
    world_view: Rect = Rect(34, 40, 1402, 877)
    minimap: Rect = Rect(1432, 74, 1588, 228)

    # Right-panel resource icons / values in main map view.
    right_resource_wood: Rect = Rect(1438, 695, 1464, 720)
    right_resource_ore: Rect = Rect(1491, 695, 1518, 720)
    right_resource_mercury: Rect = Rect(1543, 695, 1569, 720)
    right_resource_sulfur: Rect = Rect(1438, 725, 1464, 750)
    right_resource_crystal: Rect = Rect(1491, 725, 1518, 750)
    right_resource_gems: Rect = Rect(1543, 725, 1569, 750)
    right_resource_gold: Rect = Rect(1492, 748, 1556, 772)

    # Hero screen stack row and reserve rows.
    hero_stack_slots: tuple[Rect, ...] = (
        Rect(583, 333, 672, 430),
        Rect(675, 333, 764, 430),
        Rect(767, 333, 856, 430),
        Rect(859, 333, 948, 430),
        Rect(951, 333, 1040, 430),
    )
    hero_reserve_slots: tuple[Rect, ...] = (
        Rect(583, 588, 672, 679),
        Rect(675, 588, 764, 679),
        Rect(767, 588, 856, 679),
        Rect(859, 588, 948, 679),
        Rect(951, 588, 1040, 679),
    )

    # Town view (double-click town from map) - top recruit/dwelling row and castle button area.
    town_recruit_slots: tuple[Rect, ...] = (
        Rect(642, 507, 735, 611),
        Rect(740, 507, 833, 611),
        Rect(838, 507, 931, 611),
        Rect(936, 507, 1029, 611),
        Rect(1034, 507, 1127, 611),
    )
    town_castle_icon: Rect = Rect(532, 613, 642, 718)
    town_exit_button: Rect = Rect(1042, 635, 1123, 675)

    # Castle options screen (big castle icon clicked) grid.
    castle_build_grid: tuple[Rect, ...] = (
        Rect(528, 240, 640, 305), Rect(646, 240, 758, 305), Rect(764, 240, 876, 305),
        Rect(528, 311, 640, 376), Rect(646, 311, 758, 376), Rect(764, 311, 876, 376),
        Rect(528, 382, 640, 447), Rect(646, 382, 758, 447), Rect(764, 382, 876, 447),
        Rect(528, 453, 640, 518), Rect(646, 453, 758, 518), Rect(764, 453, 876, 518),
        Rect(528, 524, 640, 589), Rect(646, 524, 758, 589), Rect(764, 524, 876, 589),
        Rect(528, 595, 640, 660), Rect(646, 595, 758, 660), Rect(764, 595, 876, 660),
    )

    # Build confirmation popup buttons (OK/CANCEL)
    build_dialog_ok: Rect = Rect(723, 598, 811, 636)
    build_dialog_cancel: Rect = Rect(839, 598, 939, 636)


DEFAULT_LAYOUT = UiLayout()
