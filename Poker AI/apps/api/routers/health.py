"""Health and readiness."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from deps import cached_settings, get_db, get_schema_revision
from schemas import HealthResponse
from poker_ai import __version__
from poker_ai.store.loader import count_parsed_hands
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(session: AsyncSession = Depends(get_db)) -> HealthResponse:
    _ = cached_settings()
    n_hands: int | None = None
    try:
        n_hands = await count_parsed_hands(session)
    except Exception:
        n_hands = None
    return HealthResponse(
        version=__version__,
        schema_revision=get_schema_revision(),
        hands_in_store=n_hands,
        offline_mode=True,
    )
