#!/usr/bin/env bash
# Repo-root entrypoint — delegates to poker_ai/scripts/install.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${ROOT}/poker_ai/scripts/install.sh" "$@"
