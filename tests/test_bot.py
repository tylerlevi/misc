from pathlib import Path

from homm2bot.automation import AdventureSnapshot, HeroArmyState, TownState
from homm2bot.bot import DominatorBot
from homm2bot.models import AdventureAction, AdventureState, ArmyStack, CombatAction, CombatState
from homm2bot.performance import GameResult, PerformanceTracker
from homm2bot.strategy import MovementOption
from homm2bot.training import EvolutionTuner
from homm2bot.units import unit_profile
from homm2bot.vision_knowledge import lookup_visual_signature


def sample_adv_state() -> AdventureState:
    return AdventureState(
        day=1,
        movement_points=20,
        gold=2000,
        wood=5,
        ore=5,
        hero_level=2,
        owned_towns=1,
        artifacts_score=0.4,
        map_control=1.1,
        army=(ArmyStack("archer", 20, 6, 3, 2, 3, 10, 4),),
    )


def test_unit_encyclopedia_has_known_homm2_units() -> None:
    assert unit_profile("black dragon") is not None
    assert unit_profile("grand elf") is not None
    assert unit_profile("titan") is not None


def test_visual_knowledge_knows_core_objects() -> None:
    assert lookup_visual_signature("gold mine") is not None
    assert lookup_visual_signature("castle button") is not None




def test_visual_alias_for_resource_gold() -> None:
    sig = lookup_visual_signature("gold")
    assert sig is not None
    assert sig.key == "resource_gold"

def test_macro_prefers_progress_actions_over_low_impact_play() -> None:
    bot = DominatorBot.default()
    state = sample_adv_state()
    actions = (
        AdventureAction("take_mine", value_gain=1.0, movement_cost=6, risk=0.1),
        AdventureAction("fight_guard", value_gain=3.3, movement_cost=9, risk=0.28),
        AdventureAction("retreat", value_gain=0.1, movement_cost=1, risk=0.01),
    )

    chosen = bot.pick_adventure_action(state, actions)
    assert chosen.kind in {"fight_guard", "take_mine"}


def test_micro_heuristic_prioritizes_shooter_targets() -> None:
    bot = DominatorBot.default()
    combat = CombatState(
        friendly=(ArmyStack("griffin", 10, 8, 8, 3, 6, 25, 6),),
        enemy=(
            ArmyStack("orc", 45, 3, 3, 1, 2, 5, 5),
            ArmyStack("ogre", 4, 9, 7, 6, 12, 40, 4),
        ),
        turn=0,
        morale=0.0,
    )

    ranged = bot.micro._action_heuristic(combat, CombatAction("attack", target=0, aggression=0.8))
    melee = bot.micro._action_heuristic(combat, CombatAction("attack", target=1, aggression=0.8))
    assert ranged > melee


def test_risk_model_prefers_stronger_army() -> None:
    bot = DominatorBot.default()
    strong = bot.assess_engagement_risk(
        friendly=(ArmyStack("champion", 20, 10, 9, 5, 10, 100, 7),),
        enemy=(ArmyStack("orc", 20, 3, 3, 1, 2, 5, 5),),
    )
    weak = bot.assess_engagement_risk(
        friendly=(ArmyStack("orc", 10, 3, 3, 1, 2, 5, 5),),
        enemy=(ArmyStack("champion", 15, 10, 9, 5, 10, 100, 7),),
    )
    assert strong.win_probability > weak.win_probability


def test_movement_planner_uses_object_data() -> None:
    bot = DominatorBot.default()
    state = sample_adv_state()
    choice = bot.strategy.choose_movement_option(
        state,
        (
            MovementOption(0.4, 0.4, "sawmill", reward=2.1, risk=0.2, movement_cost=8, on_road=True, fog_reveal=0.2, object_key="sawmill"),
            MovementOption(0.5, 0.5, "gold", reward=2.1, risk=0.2, movement_cost=8, on_road=True, fog_reveal=0.2, object_key="gold_mine"),
        ),
    )
    assert choice is not None
    assert choice.object_key == "gold_mine"


