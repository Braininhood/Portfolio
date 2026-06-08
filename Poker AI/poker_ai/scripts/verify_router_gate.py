"""Phase 7b replay router gate — run against production SQLite.

Usage::

    cd poker_ai
    set POKER_AI_ROUTER_GATE=1
    .venv\\Scripts\\python.exe scripts\\verify_router_gate.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.setdefault("POKER_AI_ROUTER_GATE", "1")
    env.setdefault("POKER_AI_ROUTER_GATE_MIN", "100")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_replay_router_gate.py::test_router_gate_three_way_flop_db",
        "-q",
    ]
    print("Running replay router gate (DB integration)…")
    return subprocess.call(cmd, cwd=root, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
