from __future__ import annotations

from dataclasses import dataclass

from .models import CombatAction, CombatState
from .units import unit_profile


@dataclass(frozen=True)
class MicroWeights:
    attrition: float = 1.15
    morale: float = 0.25
    speed_bonus: float = 0.2
    target_priority: float = 0.4
    trade_efficiency: float = 0.35


class MicroPlanner:
    """Depth-limited alpha-beta search over combat action choices."""

    def __init__(self, depth: int = 3, weights: MicroWeights | None = None):
        self.depth = depth
        self.weights = weights or MicroWeights()

    def choose(self, state: CombatState) -> CombatAction:
        best_action: CombatAction | None = None
        best_score = float("-inf")

        for action in state.legal_actions():
            score = self._min_value(state.resolve(action), self.depth - 1, float("-inf"), float("inf"))
            score += self._action_heuristic(state, action)
            if score > best_score:
                best_score = score
                best_action = action

        if best_action is None:
            raise RuntimeError("No legal action available")
        return best_action

    def _action_heuristic(self, state: CombatState, action: CombatAction) -> float:
        if action.kind != "attack" or action.target is None:
            return -8.0 if action.kind == "wait" else 0.0
        if action.target < 0 or action.target >= len(state.enemy):
            return 0.0

        target = state.enemy[action.target]
        profile = unit_profile(target.name)

        threat_weight = 1.0
        if profile:
            if profile.shooter:
                threat_weight += 1.2
            if profile.has_spellcast:
                threat_weight += 0.6
            if profile.flying:
                threat_weight += 0.2
            if profile.role in {"finisher", "caster", "ranged_elite"}:
                threat_weight += 0.25

        expected_kills = self._expected_kills(state, action.target)
        trade_score = expected_kills * target.hp * self.weights.trade_efficiency

        retaliation_risk = 0.0
        if profile and not profile.no_enemy_retaliation:
            retaliation_risk = target.power * 0.015

        threat_component = (target.power ** 0.5) * (threat_weight**2) * self.weights.target_priority
        shooter_focus = 12.0 if profile and profile.shooter else 0.0
        caster_focus = 6.0 if profile and profile.has_spellcast else 0.0
        return threat_component + shooter_focus + caster_focus + trade_score - retaliation_risk

    def _expected_kills(self, state: CombatState, target_index: int) -> float:
        if not (0 <= target_index < len(state.enemy)):
            return 0.0
        target = state.enemy[target_index]
        friendly_dps = max(1.0, sum(stack.power for stack in state.friendly) / 120)
        return max(1.0, friendly_dps / max(1.0, target.hp * 0.5))

    def _max_value(self, state: CombatState, depth: int, alpha: float, beta: float) -> float:
        if depth == 0:
            return self.evaluate(state)
        value = float("-inf")
        for action in state.legal_actions():
            value = max(value, self._min_value(state.resolve(action), depth - 1, alpha, beta))
            if value >= beta:
                return value
            alpha = max(alpha, value)
        return value

    def _min_value(self, state: CombatState, depth: int, alpha: float, beta: float) -> float:
        if depth == 0:
            return self.evaluate(state)
        value = float("inf")
        for action in state.legal_actions():
            value = min(value, self._max_value(state.resolve(action), depth - 1, alpha, beta))
            if value <= alpha:
                return value
            beta = min(beta, value)
        return value

    def evaluate(self, state: CombatState) -> float:
        speed = sum(stack.speed * stack.count for stack in state.friendly)
        speed -= sum(stack.speed * stack.count for stack in state.enemy)

        return (
            state.score() * self.weights.attrition
            + state.morale * 100 * self.weights.morale
            + speed * self.weights.speed_bonus
        )
