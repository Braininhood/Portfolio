"""Decision drill — hero spots from imported hands."""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_db
from schemas import (
    ActionProb,
    DrillCompareRequest,
    DrillCompareResponse,
    DrillCompareActionRow,
    DrillCompareColumn,
    DrillHandListItem,
    DrillHandsResponse,
    DrillSpotRequest,
    DrillSpotResponse,
    DrillStepsResponse,
)
from services.drill_service import (
    build_drill_spot,
    compare_policies,
    hero_decision_indices,
)

from poker_ai.store.loader import count_parsed_hands, list_hand_summaries, load_parsed_hand_by_id

router = APIRouter(prefix="/drill", tags=["drill"])


def _hand_label(r: object) -> str:
    from poker_ai.store.loader import HandSummary

    if not isinstance(r, HandSummary):
        return ""
    cards = r.hero_cards or "?"
    board = r.board_cards or "preflop only"
    pos = r.hero_position or "?"
    return f"#{r.hand_id} · {pos} · {cards} · board {board} · {r.num_actions} actions"


def _summary_to_drill_item(hand: object, summary: object) -> DrillHandListItem:
    from poker_ai.ingest.records import ParsedHand
    from poker_ai.store.loader import HandSummary

    if not isinstance(hand, ParsedHand) or not isinstance(summary, HandSummary):
        msg = "invalid hand summary"
        raise TypeError(msg)
    indices = hero_decision_indices(hand)
    return DrillHandListItem(
        hand_id=summary.hand_id,
        stakes=summary.stakes,
        num_players=summary.num_players,
        hero_position=summary.hero_position,
        hero_cards=summary.hero_cards,
        board_preview=summary.board_cards,
        num_actions=summary.num_actions,
        label=_hand_label(summary),
        has_decision_point=bool(indices),
        hero_decision_count=len(indices),
    )


async def _drill_hand_item(session: AsyncSession, summary: object) -> DrillHandListItem:
    from poker_ai.store.loader import HandSummary

    if not isinstance(summary, HandSummary):
        msg = "invalid summary"
        raise TypeError(msg)
    hand = await load_parsed_hand_by_id(session, summary.hand_id)
    if hand is None:
        return DrillHandListItem(
            hand_id=summary.hand_id,
            stakes=summary.stakes,
            num_players=summary.num_players,
            hero_position=summary.hero_position,
            hero_cards=summary.hero_cards,
            board_preview=summary.board_cards,
            num_actions=summary.num_actions,
            label=_hand_label(summary),
            has_decision_point=False,
            hero_decision_count=0,
        )
    return await asyncio.to_thread(_summary_to_drill_item, hand, summary)


@router.get("/hands", response_model=DrillHandsResponse)
async def list_drill_hands(
    session: AsyncSession = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=200)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
    drillable_only: bool = Query(
        default=False,
        description="When true, only return hands with at least one hero decision point.",
    ),
) -> DrillHandsResponse:
    total = await count_parsed_hands(session)
    rows, _ = await list_hand_summaries(session, limit=limit, offset=offset)
    if total == 0:
        return DrillHandsResponse(
            total=0,
            hands=[],
            hint=(
                "No hands in your library yet. Open Import in the menu to upload files or "
                "choose a folder on this computer."
            ),
        )

    items = list(await asyncio.gather(*[_drill_hand_item(session, r) for r in rows]))
    if drillable_only:
        items = [i for i in items if i.has_decision_point]

    return DrillHandsResponse(total=total, hands=list(items), hint=None)


@router.post("/spot", response_model=DrillSpotResponse)
async def drill_spot(
    body: DrillSpotRequest,
    session: AsyncSession = Depends(get_db),
) -> DrillSpotResponse:
    hand = await load_parsed_hand_by_id(session, body.hand_id)
    if hand is None:
        raise HTTPException(status_code=404, detail=f"hand_id {body.hand_id} not found")

    try:
        raw = await asyncio.to_thread(
            build_drill_spot,
            hand,
            body.step_index,
            policy_name=body.policy,
            thinking_ms=body.thinking_ms,
            deep_search=body.deep_search,
            include_equity=body.include_equity,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    actions = [
        ActionProb(
            kind=str(a["kind"]),
            amount_chips=int(a["amount_chips"]),
            seat=int(a["seat"]),
            prob=float(a["prob"]),
            label=str(a.get("label")) if a.get("label") else None,
        )
        for a in raw["actions"]
    ]
    return DrillSpotResponse(
        policy_name=str(raw["policy_name"]),
        policy_version=str(raw["policy_version"]),
        latency_ms=float(raw["latency_ms"]),
        actions=actions,
        explanation=str(raw["explanation"]),
        street=raw.get("street"),
        acting_seat=raw.get("acting_seat"),
        step_index=int(raw["step_index"]),
        actual_action=str(raw["actual_action"]),
        actual_amount=raw.get("actual_amount"),
        hero_cards=raw.get("hero_cards"),
        board=raw.get("board"),
        position=raw.get("position"),
        pot_bb=raw.get("pot_bb"),
        stack_bb=raw.get("stack_bb"),
        spr=raw.get("spr"),
        action_comparison=str(raw["action_comparison"]),
        policy_vs_human=str(raw["policy_vs_human"]),
        ai_top_action=raw.get("ai_top_action"),
        ai_top_prob=raw.get("ai_top_prob"),
        hero_equity=raw.get("hero_equity"),
    )


@router.post("/compare", response_model=DrillCompareResponse)
async def drill_compare(
    body: DrillCompareRequest,
    session: AsyncSession = Depends(get_db),
) -> DrillCompareResponse:
    hand = await load_parsed_hand_by_id(session, body.hand_id)
    if hand is None:
        raise HTTPException(status_code=404, detail=f"hand_id {body.hand_id} not found")

    try:
        raw = await asyncio.to_thread(
            compare_policies,
            hand,
            body.step_index,
            thinking_ms=body.thinking_ms,
            deep_search=body.deep_search,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return DrillCompareResponse(
        policies=[
            DrillCompareColumn(
                policy_key=str(c["policy_key"]),
                policy_label=str(c["policy_label"]),
                policy_name=str(c["policy_name"]),
                latency_ms=float(c["latency_ms"]),
                actions=[
                    DrillCompareActionRow(label=str(a["label"]), prob=float(a["prob"]))
                    for a in c["actions"]
                ],
            )
            for c in raw["policies"]
        ],
        consensus=str(raw["consensus"]),
        actual_action=str(raw["actual_action"]),
        actual_amount=raw.get("actual_amount"),
        hero_cards=raw.get("hero_cards"),
        board=raw.get("board"),
        street=raw.get("street"),
        position=raw.get("position"),
        pot_bb=raw.get("pot_bb"),
        stack_bb=raw.get("stack_bb"),
        spr=raw.get("spr"),
    )


@router.get("/{hand_id}/steps", response_model=DrillStepsResponse)
async def drill_steps(
    hand_id: int,
    session: AsyncSession = Depends(get_db),
) -> DrillStepsResponse:
    hand = await load_parsed_hand_by_id(session, hand_id)
    if hand is None:
        raise HTTPException(status_code=404, detail=f"hand_id {hand_id} not found")
    indices = await asyncio.to_thread(hero_decision_indices, hand)
    return DrillStepsResponse(hand_id=hand_id, step_indices=indices)
