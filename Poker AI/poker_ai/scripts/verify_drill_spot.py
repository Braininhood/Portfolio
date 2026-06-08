"""Shim — delegates to ``apps/api/scripts/verify_drill_spot.py`` (keeps ``cd poker_ai`` workflow)."""

from __future__ import annotations

import runpy
from pathlib import Path

_TARGET = Path(__file__).resolve().parents[2] / "apps" / "api" / "scripts" / "verify_drill_spot.py"

if __name__ == "__main__":
    runpy.run_path(str(_TARGET), run_name="__main__")
