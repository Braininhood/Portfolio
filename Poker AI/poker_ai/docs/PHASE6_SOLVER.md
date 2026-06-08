# Phase 6 — CFR solvers and preflop policies

> **Canonical Phase 6 reference** — keep [doc/ROADMAP.md](../../doc/ROADMAP.md) exit criteria in sync with this file.

**Status:** **Done** (roadmap exit criteria). Tabular **CFR+** (HU) and **external-sampling MCCFR** (6-max) on an abstracted preflop tree; runtime policies stack preflop CFR with Phase 4 postflop equity (not full postflop CFR — that is Phase 7+).

## Commands (from `poker_ai/`)

```powershell
cd "D:\Poker AI\poker_ai"

# Kuhn validation smoke (OpenSpiel exploitability)
python -m poker_ai solve kuhn --iters 10000

# --- Recommended: real-equity production charts (CPU; chart-only, no exploitability gate) ---
# --production forces equity_mode=real, higher iters, prune; --equity-mode real is optional but explicit in logs.

python -m poker_ai solve preflop --positions hu --production --equity-mode real --workers 7 `
  -o artifacts/solver/preflop_hu_real.json

python -m poker_ai solve preflop --positions 6max --production --equity-mode real --workers 7 `
  --max-raises 1 -o artifacts/solver/preflop_cfr.json

# Ring tables (optional; overnight CPU) — default -o picks preflop_8max.json etc.
python -m poker_ai solve preflop --positions 8max --production --equity-mode real --workers 8
python -m poker_ai solve preflop --positions 9max --production --equity-mode real --workers 8
python -m poker_ai solve preflop --positions 10max --production --equity-mode real --workers 8

# Optional: add --measure-exploitability (slow; writes exploitability_mbb into JSON)

# End-to-end pipeline (ingest → features → parallel CFR; skips train/embed by default)
python -m poker_ai pipeline run --corpus "..\hand\5" --skip-train --skip-embed --workers 7
```

### What `--production` changes

| Setting | HU | 6-max |
|---------|-----|-------|
| `equity_mode` | **real** | **real** |
| `iterations` (min) | **50 000** | **25 000** |
| `chance_samples` | max(64, 32) → typically **64** | min(64, 32) → **32** |
| `prune_min_mass` | ≥ **10** | ≥ **10** |

First `real` run builds **1326 × `--equity-mc-samples`** Monte Carlo equities (CPU), then caches:

`artifacts/solver/cache/combo_equity_vs_uniform_n{mc_samples}.npy`

### Output file timing

The JSON (`-o …`) is written **only once** at the end, after all parallel shards finish and regrets are merged. While you see `parallel workers=N` with no new lines, the solve is usually still running — check Task Manager for multiple `python.exe` children using CPU.

### Ctrl+C / IDE stop on Windows

Cancelling (keyboard **Ctrl+C**, Cursor **Stop** on the terminal, or closing the panel) prints many `KeyboardInterrupt` / `SpawnProcess` tracebacks from old worker processes. That is **noise**, not a solver logic bug.

If you did **not** press the keyboard but see `Interrupted — cancelling CFR workers`, the **IDE or terminal** likely sent a stop signal. Run in a **standalone** PowerShell window (`Win+R` → `powershell`) for long HU solves.

While running, you should see a heartbeat every **2 minutes**: `... still solving (0/18 shards done, 18 workers active)`. No heartbeat for 10+ minutes with **zero** CPU → kill stray `python.exe` and re-run.

### Workers (`--workers` / `POKER_AI_NUM_WORKERS`)

- **CPU-only** step — use **logical cores − 1** (e.g. i7 4C/8T → `--workers 7`).
- `--workers 0` → auto (`os.cpu_count() - 1`, capped).
- More than `cpu_count` workers usually **hurts** (memory + spawn overhead on Windows).

```powershell
python -c "import os; print('cpu_count=', os.cpu_count())"
$env:POKER_AI_NUM_WORKERS = "7"   # optional default for all parallel phases
```

## CLI: `solve preflop`

