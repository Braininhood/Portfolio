# poker_ai

Canonical **local-first** No-Limit Hold’em AI package for this workspace. External AI APIs are not used; models are trained and served on your hardware.

## Quickstart

1. Install [uv](https://docs.astral.sh/uv/) and [Task](https://taskfile.dev/installation/). If PowerShell reports `uv` as unrecognized, run `python -m pip install -U uv` and use **`python -m uv`** instead of `uv`, or add your Python **Scripts** directory to `PATH`.
2. **Use Python 3.11** (repo default; matches GitHub CI). Python **3.14** breaks `uv sync --all-extras` because `pyarrow` has no Windows wheel and tries to compile (needs CMake).

   ```powershell
   cd poker_ai
   uv python install 3.11
   uv sync --all-extras --python 3.11
   ```

   Or skip Parquet analytics (no `pyarrow`): `uv sync --extra dev --extra ml` on any 3.11–3.13 interpreter.

3. From this directory:

   ```bash
   uv sync --all-extras
   task ci
   python -m poker_ai --help
   ```

   If `uv` is not on `PATH`, use:

   ```bash
   python -m uv sync --all-extras
   python -m uv run task ci
   python -m uv run python -m poker_ai --help
   ```

   If [Task](https://taskfile.dev/installation/) is not installed, run the same checks manually (use `python -m uv run` if `uv` is not on `PATH`):

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src tests
   uv run pytest
   ```

   PowerShell without `task` on `PATH` (equivalent to `task ci`):

   ```powershell
   python -m uv run ruff check .
   python -m uv run ruff format --check .
   python -m uv run mypy src tests
   python -m uv run pytest
   ```

   If you see **`No module named poker_ai`**, you ran the wrong interpreter. From this directory use the project venv or `uv run`:

   ```powershell
   .\.venv\Scripts\python.exe -m poker_ai db migrate
   # or (after `python -m uv sync --all-extras`):
   python -m uv run python -m poker_ai db migrate
   ```

4. Read the **full plan and architecture** in the repo root `doc/` folder (not duplicated here):
   - [../doc/ROADMAP.md](../doc/ROADMAP.md) — phased delivery
   - [../doc/POKER_AI_BLUEPRINT.md](../doc/POKER_AI_BLUEPRINT.md) — target architecture
   - [../doc/SECURITY_AND_COMPLIANCE.md](../doc/SECURITY_AND_COMPLIANCE.md) — compliance boundaries
   - [../doc/WEB_IMPLEMENTATION_GUIDE.md](../doc/WEB_IMPLEMENTATION_GUIDE.md) — web UI (W7–**W10**; W9 install/smoke/compliance; W10 research panels)

### Production install (W9)

| OS | Command |
|----|---------|
| Windows | `powershell -ExecutionPolicy Bypass -File scripts\install.ps1` (from `poker_ai/`) |
| Linux / macOS | `./scripts/install.sh` |

Builds `apps/web/dist`, runs migrations, starts `serve --no-web` (API serves the dashboard on port 8000). See [../doc/DATASHEET.md](../doc/DATASHEET.md).

Optional environment overrides: copy `.env.example` to `.env`; variables are prefixed with `POKER_AI_`.

## Workspace layout

**Work directory (this package):** `poker_ai/` — run CLI, tests, and migrations here. **The canonical Phase 1 database file** defaults to **`poker_ai/data/poker_ai.db`** (absolute path from the package root). If `ingest` prints a different `SQLite file: …` path, **`POKER_AI_DATABASE_URL` in `.env` is overriding** the default — remove or change it when you want rows in `data/poker_ai.db` only.

**Sibling folders (repo root `Poker AI/`, next to `poker_ai/`):**

| Path | Role |
|------|------|
| `../convert/` | Hand extraction and normalization **logic** (your converters). Run these tools to produce clean `hand_*.txt` (and other exports). **Phases 0–2 `poker_ai` code does not import `convert/`**; it only ingests **output files** you point at with `ingest`. |
| `../hand/` | **Input only** — corpus of hand files (`**/hand_*.txt`, `**/*.json` OHH, `**/*.phh`, `**/*.phhs` for NT PHH). Point `ingest` here, e.g. `..\hand` or `..\hand\5`. Do **not** put the canonical DB here. |
| `../db/` | **Legacy** analysis scripts and old SQLite helpers — **not** the Phase 1 canonical store (`poker_ai/data/poker_ai.db`). Use for ideas or one-off queries only. |

**NLH only:** ingest accepts **No-Limit Hold’em** normalized text (`NLH` on the first line), OHH with `bet_type` NL, raw PokerStars snippets that look like **No Limit** Hold’em, and **PHH/PHHS** blocks with `variant = 'NT'`. Other variants are skipped (parser returns no hand).

**Ante vs no-ante in the DB:** Each `games` row stores `uses_antes` and `total_ante_amount` (migration `0004_games_ante_columns`). They come from `ParsedHand.antes` at ingest time — **PHH** sets them; other formats may show `uses_antes = 0` until their parsers fill `antes`. Re-ingest after parser updates. Example: `SELECT COUNT(*) FROM games WHERE uses_antes = 1;`

**Multi-site / multi-folder hands:** each row stores `ingest_source` + `external_ref` (unique together). The DB column is **TEXT** (migration `0003`) so long PHH tree paths are never truncated. **Ingesting a folder:** normalized `hand_*.txt` rows use a path-based `external_ref` so the same filename in different subfolders does not overwrite. PHH/PHHS use `ingest_source=phh` and a path + hand-tail `external_ref` (multi-hand `.phhs` get distinct tails). **Ingesting a single file:** normalized hands keep the numeric id from the filename when `external_ref` is digits-only. Other formats (OHH, raw PS stub) use their own id rules.

**Performance (two different ideas):** (1) **Multi-source DB** — text + PHH + OHH rows **add up** in `games` (e.g. ~31k total after loading both); that is correct. (2) **Phase 1 exit gate (required)** — `scripts/verify_phase1_ingest.py` ingests ~19k `hand_*.txt` under `hand/6` in **< 90 s** (verified ~46 s). Corpus: `POKER_AI_CORPUS_ROOT` must be txt-only if `hand/` also contains PHH trees. PHH dev slices: `--max-hands` / `POKER_AI_INGEST_MAX_HANDS`.

**Large PHH / mixed trees:** use `--max-hands N` on `ingest` or `POKER_AI_INGEST_MAX_HANDS` in `.env` to load the first *N* successfully parsed hands for development, then re-run without a cap later for a full pass.

## Phase 1 — canonical store

### Snapshot (ingest)

- **Implemented:** normalized NLH text, OHH JSON, NT **PHH/PHHS**, PokerStars-style raw text (where detected); idempotent upsert into SQLite (or any configured async URL).
- **Ante flags on ``games``:** Alembic ``0004_games_ante_columns`` adds ``uses_antes`` and ``total_ante_amount``. Run ``python -m poker_ai db migrate`` on older DB files, then **re-ingest** PHH/PHHS so rows are re-upserted from disk (otherwise old rows keep default “no ante” until parsers fill ``ParsedHand.antes`` for other formats).
- **Stable ``hand_id``:** non-numeric refs hash to an integer **≤ JSON ``Number.MAX_SAFE_INTEGER``** so browser/JS viewers and Excel do not round ``hand_id`` and hide joined rows. **Re-run ingest** for PHH-heavy DBs created before this fix so child tables line up in those tools.
- **Completeness filter:** by default, incomplete hands are skipped (``POKER_AI_INGEST_REQUIRE_COMPLETE_HANDS=true``). Set to **false** in ``.env`` if you need every parsed row including partial PHH/OHH.
- **Hero row:** every upsert fills ``hands.hero_position`` / ``hero_cards`` (and one ``is_hero`` seat) via a default viewpoint when the format did not specify a hero (e.g. PHH). **Re-ingest** to backfill older rows.
- **Seat labels:** BTN/SB/BB/UTG/… where the parser can infer them; otherwise ``S{n}`` may appear.
- **Bulk example:** `poker-hand-histories` under `../hand/` — point `ingest` at that folder; cap with `--max-hands 15000` (or env) for a dev-sized slice. `files_seen` in the CLI summary counts **files opened until the hand cap**, not the whole tree.
- **Doc index:** [../doc/ROADMAP.md](../doc/ROADMAP.md) (Phase 1 **implementation snapshot** subsection).

```bash
python -m uv run python -m poker_ai ingest "..\hand"
python -m uv run python -m poker_ai db status
```

PHH-heavy folder with explicit DB and a dev cap (PowerShell):

```powershell
$env:POKER_AI_DATABASE_URL = "sqlite+aiosqlite:///D:/Poker AI/poker_ai/data/poker_ai.db"
python -m uv run python -m poker_ai ingest "D:\Poker AI\hand\poker-hand-histories" --max-hands 15000
```

`ingest` applies Alembic migrations to head first (same as `db migrate`), so a fresh `poker_ai/data/poker_ai.db` works without a separate migrate step. Use `db migrate` when you only want to upgrade the schema.

The SQLite file is printed as `SQLite file: ...` and defaults to **`poker_ai/data/poker_ai.db`** (under this package, not under `../hand`).

Use a strong `POKER_AI_PLAYER_UID_HMAC_SECRET` in production (see `doc/SECURITY_AND_COMPLIANCE.md`).

## Phase 2 — NLH engine + evaluator

- **Implemented:** `src/poker_ai/core/` — `cards`, `evaluator` (**phevaluator**), `game` (`GameState`, `EngineAction`, streets), `engine` (step / legal actions / **antes then blinds** / side pots), `replay` (`replay_parsed_hand` from `ParsedHand`), `profiles`. `ParsedHand.antes` (parallel to `players`) is filled from **PHH** `antes = [...]`; OHH / Stars may still omit it until parsers are extended.
- **Verify:** `uv run pytest tests/test_core_*.py -q` or full suite `uv run pytest` (100 % `poker_ai` coverage is enforced by `pyproject.toml`).
- **Try in Python** (from this directory, venv active):

  ```powershell
  .\.venv\Scripts\python.exe -c "from poker_ai.core import engine; print(engine.__doc__ or 'ok')"
  ```

- **Evaluator perf test:** optional throughput check in `tests/test_core_evaluator.py`; `POKER_AI_SKIP_PERF=1` skips; `POKER_AI_PERF_EVAL_MIN_RATE` raises the bar (see [../doc/ROADMAP.md](../doc/ROADMAP.md) Phase 2 exit criteria).
- **Roadmap detail:** [../doc/ROADMAP.md](../doc/ROADMAP.md) — **v1 complete**; MTT/ICM → v2 backlog.

## Phase 4 — Range-vs-range equity (**complete**)

- **Status:** Exit criteria green (see [../doc/ROADMAP.md](../doc/ROADMAP.md) Phase 4 snapshot). Library only — does **not** populate `data/poker_ai.db` `results.*_equity` (planned backfill later).
- **Implemented:** `src/poker_ai/equity/` — `mc.py`, `exact.py`, `range_vs_range.py`, `cache.py`, `engine.py` (`EquityEngine`), internal runout cache + Numba loop.
- **Live API:** warm board once, query many ranges:

  ```powershell
  .\.venv\Scripts\python.exe -c "from poker_ai.equity import EquityEngine; from poker_ai.core.cards import parse_card; e=EquityEngine(); f=(parse_card('Ah'),parse_card('Kd'),parse_card('7c')); e.warm_board(f); print('ok')"
  ```

- **Verify (fast, ~12 s)** — project venv only:

  ```powershell
  $env:POKER_AI_SKIP_PERF = "1"
  .\.venv\Scripts\python.exe -m pytest tests/test_equity_phase4.py -q
  ```

- **Perf + literature:** `Remove-Item Env:POKER_AI_SKIP_PERF -ErrorAction SilentlyContinue` then `pytest tests/test_equity_phase4.py -q` (includes sub-50 ms flop test); `-m slow` for AA vs random MC.
- **Bench:** `.\.venv\Scripts\python.exe scripts/bench_equity.py`
- **Env:** `POKER_AI_EQUITY_WORKERS` (table build parallelism; use `1` under pytest), `POKER_AI_EQUITY_NO_NUMBA=1` (force NumPy fallback), `POKER_AI_SKIP_PERF=1` (skip slow/perf tests).
- **If pytest hangs:** Ctrl+C; `Get-Process python | Stop-Process -Force`; never exact **uniform vs uniform** preflop.

## Phase 5 — HHFormer foundation model (**complete**)

- **Status:** Done on ~31k ingested hands. Exit criteria met: MAP **80.5 %**, SOP AUC **0.97**, probe AUC **0.79**, ~**7 min** on CUDA (see `artifacts/hhformer/v1/metrics.json`).
- **Train:** `train hhformer` · **Embed:** `features hhformer-embed` · **Ingest hook:** `ingest --train-hhformer`
- **GPU:** Default pip torch is CPU-only; RTX 50-series → `.\scripts\install_torch_cuda.ps1` then `--device cuda`.

```powershell
.\scripts\install_torch_cuda.ps1
.\.venv\Scripts\python.exe -m poker_ai train hhformer --epochs 50 --batch-size 256 --device cuda --log-every 50
.\.venv\Scripts\python.exe -m poker_ai features hhformer-embed --with-equity -w artifacts/hhformer/v1
.\.venv\Scripts\python.exe -m pytest tests/test_hhformer_phase5.py -q
```

- **Detail:** [../doc/ROADMAP.md](../doc/ROADMAP.md) · [docs/PHASE5_HHFORMER.md](docs/PHASE5_HHFORMER.md)

## Phase 6 — CFR solvers + preflop policies (**done**)

- **Status:** Roadmap exit criteria met — Kuhn CFR+ vs OpenSpiel; HU/6-max preflop tabular solves; info-set exploitability gates in tests. See [../doc/ROADMAP.md](../doc/ROADMAP.md) and [docs/PHASE6_SOLVER.md](docs/PHASE6_SOLVER.md).
- **Policies:** `CFRPolicy`, `HeuristicPolicy`, `PostflopEquityPolicy` (postflop), `StackedPolicy` (preflop CFR + postflop equity + optional HHFormer embeds).
- **Solve (production, real equity, CPU):** `--production` sets real equity + HU 50k / 6-max 25k iters. Use `--workers` ≈ logical CPUs − 1 (i7 8 threads → `7`). Combo table cached under `artifacts/solver/cache/`.

  ```powershell
  python -m poker_ai solve kuhn --iters 10000
  python -m poker_ai solve preflop --positions hu --production --equity-mode real --workers 7 `
    -o artifacts/solver/preflop_hu_real.json
  python -m poker_ai solve preflop --positions 6max --production --equity-mode real --workers 7 `
    --max-raises 1 -o artifacts/solver/preflop_cfr.json
  ```

  Omit `--measure-exploitability` for faster chart-only runs. HHFormer uses GPU; **this solver does not**.

- **Pipeline:** `python -m poker_ai pipeline run --corpus "..\hand\5" --skip-train --skip-embed --workers 7`
- **Parallelism:** `--workers` on ingest / features / solve; or `POKER_AI_NUM_WORKERS`
- **Preflop equity:** `--production` or `--equity-mode real` (Phase 4 MC buckets); `random` = legacy abstract game
- **Detail:** [docs/PHASE6_SOLVER.md](docs/PHASE6_SOLVER.md)

## Phases 7 / 7b / 7c — Solver bridge, router, Monker (**implemented**)

- **Phase 7 (HU postflop):** TexasSolver AGPL teacher + mock teacher + cache + distilled student. Install: `solve install-texas` · status: `solve texas-status` · grid: `solve grid` · train: `train student`.
- **Phase 7b (routing):** `load_best_policy()` → `RouterPolicy` — `n_active == 2` → HU stack, `n_active >= 3` → multi-way stack. Train: `train multiway-student`.
- **Phase 7c (optional):** Monker JSON import — `solve monker-import` · blend at runtime via `POKER_AI_MONKER_TEACHER_BLEND`.
- **TexasSolver troubleshooting:** corrupt zip (~5 MB) → `BadZipFile`; use `install-texas --force` or `register-texas --zip`. Vendored `TexasSolver/` is source-only unless you build and `register-texas --exe`.
- **Documentation:**
  - [docs/PHASES_0_7_COMPLETE_GUIDE.md](docs/PHASES_0_7_COMPLETE_GUIDE.md) — full summary (routing, paths, install, tests)
  - [docs/COMMANDS_PHASES_0_7.md](docs/COMMANDS_PHASES_0_7.md) — CLI cheat sheet
  - [docs/PHASE7_SOLVER_BRIDGE.md](docs/PHASE7_SOLVER_BRIDGE.md) · [docs/PHASE7B_POLICY_ROUTER.md](docs/PHASE7B_POLICY_ROUTER.md) · [docs/PHASE7C_MONKER.md](docs/PHASE7C_MONKER.md)
  - [TexasSolver/README.poker_ai.md](TexasSolver/README.poker_ai.md)
- **Roadmap:** [../doc/ROADMAP.md](../doc/ROADMAP.md) — Phases 7–7c snapshots and routing audit table

```powershell
python -m poker_ai solve install-texas
python -m poker_ai solve texas-status
python -m poker_ai solve grid --n-spots 1000 --backend mock
python -m poker_ai train student --epochs 30 --device cpu
python -m poker_ai train multiway-student --epochs 20 --device cuda
```

## In-package docs

See [docs/README.md](docs/README.md) for the full index. Canonical specifications remain under `doc/` at the repository root.
