"""Load :class:`~poker_ai.ingest.records.ParsedHand` rows from the ORM store."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer, ParsedResult
from poker_ai.store.models import Game, Hand, Player


@dataclass(frozen=True, slots=True)
class PlayerSummary:
    player_uid: str
    hands: int
    screen_name: str | None


@dataclass(frozen=True, slots=True)
class HandSummary:
    hand_id: int
    stakes: str
    num_players: int
    hero_position: str | None
    hero_cards: str | None
    board_cards: str | None
    num_actions: int


def parsed_hand_from_game(game: Game) -> ParsedHand | None:
    """Reconstruct a parsed hand from a fully-loaded :class:`Game` (relationships populated)."""
    h = game.hand_row
    if h is None:
        return None
    players = tuple(
        ParsedPlayer(
            player_id=p.player_id,
            position=p.position,
            stack_size=p.stack_size,
            bb_size=p.bb_size,
            is_hero=p.is_hero,
            player_uid=p.player_uid,
            screen_name=p.screen_name,
        )
        for p in sorted(game.players, key=lambda x: x.player_id)
    )
    actions = tuple(
        ParsedAction(
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
        for a in sorted(h.actions, key=lambda x: x.id)
    )
    results = tuple(
        ParsedResult(
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
        for r in sorted(h.results, key=lambda x: x.player_id)
    )
    antes: tuple[float, ...] = ()
    if game.uses_antes and game.num_players > 0 and game.total_ante_amount > 0:
        per = float(game.total_ante_amount) / float(game.num_players)
        antes = tuple(per for _ in players)
    return ParsedHand(
        hand_id=game.hand_id,
        stakes=game.stakes,
        game_type=game.game_type,
        num_players=game.num_players,
        small_blind=game.small_blind,
        big_blind=game.big_blind,
        hero_position=h.hero_position,
        hero_cards=h.hero_cards,
        board_cards=h.board_cards,
        pot_preflop=h.pot_preflop,
        pot_flop=h.pot_flop,
        pot_turn=h.pot_turn,
        pot_river=h.pot_river,
        antes=antes,
        players=players,
        actions=actions,
        results=results,
        ingest_source=game.ingest_source,
        external_ref=game.external_ref,
    )


async def list_hand_summaries(
    session: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[HandSummary], int]:
    """Recent ingested hands for the replayer picker."""
    from sqlalchemy import func

    total = int(await session.scalar(select(func.count()).select_from(Game)) or 0)
    stmt = (
        select(Game)
        .options(
            selectinload(Game.hand_row).selectinload(Hand.actions),
        )
        .order_by(Game.hand_id.desc())
        .offset(offset)
        .limit(limit)
    )
    games = (await session.scalars(stmt)).all()
    out: list[HandSummary] = []
    for game in games:
        h = game.hand_row
        if h is None:
            continue
        n_act = len(h.actions) if h.actions else 0
        out.append(
            HandSummary(
                hand_id=game.hand_id,
                stakes=game.stakes,
                num_players=game.num_players,
                hero_position=h.hero_position,
                hero_cards=h.hero_cards,
                board_cards=h.board_cards,
                num_actions=n_act,
            )
        )
    return out, total


async def list_player_summaries(
    session: AsyncSession,
    *,
    limit: int = 100,
) -> list[PlayerSummary]:
    """Distinct players by ``player_uid``, ordered by most hands seen."""
    stmt = (
        select(
            Player.player_uid,
            func.count(Player.hand_id).label("hands"),
            func.max(Player.screen_name).label("screen_name"),
        )
        .group_by(Player.player_uid)
        .order_by(func.count(Player.hand_id).desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        PlayerSummary(
            player_uid=str(uid),
            hands=int(hands),
            screen_name=str(name) if name else None,
        )
        for uid, hands, name in rows
    ]


async def load_hands_for_player(
    session: AsyncSession,
    player_uid: str,
    *,
    max_hands: int = 500,
) -> list[ParsedHand]:
    """Hands where ``player_uid`` appears (for profile / style lookup)."""
    stmt = (
        select(Game.hand_id)
        .join(Player, Player.hand_id == Game.hand_id)
        .where(Player.player_uid == player_uid)
        .order_by(Game.hand_id.desc())
        .limit(max_hands)
    )
    hand_ids = [int(x) for x in (await session.scalars(stmt)).all()]
    out: list[ParsedHand] = []
    for hid in hand_ids:
        hand = await load_parsed_hand_by_id(session, hid)
        if hand is not None:
            out.append(hand)
    return out


async def load_parsed_hand_by_id(session: AsyncSession, hand_id: int) -> ParsedHand | None:
    """Load one hand by primary key ``hand_id``."""
    stmt = (
        select(Game)
        .where(Game.hand_id == hand_id)
        .options(
            selectinload(Game.players),
            selectinload(Game.hand_row).selectinload(Hand.actions),
            selectinload(Game.hand_row).selectinload(Hand.results),
        )
    )
    game = await session.scalar(stmt)
    if game is None:
        return None
    return parsed_hand_from_game(game)


async def count_parsed_hands(session: AsyncSession) -> int:
    """Return total stored hands (for dashboard metadata)."""
    from sqlalchemy import func

    return int(await session.scalar(select(func.count()).select_from(Game)) or 0)


async def count_parsed_hands_since(session: AsyncSession, *, since: datetime | None = None) -> int:
    """Hands matching :func:`iter_parsed_hands_since` filter (for progress estimates)."""
    stmt = select(func.count()).select_from(Game)
    if since is not None:
        stmt = stmt.where(Game.ingested_at >= since)
    return int(await session.scalar(stmt) or 0)


async def iter_parsed_hands_since(
    session: AsyncSession,
    *,
    since: datetime | None = None,
) -> AsyncIterator[ParsedHand]:
    """Yield stored hands ordered by ``hand_id``, optionally filtered by ``ingested_at``."""
    stmt = (
        select(Game)
        .options(
            selectinload(Game.players),
            selectinload(Game.hand_row).selectinload(Hand.actions),
            selectinload(Game.hand_row).selectinload(Hand.results),
        )
        .order_by(Game.hand_id)
    )
    if since is not None:
        stmt = stmt.where(Game.ingested_at >= since)
    stream = await session.scalars(stmt)
    for game in stream:
        ph = parsed_hand_from_game(game)
        if ph is not None:
            yield ph
