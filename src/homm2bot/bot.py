from __future__ import annotations

from dataclasses import dataclass

from .automation import AdventureSnapshot, LowLevelCommand, UiCommander
from .macro import MacroPlanner, MacroWeights
from .micro import MicroPlanner, MicroWeights
from .models import AdventureAction, AdventureState, ArmyStack, CombatAction, CombatState
from .strategy import RiskReport, StrategyAdvisor


@dataclass
class DominatorBot:
    """Combined macro + micro planner tuned for aggressive snowball play."""

    macro: MacroPlanner
    micro: MicroPlanner
    ui: UiCommander
    strategy: StrategyAdvisor

    @classmethod
    def default(cls) -> "DominatorBot":
        return cls(
            macro=MacroPlanner(depth=5, beam_width=9, weights=MacroWeights(1.15, 0.95, 0.9, 1.55, 0.55)),
            micro=MicroPlanner(depth=4, weights=MicroWeights(attrition=1.2, morale=0.22, speed_bonus=0.24, target_priority=0.45, trade_efficiency=0.4)),
            ui=UiCommander(),
            strategy=StrategyAdvisor(),
        )

    def pick_adventure_action(
        self,
        state: AdventureState,
        actions: tuple[AdventureAction, ...],
    ) -> AdventureAction:
        return self.macro.choose(state, actions)

    def pick_combat_action(self, state: CombatState) -> CombatAction:
        return self.micro.choose(state)

    def plan_turn_commands(
        self,
        snapshot: AdventureSnapshot,
        target_map_xy: tuple[float, float],
    ) -> tuple[LowLevelCommand, ...]:
        return self.ui.synthesize_turn_commands(snapshot, target_map_xy)

    def assess_engagement_risk(
        self,
        friendly: tuple[ArmyStack, ...],
        enemy: tuple[ArmyStack, ...],
    ) -> RiskReport:
        return self.strategy.combat_risk(friendly, enemy)
