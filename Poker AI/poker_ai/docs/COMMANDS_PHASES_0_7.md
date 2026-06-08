# Commands — Phases 0–7 (living reference)

> **Maintain this file** whenever CLI, defaults, or phase workflows change.  
> **Full narrative (routing, TexasSolver, troubleshooting):** [PHASES_0_7_COMPLETE_GUIDE.md](PHASES_0_7_COMPLETE_GUIDE.md).  
> Canonical roadmap: [doc/ROADMAP.md](../../doc/ROADMAP.md). Per-phase detail: `docs/PHASE*.md`.

**Convention:** run everything from the `poker_ai/` directory (where `pyproject.toml` lives).

```powershell
cd "D:\Poker AI\poker_ai"
.\.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate     # Linux/macOS
```

Use `python -m poker_ai …` or the `poker-ai` script after `pip install -e .`.

---

## Phase 0 — Scaffold (tooling + CI)

| Step | Command |
|------|---------|
| Sync env | `uv sync --all-extras` |
| Lint + format + types + tests | `task ci` |
| Without Task | `uv run ruff check .` · `uv run ruff format --check .` · `uv run mypy src tests` · `uv run pytest` |
| CLI help | `python -m poker_ai --help` |
| Version | `python -m poker_ai version` |
| Install package (editable) | `pip install -e ".[dev]"` |

---

## Phase 1 — Canonical store + ingest

| Step | Command |
|------|---------|
| Migrate DB | `python -m poker_ai db migrate` |
| DB revision | `python -m poker_ai db status` |
| Ingest file or tree | `python -m poker_ai ingest "..\hand\5"` |
| Dev cap | `python -m poker_ai ingest "..\hand" --max-hands 5000` |
| Parallel ingest | `python -m poker_ai ingest "..\hand\5" --workers 7` |
| Ingest + HHFormer train | `python -m poker_ai ingest "..\hand\5" --train-hhformer` |

**Env (optional):** `POKER_AI_DATABASE_URL` · `POKER_AI_INGEST_MAX_HANDS` · `POKER_AI_INGEST_REQUIRE_COMPLETE_HANDS` · `POKER_AI_INGEST_TRAIN_HHFORMER=1`

**Tests:** `python -m pytest tests/test_phh_ingest.py tests/test_ingest_*.py -q`

**Phase 1 ingest gate (required, text-only ~19k hands in <90s):** `python scripts/verify_phase1_ingest.py` · or `POKER_AI_PERF_INGEST=1` · `pytest tests/test_ingest_perf.py -q`

---

## Phase 2 — Game engine + evaluator

No dedicated Typer subcommand — library + tests.

| Step | Command |
|------|---------|
| Core tests | `python -m pytest tests/test_core_cards.py tests/test_core_evaluator.py tests/test_core_engine.py tests/test_core_profiles.py -q` |
| Full suite + coverage | `python -m pytest tests -q --cov=poker_ai --cov-fail-under=100` |
| Evaluator perf (optional) | unset `POKER_AI_SKIP_PERF`; `python -m pytest tests/test_core_evaluator.py::test_evaluator_seven_card_throughput -q` |

**Env:** `POKER_AI_PERF_EVAL_MIN_RATE` · `POKER_AI_SKIP_PERF=1` (skip perf)

---

## Phase 3 — Features + range vectors

| Step | Command |
|------|---------|
| Build feature JSONL from DB | `python -m poker_ai features build -o features.jsonl` |
| Since date (UTC) | `python -m poker_ai features build --since 2024-01-01 -o features.jsonl` |
| Parallel | `python -m poker_ai features build --workers 7` |

**Tests:** `python -m pytest tests/test_features_phase3.py -q`

---

## Phase 4 — Range-vs-range equity

| Task | Command |
|------|---------|
| Spot equity | `python -m poker_ai equity spot --hero "Ah Kd" --board "Qs Jh 2h" --villain random` |
| DB backfill | `python -m poker_ai equity backfill` |
| Tests (fast) | `$env:POKER_AI_SKIP_PERF = "1"` · `python -m pytest tests/test_equity_phase4.py tests/test_equity_backfill.py -q` |

| Step | Command |
|------|---------|
| Tests + slow/perf | `python -m pytest tests/test_equity_phase4.py -q -m slow` |
| Bench | `python scripts/bench_equity.py` |

**Env:** `POKER_AI_EQUITY_WORKERS` · `POKER_AI_SKIP_PERF`

**Doc:** [PHASE4_EQUITY.md](PHASE4_EQUITY.md)

---

## Phase 5 — HHFormer foundation model

| Step | Command |
|------|---------|
| GPU torch (Windows RTX 50-series) | `.\scripts\install_torch_cuda.ps1` |
| Train | `python -m poker_ai train hhformer --epochs 50 --batch-size 256 --device cuda --log-every 50` |
| Train (CPU) | `python -m poker_ai train hhformer --epochs 30 --device cpu --num-workers 0` |
| Export embeddings | `python -m poker_ai features hhformer-embed -o data/processed/hhformer_embeddings.jsonl` |
| Embeddings + equity | `python -m poker_ai features hhformer-embed --with-equity -w artifacts/hhformer/v1` |

