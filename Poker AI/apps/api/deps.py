"""FastAPI dependencies (Phase 10)."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poker_ai.config.settings import Settings, get_settings
from poker_ai.store.db import get_async_session_factory
from poker_ai.store.migrate import current_revision


@lru_cache(maxsize=1)
def cached_settings() -> Settings:
    return get_settings()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory: async_sessionmaker[AsyncSession] = get_async_session_factory()
    async with factory() as session:
        yield session


def get_schema_revision() -> str | None:
    return current_revision()
