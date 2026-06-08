#!/usr/bin/env bash
# Download TexasSolver console binary for Linux/macOS (AGPL).
# Run from poker_ai/:  ./scripts/install_texassolver.sh [--force]

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="python3"
fi

ARGS=(-m poker_ai solve install-texas)
if [[ "${1:-}" == "--force" ]]; then
  ARGS+=(--force)
fi

exec "$PY" "${ARGS[@]}"
