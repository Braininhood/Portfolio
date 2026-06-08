"""Shim — run from poker_ai/: python scripts/verify_phase10.py"""
from __future__ import annotations

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parents[2] / "apps" / "api" / "scripts" / "verify_phase10.py"))
