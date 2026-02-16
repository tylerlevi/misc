from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VisualSignature:
    key: str
    screen: str
    shape_hint: str
    color_hint: str
    texture_hint: str
    interaction: str


# Human-curated visual knowledge for "what things look like" in fixed-window fheroes2.
# Used as a bridge between screen parsing labels and control strategy.
VISUAL_SIGNATURES: dict[str, VisualSignature] = {
    "castle_button": VisualSignature(
        key="castle_button",
        screen="right_panel",
        shape_hint="square icon with town skyline",
        color_hint="red/brown masonry",
        texture_hint="beveled brass frame",
        interaction="click to open town screen",
    ),
    "hero_button": VisualSignature(
        key="hero_button",
        screen="right_panel",
        shape_hint="square icon with mounted/hero figure",
        color_hint="tan/brown silhouette",
        texture_hint="beveled brass frame",
        interaction="click to open hero screen",
    ),
    "end_turn_button": VisualSignature(
        key="end_turn_button",
        screen="right_panel",
        shape_hint="hourglass icon",
        color_hint="sand/yellow glass",
        texture_hint="ornate gold border",
        interaction="click to end current turn",
    ),
    "town_build_slot": VisualSignature(
        key="town_build_slot",
        screen="castle",
        shape_hint="rectangular carved frame with empty/occupied construction slot",
        color_hint="tan stone",
        texture_hint="engraved relief",
        interaction="click to build highlighted structure",
    ),
    "hero_stack_slot": VisualSignature(
        key="hero_stack_slot",
        screen="hero",
        shape_hint="unit portrait slot with count text",
        color_hint="unit-dependent with red frame accents",
        texture_hint="polished wood/gold",
        interaction="drag between slots to split or merge stacks",
    ),
    "gold_mine": VisualSignature(
        key="gold_mine",
        screen="adventure_map",
        shape_hint="mine entrance with ore/gold motif",
        color_hint="gray rock with yellow accents",
        texture_hint="mountain-side cave",
        interaction="high-priority capture for +1000 gold/day",
    ),
    "sawmill": VisualSignature(
        key="sawmill",
        screen="adventure_map",
        shape_hint="wooden mill building with logs",
        color_hint="brown timber",
        texture_hint="saw platform",
        interaction="capture for +2 wood/day",
    ),
    "ore_pit": VisualSignature(
        key="ore_pit",
        screen="adventure_map",
        shape_hint="rock pit with excavated boulders",
        color_hint="gray-brown",
        texture_hint="open quarry",
        interaction="capture for +2 ore/day",
    ),
    "treasure_chest": VisualSignature(
        key="treasure_chest",
        screen="adventure_map",
        shape_hint="small chest sprite",
        color_hint="gold/yellow",
        texture_hint="bright highlight",
        interaction="pickup for tempo gold/xp",
    ),
    "neutral_guard": VisualSignature(
        key="neutral_guard",
        screen="adventure_map",
        shape_hint="unit sprite standing on path/object",
        color_hint="varies by creature",
        texture_hint="animated stack sprite",
        interaction="evaluate risk before engaging",
    ),
}


def normalize_visual_key(label: str) -> str:
    return label.strip().lower().replace(" ", "_")


def lookup_visual_signature(label: str) -> VisualSignature | None:
    return VISUAL_SIGNATURES.get(normalize_visual_key(label))
