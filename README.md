# Kingdom Rush Evolutionary RL Agent

This project trains a **screen-reading evolutionary agent** for Kingdom Rush with a cleaner architecture and better defaults for stability.

## What is improved

- **Modular configs**: vision, reward shaping, exploration, evolution, runtime.
- **Better state representation**: configurable **frame stacking** (temporal information).
- **Better reward shaping**: weighted brightness + contrast + motion + entropy.
- **More stable training**:
  - tournament selection
  - mutation annealing + stagnation boost
  - immigrant injection (diversity)
  - repeated evaluation with median fitness
  - epsilon + temperature exploration schedule
  - novelty search bonus (behavioral diversity)
- **Smarter interaction**:
  - auto-detect build spots from map geometry
  - auto-detect start/continue buttons to begin/end levels faster
- **Better UX**:
  - dry-run mode
  - checkpoint/resume
  - optional action JSON file (`--actions-file`)
  - optional boot-screen waiting
  - CLI knobs for exploration/reward/novelty weights
  - optional progress log file for explanations (`--progress-log`)

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Fast start

```bash
kr-train \
  --left 0 --top 0 --width 1600 --height 1000 \
  --generations 80 --population 32 --episode-seconds 90
```

## Safe dry-run (no clicks)

```bash
kr-train --dry-run --generations 2 --population 4 --episode-seconds 3
```

## Resume from checkpoint

```bash
kr-train --resume-from checkpoints/best_gen_0010.npz
```

## Progress log (chatbox-style updates)

```bash
kr-train --progress-log ./runs/progress.txt
```

The log includes notes like `new_best` or `stagnant_3` to explain what the run is doing.


## Auto-start + auto-build behavior

At the start of each episode, the bot now:

1. Scans the frame for likely circular tower build pads.
2. Scans for orange/yellow start/continue buttons.
3. Runs a deterministic opening (`build_archer`, `build_mage`, then `start_wave`) before RL actions.

If detection fails, it falls back to your configured action coordinates.

## Optional custom actions JSON

```json
[
  {"name": "build_archer", "x": 250, "y": 900, "hotkey": "1"},
  {"name": "start_wave", "x": 1480, "y": 960}
]
```

Run with:

```bash
kr-train --actions-file ./my_actions.json
```

## Practical tuning

1. Increase `--population` before increasing episode length.
2. Keep `--evaluation-repeats` at `2` or `3` for stability.
3. Use `--frame-stack 3` (default) unless your machine is very slow.
4. Adjust `--epsilon-*`, `--temperature-*`, and `--novelty-*` when exploration is too random or too greedy.
5. Calibrate action coordinates first (most important).
