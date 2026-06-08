# Blueprint — `poker_ai/` target architecture

This document is the **architectural reference** for the new project at `D:\Poker AI\poker_ai`. The phased delivery plan lives in [ROADMAP.md](ROADMAP.md); the genuinely novel technical ideas live in [NOVEL_TECHNIQUES.md](NOVEL_TECHNIQUES.md). Read all three together.

> **Hard product invariants:**
> 1. **No external AI** services. Every model is **ours**, trained and served locally. No OpenAI/Anthropic/etc. SDKs, ever.
> 2. **Local-first.** A laptop with no internet must run the full stack.
> 3. **Reproducibility.** Every artifact is keyed by `(git_sha, dataset_hash, seed, config_hash)`.
> 4. **Compliance-aware.** Owned-data analysis + simulator + dashboard. See [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md).

---

## 1. Top-level layout

```
D:\Poker AI\poker_ai\
├── pyproject.toml               # uv-managed, src layout, pinned deps
├── uv.lock                      # reproducible env
├── Taskfile.yml                 # cross-platform task runner (Windows-friendly)
├── docker-compose.yml           # OPTIONAL: Postgres + Grafana + Prometheus
├── .pre-commit-config.yaml      # ruff + mypy + gitleaks + detect-secrets
├── .env.example
├── README.md                    # 1-page quickstart -> /doc
├── LICENSES/                    # Inventory of every dep license (TexasSolver AGPL etc.)
│
├── src/poker_ai/
│   ├── __init__.py
│   ├── __main__.py              # `python -m poker_ai`
│   ├── config/                  # Pydantic Settings, profile registry
│   ├── core/                    # Cards, evaluator, GameState, engine
│   ├── ingest/                  # Site-specific parsers + OHH JSON
│   ├── store/                   # SQLAlchemy 2.0 + Alembic migrations + repositories
│   ├── features/                # Info-set encoder, board texture, range vectors
│   ├── equity/                  # MC + range-vs-range exact + cache
│   ├── solver/                  # CFR+, MCCFR, abstraction, TexasSolver bridge
│   ├── models/                  # HHFormer, student, style encoder, value net
│   ├── policy/                  # Policy interface + implementations
│   ├── profiles/                # YAML personas (TAG / LAG / Exploit / GTO-pure)
│   ├── league/                  # Self-play orchestrator, agents, evaluators
│   ├── eval/                    # AIVAT, exploitability, Elo, baselines
│   ├── learn/                   # Training jobs, datasets, registry, BOCPD, drift
│   ├── observability/           # Structured logs, metrics, audit log
│   ├── explain/                 # Symbolic explanation engine (no LLM)
│   └── apps/
│       ├── api/                 # FastAPI service
│       ├── cli/                 # Typer CLI
│       └── web/                 # React + TS + Vite dashboard
│
├── tests/                       # Mirrors src tree
├── data/
│   ├── raw/                     # Imported HHs (gitignored)
│   ├── interim/                 # Parsed parquet
│   └── processed/v<YYYY-MM-DD>/ # Versioned feature snapshots
├── artifacts/                   # Versioned models + MODEL_CARD.md + metrics.json
├── reports/                     # Drift HTML, league leaderboards
└── scripts/                     # Bootstrap, install, ad-hoc utilities
```

---

## 2. Module responsibilities (one paragraph each)

### 2.1 `core/` — the bedrock

