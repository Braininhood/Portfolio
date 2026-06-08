"""Phase 1 exit gate — ~19k ``hand_*.txt`` ingested in < 90 s.

Usage::

    cd poker_ai
    set POKER_AI_CORPUS_ROOT=..\\hand\\6
    .venv\\Scripts\\python.exe scripts\\verify_phase1_ingest.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    corpus = os.environ.get("POKER_AI_CORPUS_ROOT", "").strip()
    if not corpus:
        default = root.parent / "hand" / "6"
        if default.is_dir():
            corpus = str(default)
    env = os.environ.copy()
    env["POKER_AI_PERF_INGEST"] = "1"
    env["POKER_AI_PERF_BUDGET_SEC"] = "90"
    if corpus:
        env["POKER_AI_CORPUS_ROOT"] = corpus
    print(f"Phase 1 ingest gate (budget 90s, corpus={env.get('POKER_AI_CORPUS_ROOT', 'hand/')})…")
    return subprocess.call(
        [sys.executable, "-m", "pytest", "tests/test_ingest_perf.py", "-v", "--tb=short"],
        cwd=root,
        env=env,
    )


if __name__ == "__main__":
    raise SystemExit(main())
