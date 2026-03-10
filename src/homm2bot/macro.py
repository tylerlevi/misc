from __future__ import annotations

from dataclasses import dataclass

from .models import AdventureAction, AdventureState, total_power
from .strategy import StrategyAdvisor


ACTION_PRIOR = {
    "fight_guard": 1.7,
    "take_town": 1.7,
    "take_mine": 1.25,
    "flag_sawmill": 1.2,
    "pickup_chest": 1.05,
    "recruit": 1.35,
    "retreat": 0.35,
}


@dataclass(frozen=True)
class MacroWeights:
    economy: float = 1.0
    tempo: float = 0.8
    safety: float = 0.9
    snowball: float = 1.35
    risk_penalty: float = 0.55


class MacroPlanner:
    """Beam search planner for adventure-map macro decisions."""

    def __init__(self, depth: int = 3, beam_width: int = 5, weights: MacroWeights | None = None):
        self.depth = depth
        self.beam_width = beam_width
        self.weights = weights or MacroWeights()
        self.strategy = StrategyAdvisor()

    def choose(self, state: AdventureState, actions: tuple[AdventureAction, ...]) -> AdventureAction:
        if not actions:
            raise ValueError("actions cannot be empty")

        filtered_actions = actions
        if len(actions) > 1:
            non_retreat = tuple(action for action in actions if action.kind != "retreat")
            if non_retreat:
                filtered_actions = non_retreat

        beam: list[tuple[AdventureState, list[AdventureAction], float]] = [(state, [], self.evaluate(state))]
        for _ in range(self.depth):
            candidates: list[tuple[AdventureState, list[AdventureAction], float]] = []
            for current_state, path, _ in beam:
                for action in filtered_actions:
                    if action.movement_cost > current_state.movement_points:
                        continue
                    next_state = current_state.apply(action)
                    value = self.evaluate(next_state)
                    value += self._action_bonus(action, current_state)
                    candidates.append((next_state, [*path, action], value))
            if not candidates:
                break
            candidates.sort(key=lambda row: row[2], reverse=True)
            beam = candidates[: self.beam_width]

        best_path = max(beam, key=lambda row: row[2])[1]
        return best_path[0] if best_path else filtered_actions[0]

    def _action_bonus(self, action: AdventureAction, state: AdventureState) -> float:
        prior = ACTION_PRIOR.get(action.kind, 1.0)
        low_mp_penalty = 0.0
        if state.movement_points < 8 and action.movement_cost > 6:
            low_mp_penalty = 250

        risk_penalty = action.risk * self.weights.risk_penalty * 900
        momentum_reward = action.value_gain * 450 * prior
        retreat_penalty = 1400 if action.kind == "retreat" else 0
        strategic = self.strategy.strategic_action_score(state, action)
        return momentum_reward - risk_penalty - low_mp_penalty - retreat_penalty + strategic

    def evaluate(self, state: AdventureState) -> float:
        economy_value = state.gold + state.wood * 220 + state.ore * 220
        map_value = state.map_control * 1350 + state.owned_towns * 2600
        progression = state.hero_level * 760 + state.artifacts_score * 900
        army_value = total_power(state.army) * self.weights.snowball

        return (
            self.weights.economy * economy_value
            + self.weights.tempo * map_value
            + self.weights.safety * progression
            + army_value
        )
