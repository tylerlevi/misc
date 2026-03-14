from __future__ import annotations

# High-level map object value priors for movement planning.
# Values are normalized "tempo-equivalent" utility points.
OBJECT_VALUE_PRIORS: dict[str, float] = {
    "gold_mine": 4.6,
    "sawmill": 2.6,
    "ore_pit": 2.6,
    "gem_mine": 3.2,
    "crystal_mine": 3.2,
    "sulfur_mine": 3.2,
    "mercury_mine": 3.2,
    "treasure_chest": 1.7,
    "artifact": 2.4,
    "pandora_box": 3.4,
    "learning_stone": 1.6,
    "shrine": 1.4,
    "wagon": 1.0,
    "windmill": 0.9,
    "water_wheel": 1.1,
    "town": 6.0,
    "neutral_guard": -0.3,
    "unknown": 0.0,
}


# Curated opening build priorities by faction for week 1 pressure.
# Lower index = earlier preference.
OPENING_BUILD_ORDERS: dict[str, tuple[str, ...]] = {
    "knight": (
        "town_hall",
        "dwelling_lvl1",
        "dwelling_lvl2",
        "dwelling_lvl3",
        "marketplace",
        "blacksmith",
    ),
    "barbarian": (
        "town_hall",
        "dwelling_lvl1",
        "dwelling_lvl2",
        "dwelling_lvl3",
        "dwelling_lvl4",
        "marketplace",
    ),
    "sorceress": (
        "town_hall",
        "dwelling_lvl1",
        "dwelling_lvl2",
        "dwelling_lvl3",
        "dwelling_lvl4",
        "mage_guild_1",
    ),
    "warlock": (
        "town_hall",
        "dwelling_lvl1",
        "dwelling_lvl2",
        "dwelling_lvl3",
        "dwelling_lvl4",
        "marketplace",
    ),
    "wizard": (
        "town_hall",
        "dwelling_lvl1",
        "dwelling_lvl2",
        "mage_guild_1",
        "dwelling_lvl3",
        "marketplace",
    ),
    "necromancer": (
        "town_hall",
        "dwelling_lvl1",
        "dwelling_lvl2",
        "dwelling_lvl3",
        "mage_guild_1",
        "marketplace",
    ),
    "default": (
        "town_hall",
        "dwelling_lvl1",
        "dwelling_lvl2",
        "marketplace",
        "dwelling_lvl3",
    ),
}


# Simplified build costs used for affordability checks in UI planning
# (gold, wood, ore).
BUILD_COSTS: dict[str, tuple[int, int, int]] = {
    "town_hall": (2500, 0, 0),
    "city_hall": (5000, 0, 0),
    "capitol": (10000, 0, 0),
    "marketplace": (500, 5, 0),
    "blacksmith": (1000, 5, 0),
    "dwelling_lvl1": (300, 0, 0),
    "dwelling_lvl2": (800, 5, 0),
    "dwelling_lvl3": (1000, 0, 5),
    "dwelling_lvl4": (2000, 10, 10),
    "dwelling_lvl5": (3000, 10, 0),
    "dwelling_lvl6": (5000, 20, 0),
    "mage_guild_1": (2000, 5, 5),
}
