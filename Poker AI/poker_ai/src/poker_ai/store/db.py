"""Async engine factory with SQLite WAL + foreign keys (see doc/DATABASE_SCHEMA.md §3)."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from poker_ai.config.settings import get_settings

_session_factory: async_sessionmaker[AsyncSession] | None = None
_engine: AsyncEngine | None = None


def _sqlite_pragma_connect(dbapi_connection: Any, _record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=120000")
    if os.environ.get("POKER_AI_SQLITE_SYNC_OFF", "").strip() in ("1", "true", "yes"):
        cursor.execute("PRAGMA synchronous=OFF")
    cursor.close()


@event.listens_for(Engine, "connect")
def _enable_sqlite_pragmas(dbapi_connection: Any, _connection_record: Any) -> None:
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return
    _sqlite_pragma_connect(dbapi_connection, _connection_record)


def create_engine_and_session_factory(
    database_url: str | None = None,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create a new async engine and session factory (primarily for tests)."""
    url = database_url or get_settings().database_url
    engine = create_async_engine(
        url,
        echo=get_settings().debug,
        future=True,
    )
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    return engine, factory


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Process-wide session factory (lazy singleton)."""
    global _session_factory, _engine
    if _session_factory is None:
        _engine, _session_factory = create_engine_and_session_factory()
    return _session_factory


async def dispose_async_store() -> None:
    """Dispose the process-wide async engine (tests / CLI reload)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Yield a session and always close it."""
    factory = get_async_session_factory()
    session = factory()
    try:
        yield session
    finally:
        await session.close()
