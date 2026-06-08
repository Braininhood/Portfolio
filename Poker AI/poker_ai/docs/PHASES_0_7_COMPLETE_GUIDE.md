# Phases 0–7 — complete guide (session summary + living reference)

> **Purpose:** Single place that preserves everything from the Phases 0–7 build-out chat (HU vs multi-way routing, TexasSolver install, Monker, commands, paths, troubleshooting).  
> **Maintain:** Update this file when CLI or routing changes; keep [COMMANDS_PHASES_0_7.md](COMMANDS_PHASES_0_7.md) as the command cheat sheet.  
> **Roadmap:** [doc/ROADMAP.md](../../doc/ROADMAP.md).

**Convention:** all commands run from `poker_ai/` (directory containing `pyproject.toml`).

```powershell
cd "D:\Poker AI\poker_ai"
.\.venv\Scripts\Activate.ps1
```

---

## 1. Executive summary

| Area | Status |
|------|--------|
| Phases 0–6 | Scaffold, ingest, engine, features, equity, HHFormer, CFR preflop — **done** per roadmap |
| Phase 7 | TexasSolver (AGPL) HU postflop teacher + mock teacher + cache + distilled student — **implemented** |
| Phase 7b | **RouterPolicy** by `n_active`: HU stack vs multi-way stack — **shipped** |
| Phase 7c | Monker JSON import + multi-way student blend — **implemented** (optional, licensed) |
| TexasSolver install | `solve install-texas` + `register-texas`; corrupt zip detection fixed (2026-05-20) |
| League (Phase 9) | HU + 6/9-max sim, `--until-hours`, `load_best_policy()` → router; see [PHASE9_LEAGUE.md](PHASE9_LEAGUE.md) |

**Runtime rule (every `propose()`):**

```text
n_active = count_active_players(state)   # core/context.py

n_active == 2  →  HuStackPolicy
                 preflop: artifacts/solver/preflop_hu_real.json
                 postflop: DistilledPolicy (Phase 7 student, TexasSolver-trained)

n_active >= 3  →  MultiwayStackPolicy
                 preflop: preflop_cfr.json if num_seats ≤ 6, else HeuristicPolicy
                 postflop: MultiwayPostflopPolicy
                   → multiway student if artifacts/student/multiway_v1/student.safetensors
                   → else MC equity vs n uniform villains (equity/multiway.py)
                   → optional Monker blend (POKER_AI_MONKER_TEACHER_BLEND, default 0.15)
```

**Entry points that use the router:** `load_best_policy()`, `load_runtime_policy()`, `StackedPolicy` (delegates to `RouterPolicy`), league `main_agent`, `policy bench --best`.

**Not routed:** Phase 0–5 training/ingest (all table sizes stored); `league run` is HU-only (2 seats by design).

---

## 2. User environment (this project)

| Item | Value |
|------|--------|
| Workspace | `D:\Poker AI\poker_ai` |
| Corpus | `D:\Poker AI\hand` (~31k hands referenced in session) |
| Python | venv `.venv\Scripts\python.exe` |
| OS | Windows (`win32`) |
| Vendored TexasSolver **source** | `poker_ai/TexasSolver/` (AGPL reference; **not** built by default) |
| TexasSolver **binary** (after install) | `artifacts/third_party/texassolver/v0.2.0/TexasSolver-v0.2.0-Windows/console_solver.exe` |
| Install manifest | `artifacts/third_party/texassolver/install.json` |
| HHFormer | `artifacts/hhformer/v1/weights.safetensors` |
| HU preflop CFR | `artifacts/solver/preflop_hu_real.json` |
| 6-max preflop CFR | `artifacts/solver/preflop_cfr.json` |
| Solver cache (mock/texas) | `artifacts/solver_cache/` |
| HU student | `artifacts/student/v1/student.safetensors` |
| Multi-way student | `artifacts/student/multiway_v1/` |
| Monker example | `artifacts/solver/monker_exports/example_spot.json` |

---

## 3. Phase-by-phase (what exists)

