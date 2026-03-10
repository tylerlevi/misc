from __future__ import annotations

from dataclasses import dataclass

from .automation import AdventureSnapshot, LowLevelCommand, UiCommander
from .macro import MacroPlanner, MacroWeights
from .micro import MicroPlanner, MicroWeights
from .models import AdventureAction, AdventureState, ArmyStack, CombatAction, CombatState
from .performance import GameResult, ImprovementCoach, PerformanceSummary, PerformanceTracker
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
        """Powerhouse baseline from game 1; no warmup needed."""
        return cls(
            macro=MacroPlanner(depth=6, beam_width=11, weights=MacroWeights(1.2, 1.0, 0.95, 1.65, 0.5)),
            micro=MicroPlanner(
                depth=5,
                weights=MicroWeights(attrition=1.25, morale=0.24, speed_bonus=0.26, target_priority=0.5, trade_efficiency=0.45),
            ),
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

    def with_learning_from_history(
        self,
        tracker: PerformanceTracker,
        coach: ImprovementCoach | None = None,
    ) -> tuple["DominatorBot", PerformanceSummary]:
        """Apply conservative long-horizon nudges from aggregate historical performance."""
        coach = coach or ImprovementCoach()
        summary = tracker.summarize(window=40)
        trend = tracker.win_rate_trend(window=20)

        nudged_macro = coach.nudge_macro(self.macro.weights, summary, trend=trend)
        nudged_micro = coach.nudge_micro(self.micro.weights, summary, trend=trend)

        learned = DominatorBot(
            macro=MacroPlanner(depth=self.macro.depth, beam_width=self.macro.beam_width, weights=nudged_macro),
            micro=MicroPlanner(depth=self.micro.depth, weights=nudged_micro),
            ui=self.ui,
            strategy=self.strategy,
        )
        return learned, summary

    def record_game_result(self, tracker: PerformanceTracker, result: GameResult) -> None:
        tracker.append_result(result)
