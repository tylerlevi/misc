from __future__ import annotations

from random import Random

from .automation import UiCommander
from .bot import DominatorBot
from .macro import MacroPlanner, MacroWeights
from .micro import MicroPlanner, MicroWeights
from .models import AdventureAction, AdventureState, ArmyStack, CombatState


class EvolutionTuner:
    """Simple evolutionary tuner to steadily improve weight vectors from self-play proxies."""

    def __init__(self, seed: int = 7):
        self._rng = Random(seed)

    def improve(self, base_bot: DominatorBot, generations: int = 20, sigma: float = 0.08) -> DominatorBot:
        champion = base_bot
        champion_score = self._fitness(champion)

        for _ in range(generations):
            challenger = self._mutate(champion, sigma)
            challenger_score = self._fitness(challenger)
            if challenger_score > champion_score:
                champion = challenger
                champion_score = challenger_score
        return champion

    def _mutate(self, bot: DominatorBot, sigma: float) -> DominatorBot:
        macro = bot.macro.weights
        micro = bot.micro.weights
        mutated_macro = MacroWeights(
            economy=max(0.1, macro.economy + self._rng.gauss(0, sigma)),
            tempo=max(0.1, macro.tempo + self._rng.gauss(0, sigma)),
            safety=max(0.1, macro.safety + self._rng.gauss(0, sigma)),
            snowball=max(0.1, macro.snowball + self._rng.gauss(0, sigma)),
            risk_penalty=max(0.1, macro.risk_penalty + self._rng.gauss(0, sigma * 0.8)),
        )
        mutated_micro = MicroWeights(
            attrition=max(0.1, micro.attrition + self._rng.gauss(0, sigma)),
            morale=max(0.05, micro.morale + self._rng.gauss(0, sigma)),
            speed_bonus=max(0.05, micro.speed_bonus + self._rng.gauss(0, sigma)),
            target_priority=max(0.05, micro.target_priority + self._rng.gauss(0, sigma)),
            trade_efficiency=max(0.05, micro.trade_efficiency + self._rng.gauss(0, sigma)),
        )

        return DominatorBot(
            macro=MacroPlanner(depth=bot.macro.depth, beam_width=bot.macro.beam_width, weights=mutated_macro),
            micro=MicroPlanner(depth=bot.micro.depth, weights=mutated_micro),
            ui=UiCommander(layout=bot.ui.layout),
            strategy=bot.strategy,
        )

    def _fitness(self, bot: DominatorBot) -> float:
        scenarios = [
            self._macro_opening(bot),
            self._macro_midgame_pressure(bot),
            self._micro_remove_shooter(bot),
            self._micro_finish_dragon(bot),
        ]
        return sum(scenarios)

    def _macro_opening(self, bot: DominatorBot) -> float:
        state = AdventureState(
            day=3,
            movement_points=22,
            gold=3500,
            wood=9,
            ore=7,
            hero_level=3,
            owned_towns=1,
            artifacts_score=0.8,
            map_control=2.1,
            army=(
                ArmyStack("swordsman", 14, 8, 9, 3, 4, 35, 5),
                ArmyStack("archer", 24, 6, 3, 2, 3, 10, 4),
            ),
        )
        actions = (
            AdventureAction("take_mine", value_gain=1.8, movement_cost=7, risk=0.1),
            AdventureAction("fight_guard", value_gain=2.8, movement_cost=12, risk=0.35),
            AdventureAction("pickup_chest", value_gain=1.1, movement_cost=5, risk=0.05),
        )
        return 4.0 if bot.pick_adventure_action(state, actions).kind == "fight_guard" else 0.0

    def _macro_midgame_pressure(self, bot: DominatorBot) -> float:
        state = AdventureState(
            day=15,
            movement_points=17,
            gold=7800,
            wood=4,
            ore=2,
            hero_level=7,
            owned_towns=2,
            artifacts_score=2.5,
            map_control=4.2,
            army=(ArmyStack("champion", 9, 10, 9, 5, 10, 100, 7), ArmyStack("ranger", 30, 6, 3, 2, 3, 10, 4)),
        )
        actions = (
            AdventureAction("take_town", value_gain=3.8, movement_cost=12, risk=0.45),
            AdventureAction("recruit", value_gain=1.7, movement_cost=6, risk=0.08),
            AdventureAction("pickup_chest", value_gain=0.9, movement_cost=4, risk=0.02),
        )
        return 5.0 if bot.pick_adventure_action(state, actions).kind in {"take_town", "recruit"} else 0.0

    def _micro_remove_shooter(self, bot: DominatorBot) -> float:
        state = CombatState(
            friendly=(ArmyStack("griffin", 12, 8, 8, 3, 6, 25, 6),),
            enemy=(ArmyStack("orc", 40, 3, 4, 2, 3, 15, 4), ArmyStack("ogre", 10, 9, 7, 6, 12, 40, 4)),
            turn=0,
            morale=0.05,
        )
        pick = bot.pick_combat_action(state)
        return 4.0 if pick.kind == "attack" and pick.target == 0 else 0.0

    def _micro_finish_dragon(self, bot: DominatorBot) -> float:
        state = CombatState(
            friendly=(ArmyStack("titan", 5, 12, 10, 20, 30, 300, 6),),
            enemy=(ArmyStack("black_dragon", 2, 14, 14, 25, 50, 300, 15),),
            turn=0,
            morale=0.0,
        )
        pick = bot.pick_combat_action(state)
        bonus = 2.0 if pick.kind == "attack" else 0.0
        bonus += bot.micro.evaluate(state) * 0.001
        return bonus
