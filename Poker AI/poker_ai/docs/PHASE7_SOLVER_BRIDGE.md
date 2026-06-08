# Phase 7 — TexasSolver bridge + distilled student

> **Canonical Phase 7 reference** — keep [doc/ROADMAP.md](../../doc/ROADMAP.md) exit criteria in sync with this file.  
> **Full Phases 0–7 guide (routing + install troubleshooting):** [PHASES_0_7_COMPLETE_GUIDE.md](PHASES_0_7_COMPLETE_GUIDE.md).  
> **Commands cheat sheet:** [COMMANDS_PHASES_0_7.md](COMMANDS_PHASES_0_7.md).

**Goal.** Wrap **TexasSolver** (AGPL) as an offline **HU** teacher (`n_active == 2` postflop only), cache solved spots, and distil action frequencies into a fast neural student on top of HHFormer embeddings. Multi-way postflop is Phase 7b/7c (see [PHASE7B_POLICY_ROUTER.md](PHASE7B_POLICY_ROUTER.md)).

## Architecture

```
TexasSolver (console)  ─┐
Mock equity teacher    ─┼─► artifacts/solver_cache/  ─► train student  ─► DistilledPolicy
                        │         (xxhash keys)              │
HHFormer [CLS] 256-d ───┘                                    └── student.safetensors
```

**Integrations**

| Phase | Link |
|-------|------|
| 4 | Mock teacher uses MC / exact equity |
| 5 | Student conditions on frozen HHFormer `[CLS]` |
| 6 | Preflop via HU / multi-way stacks inside `RouterPolicy` |
| 7b | `load_best_policy()` → `RouterPolicy`; `DistilledPolicy` only when `n_active == 2` |

## Commands (from `poker_ai/`)

```powershell
cd "D:\Poker AI\poker_ai"

# 1) Fill teacher cache (mock = no TexasSolver install; texas = AGPL binary)
python -m poker_ai solve grid --n-spots 1000 --backend mock

# Optional: real TexasSolver (auto-install for your OS, then use texas backend)
python -m poker_ai solve install-texas
python -m poker_ai solve texas-status
python -m poker_ai solve grid --n-spots 200 --backend texas --continue-on-error --texas-threads 2

# Manual path override (if you installed elsewhere)
$env:POKER_AI_TEXAS_SOLVER_EXE = "C:\path\to\console_solver.exe"

# 2) Train student (requires artifacts/hhformer/v1/weights.safetensors)
python -m poker_ai train student --epochs 30 --device cpu

# 3) Runtime policy auto-selects student when weights exist
python -c "from poker_ai.policy.distilled_policy import load_best_policy; print(load_best_policy().name)"
```

### TexasSolver install commands

| Command | Purpose |
|---------|---------|
| `solve install-texas` | Download GitHub release zip for this OS, unpack, write `install.json` |
| `solve install-texas --force` | Delete corrupt/partial zip and re-download |
| `solve register-texas --zip PATH` | Unpack a browser-downloaded zip (no network) |
| `solve register-texas --exe PATH` | Register a locally built `console_solver` |
| `solve texas-status` | `installed`, paths, `driver_available` |

**Implementation:** `solver/bridge/install_texas.py`, `solver/bridge/paths.py`, discovery in `solver/bridge/texas.py` (`resolve_texas_bundle()`).

**Discovery order:** `POKER_AI_TEXAS_SOLVER_EXE` → `install.json` → scan install dir → vendored `TexasSolver/resources` for tables only.

| OS | Release asset | Valid zip size (approx.) |
|----|----------------|--------------------------|
| Windows | `TexasSolver-v0.2.0-Windows.zip` | ≥ 30 MB (~41 MB release) |
| macOS | `TexasSolver-v0.2.0-MacOs.zip` | ≥ 25 MB |
| Linux | `TexasSolver-v0.2.0-Linux.zip` | ≥ 10 MB |

Default install root: `artifacts/third_party/texassolver/` (gitignored).  
Unpacked example (Windows): `.../v0.2.0/TexasSolver-v0.2.0-Windows/console_solver.exe`.

Wrappers: `scripts/install_texassolver.ps1`, `scripts/install_texassolver.sh`.

Vendored source under `TexasSolver/` is AGPL reference + `resources/`; the bridge runs the **console** release binary, not a default CMake build. See [../TexasSolver/README.poker_ai.md](../TexasSolver/README.poker_ai.md).

**Troubleshooting `BadZipFile` / corrupt download**

