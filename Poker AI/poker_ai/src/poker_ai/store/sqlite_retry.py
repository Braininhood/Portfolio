"""Retry helpers for SQLite ``database is locked`` under concurrent API + jobs."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy.exc import OperationalError

T = TypeVar("T")

_LOCKED_MARKERS = ("database is locked", "locked")


def is_sqlite_locked(exc: BaseException) -> bool:
    msg = str(exc).lower()
    if any(m in msg for m in _LOCKED_MARKERS):
        return True
    orig = getattr(exc, "orig", None)
    return orig is not None and is_sqlite_locked(orig)


async def with_sqlite_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 12,
    base_delay_sec: float = 0.15,
    max_delay_sec: float = 2.0,
) -> T:
    """Run async ``fn`` with exponential backoff on SQLite lock errors."""
    last: BaseException | None = None
    for attempt in range(attempts):
        try:
            return await fn()
        except OperationalError as exc:
            if not is_sqlite_locked(exc) or attempt >= attempts - 1:
                raise
            last = exc
            delay = min(max_delay_sec, base_delay_sec * (2**attempt))
            await asyncio.sleep(delay)
    if last is not None:
        raise last
    msg = "with_sqlite_retry: no result"
    raise RuntimeError(msg)
