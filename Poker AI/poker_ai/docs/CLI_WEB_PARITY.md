# CLI ↔ Web parity

**Last updated:** June 2026

You can run this project two ways on the **same SQLite store and artifacts**:

| Interface | How to start | Best for |
|-----------|--------------|----------|
| **Web** | `python -m poker_ai serve` → open the dashboard (Vite dev or built SPA) | Setup wizard, play vs AI, replayer, jobs with progress bars |
| **CLI** | `python -m poker_ai <command>` (Typer) | Scripts, CI gates, overnight runs, power-user flags |

Both call the same job runner (`apps/api/services/job_runner.py`) for long tasks. The web UI submits `POST /jobs`; the CLI invokes the same Python modules directly.

**Related docs:** [doc/ROADMAP.md](../../doc/ROADMAP.md), [doc/WEB_IMPLEMENTATION_GUIDE.md](../../doc/WEB_IMPLEMENTATION_GUIDE.md), [V2_IMPLEMENTATION_GUIDE.md](V2_IMPLEMENTATION_GUIDE.md), [COMMANDS_PHASES_0_7.md](COMMANDS_PHASES_0_7.md).

---

## Web routes (18 pages)

| URL | Purpose |
|-----|---------|
| `/` | Replayer |
| `/status` | System + artifact readiness |
| `/import` | Ingest hand histories |
| `/setup` | Pipeline wizard (v1 + v2 steps) |
| `/jobs` | Task cards + job history |
| `/play` | Play vs AI + auto-learn from sessions |
| `/sim` | Live league sim (WebSocket) |
| `/equity` | HU range calculator |
| `/drill` | Spot drill + thinking/deep search |
| `/profiles` | Opponent profiles + research panels |
| `/solver` | Solver spot browser |
| `/league` | Leaderboard (Synthetic / Real hands / AIVAT / Checkpoints) |
| `/drift` | Drift / BOCPD reports |
| `/models` | Promote / rollback / gates |
| `/licenses` | Third-party licence attestation |
| `/datasheet` | In-app compliance datasheet |
| `/blueprint` | Architecture blueprint |
| `/health` | Smoke checks (first-load gate) |

---

## Pipeline & data — parity matrix

| Capability | CLI | Web | Notes |
|------------|-----|-----|-------|
| Ingest path / upload | `poker_ai ingest <path>` | `/import` → job `ingest` | Web uses folder path or small upload; same upsert logic |
| DB migrate | `poker_ai db migrate` | Install scripts / first `serve` | No dedicated web button |
| DB revision | `poker_ai db status` | `/status` → Database row | |
| Build features | `poker_ai features build` | Setup step 2, `/jobs` → `features_build` | |
| Blueprint full features | `poker_ai features build --blueprint-full` | `/jobs` → Prepare hands → **Extended (v2 blueprint)** preset | v2 Stream A |
| Export Parquet snapshot | `poker_ai features export-parquet` | Setup / `/jobs` → Export feature snapshot | v2 Stream A |
| Validate blueprint schema | `poker_ai features validate-blueprint` | Setup / `/jobs` → Validate feature schema | v2 Stream A |
| Train value net | `poker_ai train value-net` | Setup / `/jobs` → Train value net | v2 Stream A |
| Train decision quality | `poker_ai train decision-quality` | Setup / `/jobs` → Train decision quality | v2 Stream A |
| HHFormer embeddings export | `poker_ai features hhformer-embed` | `/jobs` → Export embeddings | v2 Stream D |
| Ingest + auto HHFormer | `poker_ai ingest … --train-hhformer` | Setup steps 1→3 separately | CLI convenience wrapper |
| Train HHFormer | `poker_ai train hhformer` | Setup 3, `/jobs` → `train_hhformer` | |
| Preflop CFR (HU–10-max) | `poker_ai solve preflop --positions …` | Setup 4–7, `/jobs` → `solve_preflop` | Web presets include 8/9/10-max |
| Solver cache (Texas/mock) | `poker_ai solve grid` | Setup 5, `/jobs` → `solve_grid` | |
| Train HU student | `poker_ai train student` | Setup 6, `/jobs` → `train_student` | Play-study manifest auto-merged when present |
| Train multiway student | `poker_ai train multiway-student` | Setup / `/jobs` → `train_multiway_student` | |
| Train CQL | `poker_ai train cql` | Setup 7, `/jobs` → `train_cql` | |
| HHFormer fine-tune (v2) | `poker_ai train hhformer-finetune` | Setup 8, `/jobs` → `train_hhformer_finetune` | |
| Train style encoder | `poker_ai train style` | Setup 9, `/jobs` → `train_style` | |
| Student validation gates | `poker_ai solve validate-student` | `/jobs` → **Validate student gates** | Job fails if MSE or p99 gate not met |
| League self-play | `poker_ai league run --hours N` | Setup 10, `/jobs` → `league_run` | Presets: round-robin and **Until 6h / 1h** (`until_hours`) |
| League wall-clock cap | `poker_ai league run --until-hours N` | `/jobs` → Bot league → **Until 6 hours** preset or `until_hours` field | |
| Train league exploiters | `poker_ai league train-exploiters` | `/jobs` → Train league exploiters | Phase 9 ops |
| Equity backfill (DB) | `poker_ai equity backfill` | Setup optional step, `/jobs` → `equity_backfill` | Improves AIVAT + decision quality |
| End-to-end pipeline | `poker_ai pipeline run` | `/setup` wizard (step-by-step) | CLI one-shot; web equivalent is running Setup steps |
| Play-study train + promote | `poker_ai train play-study --promote-router` | `/play` study panel, job `play_auto_learn` | Web also **auto-schedules** learn after each hand (`POKER_AI_PLAY_AUTO_LEARN`) |
| Refresh play-study manifest | — | `/play` → materialize job | Web-only job `play_study_materialize` |

