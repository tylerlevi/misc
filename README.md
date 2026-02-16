# Kingdom Rush Evolutionary RL Agent (Steam PC Focus)

This project trains a **screen-reading evolutionary agent** for Kingdom Rush, tuned to work best with the **Steam PC fullscreen 1920x1080** version.

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
- **Smarter interaction (Steam-ready)**:
  - scale-aware build-spot detection (works across resolutions)
  - detection of start/continue button
  - detection of menu buttons like `start_game`, `upgrades`, `enemy_encyclopedia`, `close_panel`
  - normalized fallback coordinates so different resolutions still work
  - deterministic opening sequence so levels start quickly
- **Better UX**:
  - dry-run mode
  - checkpoint/resume
  - optional action JSON file (`--actions-file`)
  - optional boot-screen waiting
  - CLI knobs for exploration/reward/novelty weights
  - end-of-run report files in `reports/` (no noisy live spam)

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Fast start (recommended Steam fullscreen)

```bash
kr-train \
  --left 0 --top 0 --width 1920 --height 1080 \
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

## End-of-run report

After each training run, a report is written to `reports/run_report_*.txt` including:

- best/mean/std fitness trends
- last exploration/mutation settings
- next-focus recommendations for resume

Use a custom folder if desired:

```bash
kr-train --report-dir ./reports
```

## Auto-start + auto-build behavior

At the start of each episode, the bot now:

1. Scans the frame for likely circular tower build pads.
2. Scans for start/continue and Steam UI menu buttons.
3. Runs deterministic bootstrap actions (`build_archer`, `build_mage`, then `start_wave`) before RL actions.
4. If `Hero Room` has no available heroes, closes it automatically.
5. If `Upgrades` has no available upgrade points, closes it automatically.

If detection fails, it falls back to normalized action coordinates that scale with your capture size.

## Optional custom actions JSON

```json
[
  {"name": "build_archer", "x": 0.156, "y": 0.9, "hotkey": "1"},
  {"name": "start_wave", "x": 0.925, "y": 0.96},
  {"name": "upgrades", "x": 0.81, "y": 0.455}
]
```

Run with:

```bash
kr-train --actions-file ./my_actions.json
```

## Practical tuning

1. Start with fullscreen 1920x1080 if possible.
2. Increase `--population` before increasing episode length.
3. Keep `--evaluation-repeats` at `2` or `3` for stability.
4. Use `--frame-stack 3` (default) unless your machine is very slow.
5. Adjust `--epsilon-*`, `--temperature-*`, and `--novelty-*` when exploration is too random or too greedy.
