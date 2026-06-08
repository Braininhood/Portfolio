"""GET /health/smoke — air-gapped production checklist (Phase W9)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_db
from schemas import SmokeResponse
from services.smoke_service import run_smoke

router = APIRouter(tags=["health"])


@router.get("/health/smoke", response_model=SmokeResponse)
async def health_smoke(session: AsyncSession = Depends(get_db)) -> SmokeResponse:
    """Run internal-only checks; no external network calls."""
    return await run_smoke(session)