### Phase 0 — Scaffold

- `uv sync`, `task ci`, `python -m poker_ai --help`, editable install.

### Phase 1 — Store + ingest

- `db migrate`, `ingest` on `..\hand`, optional `--train-hhformer`, workers, env caps.

### Phase 2 — Engine + evaluator

- Library + tests; no dedicated CLI.

### Phase 3 — Features

- `features build` → JSONL from DB.

### Phase 4 — Equity

- `equity/range_vs_range.py`, MC/exact; **extension** `equity/multiway.py` for hero vs *n* independent uniform opponents (Phase 7b).

### Phase 5 — HHFormer

- `train hhformer`, `features hhformer-embed`; weights under `artifacts/hhformer/v1/`.

### Phase 6 — CFR preflop

- `solve kuhn`, `solve preflop` HU and 6-max production JSONs.
- Policies: `CFRPolicy`, `HeuristicPolicy`; wired into HU / multi-way **stacks**, not the top-level router alone.

### Phase 7 — TexasSolver bridge + HU student

| Module | Role |
|--------|------|
| `solver/bridge/schemas.py` | `SpotSpec`, solved spot types |
| `solver/bridge/texas.py` | Build `.txt`, subprocess `console_solver`, parse JSON |
| `solver/bridge/install_texas.py` | Download/register zip, `install.json`, discovery |
| `solver/bridge/paths.py` | `default_texas_install_dir()`, vendored `TexasSolver/` paths |
| `solver/bridge/cache.py` | xxhash cache keys |
| `solver/bridge/grid.py` | Curated HU flop grid |
| `solver/bridge/mock_teacher.py` | Phase 4 equity labels without binary |
| `solver/bridge/batch.py` | `solve_grid` batch driver |
| `models/student.py` | MLP on HHFormer `[CLS]` + extras |
| `learn/student_dataset.py`, `learn/train_student.py` | Behavioral cloning |
| `policy/distilled_policy.py` | HU postflop student; **returns empty when `n_active >= 3`** |

**CLI:** `solve install-texas`, `solve register-texas`, `solve texas-status`, `solve grid`, `train student`.

### Phase 7b — Router + multi-way stack

| Module | Role |
|--------|------|
| `core/context.py` | `count_active_players`, `is_heads_up_context`, `is_multiway_context` |
| `policy/router_policy.py` | Routes by `n_active` |
| `policy/hu_stack.py` | HU CFR + distilled |
| `policy/multiway_stack.py` | 6-max CFR or heuristic + multi-way postflop |
| `policy/multiway_postflop.py` | Student / Monker / equity fallback |
| `models/multiway_student.py` | Multi-way head |
| `learn/multiway_dataset.py`, `learn/train_multiway_student.py` | DB imitation rows (`n_active >= 3`) |
| `policy/stacked.py` | `StackedPolicy` → `RouterPolicy` (v0.4.0) |

**Guards:** `DistilledPolicy`, `PostflopEquityPolicy` return no proposal when `n_active >= 3` so the router never double-fires HU logic.

**CLI:** `train multiway-student`.

### Phase 7c — Monker (optional)

| Module | Role |
|--------|------|
| `solver/bridge/monker.py` | Parse JSON, `MonkerTeacherCache`, safe cache keys (xxhash; no `\|` in filenames) |
| `learn/monker_rows.py` | Training rows from exports |

**CLI:** `solve monker-import`, `train multiway-student --monker-dir`.

---

## 4. TexasSolver — install, discovery, troubleshooting

### What TexasSolver is used for

- **HU postflop teacher only** (`backend=texas` in solver cache).
- Multi-way postflop uses **DB student + Monker + n-way equity**, not TexasSolver.

### Install paths (priority)

1. `POKER_AI_TEXAS_SOLVER_EXE` if set and file exists.
2. `artifacts/third_party/texassolver/install.json` from `solve install-texas` or `solve register-texas`.
3. Scan under install dir for `console_solver.exe` / `console_solver`.
4. Vendored `TexasSolver/resources` for compairer tables if needed; binary still required for `backend=texas`.

