from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from statistics import mean

from .macro import MacroWeights
from .micro import MicroWeights


@dataclass(frozen=True)
class GameResult:
    won: bool
    score_delta: float
    turns: int
    towns_controlled: int
    final_army_power: float
    losses_ratio: float


@dataclass(frozen=True)
class PerformanceSummary:
    games: int
    win_rate: float
    avg_score_delta: float
    avg_turns: float
    avg_losses_ratio: float


class PerformanceTracker:
    """Stores multi-game performance and derives stable aggregate signals."""

    def __init__(self, store_path: str = "data/performance_history.json"):
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

    def load_results(self) -> list[GameResult]:
        if not self.store_path.exists():
            return []
        payload = json.loads(self.store_path.read_text())
        return [GameResult(**row) for row in payload]

    def append_result(self, result: GameResult) -> None:
        rows = self.load_results()
        rows.append(result)
        self.store_path.write_text(json.dumps([asdict(row) for row in rows], indent=2))

    def summarize(self, window: int = 40) -> PerformanceSummary:
        rows = self.load_results()
        if not rows:
            return PerformanceSummary(games=0, win_rate=0.0, avg_score_delta=0.0, avg_turns=0.0, avg_losses_ratio=1.0)

        scope = rows[-window:]
        wins = sum(1 for row in scope if row.won)
        return PerformanceSummary(
            games=len(scope),
            win_rate=wins / len(scope),
            avg_score_delta=mean(row.score_delta for row in scope),
            avg_turns=mean(row.turns for row in scope),
            avg_losses_ratio=mean(row.losses_ratio for row in scope),
        )

    def win_rate_trend(self, window: int = 20) -> float:
        """Recent-half win rate minus previous-half win rate."""
        rows = self.load_results()
        if len(rows) < window * 2:
            return 0.0
        recent = rows[-window:]
        previous = rows[-window * 2 : -window]
        recent_rate = sum(1 for row in recent if row.won) / len(recent)
        prev_rate = sum(1 for row in previous if row.won) / len(previous)
        return recent_rate - prev_rate


class ImprovementCoach:
    """Applies small, stable weight nudges based on rolling performance metrics."""

    def nudge_macro(self, base: MacroWeights, summary: PerformanceSummary, trend: float = 0.0) -> MacroWeights:
        if summary.games < 12:
            return base

        win_gap = 0.62 - summary.win_rate
        speed_gap = summary.avg_turns - 20.0
        trend_dampen = 1.0 - max(0.0, trend)

        economy = max(0.2, base.economy + 0.04 * win_gap * trend_dampen)
        tempo = max(0.2, base.tempo + 0.025 * speed_gap / 10.0)
        safety = max(0.2, base.safety + 0.05 * summary.avg_losses_ratio)
        snowball = max(0.2, base.snowball + 0.035 * win_gap * trend_dampen)
        risk_penalty = max(0.1, base.risk_penalty + 0.045 * summary.avg_losses_ratio - 0.025 * summary.win_rate)
        return MacroWeights(economy=economy, tempo=tempo, safety=safety, snowball=snowball, risk_penalty=risk_penalty)

    def nudge_micro(self, base: MicroWeights, summary: PerformanceSummary, trend: float = 0.0) -> MicroWeights:
        if summary.games < 12:
            return base

        loss_gap = summary.avg_losses_ratio - 0.34
        win_gap = 0.62 - summary.win_rate
        trend_dampen = 1.0 - max(0.0, trend)

        attrition = max(0.1, base.attrition + 0.04 * win_gap * trend_dampen)
        morale = max(0.05, base.morale + 0.018 * loss_gap)
        speed_bonus = max(0.05, base.speed_bonus + 0.018 * win_gap * trend_dampen)
        target_priority = max(0.05, base.target_priority + 0.035 * win_gap * trend_dampen)
        trade_efficiency = max(0.05, base.trade_efficiency + 0.045 * loss_gap)

        return MicroWeights(
            attrition=attrition,
            morale=morale,
            speed_bonus=speed_bonus,
            target_priority=target_priority,
            trade_efficiency=trade_efficiency,
        )
