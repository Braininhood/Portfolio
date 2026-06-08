"""Central worker-count resolution for CPU-bound phases."""

from __future__ import annotations

import os


def default_worker_count() -> int:
    """Process count for parallel phases (env ``POKER_AI_NUM_WORKERS``, else ~75% CPUs)."""
    raw = os.environ.get("POKER_AI_NUM_WORKERS", "").strip()
    if raw:
        try:
            return max(1, int(raw))
        except ValueError:
            pass
    cpu = os.cpu_count() or 4
    return max(1, min(cpu, max(1, cpu - 1)))


def resolve_worker_count(workers: int | None) -> int:
    """``0`` or ``None`` → auto; ``1`` → single-process; ``>1`` → that many workers."""
    if workers is None or workers <= 0:
        return default_worker_count()
    return max(1, workers)
