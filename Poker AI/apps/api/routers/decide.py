"""POST /decide — policy propose + symbolic explanation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_db
from schemas import ActionProb, DecideRequest, DecideResponse
from services.decide_service import run_decide_for_state
from services.play_session_snapshot import game_state_from_dict

from poker_ai.core.replay import state_after_actions
from poker_ai.policy.bench import _postflop_state
from poker_ai.store.loader import load_parsed_hand_by_id

router = APIRouter(tags=["decide"])


@router.post("/decide", response_model=DecideResponse)
async def decide(body: DecideRequest, session: AsyncSession = Depends(get_db)) -> DecideResponse:
    if body.game_state is not None:
        try:
            state = game_state_from_dict(body.game_state)
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"invalid game_state: {exc}") from exc
    elif body.hand_id is not None:
        hand = await load_parsed_hand_by_id(session, body.hand_id)
        if hand is None:
            raise HTTPException(status_code=404, detail=f"hand_id {body.hand_id} not found")
        if body.step_index > len(hand.actions):
            raise HTTPException(status_code=400, detail="step_index exceeds action count")
        state = state_after_actions(hand, body.step_index)
    else:
        state = _postflop_state()

    try:
        result = run_decide_for_state(
            state,
            profile_id=body.profile_id,
            policy_name=body.policy,
            thinking_ms=body.thinking_ms,
            deep_search=body.deep_search,
            include_equity=body.include_equity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    actions = [
        ActionProb(
            kind=str(r["kind"]),
            amount_chips=int(r["amount_chips"]),
            seat=int(r["seat"]),
            prob=float(r["prob"]),
            label=str(r.get("label") or r["kind"]),
        )
        for r in result["actions"]
    ]
    return DecideResponse(
        policy_name=str(result["policy_name"]),
        policy_version=str(result["policy_version"]),
        latency_ms=float(result["latency_ms"]),
        actions=actions,
        explanation=str(result["explanation"]),
        street=str(result["street"]),
        acting_seat=result["acting_seat"],
        hero_equity=(
            float(result["hero_equity"]) if result.get("hero_equity") is not None else None
        ),
    )
