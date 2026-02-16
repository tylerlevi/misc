from __future__ import annotations

from .automation import AdventureSnapshot, HeroArmyState, TownState
from .bot import DominatorBot
from .models import AdventureAction, AdventureState, ArmyStack, CombatState
from .strategy import MovementOption
from .training import EvolutionTuner
from .units import UNIT_INDEX


def main() -> None:
    bot = DominatorBot.default()
    improved = EvolutionTuner(seed=42).improve(bot, generations=30)

    adventure_state = AdventureState(
        day=2,
        movement_points=24,
        gold=3000,
        wood=8,
        ore=8,
        hero_level=3,
        owned_towns=1,
        artifacts_score=1.0,
        map_control=1.8,
        army=(ArmyStack("pikeman", 30, 4, 5, 1, 3, 12, 4),),
    )
    adventure_actions = (
        AdventureAction("fight_guard", value_gain=2.3, movement_cost=10, risk=0.25),
        AdventureAction("take_mine", value_gain=1.4, movement_cost=6, risk=0.08),
        AdventureAction("flag_sawmill", value_gain=1.0, movement_cost=5, risk=0.03),
    )

    combat_state = CombatState(
        friendly=(ArmyStack("pikeman", 30, 4, 5, 1, 3, 12, 4),),
        enemy=(ArmyStack("wolf", 24, 6, 4, 2, 3, 8, 6),),
        turn=0,
        morale=0.0,
    )

    next_adv = improved.pick_adventure_action(adventure_state, adventure_actions)
    next_fight = improved.pick_combat_action(combat_state)

    risk = improved.assess_engagement_risk(combat_state.friendly, combat_state.enemy)
    econ = improved.strategy.economy_projection(adventure_state, controlled_sites=("gold_mine", "sawmill", "ore_pit"))

    snapshot = AdventureSnapshot(
        state=adventure_state,
        actions=adventure_actions,
        town=TownState(
            available_builds=("marketplace", "dwelling_lvl1", "town_hall"),
            gold=7900,
            wood=5,
            ore=5,
            current_day=1,
        ),
        hero_army=HeroArmyState(
            stacks=(
                ArmyStack("pikeman", 50, 4, 5, 1, 3, 12, 4),
                ArmyStack("archer", 12, 6, 3, 2, 3, 10, 4),
            )
        ),
        visible_labels=("gold mine", "treasure chest", "neutral guard"),
        movement_options=(
            MovementOption(0.61, 0.44, "gold_mine_path", reward=3.8, risk=0.25, movement_cost=11, guarded=True, on_road=True, fog_reveal=0.3),
            MovementOption(0.52, 0.48, "chest_pickup", reward=1.4, risk=0.05, movement_cost=6, guarded=False, on_road=False, fog_reveal=0.1),
            MovementOption(0.67, 0.39, "scout_fog", reward=0.9, risk=0.02, movement_cost=7, guarded=False, on_road=True, fog_reveal=0.9),
        ),
    )
    turn_commands = improved.plan_turn_commands(snapshot, target_map_xy=(0.56, 0.47))

    print(f"Adventure action: {next_adv.kind}")
    print(f"Combat action: {next_fight.kind}, target={next_fight.target}")
    print(f"Known unit profiles: {len(UNIT_INDEX)}")
    print(f"Risk win probability: {risk.win_probability:.2%}, expected loss ratio: {risk.expected_army_loss_ratio:.2%}")
    print(f"Projected weekly gold: {econ.weekly_gold}, wood/day: {econ.wood_per_day}, ore/day: {econ.ore_per_day}")
    print(f"Synthesized UI commands: {len(turn_commands)}")
    for command in turn_commands[:5]:
        print(f"- {command.op} {command.arg} @ {command.at}")


if __name__ == "__main__":
    main()
