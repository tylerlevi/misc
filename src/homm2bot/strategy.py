from __future__ import annotations

from dataclasses import dataclass
import math

from .domain_data import OBJECT_VALUE_PRIORS
from .models import AdventureAction, AdventureState, ArmyStack, total_power
from .units import unit_profile

# Data aligned with fheroes2 sources (buildinginfo.cpp, profit.cpp, monster_info.cpp).
BUILD_COST_GOLD: dict[str, int] = {
    "marketplace": 500,
    "town_hall": 2500,
    "city_hall": 5000,
    "capitol": 10000,
    "castle": 5000,
    "mage_guild_1": 2000,
}

# Gold/day incomes (village baseline + upgrades and economy structures).
BUILD_DAILY_INCOME_GOLD: dict[str, int] = {
    "village_hall": 500,
    "town_hall": 1000,
    "city_hall": 2000,
    "capitol": 4000,
    "statue": 250,
    "special_warlock": 500,
}

# Mines from fheroes2 profit.cpp.
MINE_DAILY_INCOME: dict[str, tuple[int, int, int]] = {
    "gold_mine": (1000, 0, 0),
    "sawmill": (0, 2, 0),
    "ore_pit": (0, 0, 2),
}

# High-impact unit economic data for cost-efficiency comparisons.
# (gold_cost, base_weekly_growth)
UNIT_ECON_DATA: dict[str, tuple[int, int]] = {
    "archer": (150, 8),
    "ranger": (200, 8),
    "pikeman": (200, 5),
    "swordsman": (300, 4),
    "orc": (150, 8),
    "wolf": (200, 5),
    "elf": (250, 4),
    "grand_elf": (300, 4),
    "griffin": (300, 4),
    "minotaur_king": (500, 3),
    "vampire_lord": (650, 3),
    "titan": (5000, 1),
    "black_dragon": (4000, 1),
}


@dataclass(frozen=True)
class RiskReport:
    win_probability: float
    expected_army_loss_ratio: float
    pressure_score: float


@dataclass(frozen=True)
class EconomyReport:
    daily_gold: int
    weekly_gold: int
    wood_per_day: int
    ore_per_day: int


@dataclass(frozen=True)
class MovementOption:
    normalized_x: float
    normalized_y: float
    label: str
    reward: float
    risk: float
    movement_cost: int
    guarded: bool = False
    on_road: bool = False
    fog_reveal: float = 0.0
    object_key: str = "unknown"


class StrategyAdvisor:
    """High-level strategy + risk engine using game data and combat math."""

    def economy_projection(self, state: AdventureState, controlled_sites: tuple[str, ...] = ()) -> EconomyReport:
        daily_gold = BUILD_DAILY_INCOME_GOLD["village_hall"]
        wood = 0
        ore = 0

        for site in controlled_sites:
            g, w, o = MINE_DAILY_INCOME.get(site, (0, 0, 0))
            daily_gold += g
            wood += w
            ore += o

        if state.owned_towns >= 2:
            daily_gold += 750

        return EconomyReport(daily_gold=daily_gold, weekly_gold=daily_gold * 7, wood_per_day=wood, ore_per_day=ore)

    def building_roi_days(self, building: str, current_daily_gold: int) -> float:
        build_cost = BUILD_COST_GOLD.get(building, 999999)
        uplift = max(1, BUILD_DAILY_INCOME_GOLD.get(building, current_daily_gold) - current_daily_gold)
        return build_cost / uplift

    def object_base_value(self, object_key: str) -> float:
        return OBJECT_VALUE_PRIORS.get(object_key, OBJECT_VALUE_PRIORS["unknown"])

    def unit_gold_efficiency(self, stack: ArmyStack) -> float:
        profile = unit_profile(stack.name)
        gold_cost, growth = UNIT_ECON_DATA.get(stack.name.lower(), (200, 4))
        role_mult = 1.0
        if profile:
            if profile.shooter:
                role_mult += 0.2
            if profile.flying:
                role_mult += 0.12
            if profile.has_spellcast:
                role_mult += 0.15
            if profile.no_enemy_retaliation:
                role_mult += 0.1
        return (stack.power / max(1, gold_cost)) * role_mult * (1 + growth / 20)

    def combat_risk(self, friendly: tuple[ArmyStack, ...], enemy: tuple[ArmyStack, ...]) -> RiskReport:
        friendly_power = total_power(friendly)
        enemy_power = total_power(enemy)
        power_ratio = friendly_power / max(1.0, enemy_power)

        friendly_speed = sum(s.speed * s.count for s in friendly)
        enemy_speed = sum(s.speed * s.count for s in enemy)
        speed_ratio = (friendly_speed + 1) / (enemy_speed + 1)

        ranged_edge = self._ranged_weight(friendly) - self._ranged_weight(enemy)
        pressure = math.log(max(0.2, power_ratio), 1.7) + 0.12 * (speed_ratio - 1) + ranged_edge * 0.08

        win_probability = 1 / (1 + math.exp(-3.2 * pressure))
        expected_loss = max(0.02, min(0.95, 1.0 - win_probability * min(1.0, power_ratio)))
        return RiskReport(win_probability=win_probability, expected_army_loss_ratio=expected_loss, pressure_score=pressure)

    def choose_movement_option(self, state: AdventureState, options: tuple[MovementOption, ...]) -> MovementOption | None:
        if not options:
            return None
        best = None
        best_score = float("-inf")
        for option in options:
            if option.movement_cost > state.movement_points:
                continue
            scouting_bonus = option.fog_reveal * 120
            road_bonus = 180 if option.on_road else 0
            guard_penalty = 220 if option.guarded else 0
            object_bonus = self.object_base_value(option.object_key) * 140
            move_eff = option.reward / max(1.0, option.movement_cost)
            score = option.reward * 320 + move_eff * 220 + scouting_bonus + road_bonus + object_bonus - option.risk * 620 - guard_penalty
            if score > best_score:
                best_score = score
                best = option
        return best

    def strategic_action_score(self, state: AdventureState, action: AdventureAction) -> float:
        early_game = state.day <= 7
        tempo_weight = 1.35 if early_game else 1.0
        econ_weight = 1.2 if action.kind in {"take_mine", "take_town", "recruit"} else 1.0

        risk = action.risk
        if action.kind == "fight_guard":
            risk *= 1.1

        move_efficiency = action.value_gain / max(1, action.movement_cost)
        return action.value_gain * 350 * tempo_weight * econ_weight + move_efficiency * 250 - risk * 520

    def _ranged_weight(self, stacks: tuple[ArmyStack, ...]) -> float:
        weight = 0.0
        for stack in stacks:
            profile = unit_profile(stack.name)
            if profile and profile.shooter:
                weight += stack.count * 0.6
                if profile.has_spellcast:
                    weight += stack.count * 0.2
        return weight