def test_movement_penalizes_recently_visited_targets() -> None:
    bot = DominatorBot.default()
    state = sample_adv_state()
    choice = bot.strategy.choose_movement_option(
        state,
        (
            MovementOption(0.4, 0.4, "loop_tile", reward=2.8, risk=0.1, movement_cost=6, on_road=True, fog_reveal=0.2, object_key="gold_mine", recently_visited=True),
            MovementOption(0.45, 0.42, "fresh_tile", reward=2.5, risk=0.1, movement_cost=6, on_road=True, fog_reveal=0.2, object_key="sawmill", recently_visited=False),
        ),
    )
    assert choice is not None
    assert choice.label == "fresh_tile"


def test_opening_build_order_bias() -> None:
    bot = DominatorBot.default()
    plan = bot.ui.build_town_plan(
        TownState(
            available_builds=("marketplace", "dwelling_lvl1", "town_hall"),
            gold=300,
            wood=5,
            ore=5,
            current_day=2,
            faction="knight",
            built_buildings=("village_hall",),
        )
    )
    assert plan is not None
    assert plan.build == "dwelling_lvl1"


def test_history_learning_nudges_from_many_games(tmp_path: Path) -> None:
    bot = DominatorBot.default()
    tracker = PerformanceTracker(store_path=str(tmp_path / "history.json"))

    for _ in range(12):
        bot.record_game_result(
            tracker,
            GameResult(won=False, score_delta=-0.7, turns=26, towns_controlled=1, final_army_power=1800, losses_ratio=0.62),
        )

    learned, summary = bot.with_learning_from_history(tracker)
    assert summary.games == 12
    assert learned.macro.weights.safety >= bot.macro.weights.safety


def test_ui_turn_script_synthesizes_castle_hero_and_map_actions() -> None:
    bot = DominatorBot.default()
    snapshot = AdventureSnapshot(
        state=sample_adv_state(),
        actions=(AdventureAction("take_mine", value_gain=1.2, movement_cost=6, risk=0.1),),
        town=TownState(
            available_builds=("dwelling_lvl1", "town_hall"),
            gold=4000,
            wood=5,
            ore=5,
            current_day=1,
            faction="knight",
            built_buildings=("village_hall",),
        ),
        hero_army=HeroArmyState(
            stacks=(
                ArmyStack("archer", 20, 6, 3, 2, 3, 10, 4),
                ArmyStack("pikeman", 30, 4, 5, 1, 3, 12, 4),
            )
        ),
        visible_labels=("gold mine", "neutral guard"),
        movement_options=(
            MovementOption(0.3, 0.3, "scout", reward=1.0, risk=0.03, movement_cost=6, on_road=True, fog_reveal=0.8, object_key="unknown"),
            MovementOption(0.6, 0.4, "mine", reward=3.0, risk=0.2, movement_cost=9, on_road=False, fog_reveal=0.2, guarded=True, object_key="gold_mine"),
        ),
    )

    commands = bot.plan_turn_commands(snapshot, (0.5, 0.5))
    labels = [command.arg for command in commands]
    assert any(label and label.startswith("visible:") for label in labels)
    assert "open_town" in labels
    assert "open_castle_options" in labels
    assert any(label and label.startswith("confirm_build:") for label in labels)
    assert any(label and label.startswith("confirm_build_retry:") for label in labels)
    assert "open_castle_options_retry" in labels
    assert "open_hero" in labels
    assert "move_hero" in labels
    assert "end_turn" in labels


def test_evolution_tuner_returns_working_bot() -> None:
    base = DominatorBot.default()
    tuned = EvolutionTuner(seed=1).improve(base, generations=10)
    assert tuned.pick_adventure_action(
        sample_adv_state(),
        (
            AdventureAction("flag_sawmill", value_gain=0.9, movement_cost=4, risk=0.05),
            AdventureAction("fight_guard", value_gain=2.0, movement_cost=10, risk=0.25),
        ),
    ).kind in {"flag_sawmill", "fight_guard"}
