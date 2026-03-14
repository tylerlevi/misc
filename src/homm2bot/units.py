from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnitProfile:
    key: str
    faction: str
    tier: int
    role: str
    shooter: bool = False
    flying: bool = False
    retaliates_twice: bool = False
    no_enemy_retaliation: bool = False
    has_spellcast: bool = False
    speed_bias: float = 0.0
    durability_bias: float = 0.0
    damage_bias: float = 0.0


# Compact tactical priors used by the planners.
UNIT_INDEX: dict[str, UnitProfile] = {
    # Knight
    "peasant": UnitProfile("peasant", "knight", 1, "swarm", speed_bias=-0.2, durability_bias=-0.2),
    "archer": UnitProfile("archer", "knight", 2, "ranged", shooter=True, damage_bias=0.2),
    "ranger": UnitProfile("ranger", "knight", 2, "ranged", shooter=True, damage_bias=0.3),
    "pikeman": UnitProfile("pikeman", "knight", 3, "line", durability_bias=0.05),
    "veteran_pikeman": UnitProfile("veteran_pikeman", "knight", 3, "line", durability_bias=0.1),
    "swordsman": UnitProfile("swordsman", "knight", 4, "line", durability_bias=0.25, damage_bias=0.1),
    "master_swordsman": UnitProfile("master_swordsman", "knight", 4, "line", retaliates_twice=True, durability_bias=0.3),
    "cavalry": UnitProfile("cavalry", "knight", 5, "charger", speed_bias=0.25, damage_bias=0.25),
    "champion": UnitProfile("champion", "knight", 5, "charger", speed_bias=0.35, damage_bias=0.35),
    "paladin": UnitProfile("paladin", "knight", 6, "elite", durability_bias=0.4),
    "crusader": UnitProfile("crusader", "knight", 6, "elite", retaliates_twice=True, damage_bias=0.4),
    # Barbarian
    "goblin": UnitProfile("goblin", "barbarian", 1, "swarm", speed_bias=-0.1),
    "orc": UnitProfile("orc", "barbarian", 2, "ranged", shooter=True, damage_bias=0.1),
    "orc_chief": UnitProfile("orc_chief", "barbarian", 2, "ranged", shooter=True, damage_bias=0.2),
    "wolf": UnitProfile("wolf", "barbarian", 3, "flanker", retaliates_twice=True, speed_bias=0.25),
    "ogre": UnitProfile("ogre", "barbarian", 4, "tank", durability_bias=0.35),
    "ogre_lord": UnitProfile("ogre_lord", "barbarian", 4, "tank", durability_bias=0.45),
    "troll": UnitProfile("troll", "barbarian", 5, "ranged_tank", shooter=True, durability_bias=0.3, damage_bias=0.2),
    "war_troll": UnitProfile("war_troll", "barbarian", 5, "ranged_tank", shooter=True, durability_bias=0.4, damage_bias=0.35),
    "cyclops": UnitProfile("cyclops", "barbarian", 6, "siege", shooter=True, damage_bias=0.45),
    # Sorceress
    "sprite": UnitProfile("sprite", "sorceress", 1, "skirmisher", flying=True, no_enemy_retaliation=True, speed_bias=0.45),
    "dwarf": UnitProfile("dwarf", "sorceress", 2, "tank", durability_bias=0.45),
    "battle_dwarf": UnitProfile("battle_dwarf", "sorceress", 2, "tank", durability_bias=0.55),
    "elf": UnitProfile("elf", "sorceress", 3, "ranged", shooter=True, retaliates_twice=True, damage_bias=0.45),
    "grand_elf": UnitProfile("grand_elf", "sorceress", 3, "ranged", shooter=True, retaliates_twice=True, damage_bias=0.55),
    "druid": UnitProfile("druid", "sorceress", 4, "ranged", shooter=True, has_spellcast=True, damage_bias=0.3),
    "greater_druid": UnitProfile("greater_druid", "sorceress", 4, "ranged", shooter=True, has_spellcast=True, damage_bias=0.4),
    "unicorn": UnitProfile("unicorn", "sorceress", 5, "elite", speed_bias=0.2, durability_bias=0.25),
    "phoenix": UnitProfile("phoenix", "sorceress", 6, "finisher", flying=True, speed_bias=0.7, damage_bias=0.5),
    # Warlock
    "centaur": UnitProfile("centaur", "warlock", 1, "skirmisher", speed_bias=0.1),
    "gargoyle": UnitProfile("gargoyle", "warlock", 2, "screen", flying=True, speed_bias=0.2, durability_bias=0.1),
    "griffin": UnitProfile("griffin", "warlock", 3, "anchor", flying=True, retaliates_twice=True, speed_bias=0.25),
    "minotaur": UnitProfile("minotaur", "warlock", 4, "line", damage_bias=0.3, durability_bias=0.1),
    "minotaur_king": UnitProfile("minotaur_king", "warlock", 4, "line", damage_bias=0.45, durability_bias=0.2),
    "hydra": UnitProfile("hydra", "warlock", 5, "aoe", no_enemy_retaliation=True, durability_bias=0.4),
    "red_dragon": UnitProfile("red_dragon", "warlock", 6, "finisher", flying=True, no_enemy_retaliation=True, speed_bias=0.45, damage_bias=0.55),
    "black_dragon": UnitProfile("black_dragon", "warlock", 6, "finisher", flying=True, no_enemy_retaliation=True, speed_bias=0.55, damage_bias=0.65),
    # Wizard
    "halfling": UnitProfile("halfling", "wizard", 1, "ranged", shooter=True, damage_bias=0.1),
    "boar": UnitProfile("boar", "wizard", 2, "line", speed_bias=0.1),
    "iron_golem": UnitProfile("iron_golem", "wizard", 3, "tank", durability_bias=0.45),
    "steel_golem": UnitProfile("steel_golem", "wizard", 3, "tank", durability_bias=0.6),
    "roc": UnitProfile("roc", "wizard", 4, "dive", flying=True, speed_bias=0.3),
    "mage": UnitProfile("mage", "wizard", 5, "caster", shooter=True, has_spellcast=True, damage_bias=0.35),
    "archmage": UnitProfile("archmage", "wizard", 5, "caster", shooter=True, has_spellcast=True, damage_bias=0.45),
    "giant": UnitProfile("giant", "wizard", 6, "ranged_elite", shooter=True, durability_bias=0.35, damage_bias=0.35),
    "titan": UnitProfile("titan", "wizard", 6, "ranged_elite", shooter=True, durability_bias=0.5, damage_bias=0.5),
    # Necromancer
    "skeleton": UnitProfile("skeleton", "necromancer", 1, "swarm", speed_bias=-0.15),
    "zombie": UnitProfile("zombie", "necromancer", 2, "tank", speed_bias=-0.3, durability_bias=0.25),
    "mutant_zombie": UnitProfile("mutant_zombie", "necromancer", 2, "tank", speed_bias=-0.2, durability_bias=0.35),
    "mummy": UnitProfile("mummy", "necromancer", 3, "line", durability_bias=0.2),
    "royal_mummy": UnitProfile("royal_mummy", "necromancer", 3, "line", durability_bias=0.3),
    "vampire": UnitProfile("vampire", "necromancer", 4, "drain", flying=True, no_enemy_retaliation=True, speed_bias=0.35, damage_bias=0.25),
    "vampire_lord": UnitProfile("vampire_lord", "necromancer", 4, "drain", flying=True, no_enemy_retaliation=True, speed_bias=0.45, damage_bias=0.35),
    "lich": UnitProfile("lich", "necromancer", 5, "caster", shooter=True, has_spellcast=True, damage_bias=0.45),
    "power_lich": UnitProfile("power_lich", "necromancer", 5, "caster", shooter=True, has_spellcast=True, damage_bias=0.55),
    "bone_dragon": UnitProfile("bone_dragon", "necromancer", 6, "terror", flying=True, speed_bias=0.2, damage_bias=0.25),
    # Common neutrals
    "rogue": UnitProfile("rogue", "neutral", 2, "scout", speed_bias=0.3),
    "nomad": UnitProfile("nomad", "neutral", 4, "charger", speed_bias=0.3, damage_bias=0.2),
    "ghost": UnitProfile("ghost", "neutral", 4, "drain", flying=True, no_enemy_retaliation=True, speed_bias=0.35),
    "genie": UnitProfile("genie", "neutral", 5, "caster", flying=True, has_spellcast=True, speed_bias=0.35, damage_bias=0.35),
    "medusa": UnitProfile("medusa", "neutral", 4, "ranged", shooter=True, has_spellcast=True, damage_bias=0.3),
    "earth_elemental": UnitProfile("earth_elemental", "neutral", 5, "tank", speed_bias=-0.4, durability_bias=0.7),
    "air_elemental": UnitProfile("air_elemental", "neutral", 5, "skirmisher", speed_bias=0.5, damage_bias=0.15),
    "fire_elemental": UnitProfile("fire_elemental", "neutral", 5, "striker", speed_bias=0.2, damage_bias=0.45),
    "water_elemental": UnitProfile("water_elemental", "neutral", 5, "balanced", speed_bias=0.1, durability_bias=0.1, damage_bias=0.1),
}


def unit_profile(name: str) -> UnitProfile | None:
    return UNIT_INDEX.get(name.strip().lower().replace(" ", "_"))
