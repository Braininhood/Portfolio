"""Run Alembic migrations programmatically (Typer ``db migrate``)."""

from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from poker_ai.config.settings import get_settings

_UPGRADE_DONE = False


def _sync_sqlalchemy_url(async_url: str) -> str:
    """Alembic revision scripts use the synchronous SQLite driver."""
    if "+aiosqlite" in async_url:
        return async_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    if "+asyncpg" in async_url:
        return async_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return async_url


def alembic_config() -> Config:
    root = Path(__file__).resolve().parents[3]
    ini = root / "alembic.ini"
    cfg = Config(str(ini))
    cfg.set_main_option("sqlalchemy.url", _sync_sqlalchemy_url(get_settings().database_url))
    return cfg


def upgrade_head() -> None:
    """Apply pending migrations once per process (no-op if already at head)."""
    global _UPGRADE_DONE
    if _UPGRADE_DONE:
        return
    cfg = alembic_config()
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()
    current = current_revision()
    if head is not None and current == head:
        _UPGRADE_DONE = True
        return
    alembic_log = logging.getLogger("alembic")
    prev = alembic_log.level
    alembic_log.setLevel(logging.WARNING)
    try:
        command.upgrade(cfg, "head")
    finally:
        alembic_log.setLevel(prev)
    _UPGRADE_DONE = True


def current_revision() -> str | None:
    """Return current Alembic revision id, or ``None`` if DB is empty / unknown."""
    from alembic.runtime.migration import MigrationContext

    url = _sync_sqlalchemy_url(get_settings().database_url)
    eng = None
    try:
        eng = create_engine(url)
    except OperationalError:
        return None
    try:
        with eng.connect() as conn:
            ctx = MigrationContext.configure(conn)
            return ctx.get_current_revision()
    except OperationalError:
        return None
    finally:
        if eng is not None:
            eng.dispose()
