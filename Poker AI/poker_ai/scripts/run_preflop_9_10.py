"""Chain 9-max and 10-max preflop production solves after 8-max (playbook)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "reports" / "playbook_logs"
LOG.mkdir(parents=True, exist_ok=True)
PY = ROOT / ".venv" / "Scripts" / "python.exe"


def run(positions: str) -> None:
    log = LOG / f"preflop_{positions}.log"
    err = LOG / f"preflop_{positions}.err.log"
    with log.open("a", encoding="utf-8") as out, err.open("a", encoding="utf-8") as er:
        out.write(f"\n=== solve preflop {positions} --production ===\n")
        out.flush()
        rc = subprocess.call(
            [str(PY), "-m", "poker_ai", "solve", "preflop", "--positions", positions, "--production"],
            cwd=str(ROOT),
            stdout=out,
            stderr=er,
        )
        out.write(f"exit code {rc}\n")
    if rc != 0:
        raise SystemExit(rc)


if __name__ == "__main__":
    for fmt in ("9max", "10max"):
        run(fmt)
