# Phases 0–9 — what is done vs open

Living checklist for the canonical `poker_ai` package. See [doc/ROADMAP.md](../../doc/ROADMAP.md) for full deliverables.

**CLI ↔ Web:** Both interfaces share the same DB and artifacts — see [CLI_WEB_PARITY.md](CLI_WEB_PARITY.md).

**v1 status:** **Complete** (Phases 0–12 + web W0–W10).  
**v2 status:** **Complete** (Streams A–D, June 2026) — [V2_IMPLEMENTATION_GUIDE.md](V2_IMPLEMENTATION_GUIDE.md).

**Last updated:** June 2026 (v1 + v2 sign-off).

## Phase 0 — Scaffold

| Item | Status |
|------|--------|
| uv, ruff, mypy, pytest, Typer CLI | Done |
| GitHub CI green on Windows + Ubuntu | **Done** (`.github/workflows/ci.yml`) |

## Phase 1 — Ingest / store

| Item | Status |
|------|--------|
| Multi-format NLH ingest, idempotent upsert | Done |
| OHH + PokerStars + PHH antes → `ParsedHand.antes` | Done (`ingest/antes.py`) |
| Text-only ingest &lt;90s (~19k ``hand_*.txt``, ``hand/6``) | Done (~46s; `scripts/verify_phase1_ingest.py`) |
| Bulk PHH policy (cash/MTT filter, licence) | Done — [PHH_CORPUS_POLICY.md](PHH_CORPUS_POLICY.md) |

## Phase 2 — Engine

| Item | Status |
|------|--------|
| 2–10 seats, replay, posted antes | Done |

## Phase 3 — Features

| Item | Status |
|------|--------|
| Feature JSONL, parallel workers, v1 exit criteria | Done |
| v2 blueprint full columns + schema validate + Parquet export | Done (Stream A) |
| Value net + decision quality heads | Done (Stream A) |

## Phase 4 — Equity

| Item | Status |
|------|--------|
| HU + multi-way MC/exact library | Done |
| DB backfill `results.*_equity` | Done (playbook ~40k hands) |
| CLI + web `equity_backfill` | Done |
| Replayer / Drill / Play / W5 calculator | Done |

## Phase 5 — HHFormer

| Item | Status |
|------|--------|
| Pretrain + inference path | Done (artifact-dependent) |
| HHFormer embed export (CLI + web job) | Done (Stream D) |

## Phase 6 — CFR / solvers

| Item | Status |
|------|--------|
| Preflop HU / 6-max, parallel CFR | Done (artifact-dependent) |
| Preflop 8/9/10-max + artifact routing | Done |
| TexasSolver postflop bridge | Done |
| Kuhn CFR sanity (CLI + web job) | Done (Stream D) |

## Phase 7 — Distilled student + router

| Item | Status |
|------|--------|
| `RouterPolicy` HU vs multi-way | Done |
| `solve validate-student` + web `validate_student` | Done |
| Multi-way student + Monker blend | Done |
| Multi-way train on corpus | Done (5,095 rows, MSE val ≈ 0.047) |
| Replay router gate | Done (`verify_router_gate.py`) |

## Phase 7c — Monker (optional, licensed)

| Item | Status |
|------|--------|
| Import + train blend + runtime cache | Done |
| ≥500 Monker spots + MODEL_CARD license | Done (playbook validated) |

## Phase 8 — Style / exploit

| Item | Status |
|------|--------|
| Style encoder, kNN gate, league style bridge | Done |
| `opponents eval-exploit` | Done (CLI + Profiles + web job) |
| `main_exploiter` + `ExploitPolicy` | Done |

## Phase 9 — League

| Item | Status |
|------|--------|
| HU + 6/8/9-max sim, brain-switch stats | Done |
| AIVAT + Elo promotion gate (v1) | Done |
| Full AIVAT audit (`eval/aivat.py`, web job, League tab) | Done (Stream B) |
| DB replay league (`league run-replay`, web job) | Done (Stream C) |
| `--until-hours` + web Bot league presets | Done |
| Checkpoint registry + train-exploiters (CLI + web) | Done |
| Policy bench (CLI + Health + web job) | Done (Stream D) |
| 6 h wall-clock league (playbook) | Done |

