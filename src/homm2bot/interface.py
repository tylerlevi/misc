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

    # Right panel quick buttons (from screenshots)
    btn_hero: Rect = Rect(1423, 516, 1469, 562)
    btn_castle: Rect = Rect(1475, 516, 1521, 562)
    btn_spellbook: Rect = Rect(1527, 516, 1573, 562)
    btn_end_turn: Rect = Rect(1578, 567, 1626, 615)

    # Playfield and minimap
    world_view: Rect = Rect(34, 40, 1402, 877)
    minimap: Rect = Rect(1432, 74, 1588, 228)

    # Hero screen stack row and reserve rows
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

    # Town screen build slots across top row under castle portrait.
    town_build_slots: tuple[Rect, ...] = (
        Rect(643, 513, 736, 613),
        Rect(742, 513, 835, 613),
        Rect(840, 513, 933, 613),
        Rect(939, 513, 1032, 613),
        Rect(1037, 513, 1130, 613),
    )


DEFAULT_LAYOUT = UiLayout()
