"""HOMM2 bot framework."""

from .automation import AdventureSnapshot, HeroArmyState, LowLevelCommand, TownState, UiCommander
from .bot import DominatorBot
from .interface import DEFAULT_LAYOUT, Point, Rect, UiLayout
from .models import (
    AdventureAction,
    AdventureState,
    ArmyStack,
    CombatAction,
    CombatState,
)
from .performance import GameResult, ImprovementCoach, PerformanceSummary, PerformanceTracker
from .strategy import EconomyReport, MovementOption, RiskReport, StrategyAdvisor
from .training import EvolutionTuner
from .units import UNIT_INDEX, UnitProfile, unit_profile
from .vision_knowledge import VISUAL_SIGNATURES, VisualSignature, lookup_visual_signature

__all__ = [
    "AdventureAction",
    "AdventureSnapshot",
    "AdventureState",
    "ArmyStack",
    "CombatAction",
    "CombatState",
    "DEFAULT_LAYOUT",
    "DominatorBot",
    "EconomyReport",
    "EvolutionTuner",
    "GameResult",
    "HeroArmyState",
    "ImprovementCoach",
    "LowLevelCommand",
    "MovementOption",
    "PerformanceSummary",
    "PerformanceTracker",
    "Point",
    "Rect",
    "RiskReport",
    "StrategyAdvisor",
    "TownState",
    "UNIT_INDEX",
    "UiCommander",
    "UiLayout",
    "UnitProfile",
    "VISUAL_SIGNATURES",
    "VisualSignature",
    "lookup_visual_signature",
    "unit_profile",
]