- **Symptom:** `BadZipFile: File is not a zip file` after `install-texas`.
- **Cause:** Truncated download (e.g. **5,242,880 bytes** on Windows vs **~41 MB** valid zip); may be HTML error page or timeout.
- **Fix:** Installer validates `PK` header + minimum size, deletes bad file, retries (600s timeout, GitHub API asset URL when available).
- **Recovery:** `solve install-texas --force`, or manual download from [releases](https://github.com/bupticybee/TexasSolver/releases) then:

```powershell
python -m poker_ai solve register-texas --zip "C:\Downloads\TexasSolver-v0.2.0-Windows.zip"
```

Built from vendored source:

```powershell
python -m poker_ai solve register-texas --exe "D:\Poker AI\poker_ai\TexasSolver\build\...\console_solver.exe"
```

### `solve grid`

| Flag | Default | Meaning |
|------|---------|---------|
| `--n-spots` | 128 | Curated HU flop grid size (same `seed` → same keys) |
| `--cache-dir` | `artifacts/solver_cache` | Disk cache root |
| `--backend` | `auto` | `mock` \| `texas` \| `auto` |
| `--refresh` | off | Re-solve even when `spots/<key>.json` exists |
| `--continue-on-error` | off | Skip spots where `console_solver` crashes; log `failed_spots.jsonl` |
| `--texas-threads` | 2 | Threads passed to TexasSolver (lower = more stable on Windows) |

**Cache behavior:** Keys are board+ranges+tree only — **not** backend. `solve grid --backend texas` **skips** existing files (including **mock**). To train on Texas labels only:

1. Fresh dir: `--cache-dir artifacts/solver_cache_texas_only`, or  
2. Delete non-texas `spots/*.json`, or  
3. `--refresh --backend texas` (slow; re-solves all keys).

**Windows crash** `3221225477` (access violation): use `--continue-on-error --texas-threads 1`. Output path uses absolute `dump_result` path (fixed in bridge).

**Parser:** TexasSolver v0.2 JSON uses per-combo strategy lists; `parse_result_json` aggregates to student actions.

### `train student`

| Flag | Default | Meaning |
|------|---------|---------|
| `--cache-dir` | `artifacts/solver_cache` | Teacher labels |
| `--hhformer-dir` | `artifacts/hhformer/v1` | Frozen encoder weights |
| `-o` | `artifacts/student/v1` | Output `student.safetensors` + `MODEL_CARD.md` |

## Cache keys

`(board_hash, sizing_tree_hash, ranges_hash)` → single xxhash `cache_key` under `artifacts/solver_cache/spots/<key>.json`.

## Exit criteria

| Criterion | How to verify |
|-----------|----------------|
| MSE ≤ 0.05 vs teacher (1k spots) | `python -m poker_ai solve validate-student --n-spots 1000` or `pytest tests/test_solver_phase7.py -m ml` |
| Inference p99 < 10 ms CPU | `solve validate-student` or `test_distilled_inference_latency_p99` |
| AGPL documented | `artifacts/student/v1/MODEL_CARD.md` cites TexasSolver |

## License

TexasSolver is **AGPL-3.0**. Rows with `backend=texas` are derived works. The student code is MIT; do not redistribute teacher caches or AGPL binaries without compliance.

## Pipeline integration

```powershell
# CFR + teacher grid + student distil in one run
python -m poker_ai pipeline run --skip-ingest --skip-features --skip-solve `
  --solver-grid --train-student --student-spots 512 --student-epochs 20
```

## Policy bench (p99 latency)

```powershell
python -m poker_ai policy bench --samples 500 -o reports/policy_bench.json
```

## League (Phase 9 — student as `main_agent`)

See [PHASE9_LEAGUE.md](PHASE9_LEAGUE.md) for schedules and promotion gates.

```powershell
python -m poker_ai league run --until-hours 0.3 --until-hu --table-sizes hu,6max,9max --hands-per-matchup 100 --workers 16
python -m poker_ai league leaderboard
```

Leaderboard fields:

- **bb_per_100** — net chips vs 100 BB start stack, per 100 hands (zero-sum across all agents).
- **chip_balance** — sum of all agents' chips won (must be **0**).
- **elo** — head-to-head hand wins (independent of bb/100 scale).

## Tests

```powershell
pytest tests/test_solver_phase7.py -q
pytest tests/test_solver_phase7.py -m ml -q
pytest tests/test_league_phase9.py -q
```

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | `install_texas.py` zip validation; `register-texas`; BadZipFile troubleshooting; HU-only scope note; links to complete guide |
