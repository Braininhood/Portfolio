"""Hand list for the replayer."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_db
from schemas import HandListItem, HandListResponse

from poker_ai.store.loader import count_parsed_hands, list_hand_summaries

router = APIRouter(prefix="/hands", tags=["hands"])


@router.get("", response_model=HandListResponse)
async def list_hands(
    session: AsyncSession = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=200)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> HandListResponse:
    total = await count_parsed_hands(session)
    rows, _ = await list_hand_summaries(session, limit=limit, offset=offset)
    if total == 0:
        return HandListResponse(
            total=0,
            hands=[],
            hint=(
                "No hands in your library yet. Open Import in the menu to upload files or "
                "choose a folder on this computer."
            ),
        )
    return HandListResponse(
        total=total,
        hands=[
            HandListItem(
                hand_id=r.hand_id,
                stakes=r.stakes,
                num_players=r.num_players,
                hero_position=r.hero_position,
                hero_cards=r.hero_cards,
                board_preview=r.board_cards,
                num_actions=r.num_actions,
                label=_hand_label(r),
            )
            for r in rows
        ],
        hint=None,
    )


def _hand_label(r: object) -> str:
    from poker_ai.store.loader import HandSummary

    if not isinstance(r, HandSummary):
        return ""
    cards = r.hero_cards or "?"
    board = r.board_cards or "preflop only"
    pos = r.hero_position or "?"
    return f"#{r.hand_id} · {pos} · {cards} · board {board} · {r.num_actions} actions"