**Artifacts:** `artifacts/hhformer/v1/weights.safetensors` · `metrics.json` · `MODEL_CARD.md`

**Tests:** `python -m pytest tests/test_hhformer_phase5.py -q`

**Doc:** [PHASE5_HHFORMER.md](PHASE5_HHFORMER.md)

---

## Phase 6 — CFR preflop + policies

| Step | Command |
|------|---------|
| Kuhn smoke (CFR+) | `python -m poker_ai solve kuhn --iters 10000` |
| HU preflop (production) | `python -m poker_ai solve preflop --positions hu --production --equity-mode real --workers 7 -o artifacts/solver/preflop_hu_real.json` |
| 6-max preflop (production) | `python -m poker_ai solve preflop --positions 6max --production --equity-mode real --workers 7 --max-raises 1 -o artifacts/solver/preflop_cfr.json` |
| 8/9/10-max (production, long) | `python -m poker_ai solve preflop --positions 9max --production --equity-mode real --workers 8` |
| Exploitability (slow) | add `--measure-exploitability` to `solve preflop` |
| Pipeline (ingest → features → CFR) | `python -m poker_ai pipeline run --corpus "..\hand\5" --skip-train --skip-embed --workers 7` |

**Env:** `POKER_AI_NUM_WORKERS=7`

**Tests:** `python -m pytest tests/test_solver_phase6.py -q`  
**Slow gates:** `python -m pytest tests/test_solver_phase6.py -m slow -q`

**Doc:** [PHASE6_SOLVER.md](PHASE6_SOLVER.md)

---

## Phase 7 — TexasSolver bridge + distilled student (HU postflop only)

TexasSolver is the **HU** (`n_active == 2`) postflop teacher. Multi-way uses Phase 7b/7c (DB + Monker + equity), not TexasSolver.

| Step | Command |
|------|---------|
| Install TexasSolver (download OS zip) | `python -m poker_ai solve install-texas` |
| Re-install (delete bad zip + re-download) | `python -m poker_ai solve install-texas --force` |
| Register local zip (no download) | `python -m poker_ai solve register-texas --zip "C:\Downloads\TexasSolver-v0.2.0-Windows.zip"` |
| Register built `console_solver` | `python -m poker_ai solve register-texas --exe "PATH\to\console_solver.exe"` |
| Install wrapper (PS) | `.\scripts\install_texassolver.ps1` |
| Install wrapper (bash) | `./scripts/install_texassolver.sh` |
| Status (`installed`, `driver_available`) | `python -m poker_ai solve texas-status` |
| Teacher grid (mock, no binary) | `python -m poker_ai solve grid --n-spots 1000 --backend mock` |
| Teacher grid (TexasSolver AGPL) | `python -m poker_ai solve grid --n-spots 200 --backend texas` |
| Train HU student | `python -m poker_ai train student --epochs 30 --device cpu` |
| Validate gates (MSE + p99) | `python -m poker_ai solve validate-student --n-spots 1000 --backend mock` |
| Runtime policy name | `python -c "from poker_ai.policy.distilled_policy import load_best_policy; print(load_best_policy().name)"` |
| Policy latency bench | `python -m poker_ai policy bench --samples 500 -o reports/policy_bench.json` |
| Pipeline (grid + student) | `python -m poker_ai pipeline run --skip-ingest --skip-features --skip-solve --solver-grid --train-student --student-spots 512 --student-epochs 20` |

**Install layout (default):**

- Zip cache: `artifacts/third_party/texassolver/TexasSolver-v0.2.0-Windows.zip` (~41 MB valid on Windows)
- Unpacked: `artifacts/third_party/texassolver/v0.2.0/TexasSolver-v0.2.0-Windows/console_solver.exe`
- Manifest: `artifacts/third_party/texassolver/install.json`
- Vendored **source** (not auto-built): `TexasSolver/`

**Troubleshooting `BadZipFile`:** truncated download (~5 MB) is rejected; delete zip and `--force`, or `register-texas --zip`. See [PHASE7_SOLVER_BRIDGE.md](PHASE7_SOLVER_BRIDGE.md).

**Env:** `POKER_AI_TEXAS_SOLVER_EXE` · `POKER_AI_TEXAS_SOLVER_INSTALL_DIR` · `POKER_AI_SOLVER_CACHE_DIR` · `POKER_AI_STUDENT_ARTIFACT_DIR`

**Artifacts:** `artifacts/solver_cache/` · `artifacts/student/v1/student.safetensors`

**Tests:** `python -m pytest tests/test_solver_phase7.py -q`  
**ML gate (after grid + train):** `python -m pytest tests/test_solver_phase7.py -m ml -q`

**Doc:** [PHASE7_SOLVER_BRIDGE.md](PHASE7_SOLVER_BRIDGE.md) · [PHASES_0_7_COMPLETE_GUIDE.md](PHASES_0_7_COMPLETE_GUIDE.md) · [../TexasSolver/README.poker_ai.md](../TexasSolver/README.poker_ai.md)

---

## Phase 7b — HU vs multi-way router

