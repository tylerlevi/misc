# HOMM2 Dominator Bot

A practical, code-first framework for building a strong **Heroes of Might and Magic II** bot focused on:

- **Macro dominance** on the adventure map (economy, tempo, expansion, snowballing)
- **Micro combat control** with tactical search + trade modeling
- **Continuous improvement** via evolutionary tuning
- **Unit-aware tactics** powered by a built-in HOMM2 unit encyclopedia
- **UI-aware command planning** for fixed-resolution fheroes2 window controls
- **Math-heavy risk assessment** using expected-value and probability scoring
- **Visual object knowledge** for map/UI recognition and action mapping

> This repo is engine-agnostic but includes a concrete command-synthesis layer calibrated to the windowed UI layout shown in your screenshots.

## Data-informed strategy upgrade

The bot now uses game data and strategy patterns to drive decisions:

- **Raw game data sources (online)**
  - fheroes2 `buildinginfo.cpp`: building costs and tech structure
  - fheroes2 `profit.cpp`: mine incomes and building gold incomes
  - fheroes2 `monster_info.cpp`: monster costs and weekly growth
- **High-level strategy patterns encoded**
  - week 1 tempo: early mines / income acceleration
  - ROI-first town development with growth pressure
  - ranged stack splitting for initiative and focus-fire
  - risk-aware engagement filtering instead of blind aggression
  - movement routing that trades reward, risk, road tempo, and fog reveal

## Architecture

### 1) Unit knowledge (`units.py`)
- Tactical profiles for core HOMM2 units and upgrades (faction, tier, role, abilities).
- Captures shooter/flying/spellcasting/retaliation traits.
- Used by both strategic and tactical evaluation.

### 2) Visual recognition knowledge (`vision_knowledge.py`)
- Contains canonical visual signatures for key controls and map objects:
  - castle/hero/end-turn buttons
  - town build slots / hero stack slots
  - mines, chests, and neutral guards
- Lets parser labels be normalized into planning-relevant object classes.

### 3) Strategy math engine (`strategy.py`)
- Risk model computes win probability, expected loss ratio, and pressure score.
- Economy model projects daily/weekly resource income and build ROI.
- Movement model selects route targets by risk-adjusted value and tempo.
- Action scoring applies risk penalties, movement efficiency, and early-game tempo multipliers.

### 4) Macro planner (`MacroPlanner`)
- Beam search over adventure-map actions.
- Rewards towns, map control, economy, and army power.
- Adds strategy-engine risk-adjusted action score.

### 5) Micro planner (`MicroPlanner`)
- Depth-limited alpha-beta combat search.
- Evaluates attrition, morale, speed.
- Adds kill-trade heuristic with retaliation risk and threat suppression for shooters/casters/fliers.

### 6) UI command layer (`interface.py` + `automation.py`)
- Encodes fixed-window control coordinates for:
  - right-panel hero/castle/end-turn buttons
  - hero army row + reserve slots (for stack splitting)
  - town build slots (castle screen)
  - world map viewport click projection
- Synthesizes one coordinated per-turn command list that:
  1. classifies visible objects from parser labels
  2. opens castle and builds best ROI/priority structure
  3. opens hero and performs stack split plan for ranged tempo
  4. chooses movement target from risk/reward options
  5. clicks target map position and ends turn

### 7) Improvement loop (`EvolutionTuner`)
- Mutates planner weights.
- Scores candidates across multiple macro and micro scenarios.
- Keeps stronger variants over generations.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m homm2bot.cli
pytest
```

## Integrating with a real fheroes2 loop

1. Read game state from memory/API/screen parser into:
   - `AdventureState`, `AdventureAction`s
   - `TownState`, `HeroArmyState`
   - `visible_labels` and movement options from your parser
2. Use decision core:
   - `DominatorBot.pick_adventure_action(...)`
   - `DominatorBot.pick_combat_action(...)`
   - `DominatorBot.assess_engagement_risk(...)`
3. Use UI command core:
   - `DominatorBot.plan_turn_commands(snapshot, target_map_xy)`
4. Execute `LowLevelCommand`s via your input driver (Win32, pyautogui, etc.).

Because this layout is fixed-window, command coordinates are deterministic and can be calibrated once per machine/profile.
