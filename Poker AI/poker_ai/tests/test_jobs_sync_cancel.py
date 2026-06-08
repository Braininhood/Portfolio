"""Sync job cancel avoids 500 under worker load."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from poker_ai.store import jobs_store


def test_sync_cancel_job_updates_running_row(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "jobs.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE jobs (
            id TEXT PRIMARY KEY,
            type TEXT,
            status TEXT,
            created_at TEXT,
            started_at TEXT,
            finished_at TEXT,
            params_json TEXT,
            progress_json TEXT,
            result_json TEXT,
            error TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO jobs (id, type, status) VALUES (?, ?, ?)",
        ("job-1", "solve_preflop", "running"),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(
        jobs_store,
        "sqlite_path_from_database_url",
        lambda url=None: db,
    )

    ok = jobs_store.sync_cancel_job("job-1", reason="Stopped by user")
    assert ok is True

    row = sqlite3.connect(db).execute(
        "SELECT status, error, progress_json FROM jobs WHERE id = 'job-1'"
    ).fetchone()
    assert row[0] == "cancelled"
    assert row[1] == "Stopped by user"
    assert json.loads(row[2])["msg"] == "Stopped"