### Commands

```powershell
# Auto-download official release (v0.2.0 default)
python -m poker_ai solve install-texas
python -m poker_ai solve install-texas --force   # re-download if corrupt

# Status + driver probe
python -m poker_ai solve texas-status

# Manual zip (browser download) — skips network
python -m poker_ai solve register-texas --zip "C:\Downloads\TexasSolver-v0.2.0-Windows.zip"

# Local CMake build
python -m poker_ai solve register-texas --exe "D:\Poker AI\poker_ai\TexasSolver\build\...\console_solver.exe"
```

Wrappers: `scripts/install_texassolver.ps1`, `scripts/install_texassolver.sh`.

### Release assets (GitHub bupticybee/TexasSolver)

| OS | Zip name | Approx. size |
|----|----------|----------------|
| Windows | `TexasSolver-v0.2.0-Windows.zip` | ~41 MB |
| macOS | `TexasSolver-v0.2.0-MacOs.zip` | ~25+ MB |
| Linux | `TexasSolver-v0.2.0-Linux.zip` | ~10+ MB |

### BadZipFile / corrupt download (fixed 2026-05-20)

**Symptom:** `BadZipFile: File is not a zip file` after `solve install-texas`.

**Cause:** Truncated download saved as zip (e.g. **5,242,880 bytes** = 5×2²⁰ on Windows; valid release **~41 MB**). Often HTML error page or timeout.

**Fix in code:** `_is_valid_zip()` checks `PK` header + minimum size; invalid file deleted; re-download with 600s timeout; GitHub API asset URL when available; clear error pointing to `register-texas --zip`.

**User recovery:**

1. Delete bad zip under `artifacts/third_party/texassolver/`.
2. `python -m poker_ai solve install-texas --force`, or browser download + `register-texas --zip`.

### Vendored source vs binary

- `poker_ai/TexasSolver/` = full C++ tree + `resources/` for reference and optional local build.
- Bridge runs **console release**, not CMake by default.
- See [../TexasSolver/README.poker_ai.md](../TexasSolver/README.poker_ai.md).

### After install — teacher workflow

```powershell
python -m poker_ai solve grid --n-spots 200 --backend texas
python -m poker_ai train student --epochs 30 --device cpu
```

Without TexasSolver: `solve grid --backend mock` still fills cache for student training.

---

## 5. Environment variables (Phases 7–7c)

| Variable | Default | Meaning |
|----------|---------|---------|
| `POKER_AI_TEXAS_SOLVER_EXE` | (auto) | Override console binary path |
| `POKER_AI_TEXAS_SOLVER_INSTALL_DIR` | `artifacts/third_party/texassolver` | Install root |
| `POKER_AI_SOLVER_CACHE_DIR` | `artifacts/solver_cache` | Teacher spot cache |
| `POKER_AI_STUDENT_ARTIFACT_DIR` | `artifacts/student/v1` | HU distilled student |
| `POKER_AI_MULTIWAY_STUDENT_DIR` | `artifacts/student/multiway_v1` | Multi-way student (via settings) |
| `POKER_AI_MONKER_EXPORT_DIR` | `artifacts/solver/monker_exports` | Monker JSON directory |
| `POKER_AI_MONKER_TEACHER_BLEND` | `0.15` | Runtime Monker frequency blend |

---

## 6. Automatic routing audit (Phases 0–7)

| Phase | Component | `n_active == 2` | `n_active >= 3` |
|-------|-----------|-----------------|-----------------|
| 0–3 | Ingest, engine, features | All table sizes | Same |
| 4 | `equity/multiway.py` | HU equity via stacks | MC vs *n* villains |
| 5 | HHFormer | All hands | Same embeddings |
| 6 preflop | Stacks | `preflop_hu_real.json` | `preflop_cfr.json` if seats≤6, else heuristic (7–10) |
| 7 postflop | Student policies | TexasSolver-distilled HU | DB + Monker + multi-way equity |
| 7 guards | `DistilledPolicy`, `PostflopEquityPolicy` | Active | Empty proposals |
| Legacy | `StackedPolicy` | → `RouterPolicy` | Same |

