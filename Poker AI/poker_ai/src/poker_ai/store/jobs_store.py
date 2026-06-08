"""Async CRUD for the ``jobs`` table (Phase W1 job queue)."""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from poker_ai.config.settings import get_settings


def sqlite_path_from_database_url(database_url: str | None = None) -> Path:
    """Resolve a filesystem path from a SQLAlchemy SQLite URL."""
    url = database_url or get_settings().database_url
    parsed = urlparse(url.replace("+aiosqlite", ""))
    if parsed.scheme not in ("sqlite", ""):
        raise ValueError(f"Expected sqlite URL, got {url!r}")
    raw = unquote(parsed.path or "")
    if raw.startswith("/") and len(raw) > 2 and raw[2] == ":":
        raw = raw.lstrip("/")
    return Path(raw).resolve()


def sync_update_progress(job_id: str, progress_json: str) -> None:
    """Thread-safe progress write for CPU-heavy jobs (does not need the asyncio loop)."""
    path = sqlite_path_from_database_url()
    for attempt in range(12):
        conn = sqlite3.connect(str(path), timeout=120)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=120000")
            conn.execute(
                "UPDATE jobs SET progress_json = ? WHERE id = ?",
                (progress_json, job_id),
            )
            conn.commit()
            return
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower() or attempt >= 11:
                raise
            time.sleep(min(2.0, 0.15 * (2**attempt)))
        finally:
            conn.close()


def sync_cancel_job(job_id: str, *, reason: str) -> bool:
    """Thread-safe cancel for queued/running jobs (avoids async/session lock fights)."""
    path = sqlite_path_from_database_url()
    now = utcnow_naive()
    progress = json.dumps(
        {"pct": 0, "msg": "Stopped", "detail": {"forced": True}},
        separators=(",", ":"),
    )
    conn = sqlite3.connect(str(path), timeout=60)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=120000")
        cur = conn.execute(
            "UPDATE jobs SET status = 'cancelled', finished_at = ?, error = ?, progress_json = ? "
            "WHERE id = ? AND status IN ('queued', 'running')",
            (now.isoformat(sep=" "), reason, progress, job_id),
        )
        conn.commit()
        return int(cur.rowcount or 0) > 0
    finally:
        conn.close()


def sync_insert_job(
    *,
    job_id: str,
    job_type: str,
    status: str,
    params: dict[str, Any],
    database_url: str | None = None,
) -> None:
    """Insert a job row on a dedicated sync connection (avoids API session lock fights)."""
    path = sqlite_path_from_database_url(database_url)
    params_json = json.dumps(params, separators=(",", ":"))
    conn = sqlite3.connect(str(path), timeout=120)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=120000")
        for attempt in range(12):
            try:
                conn.execute(
                    "INSERT INTO jobs (id, type, status, params_json, progress_json) "
                    "VALUES (?, ?, ?, ?, NULL)",
                    (job_id, job_type, status, params_json),
                )
                conn.commit()
                return
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc).lower() or attempt >= 11:
                    raise
                time.sleep(min(2.0, 0.15 * (2**attempt)))
    finally:
        conn.close()


async def insert_job(
    session: AsyncSession,
    *,
    job_id: str,
    job_type: str,
    status: str,
    params: dict[str, Any],
) -> None:
    from poker_ai.store.sqlite_retry import with_sqlite_retry

    async def _run() -> None:
        await session.execute(
            text(
                "INSERT INTO jobs (id, type, status, params_json, progress_json) "
                "VALUES (:id, :type, :status, :params_json, :progress_json)"
            ),
            {
                "id": job_id,
                "type": job_type,
                "status": status,
                "params_json": json.dumps(params, separators=(",", ":")),
                "progress_json": None,
            },
        )

    await with_sqlite_retry(_run)