| Step | Command |
|------|---------|
| Train multi-way student (DB imitation) | `python -m poker_ai train multiway-student --epochs 20 --device cuda` |
| Train with Monker labels | `python -m poker_ai train multiway-student --monker-dir artifacts/solver/monker_exports` |
| Router tests | `python -m pytest tests/test_policy_router.py tests/test_multiway_equity.py -q` |

**Runtime rule:** `n_active = count_active_players(state)` — re-evaluated every `propose()`.

| `n_active` | Brain | Preflop | Postflop |
|------------|-------|---------|----------|
| `== 2` | `HuStackPolicy` | `preflop_hu_real.json` | Phase 7 `DistilledPolicy` |
| `>= 3` | `MultiwayStackPolicy` | `preflop_{n}max.json` via `preflop_artifacts` when present | student / Monker blend / `equity/multiway.py` |

**Entry points:** `load_best_policy()`, `StackedPolicy` (→ `RouterPolicy`), league `main_agent`, `policy bench --best`.

**Guards:** `DistilledPolicy` and `PostflopEquityPolicy` return empty when `n_active >= 3`.

**Env:** `POKER_AI_MULTIWAY_STUDENT_DIR` (default `artifacts/student/multiway_v1`) · `POKER_AI_MONKER_TEACHER_BLEND` (default `0.15`)

**Artifacts:** `artifacts/solver/preflop_hu_real.json` · `artifacts/solver/preflop_cfr.json` · `artifacts/student/multiway_v1/student.safetensors`

**Doc:** [PHASE7B_POLICY_ROUTER.md](PHASE7B_POLICY_ROUTER.md) · [PHASES_0_7_COMPLETE_GUIDE.md](PHASES_0_7_COMPLETE_GUIDE.md)

---

## Phase 7c — Monker exports (optional, commercial license)

| Step | Command |
|------|---------|
| Import Monker JSON | `python -m poker_ai solve monker-import -d artifacts/solver/monker_exports` |
| Train with Monker labels | `python -m poker_ai train multiway-student --monker-dir artifacts/solver/monker_exports` |

**Example spot:** `artifacts/solver/monker_exports/example_spot.json`

**Env:** `POKER_AI_MONKER_EXPORT_DIR` · `POKER_AI_MONKER_TEACHER_BLEND` (runtime blend into multi-way student)

**Doc:** [PHASE7C_MONKER.md](PHASE7C_MONKER.md)

---

## End-to-end (Phases 1 → 7, typical order)

```powershell
cd "D:\Poker AI\poker_ai"

# 1 — Store
python -m poker_ai db migrate
python -m poker_ai ingest "..\hand\5" --workers 7

# 2–3 — Features (optional JSONL for analysis)
python -m poker_ai features build -o data/processed/features.jsonl --workers 7

# 5 — Foundation model
python -m poker_ai train hhformer --epochs 50 --device cuda --num-workers 0
python -m poker_ai features hhformer-embed -o data/processed/hhformer_embeddings.jsonl

# 6 — Preflop CFR
python -m poker_ai solve preflop --positions hu --production --equity-mode real --workers 7 -o artifacts/solver/preflop_hu_real.json
python -m poker_ai solve preflop --positions 6max --production --equity-mode real --workers 7 -o artifacts/solver/preflop_cfr.json

# 7 — Postflop teacher + student (HU)
python -m poker_ai solve install-texas
python -m poker_ai solve texas-status
python -m poker_ai solve grid --n-spots 1000 --backend mock
# optional real teacher:
# python -m poker_ai solve grid --n-spots 200 --backend texas
python -m poker_ai train student --epochs 30 --device cpu

# 7b — Multi-way (optional)
python -m poker_ai train multiway-student --epochs 20 --device cuda

# 7c — Monker (optional, licensed)
# python -m poker_ai solve monker-import -d artifacts/solver/monker_exports
```

**One-shot pipeline (subset):**

```powershell
python -m poker_ai pipeline run --corpus "..\hand\5" --workers 7 `
  --solver-grid --train-student --student-spots 512 --student-epochs 20 `
  --solver-backend mock
```

---

## Quick test matrix (all phases)

```powershell
python -m pytest tests/test_smoke.py tests/test_features_phase3.py tests/test_core_*.py `
  tests/test_equity_phase4.py tests/test_hhformer_phase5.py tests/test_solver_phase6.py `
  tests/test_solver_phase7.py tests/test_policy_router.py tests/test_multiway_equity.py `
  tests/test_monker_import.py tests/test_monker_bridge.py -q `
  --ignore-glob="*slow*" -o "POKER_AI_SKIP_PERF=1"
```

Or set `$env:POKER_AI_SKIP_PERF = "1"` first, then run `python -m pytest tests -q` (longer).

---

## Changelog (edit when you update this file)

| Date | Change |
|------|--------|
| 2026-05-20 | Initial Phases 0–7 command sheet; `solve install-texas`, `solve texas-status` |
| 2026-05-20 | `solve register-texas`; install `--force`; BadZipFile troubleshooting; Phase 7b/7c env; link to `PHASES_0_7_COMPLETE_GUIDE.md` |