**Table sizes:** engine 2–10 seats; 6-max CFR when `num_seats ≤ 6`; 7–10 heuristic preflop until extended solves.

---

## 7. Tests (quick matrix)

```powershell
python -m pytest tests/test_smoke.py tests/test_features_phase3.py tests/test_core_*.py `
  tests/test_equity_phase4.py tests/test_hhformer_phase5.py tests/test_solver_phase6.py `
  tests/test_solver_phase7.py tests/test_policy_router.py tests/test_multiway_equity.py `
  tests/test_monker_import.py tests/test_monker_bridge.py -q
```

| Test file | Covers |
|-----------|--------|
| `test_solver_phase7.py` | Cache, mock teacher, texas parse, install manifest, `_is_valid_zip` |
| `test_policy_router.py` | HU vs multi-way routing |
| `test_multiway_equity.py` | n-way MC equity |
| `test_monker_import.py`, `test_monker_bridge.py` | Monker JSON |
| `test_solver_phase6.py` | CFR; `StackedPolicy` → `RouterPolicy` |

ML gate (after grid + train): `pytest tests/test_solver_phase7.py -m ml -q`

---

## 8. End-to-end command order (fresh machine)

See [COMMANDS_PHASES_0_7.md](COMMANDS_PHASES_0_7.md) for per-phase tables. Typical sequence:

1. `db migrate` → `ingest`
2. `train hhformer` → `features hhformer-embed`
3. `solve preflop` HU + 6-max
4. `solve install-texas` → `solve grid` → `train student`
5. `train multiway-student` (optional)
6. `solve monker-import` (optional, licensed)

---

## 9. v1 done · v2 TODO

**v1 complete (June 2026):**

- [x] Phase 7 exit: student MSE ≤ 0.05 on 1k spots (`solve validate-student`)
- [x] Phase 7b: `train multiway-student` on full corpus; MSE in `multiway_v1/metrics.json`
- [x] Phase 7b: replay gate — `verify_router_gate.py`
- [x] Phase 7c: Monker import path + MODEL_CARD license
- [x] League: HU + 6/8/9-max mixed formats (not HU-only)

**v2 backlog** ([ROADMAP §v2 backlog](../../doc/ROADMAP.md#v2-backlog--next-version-todo)):

- [ ] MTT / ICM product (blind schedules, payouts, table balancing)
- [ ] Full blueprint feature set (extended Phase 3)
- [ ] Full AIVAT theory; league on real DB replay
- [ ] Optional: `train multiway-student` in one `pipeline run` flag

---

## 10. Document index

| Doc | Content |
|-----|---------|
| [COMMANDS_PHASES_0_7.md](COMMANDS_PHASES_0_7.md) | Command cheat sheet + changelog |
| [PHASE7_SOLVER_BRIDGE.md](PHASE7_SOLVER_BRIDGE.md) | Phase 7 TexasSolver + student detail |
| [PHASE7B_POLICY_ROUTER.md](PHASE7B_POLICY_ROUTER.md) | Router + stacks |
| [PHASE7C_MONKER.md](PHASE7C_MONKER.md) | Monker import + blend |
| [PHASE6_SOLVER.md](PHASE6_SOLVER.md) | CFR preflop |
| [PHASE5_HHFORMER.md](PHASE5_HHFORMER.md) | Foundation model |
| [PHASE4_EQUITY.md](PHASE4_EQUITY.md) | Equity module |
| [../TexasSolver/README.poker_ai.md](../TexasSolver/README.poker_ai.md) | Vendored solver tree |
| [../../doc/ROADMAP.md](../../doc/ROADMAP.md) | Canonical roadmap + exit criteria |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial complete guide: session summary, routing, TexasSolver install/troubleshooting, file map |
| 2026-05-20 | TexasSolver `install_texas.py` zip validation; `solve register-texas`; BadZipFile fix |
