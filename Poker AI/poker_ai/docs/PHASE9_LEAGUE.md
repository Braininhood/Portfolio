# Phase 9 — Self-play league (complete guide)

> **Roadmap:** [doc/ROADMAP.md](../../doc/ROADMAP.md) §Phase 9 · **Commands:** [COMMANDS_PHASE9.md](COMMANDS_PHASE9.md) · **Status:** [PHASES_0_9_STATUS.md](PHASES_0_9_STATUS.md)

## Session summary (May 2026)

Work in this phase delivered:

| Area | What shipped |
|------|----------------|
| **League sim** | HU + 6-max + 9-max; `RouterPolicy` brain-switch stats |
| **Orchestrator** | Round-robin + **`--until-hours`** random matchups (multi-way default) |
| **Workers** | `matchup_worker.py` process pool |
| **Agents** | 10+ frozen archetypes (TAG, LAG, NIT, fish, …) |
| **Eval** | Elo, AIVAT BB/100, promotion gate (`promoted` in report JSON) |
| **Texas bridge** | Absolute dump path + combo-strategy JSON parser; `--continue-on-error` |
| **Training path** | Texas-only cache → `train student`; multi-way from DB |

**Validated promotion run** (synthetic league, not DB replay):

```text
league run --until-hours 0.3 --until-hu --table-sizes hu,6max,9max --hands-per-matchup 100 --workers 16
promoted=True  main_elo≈1612  aivat_p≈0.0001  hands≈283k  wall≈19 min
```

**June 2026 additions:** `league/style_bridge.py` (per-seat opponent styles), `league/checkpoint_registry.py` + CLI `league checkpoints`, `main_exploiter` → `ExploitPolicy`, **`league train-exploiters`** (CLI + web) → `artifacts/league/exploiters/v1/`, web **Until 6 hours** league preset.

**v2 TODO (not v1):** full AIVAT theory, league on real DB replay — see [ROADMAP §v2 backlog](../../doc/ROADMAP.md#v2-backlog--next-version-todo).

---

## Two schedule modes

| Mode | Flag | Stops when |
|------|------|------------|
| **Round-robin** | `--hours N` (default 0.1) | All agent pairs × `hands-per-matchup` done **or** wall cap |
| **Until wall** | `--until-hours N` | Wall clock elapsed (random pairings) |

**Important:** `--hours 6` often finishes in **minutes** with many workers (finite 78 matchups). For ~6 h of play use **`--until-hours 6`**.

Until mode defaults to **`6max,9max`** only; add HU with **`--until-hu --table-sizes hu,6max,9max`**.

---

## Promotion gates (`reports/league_leaderboard.json`)

All must pass for `"promoted": true`:

1. `main_agent` **hands ≥ 1000**
2. `main_agent` **Elo ≥ 1550** (start 1500, +50)
3. Every **frozen** agent Elo **&lt; main_agent**
4. **AIVAT** p-value **&lt; 0.05** and positive AIVAT BB/100

Quick check:

```powershell
python -c "import json; d=json.load(open('reports/league_leaderboard.json')); print('promoted',d.get('promoted')); m=next(r for r in d['leaderboard'] if r['agent_id']=='main_agent'); frozen={'tag','lag','nit','rock','call_station','fish','passive_reg','random','cfr_stacked','distilled_gto'}; bad=[r for r in d['leaderboard'] if r['agent_id'] in frozen and r['elo']>=m['elo']]; print('main',m['elo'],m['hands'],m['aivat_pvalue']); print('frozen_not_beaten',bad)"
```

**Do not** use raw BB/100 from league as live win rate — ghost seats inflate multi-way numbers.

---

## Training pipeline before league

| Step | Command |
|------|---------|
| 1 Ingest (if needed) | `python -m poker_ai ingest PATH --workers 8` |
| 2 Features | `python -m poker_ai features build` · `features hhformer-embed` |
| 3 Texas teachers | `solve grid --n-spots 1024 --backend texas --cache-dir artifacts/solver_cache_texas_only --continue-on-error --texas-threads 2` |
| 4 HU student | `train student --cache-dir artifacts/solver_cache_texas_only --epochs 50 --device auto` |
| 5 Multi-way student | `train multiway-student --epochs 25 --row-limit 50000 --device auto` |
| 6 HU preflop (optional) | `solve preflop --positions hu --production --equity-mode real` |
| 6b Ring preflop (optional) | `solve preflop --positions 8max --production` (repeat 9max, 10max) |
| 7 League | `league run --until-hours 2 --until-hu --table-sizes hu,6max,9max --workers 16` |

See [PHASE7_SOLVER_BRIDGE.md](PHASE7_SOLVER_BRIDGE.md) for cache/mock vs texas behavior.

---

## PyTorch CUDA

`train student --device cuda` requires a **CUDA PyTorch wheel** (`torch … +cu128`), not `+cpu`. Driver alone (`nvidia-smi`) is insufficient.

```powershell
uv pip install torch --index-url https://download.pytorch.org/whl/cu128
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

---

## What league is *not*

- **Not** replay of ingested hand histories — synthetic deals only.
- **Not** Phase 8 `ExploitPolicy` — `main_agent` = `RouterPolicy` / `load_best_policy()`.
- **Not** guaranteed live-table win rate — Elo vs scripted archetypes in sim.

---

## Code map

| Path | Role |
|------|------|
| `league/sim.py` | Table hand + `play_hand` |
| `league/orchestrator.py` | Schedules, `run_until_wall`, report JSON |
| `league/matchup_worker.py` | Parallel workers |
| `league/evaluator.py` | Elo, AIVAT, `promotion_significant` |
| `league/agents/` | Roster + baselines |
| `solver/bridge/batch.py` | `solve_grid`, `--continue-on-error` |
| `solver/bridge/texas.py` | TexasSolver driver + JSON parse |
