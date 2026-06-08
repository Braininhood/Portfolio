"""v2 Stream C — DB replay league."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("POKER_AI_REPLAY_LEAGUE", "1")

from poker_ai.league.replay_league import run_replay_league


def main() -> int:
    report = run_replay_league(limit=500, strata="hu,mw")
    if report.hands_scored < 1:
        print("SKIP: no hands scored (empty DB?)")
        return 0
    if report.hero_decisions < 1:
        print("FAIL: zero hero decisions scored")
        return 1
    print(
        f"OK: hands={report.hands_scored} decisions={report.hero_decisions} "
        f"report={report.report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