| Flag | Default | Meaning |
|------|---------|---------|
| `--positions` | `6max` | `6max` or `hu` |
| `--iters` | `20000` | Total iterations (split across `--workers`) |
| `--workers` | `0` | Process shards (`0` = auto; env `POKER_AI_NUM_WORKERS`) |
| `--chance-samples` | `64` | Root deal samples in the abstraction |
| `--max-raises` | `1` | Cap raises per hand (keeps tree tractable) |
| `--equity-mode` | `random` | `real` = Phase 4 MC equity vs random range → 50 buckets |
| `--equity-mc-samples` | `2000` | MC samples when building the 1326-combo table (`real` only) |
| `--production` | off | **Real equity** + higher iters (HU 50k / 6-max 25k min) + stricter prune |
| `--prune-min-mass` | `5` | Drop low-visit info sets from the exported table |
| `--measure-exploitability` | off | Info-set best response after solve (HU practical; 6-max subsamples roots) |
| `-o` | `artifacts/solver/preflop_cfr.json` | Output JSON path |

## Strategy artifact JSON

| Field | Meaning |
|-------|---------|
| `equity_mode` | `random` or `real` (must match how you train **and** lookup) |
| `equity_mc_samples` | MC table size used for `real` |
| `exploitability_mbb` | mbb/g if measured; **`-1`** = skipped |
| `strategy` | Map of info-set keys → `[fold, call, raise, all-in]` probabilities |

**Info-set key:** `n{players}|p{seat}|b{bucket}|h{history}` — e.g. `n2|p1|b47|h1,6,3` (HU, seat 1, bucket 47, encoded action history).

## Exploitability

- **Info-set** best response (keys use the acting player’s bucket only).
- **6-max:** **max** per-player gap in mbb/g (not summed NashConv).
- When measuring on 6-max, only the first **24** chance roots are used (speed).

## Policies

| Class | Role |
|-------|------|
| `HeuristicPolicy` | Chart-based fallback |
| `CFRPolicy` | Tabular preflop CFR lookup (`load_json`) |
| `PostflopEquityPolicy` | Phase 4 `EquityEngine` on flop+ (not CFR) |
| `StackedPolicy` | CFR preflop → postflop equity → heuristic; optional HHFormer embed JSONL |

```python
from poker_ai.policy.stacked import load_runtime_policy

policy = load_runtime_policy()
```

For `equity_mode=real`, set `GameState.seat_holes` (hero combo ints) via `initial_state_from_parsed_hand`.

## Parallelism (Phases 1–6)

| Step | Flag / env |
|------|------------|
| Ingest | `ingest --workers N` |
| Features | `features build --workers N` |
| CFR | `solve preflop --workers N` |
| Default | `POKER_AI_NUM_WORKERS` or auto ≈ CPU−1 |

## Tests

```powershell
python -m pytest tests/test_solver_phase6.py -q -m "not slow"
python -m pytest tests/test_solver_phase6.py -q -m slow   # exploitability < 5 mbb/g gates
```

## Why CPU, not GPU

| Component | Hardware | Reason |
|-----------|----------|--------|
| CFR / MCCFR regrets | **CPU** | Tabular dict + Python tree walk; not batched like neural nets |
| Preflop equity table (`real`) | **CPU** | Phase 4 Numba Monte Carlo (same as `EquityEngine`) |
| HU combo showdown | **CPU** | Small MC per terminal node |
| HHFormer **training** | **GPU** optional | Separate `train hhformer` command |

Deep CFR / batched GPU regret nets are **Phase 9** (ROADMAP). For now, speed comes from **parallel CPU workers** and **cached** combo tables (`artifacts/solver/cache/combo_equity_vs_uniform_n{mc}.npy`).

## Faster runs

| Goal | Command |
|------|---------|
| Real equity chart, skip exploitability gate | Drop `--measure-exploitability` |
| Lighter MC table (first build) | `--equity-mc-samples 500` (less accurate buckets) |
| Dev iteration count | Omit `--production`; use `--iters 5000 --equity-mode real` |
| Reuse cached table | Second run with same `--equity-mc-samples` loads cache instantly |

`--production` already sets `equity_mode=real`; add `--equity-mode real` only if you want it visible in the CLI banner without `--production`.

## Out of scope (documented in ROADMAP)

- Full **multi-street postflop CFR** → Phase 7+ (TexasSolver bridge, distilled student).
- Deep **HHFormer → policy** fusion (embed JSONL hook only today).
- **GPU CFR** → Phase 9 Deep CFR.
