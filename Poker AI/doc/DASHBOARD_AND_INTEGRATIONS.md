# Backend, dashboard (JS), DB testing, settings, and bot “how they play”

> **Current implementation (May 2026):** See [WEB_IMPLEMENTATION_GUIDE.md](WEB_IMPLEMENTATION_GUIDE.md) § *Session summary — May 2026* for Import (`/import`), Tasks/job queue (`/jobs`), cancel/release-all, and `python -m poker_ai serve`. This doc remains the original stack rationale.

## Recommended stack — **Python backend + JavaScript frontend**

### Backend: **FastAPI** (Python 3.10+)

| Why | Detail |
|-----|--------|
| Typed APIs | **Pydantic** models mirror DB rows and API contracts. |
| Async-ready | `async` routes + `asyncpg` / `aiosqlite` for non-blocking reads. |
| Ops | OpenAPI at `/docs` for free QA of endpoints. |

**Layout:**

```
apps/
  api/                    # FastAPI application
    main.py               # create_app(), CORS, routers
    deps.py               # get_db(), get_settings()
    routers/
      hands.py            # CRUD / search by hand_id, date, site
      health.py           # DB ping, schema version
      sim.py              # start sim, stream decisions (WebSocket)
    settings.py           # Pydantic BaseSettings → env + .env file
  web/                    # Frontend (see below)
```

**Serve in dev:** API on `http://localhost:8000`, frontend on `http://localhost:5173` with **CORS** allowing the Vite origin. In production, same host reverse-proxy (`/api` → uvicorn).

### Frontend: **React + TypeScript + Vite** (default “best JS” choice)

| Why | Detail |
|-----|--------|
| Ecosystem | Largest pool of components, examples, and hiring. |
| Performance | **Vite** = fast HMR, sensible defaults. |
| Data | **TanStack Query** (React Query) for caching, retries, stale-while-revalidate against FastAPI. |
| UI | **shadcn/ui** (Radix + Tailwind) or **MUI** for a professional dashboard quickly. |
| Tables | **TanStack Table** for millions of rows with virtual scrolling (or server-side pagination). |
| Charts | **Recharts** or **Apache ECharts** for VPIP, EV, profile comparisons. |

**Alternatives (when to pick them):**

| Stack | When |
|-------|------|
| **Next.js (App Router)** | You want SSR/SEO, single deploy, or API routes colocated with UI. |
| **SvelteKit** | Smaller bundles, less boilerplate; smaller ecosystem than React. |
| **Vue 3 + Vite** | Team already on Vue. |

**Not recommended as primary** for a new “pro” dashboard: **Streamlit** — fastest for **internal** prototypes only; weak story for custom replayer, WebSocket-heavy sim UI, and multi-tab product UX compared to React+Vite.

---

## Settings — how to change configuration safely

### Pattern: **Pydantic Settings** + environment layers

1. **`.env`** (gitignored) — local secrets and paths:  
   `DATABASE_URL=sqlite:///./data/poker.db`  
   `HANDS_DIR=D:\PokerData\hands`  
   `API_CORS_ORIGINS=http://localhost:5173`

2. **`config/settings.yaml`** (optional, committed) — non-secret defaults: pagination limits, feature flags.

3. **`Settings` class** (`pydantic-settings`) reads env with **prefix** e.g. `POKER_AI_` to avoid collisions.

4. **Profiles:** `APP_ENV=development|staging|production` switches log level, DB URL, and CORS.

**Frontend settings:** build-time `VITE_API_BASE_URL`; per-user prefs in **localStorage** (theme, table page size) — not secrets.

**Migration from today’s repo:** replace hard-coded `DB_PATH` / `FOLDER_PATH` in `db/*.py` with `os.environ` or a shared `poker_ai.config` module imported by both CLI scripts and FastAPI `deps.py`.

---

## Testing a **new** database — approaches

| Goal | Solution |
|------|----------|
| **CI / unit tests** | **`pytest`** + **`tmp_path`**: create empty SQLite, run migrations / `create_tables`, insert fixture rows, assert queries. Never use production `poker.db`. |
| **Copy production safely** | `sqlite3 poker.db ".backup test-copy.db"` or file copy; point `DATABASE_URL` at copy. |
| **Schema drift** | **Alembic** migrations; in CI run `alembic upgrade head` then tests. |
| **Golden hands** | Small `tests/fixtures/hands/*.txt` committed; parser → expected JSON or row counts. |
| **API contract** | **pytest + httpx** `AsyncClient(app=app)` against FastAPI; or **Schemathesis** from OpenAPI. |
| **Parallel dev DBs** | `poker_dev.db`, `poker_qa.db` via `.env.development` / `.env.qa` only. |

**Exit gate before “new DB” in prod:** migration applied, `health` endpoint returns schema version, smoke test imports 1 known hand.

---

## Bots showing **how** they play — new DB + different profiles

**Idea:** separate **(A) data** from **(B) policy** from **(C) persona**.

| Piece | Implementation |
|-------|----------------|
| **Data** | Bots read **`Games` / `Hands` / `Actions`** (or replay from **JSON/OHH**) from the DB you select via `DATABASE_URL`. |
| **Policy** | Python `Policy` interface: `decide(state) -> ActionDist`. Implementations: `PolicyGTOFromDb`, `PolicyExploit`, `PolicyTorch`, etc. |
| **Profile** | `profile_id` → YAML/JSON: temperature, aggression multiplier, sizing noise, exploit weight. Applied **after** base logits or by mixing policies. |

### How to **show** play to users

1. **Replayer UI (React)** — Street timeline from `Actions`; optional overlay: **frequencies** from `GTO_Solutions` or bot choice.  
2. **Live sim WebSocket** — FastAPI **WebSocket** `/ws/sim`: server sends `{street, acting_seat, legal_actions, chosen_action, pot, profile_id}`; client renders table + chat-style log.  
3. **Batch export** — Run N hands in sim, write **`Bot_Performance`**-style rows + **`session_id`**; dashboard compares **Profile A vs Profile B** on same seed.  
4. **Video / GIF** — Optional later (headless browser or canvas record); not required for MVP.

### Different profiles, same DB

- Store **`profiles` table** or YAML files: `tag`, `lag`, `gto_pure`, `exploit_max`.  
- Sim loop: `for profile in profiles: run_league(seed, profile_id)` → aggregate stats in **`Results`-like sim table** (do not confuse with real hand `Results` unless namespaced).

### Compliance reminder

Show “how bots play” in **your simulator or analysis tool** on **data you own**. Do not document bypassing third-party clients.

---

## HM2 / trackers (unchanged summary)

- **File path:** HM2 exports **`.txt`** — same family as PT4 “from disk” imports.  
- **SQL path:** read-only PostgreSQL → canonical tables (versioned mapper).  

See [HAND_HISTORY_FORMATS.md](HAND_HISTORY_FORMATS.md) for full format list and [ROADMAP.md](ROADMAP.md) for phases.

---

## Doc map

| Topic | File |
|-------|------|
| All hand file / DB sources | [HAND_HISTORY_FORMATS.md](HAND_HISTORY_FORMATS.md) |
| Repo layout today | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Phased delivery | [ROADMAP.md](ROADMAP.md) |
