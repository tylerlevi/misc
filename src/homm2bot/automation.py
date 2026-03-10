from __future__ import annotations

from dataclasses import dataclass, field

from .domain_data import BUILD_COSTS, OPENING_BUILD_ORDERS
from .interface import DEFAULT_LAYOUT, Point, UiLayout
from .models import AdventureAction, AdventureState, ArmyStack
from .strategy import BUILD_DAILY_INCOME_GOLD, MovementOption, StrategyAdvisor
from .units import unit_profile
from .vision_knowledge import lookup_visual_signature


@dataclass(frozen=True)
class LowLevelCommand:
    op: str
    at: Point | None = None
    arg: str | None = None


@dataclass(frozen=True)
class TownState:
    available_builds: tuple[str, ...]
    gold: int
    wood: int
    ore: int
    current_day: int
    faction: str = "default"
    built_buildings: tuple[str, ...] = ()


@dataclass(frozen=True)
class HeroArmyState:
    stacks: tuple[ArmyStack, ...]


@dataclass(frozen=True)
class AdventureSnapshot:
    state: AdventureState
    actions: tuple[AdventureAction, ...]
    town: TownState | None = None
    hero_army: HeroArmyState | None = None
    visible_labels: tuple[str, ...] = ()
    movement_options: tuple[MovementOption, ...] = ()


@dataclass(frozen=True)
class TownBuildPlan:
    build: str
    ui_slot: int


@dataclass(frozen=True)
class ArmySplitPlan:
    source_slot: int
    reserve_slot: int
    amount: int


