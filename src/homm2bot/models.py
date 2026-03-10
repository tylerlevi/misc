from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

from .units import unit_profile


@dataclass(frozen=True)
class ArmyStack:
    name: str
    count: int
    attack: int
    defense: int
    min_damage: int
    max_damage: int
    hp: int
    speed: int

    @property
    def power(self) -> float:
        avg_damage = (self.min_damage + self.max_damage) / 2
        profile = unit_profile(self.name)
        role_bonus = 1.0
        if profile:
            role_bonus += profile.damage_bias * 0.45
            role_bonus += profile.durability_bias * 0.3
            role_bonus += profile.speed_bias * 0.25
            if profile.shooter:
                role_bonus += 0.08
            if profile.flying:
                role_bonus += 0.05
            if profile.retaliates_twice:
                role_bonus += 0.07
            if profile.no_enemy_retaliation:
                role_bonus += 0.08
            if profile.has_spellcast:
                role_bonus += 0.06

        baseline = avg_damage + self.attack * 0.4 + self.defense * 0.3 + self.hp * 0.08 + self.speed * 0.2
        return self.count * baseline * role_bonus


@dataclass(frozen=True)
class AdventureAction:
    kind: str
    value_gain: float = 0.0
    movement_cost: int = 0
    risk: float = 0.0


@dataclass(frozen=True)
class AdventureState:
    day: int
    movement_points: int
    gold: int
    wood: int
    ore: int
    hero_level: int
    owned_towns: int
    artifacts_score: float
    map_control: float
    army: tuple[ArmyStack, ...] = field(default_factory=tuple)

    def apply(self, action: AdventureAction) -> "AdventureState":
        remaining_mp = max(0, self.movement_points - action.movement_cost)
        gold_delta = int(action.value_gain * 125)
        map_delta = action.value_gain * 0.5 - action.risk * 0.3
        level_up = 1 if action.kind == "fight_guard" and action.value_gain > 2 else 0
        return replace(
            self,
            movement_points=remaining_mp,
            gold=max(0, self.gold + gold_delta),
            hero_level=self.hero_level + level_up,
            map_control=max(0.0, self.map_control + map_delta),
            artifacts_score=max(0.0, self.artifacts_score + action.value_gain * 0.1),
        )


@dataclass(frozen=True)
class CombatAction:
    kind: str
    target: int | None = None
    aggression: float = 0.5


@dataclass(frozen=True)
class CombatState:
    friendly: tuple[ArmyStack, ...]
    enemy: tuple[ArmyStack, ...]
    turn: int
    morale: float = 0.0

    def legal_actions(self) -> tuple[CombatAction, ...]:
        actions: list[CombatAction] = [CombatAction(kind="wait", aggression=0.1)]
        for idx, stack in enumerate(self.enemy):
            if stack.count > 0:
                actions.append(CombatAction(kind="attack", target=idx, aggression=0.8))
        actions.append(CombatAction(kind="defend", aggression=0.2))
        return tuple(actions)

    def score(self) -> float:
        friendly_power = sum(stack.power for stack in self.friendly)
        enemy_power = sum(stack.power for stack in self.enemy)
        return friendly_power - enemy_power + self.morale * 40

    def resolve(self, action: CombatAction) -> "CombatState":
        if action.kind == "wait":
            return replace(self, turn=self.turn + 1, morale=self.morale + 0.02)

        if action.kind == "defend":
            return replace(self, turn=self.turn + 1, morale=self.morale + 0.03)

        if action.kind == "attack" and action.target is not None:
            enemy = list(self.enemy)
            if 0 <= action.target < len(enemy):
                target = enemy[action.target]
                if target.count > 0 and self.friendly:
                    friendly_dps = max(1.0, sum(stack.power for stack in self.friendly) / 120)
                    kills = max(1, int(friendly_dps / max(1, target.hp * 0.5)))
                    enemy[action.target] = replace(target, count=max(0, target.count - kills))
            return replace(self, enemy=tuple(enemy), turn=self.turn + 1, morale=self.morale + 0.01)

        return replace(self, turn=self.turn + 1)


def total_power(stacks: Iterable[ArmyStack]) -> float:
    return sum(stack.power for stack in stacks)
