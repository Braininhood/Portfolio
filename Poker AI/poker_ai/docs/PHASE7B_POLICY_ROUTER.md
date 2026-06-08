# Phase 7b — HU vs multi-way policy router

> **Commands:** [COMMANDS_PHASES_0_7.md](COMMANDS_PHASES_0_7.md) · **Full guide:** [PHASES_0_7_COMPLETE_GUIDE.md](PHASES_0_7_COMPLETE_GUIDE.md) · **Roadmap:** [doc/ROADMAP.md](../../doc/ROADMAP.md).

## Rule

```text
n_active = count_active_players(state)   # core/context.py

n_active == 2  →  HuStackPolicy
n_active >= 3  →  MultiwayStackPolicy
```

Re-evaluated on **every** `propose()` call (after each fold).

## Brains

| Brain | Preflop | Postflop |
|-------|---------|----------|
| **HU** | `artifacts/solver/preflop_hu_real.json` | Phase 7 `DistilledPolicy` (`artifacts/student/v1/`) — TexasSolver- or mock-trained |
| **Multi-way** | `resolve_preflop_cfr_path(num_seats)` → `preflop_cfr.json` / `preflop_8max.json` / `preflop_9max.json` / `preflop_10max.json` when present; else heuristic | `MultiwayPostflopPolicy`: DB student + Monker blend + multi-way equity |

## Source files

| Path | Role |
|------|------|
| `core/context.py` | `count_active_players`, `is_heads_up_context`, `is_multiway_context` |
| `policy/router_policy.py` | Top-level router |
| `policy/hu_stack.py` | HU CFR + distilled |
| `policy/multiway_stack.py` | 6-max CFR / heuristic + postflop delegate |
| `policy/multiway_postflop.py` | Student, Monker cache, equity fallback |
| `policy/stacked.py` | `StackedPolicy` delegates to `RouterPolicy` (v0.4.0) |
| `policy/distilled_policy.py` | Returns **empty** when `n_active >= 3` |
| `equity/multiway.py` | Hero vs *n* independent uniform opponent ranges (MC) |
| `models/multiway_student.py` | Multi-way MLP head |
| `learn/multiway_dataset.py` | DB rows: hero postflop, `n_active >= 3` |
| `learn/train_multiway_student.py` | Training loop |
| `policy/distilled_policy.py` | `load_best_policy()` → `RouterPolicy` |

## Table sizes

- **Engine:** 2–10 seats (`core/engine.py`).
- **HHFormer:** trained on all ingested hands (any `num_players`).
- **6-max CFR:** `artifacts/solver/preflop_cfr.json`.
- **8/9/10-max:** `solve preflop --positions 8max|9max|10max --production` → `preflop_{n}max.json`; router picks best file via `solver/preflop_artifacts.py`.
- **Fallback:** 6-max chart or `HeuristicPolicy` when ring artifact missing.

## Runtime entry points

- `load_best_policy()` / `load_runtime_policy()`
- `StackedPolicy` (legacy name; uses router)
- League `main_agent`
- `python -m poker_ai policy bench --best`

**League:** 2–10 seats; `league/style_bridge.py` passes opponent style vectors per seat into `play_hand`.

## CLI

```powershell
# Train multi-way student from DB (hero postflop, n_active >= 3)
python -m poker_ai train multiway-student --epochs 20 --device cuda

# With Monker JSON labels (Phase 7c)
python -m poker_ai train multiway-student --monker-dir artifacts/solver/monker_exports
```

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `POKER_AI_MULTIWAY_STUDENT_DIR` | `artifacts/student/multiway_v1` | Multi-way weights |
| `POKER_AI_MONKER_TEACHER_BLEND` | `0.15` | Runtime Monker frequency blend |

## Monker (Phase 7c)

Drop JSON under `artifacts/solver/monker_exports/` → `solve monker-import` → `train multiway-student`. Runtime blends Monker labels when cache keys match. See [PHASE7C_MONKER.md](PHASE7C_MONKER.md).

## Tests

```powershell
python -m pytest tests/test_policy_router.py tests/test_multiway_equity.py -q
```

## Exit criteria (roadmap)

- [x] Router unit tests
- [x] Multi-way equity tests
- [x] HU student isolated (`DistilledPolicy` empty when `n_active >= 3`)
- [x] Replay gate: ≥ 100 DB 3-way flop decisions never hit HU student (`verify_router_gate.py`)
- [x] Full-corpus `train multiway-student`; val MSE in `multiway_v1/metrics.json` (playbook: 5,095 rows, MSE ≈ 0.047)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Expanded: file map, entry points, env, exit criteria, cross-links |