@dataclass
class UiCommander:
    layout: UiLayout = field(default_factory=lambda: DEFAULT_LAYOUT)
    strategy: StrategyAdvisor = field(default_factory=StrategyAdvisor)

    TOWN_BUILD_PRIORITY: tuple[str, ...] = (
        "town_hall",
        "city_hall",
        "capitol",
        "marketplace",
        "blacksmith",
        "dwelling_lvl1",
        "dwelling_lvl2",
        "dwelling_lvl3",
        "dwelling_lvl4",
        "dwelling_lvl5",
        "dwelling_lvl6",
        "mage_guild_1",
        "mage_guild_2",
        "mage_guild_3",
    )

    def _can_afford(self, town: TownState, build: str) -> bool:
        cost = BUILD_COSTS.get(build)
        if not cost:
            return True
        gold, wood, ore = cost
        return town.gold >= gold and town.wood >= wood and town.ore >= ore

    def build_town_plan(self, town: TownState) -> TownBuildPlan | None:
        if not town.available_builds:
            return None

        # Pain point: trying unaffordable builds wastes clicks. Filter first.
        affordable = tuple(build for build in town.available_builds if self._can_afford(town, build))
        if not affordable:
            return None

        if town.current_day <= 7:
            opening = OPENING_BUILD_ORDERS.get(town.faction, OPENING_BUILD_ORDERS["default"])
            for build in opening:
                if build in affordable and build not in town.built_buildings:
                    slot = min(town.available_builds.index(build), len(self.layout.castle_build_grid) - 1)
                    return TownBuildPlan(build=build, ui_slot=slot)

        current_income = BUILD_DAILY_INCOME_GOLD["village_hall"]
        ranked: list[tuple[float, str]] = []
        for build in affordable:
            roi_days = self.strategy.building_roi_days(build, current_income)
            priority_bonus = 0.0
            if build in self.TOWN_BUILD_PRIORITY:
                priority_bonus = (len(self.TOWN_BUILD_PRIORITY) - self.TOWN_BUILD_PRIORITY.index(build)) * 0.15
            score = priority_bonus + (12.0 / max(2.0, roi_days))
            ranked.append((score, build))

        ranked.sort(key=lambda item: item[0], reverse=True)
        best_build = ranked[0][1]
        slot = min(town.available_builds.index(best_build), len(self.layout.castle_build_grid) - 1)
        return TownBuildPlan(build=best_build, ui_slot=slot)

    def town_upgrade_flow(self, town: TownState) -> tuple[LowLevelCommand, ...]:
        """Map -> town -> castle options -> build tile -> confirm, with retry-safe clicks."""
        plan = self.build_town_plan(town)
        if not plan:
            return tuple()
        tile = self.layout.castle_build_grid[plan.ui_slot].center()
        return (
            LowLevelCommand("click", self.layout.btn_castle.center(), "open_town"),
            LowLevelCommand("click", self.layout.btn_castle.center(), "open_town_twice"),
            LowLevelCommand("click", self.layout.town_castle_icon.center(), "open_castle_options"),
            LowLevelCommand("click", self.layout.town_castle_icon.center(), "open_castle_options_retry"),
            LowLevelCommand("click", tile, f"inspect_build:{plan.build}"),
            LowLevelCommand("click", self.layout.build_dialog_ok.center(), f"confirm_build:{plan.build}"),
            LowLevelCommand("click", self.layout.build_dialog_ok.center(), f"confirm_build_retry:{plan.build}"),
        )

    def army_split_plan(self, hero: HeroArmyState) -> tuple[ArmySplitPlan, ...]:
        plans: list[ArmySplitPlan] = []
        for slot_idx, stack in enumerate(hero.stacks[: len(self.layout.hero_stack_slots)]):
            profile = unit_profile(stack.name)
            if not profile or not profile.shooter or stack.count < 10:
                continue
            amount = max(1, stack.count // 4)
            reserve_slot = min(slot_idx, len(self.layout.hero_reserve_slots) - 1)
            plans.append(ArmySplitPlan(source_slot=slot_idx, reserve_slot=reserve_slot, amount=amount))
        return tuple(plans)

    def movement_click(self, normalized_x: float, normalized_y: float) -> Point:
        clamped_x = max(0.0, min(1.0, normalized_x))
        clamped_y = max(0.0, min(1.0, normalized_y))
        view = self.layout.world_view
        px = view.left + int((view.right - view.left) * clamped_x)
        py = view.top + int((view.bottom - view.top) * clamped_y)
        return Point(px, py)

    def classify_visible_objects(self, labels: tuple[str, ...]) -> tuple[str, ...]:
        resolved: list[str] = []
        for label in labels:
            sig = lookup_visual_signature(label)
            resolved.append(sig.key if sig else "unknown_object")
        return tuple(resolved)

    def choose_movement_target(self, snapshot: AdventureSnapshot, fallback_xy: tuple[float, float]) -> tuple[float, float]:
        if snapshot.movement_options:
            best = self.strategy.choose_movement_option(snapshot.state, snapshot.movement_options)
            if best:
                return (best.normalized_x, best.normalized_y)
        return fallback_xy

    def synthesize_turn_commands(
        self,
        snapshot: AdventureSnapshot,
        target_map_xy: tuple[float, float],
    ) -> tuple[LowLevelCommand, ...]:
        commands: list[LowLevelCommand] = []

        if snapshot.visible_labels:
            visible = self.classify_visible_objects(snapshot.visible_labels)
            commands.append(LowLevelCommand("annotate", None, f"visible:{','.join(visible[:6])}"))

        if snapshot.town:
            commands.extend(self.town_upgrade_flow(snapshot.town))

        if snapshot.hero_army:
            commands.append(LowLevelCommand("click", self.layout.btn_hero.center(), "open_hero"))
            for split in self.army_split_plan(snapshot.hero_army):
                src = self.layout.hero_stack_slots[split.source_slot].center()
                dst = self.layout.hero_reserve_slots[split.reserve_slot].center()
                commands.append(LowLevelCommand("drag", src, f"split:{split.amount}"))
                commands.append(LowLevelCommand("drop", dst, "confirm_split"))

        chosen_target = self.choose_movement_target(snapshot, target_map_xy)
        move_point = self.movement_click(*chosen_target)
        commands.append(LowLevelCommand("click", move_point, "move_hero"))
        commands.append(LowLevelCommand("click", self.layout.btn_end_turn.center(), "end_turn"))

        return tuple(commands)
