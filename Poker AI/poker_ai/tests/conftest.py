"""Pytest defaults for the poker_ai package."""

from __future__ import annotations

import os

# ProcessPool table build + pytest on Windows often hangs at shutdown; use serial in tests.
os.environ.setdefault("POKER_AI_EQUITY_WORKERS", "1")