---

## Play, sim, and advice

| Capability | CLI | Web | Notes |
|------------|-----|-----|-------|
| Interactive play vs bots | — | `/play` | **Web-primary** |
| Live sim stream | — | `/sim` (`/ws/sim`) | Throughput gate: `GET /sim/throughput` |
| Spot drill | — | `/drill` | Uses `/decide` + drill APIs |
| HU equity calculator | `poker_ai equity spot` | `/equity` (`POST /equity`) | |
| Replayer | — | `/` | |
| Decide / hints API | — | Drill, Play, Solver | CLI uses policies in league/scripts |

---

## League, models, opponents

| Capability | CLI | Web | Notes |
|------------|-----|-----|-------|
| Leaderboard | `poker_ai league leaderboard` | `/league` → Synthetic tab | |
| Checkpoint registry list | `poker_ai league checkpoints` | `/league` → Checkpoints tab | v2 Stream D |
| DB replay league | `poker_ai league run-replay` | `/league` → Real hands + `/jobs` → League on your library | v2 Stream C |
| AIVAT audit | `poker_ai eval aivat-audit` | `/league` → AIVAT + `/jobs` → Run AIVAT audit | v2 Stream B; set `POKER_AI_AIVAT_FULL=1` for full mode |
| Eval exploit vs baseline | `poker_ai opponents eval-exploit` | `/profiles` → Run exploit test + `/jobs` | v2 Stream D |
| Opponent profile | `poker_ai opponents profile <uid>` | `/profiles` → player card | |
| Model list | `poker_ai models list` | `/models`, `/status` | Value net + Decision quality rows on `/status` |
| Promotion gates | `poker_ai models gates` | `/models` → Check gates | |
| Promote / rollback | `poker_ai models promote\|rollback` | `/models` | |
| Router play-study promote | `poker_ai models router promote-play-study` | `/models`, `/play` | |

---

## Solver tooling & diagnostics

| Capability | CLI | Web | Notes |
|------------|-----|-----|-------|
| Kuhn CFR sanity | `poker_ai solve kuhn` | `/jobs` → Solver sanity (Kuhn) | v2 Stream D |
| Monker import | `poker_ai solve monker-import` | — | Bulk Monker JSON → cache; CLI / ops |
| TexasSolver install/register | `solve install-texas`, `register-texas`, `texas-status` | `/health`, Setup solver step | |
| Policy bench | `poker_ai policy bench` | `/health` link + `/jobs` → Policy speed test | v2 Stream D |
| Drift report | (observability module) | `/drift` | **Web-primary** for viewing |
| Serve API + UI | `poker_ai serve` | All pages | CLI starts both processes |

---

## Intentionally CLI-only (documented, not web)

