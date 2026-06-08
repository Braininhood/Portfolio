"""v2 Stream B — full AIVAT audit stderr reduction."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ["POKER_AI_AIVAT_FULL"] = "1"

from poker_ai.eval.aivat import run_aivat_audit


def main() -> int:
    report = run_aivat_audit(hands=1000, seed=42)
    if report.stderr_reduction_pct < 0:
        print(f"WARN: negative reduction {report.stderr_reduction_pct}%")
    print(
        f"AIVAT audit: naive_stderr={report.naive_stderr:.4f} "
        f"full_stderr={report.full_stderr:.4f} "
        f"reduction={report.stderr_reduction_pct:.1f}%"
    )
    print(f"Report: {report.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