## Phase 10+ (see ROADMAP)

| Item | Status |
|------|--------|
| Dashboard W0–W10 | Shipped |
| `verify_phase10.py` (6/6) | Done |
| Phase 12 install verify | Done |
| Phase 11 promotion gates + drift + models UI | Done |
| Play auto-learn (`play_auto_learn`) | Done |

---

## v2 shipped — June 2026

Full plan: **[V2_IMPLEMENTATION_GUIDE.md](V2_IMPLEMENTATION_GUIDE.md)** · Parity: **[CLI_WEB_PARITY.md](CLI_WEB_PARITY.md)**

| Stream | Item | CLI verify | Web |
|--------|------|------------|-----|
| **A** | Blueprint features + value/decision heads | `verify_v2_blueprint_features.py` | Setup + Tasks (27 job types) |
| **B** | Full AIVAT | `verify_v2_aivat.py` | League AIVAT + `aivat_audit` job |
| **C** | DB replay league | `verify_v2_replay_league.py` | League Real hands + `league_replay_run` |
| **D** | Diagnostics parity | `verify_v2_diagnostics_parity.py` | Health + Jobs + League + Profiles |

**Future (post-v2):** MTT/ICM product, drift KS/PSI on blueprint tensors, optional replay BB/100 promotion gate — [ROADMAP §v2 backlog](../../doc/ROADMAP.md#v2-backlog--next-version-todo).

---

## Quick commands (CLI)

```bash
python -m poker_ai equity backfill
python scripts/verify_phase1_ingest.py
python -m poker_ai features build --blueprint-full
python -m poker_ai features validate-blueprint --blueprint-full
python -m poker_ai train value-net
python -m poker_ai train decision-quality
python -m poker_ai eval aivat-audit --hands 1000
python -m poker_ai league run-replay --limit 500
python -m poker_ai solve validate-student --n-spots 1000 --backend mock
python -m poker_ai league run --until-hours 6 --hands-per-matchup 200 --workers 16
python -m poker_ai league train-exploiters --hands 400
python scripts/verify_v2_blueprint_features.py
python scripts/verify_v2_aivat.py
python scripts/verify_v2_replay_league.py
python scripts/verify_v2_diagnostics_parity.py
POKER_AI_ROUTER_GATE=1 python scripts/verify_router_gate.py
python ../apps/api/scripts/verify_phase10.py
python ../apps/api/scripts/verify_phase12_install.py
```

## Web equivalents

| CLI | Web |
|-----|-----|
| `features build --blueprint-full` | Tasks → Prepare hands → **Extended (v2 blueprint)** |
| `features validate-blueprint` | Tasks → **Validate feature schema** |
| `features export-parquet` | Tasks → **Export feature snapshot** |
| `train value-net` | Status / Tasks → **Train value net** (redirects to solver cache if needed) |
| `train decision-quality` | Status / Tasks → **Train decision quality** |
| `eval aivat-audit` | League → AIVAT or Tasks → **Run AIVAT audit** |
| `league run-replay` | League → Real hands or Tasks → **League on your library** |
| `policy bench` | Health or Tasks → **Policy speed test** |
| `opponents eval-exploit` | Profiles → **Run exploit test** |
| `solve validate-student` | Tasks → **Validate student gates** |
| `league run --until-hours 6` | Tasks → **Bot league → Until 6 hours** |
| `league train-exploiters` | Tasks → **Train league exploiters** |

Task links use `?task=…&preset=recommended` and **smart prerequisite redirects** via `apps/web/src/lib/taskNavigation.ts`.

See [COMMANDS_PHASE9.md](COMMANDS_PHASE9.md), [PHASE9_LEAGUE.md](PHASE9_LEAGUE.md), [CLI_WEB_PARITY.md](CLI_WEB_PARITY.md).