| Capability | CLI | Why no web button |
|------------|-----|-------------------|
| DB migrate | `poker_ai db migrate` | Install / first `serve` |
| End-to-end one-shot | `poker_ai pipeline run` | Setup wizard is the web equivalent |
| Monker bulk import | `poker_ai solve monker-import` | Ops / power-user |
| Ingest convenience flags | `--train-hhformer`, etc. | Web runs steps separately |
| Head-to-head AIVAT compare | *(not shipped)* | Research-only; use `eval aivat-audit` job |

---

## Verification & CI (CLI / scripts)

These gate roadmap exit criteria — run in CI or before release:

| Script | Purpose |
|--------|---------|
| `poker_ai/scripts/verify_phase1_ingest.py` | Phase 1 ingest &lt;90s |
| `poker_ai/scripts/verify_router_gate.py` | Phase 7b replay router gate |
| `poker_ai/scripts/verify_v2_blueprint_features.py` | v2 Stream A — schema, parquet, encode speed |
| `poker_ai/scripts/verify_v2_aivat.py` | v2 Stream B — full AIVAT stderr reduction |
| `poker_ai/scripts/verify_v2_replay_league.py` | v2 Stream C — DB replay league |
| `poker_ai/scripts/verify_v2_diagnostics_parity.py` | v2 Stream D — CLI vs job result shapes |
| `apps/api/scripts/verify_phase10.py` | Phase 10 API + sim throughput |
| `apps/api/scripts/verify_phase12_install.py` | Phase 12 VM install timing |
| `pytest tests/test_replay_router_gate.py` | Router gate with `POKER_AI_ROUTER_GATE=1` |

---

## Job types (web background tasks)

Registered in `job_runner.py` and submittable via `POST /jobs`, Setup wizard, or Tasks UI (**27 types**):

`ingest`, `features_build`, `features_export_parquet`, `features_validate_blueprint`, `train_hhformer`, `train_hhformer_finetune`, `solve_preflop`, `solve_grid`, `train_student`, `train_cql`, `train_style`, `league_run`, `league_replay_run`, `train_multiway_student`, `play_study_materialize`, `play_auto_learn`, `equity_backfill`, `validate_student`, `league_train_exploiters`, `aivat_audit`, `policy_bench`, `solve_kuhn`, `features_hhformer_embed`, `opponents_eval_exploit`, `train_value_net`, `train_decision_quality`

---

## Verdict (ROADMAP alignment)

| ROADMAP claim | Status |
|---------------|--------|
| Phases 0–12 + W0–W10 v1 complete | **Yes** |
| v2 Streams A–D (CLI + web) | **Yes** — 27 job types; smart task navigation |
| Phases 1–9 pipeline triggerable from web | **Yes** — Setup + `/jobs` |
| Same artifacts whether CLI or web | **Yes** |
| Every product CLI command has a web path | **Yes** — except documented CLI-only ops above |
| Play vs AI + auto-learn | **Web-first**; CLI `train play-study` for manual runs |
| Phase 10 sim throughput | Web `/sim` + verify script |

**Practical split:** use **web** for day-to-day setup, play, replayer, and monitoring; use **CLI** for scripted pipelines, CI verify scripts, Monker import, and overnight runs.

---

## Web task navigation (June 2026)

Links from **Status**, **Models**, **League**, **Health**, **Profiles**, and job **next steps** use:

- Query params: `/jobs?task=<job_type>&preset=recommended|quick|full`
- **Smart redirects** (`apps/web/src/lib/taskNavigation.ts`): e.g. **Train value net** when Solver Cache is missing → **Solver teacher cache** (mock quick if TexasSolver not installed, Texas recommended if installed)
- Blocked task forms show a **Run prerequisite first →** button

Rebuild the SPA after web changes: `cd apps/web && npm run build`.

---

## Quick start (both interfaces)

```powershell
cd "D:\Poker AI\poker_ai"
.\.venv\Scripts\python.exe -m poker_ai serve
# Web: http://localhost:5173 (dev) or served static bundle
# API: http://localhost:8000/docs
```

```powershell
# Same machine, CLI-only examples
.\.venv\Scripts\python.exe -m poker_ai ingest ..\hand\6 --max-hands 5000
.\.venv\Scripts\python.exe -m poker_ai features build --blueprint-full
.\.venv\Scripts\python.exe -m poker_ai features validate-blueprint --blueprint-full
.\.venv\Scripts\python.exe -m poker_ai train value-net
.\.venv\Scripts\python.exe -m poker_ai league run-replay --limit 500
```
