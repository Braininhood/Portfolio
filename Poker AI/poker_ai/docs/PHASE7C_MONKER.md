# Phase 7c — Monker multi-way teacher

> **Commands:** [COMMANDS_PHASES_0_7.md](COMMANDS_PHASES_0_7.md) · **Router context:** [PHASE7B_POLICY_ROUTER.md](PHASE7B_POLICY_ROUTER.md) · **Full guide:** [PHASES_0_7_COMPLETE_GUIDE.md](PHASES_0_7_COMPLETE_GUIDE.md).

**Goal.** Import licensed **MonkerSolver** (or compatible) JSON exports as offline postflop labels for **3+ players**; optional runtime blend into `MultiwayPostflopPolicy` (same pattern as TexasSolver for HU, but multi-way only).

**Not a substitute for TexasSolver:** Monker does not replace the HU AGPL teacher; it supplements multi-way training/runtime.

## Export format

Place licensed Monker (or compatible) JSON under `artifacts/solver/monker_exports/`:

```json
{
  "board": "Qs,Jh,2h",
  "n_active": 3,
  "num_seats": 6,
  "pot_chips": 12,
  "effective_stack": 88,
  "strategy": {
    "fold": 0.08,
    "check": 0.42,
    "bet_33": 0.28,
    "bet_66": 0.15,
    "allin": 0.07
  }
}
```

**Example in repo:** `artifacts/solver/monker_exports/example_spot.json`

## Implementation

| Module | Role |
|--------|------|
| `solver/bridge/monker.py` | JSON parser, `MonkerTeacherCache`, `solve_multiway_spot()` |
| `learn/monker_rows.py` | Training rows merged into multi-way dataset |
| `policy/multiway_postflop.py` | Runtime lookup + blend |

Cache keys use **xxhash**; filenames avoid `|` and other unsafe characters.

## CLI

```powershell
# Import into cache + count training rows
python -m poker_ai solve monker-import -d artifacts/solver/monker_exports

# Train multi-way student (DB rows + all JSON in monker dir)
python -m poker_ai train multiway-student --monker-dir artifacts/solver/monker_exports
```

## Runtime

`load_best_policy()` → `RouterPolicy` → `MultiwayStackPolicy` → `MultiwayPostflopPolicy`.

When a spot key matches the Monker cache, frequencies are blended into the multi-way student output:

- **`POKER_AI_MONKER_TEACHER_BLEND`** — default `0.15` (0 = off, 1 = Monker only).

## Environment

| Variable | Default |
|----------|---------|
| `POKER_AI_MONKER_EXPORT_DIR` | `artifacts/solver/monker_exports` |
| `POKER_AI_MONKER_TEACHER_BLEND` | `0.15` |

## License

MonkerSolver is **commercial** — only import exports you are licensed to use. Document provenance in `artifacts/student/multiway_v1/MODEL_CARD.md`.

## Tests

```powershell
python -m pytest tests/test_monker_import.py tests/test_monker_bridge.py -q
```

## Exit criteria (roadmap)

- [x] ≥ 500 imported spots train without error
- [x] License documented in `artifacts/student/multiway_v1/MODEL_CARD.md`

**Status:** **Done** (June 2026 playbook).

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Expanded: implementation map, env, tests, example path, TexasSolver distinction |