A pure-Python, zero-IO, fully typed game model. Cards as small ints (Cactus Kev–style `0..51` in the shipped code). `GameState` is advanced via `engine.step(state, action) → state'` (fresh state object; callers do not mutate the prior instance in the public API). **Shipped:** 2–10 seats, **posted antes** when `ParsedHand.antes` is populated (PHH today), then **posted blinds**, side pots, all-in chops. **Ingest follow-up:** OHH / PokerStars text should populate `antes` when the format exposes them. **Full MTT meta** (levels, payouts, ICM) is not in `core/` yet. Where possible, math will later be expressed against tensors so the same code path serves simulation and gradient training. Hand evaluator uses [`phevaluator`](https://github.com/HenryRLee/PokerHandEvaluator) only today. Throughput target: **≥ 2 M 7-card evals/sec on one core** (see roadmap perf-test env vars).

### 2.2 `ingest/` — front doors for hand data

One file per format: `pokerstars_text.py`, `ohh_json.py`, `phh_text.py` (ACPC / HandHQ / Pluribus-style **`.phh` / `.phhs`**, `variant = 'NT'`), `gg_text.py`, `hm2_sql.py` (read-only, future). **Shipped CLI** routes by suffix and tree walk (``*.txt``, ``*.json``, ``*.phh``, ``*.phhs``). Target model name in this doc is `HandRecord`; the implemented code path uses the SQLAlchemy-oriented `ParsedHand` / upsert pipeline (same information). HH input is **never** fully trusted: invalid hands are skipped. See [HAND_HISTORY_FORMATS.md](HAND_HISTORY_FORMATS.md) for the wider format catalogue.

### 2.3 `store/` — the data lake

SQLAlchemy 2.0 with **async** sessions. **SQLite + WAL** by default; same code runs against PostgreSQL via `DATABASE_URL`. Alembic migrations are versioned and applied automatically on startup. **No silent drops, ever**: destructive ops require a `--reset` flag. Schema mirrors [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) but adds `Players_Global(player_uid TEXT PK)` to fix the per-hand `player_id` collision pitfall. Optional **DuckDB** layer for analytical scans on parquet exports.

### 2.4 `features/` — encoders that everything else depends on

Pure functions: `(GameState | DB row) → tensor`. Includes:

- `info_set.encode(state) → InfoSetKey` — a stable, hashable identity for CFR.
- `board_texture.embed(board) → np.ndarray[16]` — connectedness, pairedness, suited groups, draw density, dynamism.
- `range.from_combos(combos) → np.ndarray[1326]` — the canonical range vector primitive.
- `sequence.pack_action_token` / `features/hhformer_tokens.encode_hand_sequence` — action + meta + board tokens for HHFormer (Phase 5 **shipped**).

### 2.5 `equity/` — fast and exact (Phase 4 **done**)

Layers:

1. `mc.py` — Monte Carlo with seedable RNG (preflop and fallback).
2. `exact.py` — exact postflop range-vs-range via cached runout rank table (≤ 2000 runouts per board).
3. `range_vs_range.py` — public RvR API, combo histograms, FFT equity-bucket convolution.
4. `cache.py` — optional parquet disk cache (xxhash keys; not SQLite).
5. `engine.py` — `EquityEngine`: `warm_board()` then fast `equity()` for live tooling.
6. `breakdown.py`, `range_notation.py`, `spot_insight.py` — W5 web helpers (win/tie split, range strings, UI hints).
7. **Web:** `POST /equity` + `/equity` page (Phase W5) — standalone calculator; policies use the library directly, not this HTTP route.

Internal: `_runout_cache.py`, `_fast_loop.py` (Numba, `cache=False`), `_tables.py`. Does **not** backfill `results.*_equity` in `poker_ai.db` yet. Full integration map: [poker_ai/docs/PHASE4_EQUITY.md](../poker_ai/docs/PHASE4_EQUITY.md).

### 2.6 `solver/` — algorithmic ground truth

`cfr.py` is **textbook CFR / CFR+ / external-sampling MCCFR**, validated against OpenSpiel exploitability targets on Kuhn and Leduc. Production poker uses an action abstraction (`{0, 33%, 66%, 150%, allin}`) and a card abstraction (50 equity buckets per street). `bridge/texas.py` orchestrates [TexasSolver](https://github.com/bupticybee/TexasSolver) as an offline teacher; outputs land in `artifacts/solver_cache/`. License compliance is enforced (AGPL artifacts cannot be redistributed without source).

### 2.7 `models/` — owned AI only

Five small networks, all trainable on a laptop GPU or CPU:

| Model | Size | Purpose |
|-------|------|---------|
| `HHFormer` | ~10 M params | Self-supervised foundation model on hand histories (**Phase 5 shipped** — `models/hhformer.py`, `train hhformer`). |
| `student` | ~5 M params | Behavioral clone of the offline solver teacher. |
| `style_encoder` | ~3 M params | Contrastive opponent embeddings (64-dim). |
| `value_net` | ~2 M params | Depth-limited subgame value head (DeepStack-lite). |
| `decision_quality_head` | ~0.5 M params | Audits hero decisions vs. distilled GTO. |

All weights stored as `*.safetensors`. Each version directory contains `MODEL_CARD.md`, `metrics.json`, `input_features.json`, `training_data.json`. **No weights from any external service** are imported.

### 2.8 `policy/` — the runtime decision contract

A single Python interface:

```python
from typing import Protocol
import numpy as np
from poker_ai.core.game import GameState
from poker_ai.profiles import ProfileSpec

class Policy(Protocol):
    name: str
    version: str

    def propose(
        self,
        state: GameState,
        profile: ProfileSpec,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> "ActionDist": ...

    def explain(self, state: GameState, decision: "ActionDist") -> str: ...
```

Implementations:

- `HeuristicPolicy` — chart-based open ranges; always available.
- `CFRPolicy` — tabular CFR+ / MCCFR over an abstracted preflop tree (`--equity-mode real` or `random`).
- `PostflopEquityPolicy` — Phase 4 range-vs-range equity on flop+ (Phase 6 bridge; not CFR).
- `StackedPolicy` — CFR preflop → postflop equity → heuristic; optional HHFormer embed JSONL.
- `DistilledPolicy` — neural student trained on TexasSolver outputs (Phase 7).
- `ExploitPolicy` — distilled policy + style-conditioned head + optional `thinking_ms` sub-tree solve (Phase 8).

`thinking_ms > 0` triggers depth-limited re-solving (see [NOVEL_TECHNIQUES.md](NOVEL_TECHNIQUES.md) §“Differentiable re-solver”).

### 2.9 `profiles/` — personas via YAML

```yaml
# profiles/exploit_lag.yaml
id: exploit_lag
description: "Loose-aggressive exploit profile for soft games"
sizing_jitter: 0.10
aggression_multiplier: 1.25
exploit_weight: 0.65            # blend toward style-conditioned head
temperature: 1.05
clamp:
  max_3bet_freq: 0.18
  min_fold_freq: 0.08
```

Profiles **post-process** policy logits — they never modify weights. This decouples *what to play* from *who is playing*.

### 2.10 `league/` — local self-play that actually improves

Population slots: `main_agent`, `main_exploiter`, `league_exploiter`, `frozen_baselines`. Match scheduling, Elo, and **AIVAT-corrected** EV are all in-process; no external scheduler. Promotions require AIVAT-significant wins (p < 0.05 over ≥ 1 000 hands). See [NOVEL_TECHNIQUES.md](NOVEL_TECHNIQUES.md) §“Local self-play league”.

### 2.11 `eval/` — measure what you ship

- `aivat.py` — variance-reduced unbiased estimator.
- `exploitability.py` — best-response computation against fixed strategies on small games (smoke test).
- `elo.py` — standard rating updates.
- `baselines.py` — random, always-call, TAG script, calling station, maniac.

### 2.12 `learn/` — training jobs and the model registry

Each script is a Typer subcommand (`poker_ai train hhformer`, `poker_ai train student`, `poker_ai train league`). All read from versioned `data/processed/v<date>/`. Outputs land in `artifacts/<model>/v<date>/`. A flat-file registry (`artifacts/<model>/CURRENT`) is the single source of truth; rollback is one command. Optional MLflow integration if the user opts in.

### 2.13 `observability/` — see what is happening

- `logs.py` — `structlog` JSON, correlation IDs.
- `metrics.py` — `prometheus_client` counters/histograms.
- `drift.py` — KS / PSI / Wasserstein on key features; HTML reports (`data/drift/`). **Web:** `/drift`.
- `audit.py` — append-only audit log table for compliance.

**Related (Phase 11 / W8, under `learn/`):**

- `changepoint.py` — Bayesian Online Changepoint Detection per opponent. **Web:** `/drift` changepoints panel.
- `model_registry.py` — version pointers (`artifacts/<model>/CURRENT`). **Web:** `/models` promote/rollback.

See [OBSERVABILITY.md](OBSERVABILITY.md) for the deeper plan.

### 2.14 `explain/` — auditable rationale, no LLM

Templates parameterised by `(position, SPR_bucket, board_texture, action_bucket)`. The output is a deterministic English string:

```
BTN open 2.5x is GTO frequency 0.92 over the top 45% of hands;
SPR 12 favors raise sizes <= pot; board not yet dealt.
```

Templates are unit-tested. There is **no generative LLM in the loop**.

### 2.15 `apps/`

- `api/` — FastAPI; routers split by domain (`hands`, `decide`, `league`, `replay`, `health`).
- `cli/` — Typer commands for every operational task.
- `web/` — React + TS + Vite + TanStack Query + shadcn/ui.

---

## 3. Dependency policy

**Whitelist** (everything used must be in `pyproject.toml` and reviewed):

| Concern | Library | Why |
|---------|---------|-----|
| HTTP API | `fastapi`, `uvicorn[standard]` | Best-in-class async Python web. |
| ORM | `sqlalchemy[asyncio]`, `alembic` | Single source of schema truth. |
| Settings | `pydantic-settings` | Typed config from env + .env. |
| CLI | `typer[all]`, `rich` | Modern Python CLI UX. |
| Numerics | `numpy`, `scipy` | Core math, FFT. |
| Tensors | `torch` (CPU build acceptable) | Models. |
| Card eval | `phevaluator` | Fastest 7-card evaluator. |
| Tables | `pandas`, `pyarrow`, `duckdb` | Analytics + parquet. |
| Logs | `structlog` | JSON logging. |
| Metrics | `prometheus_client` | `/metrics` endpoint. |
| Tests | `pytest`, `pytest-asyncio`, `pytest-cov`, `hypothesis`, `httpx`, `schemathesis` | See [TESTING_AND_QA.md](TESTING_AND_QA.md). |
| Lint/type | `ruff`, `mypy`, `gitleaks`, `detect-secrets` | Static quality gates. |
| Drift | `evidently` (optional), `whylogs` (optional) | Reports. |

**Forbidden** (and why):

- Any `openai`, `anthropic`, `cohere`, `mistralai`, `replicate`, `together`, `huggingface_hub` (inference API), `langchain` LLM wrappers, etc. — violates the no-external-AI rule.
- `requests` to any external AI endpoint anywhere in the codebase. CI grep blocks it.
- Closed-source poker libraries we cannot audit.

CI fails the build if any forbidden import shows up.

---

## 4. Configuration

`config/settings.py` (Pydantic Settings) loads in this order:

1. `.env` (gitignored).
2. `config/profiles/<APP_ENV>.yaml` (committed defaults).
3. Process environment.

Keys (prefix `POKER_AI_`):

| Key | Default | Purpose |
|-----|---------|---------|
| `DATABASE_URL` | `sqlite:///./data/poker_ai.db` | Store. |
| `HANDS_DIR` | `./data/raw/` | Ingest input. |
| `ARTIFACTS_DIR` | `./artifacts` | Models. |
| `MC_SIMULATIONS_INGEST` | `2000` | Default MC rollouts. |
| `LEAGUE_HOURS` | `6` | Self-play default budget. |
| `THINKING_MS_DEFAULT` | `0` | Decision-time compute knob. |
| `LOG_LEVEL` | `INFO` | structlog. |

---

## 5. CLI surface (Typer)

```
poker_ai db migrate
poker_ai db status
poker_ai ingest <path> [--site auto|pokerstars|gg|ohh]
poker_ai features build [--since <date>]
poker_ai train hhformer [--epochs 50]
poker_ai train student   [--teacher texas]
poker_ai train style     [--epochs 30]
poker_ai solve preflop   [--positions hu|6max --production --equity-mode real --workers N]
poker_ai pipeline run  [--corpus <path> --workers 0]
poker_ai league run      [--hours 6]
poker_ai league leaderboard
poker_ai eval aivat <session_id>
poker_ai opponents profile <player_uid>
poker_ai serve           [--host 127.0.0.1 --port 8000]
poker_ai models list | promote <name> <version> | rollback <name>
```

Every command is documented in `--help` and re-tested by `tests/cli/`.

---

## 6. Service surface (FastAPI)

| Endpoint | Verb | Purpose |
|----------|------|---------|
| `/api/health` | GET | DB ping, schema version, current model versions. |
| `/api/hands` | GET | Paginated list with filters. |
| `/api/hands/{hand_id}` | GET | Detail + replay timeline. |
| `/api/decide` | POST | Body: `GameState` JSON + `profile_id`; returns `ActionDist` + `explain`. |
| `/api/replay/{hand_id}` | GET | Timeline + GTO frequencies overlay. |
| `/api/league/leaderboard` | GET | Elo + AIVAT EVs. |
| `/api/opponents/{player_uid}` | GET | Style vector, stats, BOCPD regimes. |
| `/api/sim/start` | POST | Boot a sim session, returns `session_id`. |
| `/ws/sim/{session_id}` | WS | Stream sim decisions. |

**Auth** (when exposed beyond loopback): API key via `Authorization: Bearer …`; rate-limited via `slowapi`. No external SSO.

---

## 7. Data contracts

`HandRecord` (the canonical Pydantic model):

```python
from pydantic import BaseModel, Field
from datetime import datetime

class Player(BaseModel):
    seat: int
    position: str
    player_uid: str          # HMAC(salt, nickname)
    stack: float
    is_hero: bool

class Action(BaseModel):
    street: str              # "preflop" | "flop" | "turn" | "river"
    seat: int
    type: str                # "fold" | "call" | "raise" | "bet" | "check"
    amount: float = 0.0
    is_all_in: bool = False
    pot_before: float
    pot_after: float

class HandRecord(BaseModel):
    hand_id: str
    site: str
    played_at: datetime
    stakes: tuple[float, float]
    game_type: str           # "NLH"
    num_players: int
    players: list[Player]
    hero_cards: tuple[str, str] | None
    board: list[str] = Field(default_factory=list)
    actions: list[Action]
    pots: dict[str, float]   # per-street running pot
    rake: float = 0.0
    showdowns: list[dict]    # who showed, won, net
    raw: str | None = None   # original text for forensic replay
```

This is the **only** model crossing module boundaries on ingest.

---

## 8. Test plan summary

See [TESTING_AND_QA.md](TESTING_AND_QA.md) for the full pyramid. Highlights:

- **Unit (~70 %)**: parsers, evaluator, CFR math, regret matching, range vector ops.
- **Integration (~25 %)**: ingest → store → features; train job smoke; policy decisions.
- **End-to-end (~5 %)**: golden hand replay; FastAPI `/decide` happy path; **air-gapped smoke test** (deny network, run pipeline, expect green).
- **Property tests** (`hypothesis`): chip conservation, equity sums, range-vector L1.
- **Canary tests**: each model has a fixed input → expected output within tolerance.

---

## 9. Local-first ops

Everything runs on a single workstation:

- **No** Kubernetes. **No** managed cloud. **No** external secret manager.
- Optional `docker-compose` brings up Postgres + Grafana + Prometheus locally if the user wants the full observability stack.
- Backups are `sqlite3 .backup` or `pg_dump`.
- Updates: `git pull && uv sync && task migrate && task ci`.

A **deny-egress firewall test** in CI verifies the system runs to completion with all outbound network blocked except `127.0.0.1` and the local dashboard origin.

---

## 10. Versioning, release, and rollback

- **SemVer** on the package (`poker_ai>=0.1.0`).
- Every model: `artifacts/<name>/v<YYYY-MM-DD>-<short-sha>/` with `MODEL_CARD.md`, `metrics.json`, `weights.safetensors`.
- `artifacts/<name>/CURRENT` is a one-line text file pointing at the active version.
- `poker_ai models rollback <name>` restores the previous `CURRENT`.

**Promotable registry names** (mirror `RouterPolicy` + Status page — not HU-only):

| `name` | Applies when |
|---|---|
| `hhformer` | All decisions (shared encoder) |
| `student_hu` | `n_active == 2` postflop |
| `student_multiway` | `n_active >= 3` postflop (6-max, 8-max, 9-max, full ring) |
| `preflop_hu` | HU preflop |
| `preflop_6max` | 6-max preflop (`num_seats ≤ 6`) |
| `style_encoder` | Profiling / exploit |
| `solver_cache` | HU TexasSolver teacher cache |

- A **promotion** requires:
  1. AIVAT-significant league win (p < 0.05, ≥ 1 000 hands) on the **matching format** (HU student → HU league legs; multi-way student → 6-max/9-max legs).
  2. All canary tests pass.
  3. Drift report is green.
  4. Manual `--confirm` flag.

---

## 11. Security & compliance hooks

- All ingest pseudonymises nicknames into `player_uid` before write.
- Optional SQLCipher mode for at-rest encryption.
- Right-to-erasure CLI: `poker_ai privacy erase <player_uid>`.
- Audit log table records every `/decide`, `/sim/*`, and model promotion.
- See [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md) for the full posture.

---

## 12. What you will see after Phase 10

1. `poker_ai serve` boots in < 5 s with all models loaded.
2. The dashboard opens at `http://127.0.0.1:5173`:
   - **Replayer** — pick any of your 19 k hands, scrub through, see GTO frequencies + your action.
   - **Live Sim** — start a 6-max session vs. league agents, watch decisions stream in.
   - **Player Profiles** — search by `player_uid`, see style vector, classical stats, BOCPD regime timeline.
   - **Solver Spots** — browse cached TexasSolver outputs by board.
   - **League** — leaderboard with Elo + AIVAT EV.
   - **Drift** — auto-generated weekly report.
3. The same code runs offline on a laptop in the train, with no internet at all.

That is the “hero” end-state. The roadmap to it is in [ROADMAP.md](ROADMAP.md), and the unique levers — HHFormer, range-FFT equity, distilled student, style embeddings, local league, BOCPD, symbolic explain — are detailed in [NOVEL_TECHNIQUES.md](NOVEL_TECHNIQUES.md).
