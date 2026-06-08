"""Optional progress callbacks for long-running library entrypoints (Phase W1)."""

from __future__ import annotations

from typing import Any, Callable

ProgressFn = Callable[[dict[str, Any]], None] | None
