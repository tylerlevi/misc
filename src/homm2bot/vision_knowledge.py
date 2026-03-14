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


VISUAL_SIGNATURES: dict[str, VisualSignature] = {
    # Right panel controls
    "castle_button": VisualSignature("castle_button", "right_panel", "square icon with town skyline", "red/brown masonry", "beveled brass frame", "click to open town screen"),
    "hero_button": VisualSignature("hero_button", "right_panel", "square icon with hero portrait", "tan/brown", "beveled brass frame", "click to open hero screen"),
    "spellbook_button": VisualSignature("spellbook_button", "right_panel", "square icon with open book", "cream/blue", "beveled brass frame", "click to open spellbook"),
    "end_turn_button": VisualSignature("end_turn_button", "right_panel", "hourglass icon", "sand/yellow", "ornate gold border", "click to end current turn"),

    # Town / castle screens
    "town_castle_icon": VisualSignature("town_castle_icon", "town_screen", "large castle crest button", "tan/gold", "engraved stone", "click to open castle upgrades"),
    "town_recruit_slot": VisualSignature("town_recruit_slot", "town_screen", "horse-head embossed slot", "sand/tan", "carved tile", "click to recruit creatures"),
    "castle_build_tile": VisualSignature("castle_build_tile", "castle_options", "rectangular building card", "mixed by building", "wooden framed tile", "click to inspect/build structure"),
    "build_dialog_ok": VisualSignature("build_dialog_ok", "build_dialog", "OK button", "tan with dark text", "stone-like button", "confirm construction"),
    "build_dialog_cancel": VisualSignature("build_dialog_cancel", "build_dialog", "CANCEL button", "tan with dark text", "stone-like button", "cancel construction"),

    # Resources visual forms
    "resource_wood": VisualSignature("resource_wood", "right_panel", "stacked logs", "brown", "wood grain", "resource recognition/trade decisions"),
    "resource_ore": VisualSignature("resource_ore", "right_panel", "rock cluster", "gray", "rough stone", "resource recognition/trade decisions"),
    "resource_mercury": VisualSignature("resource_mercury", "right_panel", "silver vial", "silver/white", "glass shine", "resource recognition/trade decisions"),
    "resource_sulfur": VisualSignature("resource_sulfur", "right_panel", "yellow mound", "yellow", "powder texture", "resource recognition/trade decisions"),
    "resource_crystal": VisualSignature("resource_crystal", "right_panel", "blue crystal", "blue", "faceted gem", "resource recognition/trade decisions"),
    "resource_gems": VisualSignature("resource_gems", "right_panel", "colored gems", "multi-color", "faceted jewels", "resource recognition/trade decisions"),
    "resource_gold": VisualSignature("resource_gold", "right_panel", "gold piles", "gold", "coin shine", "resource recognition/trade decisions"),

    # Adventure objects
    "gold_mine": VisualSignature("gold_mine", "adventure_map", "mine entrance", "gray/yellow", "mountain cave", "high-priority capture for +1000 gold/day"),
    "sawmill": VisualSignature("sawmill", "adventure_map", "mill + logs", "brown timber", "saw platform", "capture for +2 wood/day"),
    "ore_pit": VisualSignature("ore_pit", "adventure_map", "quarry pit", "gray-brown", "open rock pit", "capture for +2 ore/day"),
    "treasure_chest": VisualSignature("treasure_chest", "adventure_map", "small chest sprite", "gold/yellow", "bright highlight", "pickup for tempo gold/xp"),
    "neutral_guard": VisualSignature("neutral_guard", "adventure_map", "unit stack sprite", "varies", "animated creature", "evaluate risk before engaging"),
    "town": VisualSignature("town", "adventure_map", "large settlement sprite", "faction dependent", "stone walls/buildings", "capture/visit for economy and production"),
}


ALIASES: dict[str, str] = {
    "castle": "town",
    "wood": "resource_wood",
    "ore": "resource_ore",
    "mercury": "resource_mercury",
    "sulfur": "resource_sulfur",
    "crystal": "resource_crystal",
    "gems": "resource_gems",
    "gold": "resource_gold",
}


def normalize_visual_key(label: str) -> str:
    raw = label.strip().lower().replace(" ", "_")
    return ALIASES.get(raw, raw)


def lookup_visual_signature(label: str) -> VisualSignature | None:
    return VISUAL_SIGNATURES.get(normalize_visual_key(label))
