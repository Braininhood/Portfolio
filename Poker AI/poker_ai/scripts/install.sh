#!/usr/bin/env bash
# Poker AI — Linux / macOS bootstrap (Phase W9 / Phase 12)
# Run from repo root:  ./poker_ai/scripts/install.sh
# Or:  bash poker_ai/scripts/install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POKER_AI="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [[ -f "${POKER_AI}/pyproject.toml" ]]; then
  ROOT="$(cd "${POKER_AI}/.." && pwd)"
else
  ROOT="${POKER_AI}"
  POKER_AI="${ROOT}/poker_ai"
fi
WEB="${ROOT}/apps/web"

echo "Poker AI install — repo: ${ROOT}"

# 1. Python 3.11+
if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 not found. Install Python 3.11+ and ensure it is on PATH." >&2
  exit 1
fi
PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "error: Python 3.11+ required (found ${PY_VER})." >&2
  exit 1
fi
echo "Python ${PY_VER} OK"

# 2. uv
export PATH="${HOME}/.local/bin:${HOME}/.cargo/bin:${PATH}"
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv…"
  curl -fsSL https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${HOME}/.cargo/bin:${PATH}"
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv not available after install. Add ~/.local/bin to PATH and retry." >&2
  exit 1
fi

# 3. Sync poker_ai + API extras
echo "Syncing dependencies (uv sync --all-extras)…"
(cd "${POKER_AI}" && uv sync --all-extras)

# 4. Build web (same-origin API — no /api prefix)
if ! command -v npm >/dev/null 2>&1; then
  echo "error: npm not found. Install Node.js 18+ for the dashboard build." >&2
  exit 1
fi
(
  cd "${WEB}"
  if [[ ! -d node_modules ]]; then
    echo "npm install…"
    npm install
  fi
  export VITE_API_BASE_URL=""
  export VITE_WS_BASE_URL="ws://127.0.0.1:8000"
  echo "npm run build…"
  npm run build
)

# 5. Migrations
echo "Database migrate…"
(cd "${POKER_AI}" && uv run python -m poker_ai db migrate)

# 6. Start API (serves apps/web/dist when present; serve opens browser when ready)
echo "Starting server (API + static dashboard)…"
LOG="${TMPDIR:-/tmp}/poker-ai-serve.log"
(
  cd "${POKER_AI}"
  nohup uv run python -m poker_ai serve --no-web --no-reload >>"${LOG}" 2>&1 &
  echo $! >"${POKER_AI}/.serve-install.pid"
)
PID="$(cat "${POKER_AI}/.serve-install.pid")"
echo "Server PID ${PID} — log: ${LOG}"
echo "Dashboard: http://127.0.0.1:8000/status (browser opens when the API is ready)"
echo "Stop: kill ${PID}  —  Foreground: cd poker_ai && uv run python -m poker_ai serve --no-web"
