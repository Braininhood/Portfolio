"""Optional DuckDB read-only bridge over the SQLite canonical store."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def attach_sqlite_readonly(sqlite_path: Path) -> Any:
    """Return a DuckDB connection with the SQLite file attached read-only.

    Requires the ``analytics`` extra (``uv sync --extra analytics``).
    """
    import duckdb

    sqlite_url = sqlite_path.resolve().as_posix().replace("'", "''")
    con = duckdb.connect(database=":memory:")
    con.execute(
        f"ATTACH '{sqlite_url}' AS poker (TYPE sqlite, READ_ONLY);",
    )
    return con


def explain_analytics_layer() -> str:
    """Human-readable pointer for doc/ROADMAP.md Phase 1 DuckDB hook."""
    return (
        "DuckDB can attach the SQLite store read-only for vectorized analytics; "
        "export snapshots to Parquet for heavy scans (see doc/PERFORMANCE_AND_SCALING.md)."
    )
