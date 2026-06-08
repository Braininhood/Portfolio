"""Guard against overlapping background jobs (SQLite single-writer safety)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from poker_ai.store import jobs_store


class JobConflictError(Exception):
    """Another job is already queued or running."""

    def __init__(self, active: dict[str, Any]) -> None:
        self.active = active
        self.job_type = str(active.get("type", "task"))
        self.job_id = str(active.get("id", ""))
        super().__init__(
            f"Another task is still active ({self.job_type}). "
            "Open Tasks → Stop or Release all, then start again."
        )


async def assert_no_active_job(session: AsyncSession, *, exclude_job_id: str | None = None) -> None:
    active_list = await jobs_store.list_active_jobs(session, limit=10)
    for active in active_list:
        if exclude_job_id and str(active["id"]) == exclude_job_id:
            continue
        raise JobConflictError(active)
