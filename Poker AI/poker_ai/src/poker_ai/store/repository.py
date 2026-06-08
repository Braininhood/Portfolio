"""Upsert one hand at a time (idempotent re-ingest)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from poker_ai.ingest.hero_viewpoint import ensure_hero_viewpoint
from poker_ai.ingest.records import ParsedHand, hand_uses_antes, total_ante_amount
from poker_ai.store.models import Action, Game, Hand, Player, Result


UpsertOutcome = Literal["new", "updated"]


def _attach_hand_rows(session: AsyncSession, hand: ParsedHand) -> None:
    """Insert game/hand/player/action/result rows (caller owns delete/replace logic)."""
    session.add(
        Game(
            hand_id=hand.hand_id,
            ingest_source=hand.ingest_source,
            external_ref=hand.external_ref or str(hand.hand_id),
            stakes=hand.stakes,
            game_type=hand.game_type,
            num_players=hand.num_players,
            small_blind=hand.small_blind,
            big_blind=hand.big_blind,
            uses_antes=hand_uses_antes(hand),
            total_ante_amount=total_ante_amount(hand),
            ingested_at=datetime.now(UTC),
        )
    )
    for p in hand.players:
        session.add(
            Player(
                hand_id=hand.hand_id,
                player_id=p.player_id,
                position=p.position,
                stack_size=p.stack_size,
                bb_size=p.bb_size,
                is_hero=p.is_hero,
                player_uid=p.player_uid,
                screen_name=p.screen_name,
            )
        )
    session.add(
        Hand(
            hand_id=hand.hand_id,
            hero_position=hand.hero_position,
            hero_cards=hand.hero_cards,
            board_cards=hand.board_cards,
            pot_preflop=hand.pot_preflop,
            pot_flop=hand.pot_flop,
            pot_turn=hand.pot_turn,
            pot_river=hand.pot_river,
        )
    )
    for a in hand.actions:
        session.add(
            Action(
                hand_id=hand.hand_id,
                player_id=a.player_id,
                position=a.position,
                street=a.street,
                action_type=a.action_type,
                amount=a.amount,
                is_all_in=a.is_all_in,
                effective_stack=a.effective_stack,
                pot_before=a.pot_before,
                pot_after=a.pot_after,
                bet_to_pot_ratio=a.bet_to_pot_ratio,
            )
        )
    for r in hand.results:
        session.add(
            Result(
                hand_id=hand.hand_id,
                player_id=r.player_id,
                position=r.position,
                cards=r.cards,
                net_result=r.net_result,
                won_pot=r.won_pot,
                showdown=r.showdown,
                final_equity=r.final_equity,
                preflop_equity=r.preflop_equity,
                flop_equity=r.flop_equity,
                turn_equity=r.turn_equity,
                river_equity=r.river_equity,
            )
        )


async def insert_hand(session: AsyncSession, hand: ParsedHand) -> None:
    """Append one hand — no existence probe (empty DB / append-only bulk load)."""
    hand = ensure_hero_viewpoint(hand)
    _attach_hand_rows(session, hand)


async def upsert_hand(session: AsyncSession, hand: ParsedHand) -> UpsertOutcome:
    """Replace rows for ``hand.hand_id`` and any stale row with the same provenance key."""
    hand = ensure_hero_viewpoint(hand)
    hid = hand.hand_id
    ref = (hand.external_ref or str(hid)).strip()
    src = hand.ingest_source
    res = await session.execute(
        select(Game.hand_id).where(
            or_(
                Game.hand_id == hid,
                and_(Game.ingest_source == src, Game.external_ref == ref),
            )
        )
    )
    existing_ids = {int(x) for x in res.scalars().all()}
    is_new = len(existing_ids) == 0
    if existing_ids:
        to_remove = set(existing_ids)
        to_remove.add(hid)
        for rid in to_remove:
            await session.execute(delete(Action).where(Action.hand_id == rid))
            await session.execute(delete(Result).where(Result.hand_id == rid))
            await session.execute(delete(Player).where(Player.hand_id == rid))
            await session.execute(delete(Hand).where(Hand.hand_id == rid))
            await session.execute(delete(Game).where(Game.hand_id == rid))
        await session.flush()

    _attach_hand_rows(session, hand)
    return "new" if is_new else "updated"
