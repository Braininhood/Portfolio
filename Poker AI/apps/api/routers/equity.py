"""POST /equity — instant heads-up equity calculator (Phase W5)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from schemas import EquityRequest, EquityResponse
from services.equity_service import compute_equity

router = APIRouter(tags=["equity"])


@router.post("/equity", response_model=EquityResponse)
async def calculate_equity(body: EquityRequest) -> EquityResponse:
    try:
        result = compute_equity(
            hero_cards=body.hero_cards,
            board_cards=body.board_cards,
            villain_range=body.villain_range,
            mode=body.mode,
            num_samples=body.num_samples,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return EquityResponse(**result)
