# Poker AI — Web Application

Local-only FastAPI service and React/Vite dashboard. No outbound network in normal operation.

## Quick Start

From `poker_ai/` (with editable install):

```bash
pip install -e ".[api,ml]"
python -m alembic upgrade head
python -m poker_ai serve
```

- **API**: http://127.0.0.1:8000 (OpenAPI at `/docs`)
- **Dashboard**: http://127.0.0.1:5173

If port 8000 is busy, the server tries **8765** automatically.

## Production Build

```bash
cd apps/web
npm run build
cd ../../poker_ai
python -m poker_ai serve --no-web
# → http://127.0.0.1:8000/status
```

## Directory Structure

| Path | Description |
|------|-------------|
| `api/` | FastAPI backend (routers, services, schemas) |
| `web/` | React + TypeScript + Vite frontend |
| `api/scripts/` | Verification scripts |

## Main Pages

| URL | Purpose |
|-----|---------|
| `/setup` | Setup wizard with guided steps |
| `/import` | Import hand histories |
| `/status` | System status and model artifacts |
| `/jobs` | AI pipeline tasks |
| `/play` | Play vs AI bots |
| `/drill` | Decision training |
| `/equity` | HU equity calculator |
| `/league` | League leaderboard |
| `/profiles` | Player analysis |
| `/models` | Model versions and registry |
| `/drift` | Drift monitoring |
| `/health` | System health check |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /jobs` | Start background task |
| `POST /decide` | Get AI decision |
| `POST /equity` | Calculate equity |
| `GET /health/smoke` | Air-gapped smoke test |
| `WS /ws/play/{id}` | Live play session |
| `WS /ws/jobs/{id}` | Job progress stream |

## Verification

```bash
python apps/api/scripts/verify_phase10.py
python apps/api/scripts/verify_phase12_install.py
```

## Documentation

See [../doc/WEB_IMPLEMENTATION_GUIDE.md](../doc/WEB_IMPLEMENTATION_GUIDE.md) for the complete web product guide.
