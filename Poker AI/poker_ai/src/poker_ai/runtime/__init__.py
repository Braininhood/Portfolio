"""Runtime helpers (worker pools, device selection)."""

from poker_ai.runtime.workers import default_worker_count, resolve_worker_count

__all__ = ["default_worker_count", "resolve_worker_count"]