async def update_job(
    session: AsyncSession,
    job_id: str,
    *,
    status: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    progress_json: str | None = None,
    result_json: str | None = None,
    error: str | None = None,
) -> None:
    parts: list[str] = []
    bind: dict[str, Any] = {"id": job_id}
    if status is not None:
        parts.append("status = :status")
        bind["status"] = status
    if started_at is not None:
        parts.append("started_at = :started_at")
        bind["started_at"] = started_at
    if finished_at is not None:
        parts.append("finished_at = :finished_at")
        bind["finished_at"] = finished_at
    if progress_json is not None:
        parts.append("progress_json = :progress_json")
        bind["progress_json"] = progress_json
    if result_json is not None:
        parts.append("result_json = :result_json")
        bind["result_json"] = result_json
    if error is not None:
        parts.append("error = :error")
        bind["error"] = error
    if not parts:
        return
    sql = "UPDATE jobs SET " + ", ".join(parts) + " WHERE id = :id"
    await session.execute(text(sql), bind)


async def fetch_job(session: AsyncSession, job_id: str) -> dict[str, Any] | None:
    row = (
        await session.execute(
            text(
                "SELECT id, type, status, created_at, started_at, finished_at, "
                "params_json, progress_json, result_json, error FROM jobs WHERE id = :id"
            ),
            {"id": job_id},
        )
    ).mappings().first()
    return dict(row) if row else None


async def fetch_active_job(session: AsyncSession) -> dict[str, Any] | None:
    """Most recent job that is still queued or running."""
    active = await list_active_jobs(session, limit=1)
    return active[0] if active else None


async def list_active_jobs(session: AsyncSession, *, limit: int = 20) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            text(
                "SELECT id, type, status, created_at, started_at, finished_at, "
                "params_json, progress_json, result_json, error "
                "FROM jobs WHERE status IN ('queued', 'running') "
                "ORDER BY datetime(created_at) DESC LIMIT :lim"
            ),
            {"lim": limit},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def cancel_all_active(
    session: AsyncSession,
    *,
    error: str,
) -> list[str]:
    """Mark every queued/running job cancelled; returns affected job ids."""
    now = utcnow_naive()
    rows = await list_active_jobs(session, limit=500)
    ids = [str(r["id"]) for r in rows]
    if not ids:
        return []
    for job_id in ids:
        await update_job(
            session,
            job_id,
            status="cancelled",
            finished_at=now,
            error=error,
            progress_json=json.dumps(
                {"pct": 0, "msg": "Stopped", "detail": {"forced": True}},
                separators=(",", ":"),
            ),
        )
    return ids


async def count_jobs_by_status(session: AsyncSession) -> dict[str, int]:
    rows = (
        await session.execute(
            text("SELECT status, COUNT(*) AS n FROM jobs GROUP BY status"),
        )
    ).mappings().all()
    return {str(r["status"]): int(r["n"]) for r in rows}


async def list_jobs_recent(session: AsyncSession, *, limit: int = 50) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            text(
                "SELECT id, type, status, created_at, started_at, finished_at, "
                "params_json, progress_json, result_json, error "
                "FROM jobs ORDER BY datetime(created_at) DESC LIMIT :lim"
            ),
            {"lim": limit},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def last_finished_job(
    session: AsyncSession,
    job_type: str,
) -> dict[str, Any] | None:
    row = (
        await session.execute(
            text(
                "SELECT id, type, status, finished_at FROM jobs "
                "WHERE type = :t AND status IN ('done', 'error') "
                "ORDER BY datetime(finished_at) DESC LIMIT 1"
            ),
            {"t": job_type},
        )
    ).mappings().first()
    return dict(row) if row else None


async def last_nightly_run_at(session: AsyncSession) -> str | None:
    """Most recent finished time among core nightly job types."""
    types = (
        "features_build",
        "train_hhformer",
        "train_multiway_student",
        "train_student",
        "league_run",
    )
    placeholders = ", ".join(f":t{i}" for i in range(len(types)))
    bind = {f"t{i}": t for i, t in enumerate(types)}
    row = (
        await session.execute(
            text(
                f"SELECT MAX(finished_at) AS last_at FROM jobs "
                f"WHERE type IN ({placeholders}) AND status = 'done'"
            ),
            bind,
        )
    ).mappings().first()
    if not row or row.get("last_at") is None:
        return None
    return str(row["last_at"])


def utcnow_naive() -> datetime:
    """SQLite-friendly naive UTC timestamp."""
    return datetime.now(UTC).replace(tzinfo=None)
