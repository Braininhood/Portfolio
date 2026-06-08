"""Backfill ``results.*_equity`` columns from known hole cards (Phase 4 enrich)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poker_ai.core.cards import cards_from_space_separated
from poker_ai.equity.multiway import hero_equity_vs_n_uniform
from poker_ai.ingest.records import ParsedHand, ParsedResult
from poker_ai.store.loader import iter_parsed_hands_since, load_parsed_hand_by_id
from poker_ai.store.models import Result
from poker_ai.store.sqlite_retry import with_sqlite_retry


ProgressFn = Callable[[dict[str, object]], None]


@dataclass(frozen=True, slots=True)
class SeatEquitySnapshot:
    preflop_equity: float | None
    flop_equity: float | None
    turn_equity: float | None
    river_equity: float | None
    final_equity: float | None


@dataclass(frozen=True, slots=True)
class BackfillStats:
    hands_scanned: int
    hands_updated: int
    seats_enriched: int
    skipped_no_cards: int


def _board_at_street(board_cards: tuple[int, ...], street: str) -> tuple[int, ...]:
    if street == "Preflop":
        return ()
    if street == "Flop":
        return board_cards[:3]
    if street == "Turn":
        return board_cards[:4]
    return board_cards[:5]


def _hole_for_player(hand: ParsedHand, player_id: int) -> tuple[int, int] | None:
    if hand.hero_cards and any(p.player_id == player_id and p.is_hero for p in hand.players):
        try:
            cs = cards_from_space_separated(hand.hero_cards)
            if len(cs) == 2:
                return int(cs[0]), int(cs[1])
        except ValueError:
            pass
    for r in hand.results:
        if r.player_id != player_id or not r.cards.strip():
            continue
        try:
            cs = cards_from_space_separated(r.cards)
            if len(cs) == 2:
                return int(cs[0]), int(cs[1])
        except ValueError:
            continue
    return None


def compute_seat_equities(
    hand: ParsedHand,
    *,
    mc_samples: int = 6000,
) -> dict[int, SeatEquitySnapshot]:
    """Hero-style MC equity vs ``n_players - 1`` uniform opponents at each street."""
    n_players = max(hand.num_players, len(hand.players))
    if n_players < 2:
        return {}
    n_opp = n_players - 1
    board_full: tuple[int, ...] = ()
    if hand.board_cards:
        try:
            board_full = tuple(int(c) for c in cards_from_space_separated(hand.board_cards))
        except ValueError:
            board_full = ()

    out: dict[int, SeatEquitySnapshot] = {}
    for pid in {p.player_id for p in hand.players}:
        hole = _hole_for_player(hand, pid)
        if hole is None:
            continue
        hole_cards: tuple[int, int] = hole
        seed = int(hand.hand_id) * 997 + int(pid)

        def _eq(street: str) -> float:
            b = _board_at_street(board_full, street)
            return float(
                hero_equity_vs_n_uniform(
                    hole_cards,
                    b,
                    n_opp,
                    n_samples=mc_samples,
                    seed=seed + len(b),
                )
            )

        out[pid] = SeatEquitySnapshot(
            preflop_equity=_eq("Preflop"),
            flop_equity=_eq("Flop") if len(board_full) >= 3 else None,
            turn_equity=_eq("Turn") if len(board_full) >= 4 else None,
            river_equity=_eq("River") if len(board_full) >= 5 else None,
            final_equity=_eq("River") if len(board_full) >= 5 else _eq("Preflop"),
        )
    return out


def enrich_hand_results(hand: ParsedHand, *, mc_samples: int = 6000) -> ParsedHand:
    """Return a copy of ``hand`` with ``ParsedResult.*_equity`` filled where possible."""
    eq_map = compute_seat_equities(hand, mc_samples=mc_samples)
    if not eq_map:
        return hand
    new_results: list[ParsedResult] = []
    for r in hand.results:
        snap = eq_map.get(r.player_id)
        if snap is None:
            new_results.append(r)
            continue
        new_results.append(
            ParsedResult(
                player_id=r.player_id,
                position=r.position,
                cards=r.cards,
                net_result=r.net_result,
                won_pot=r.won_pot,
                showdown=r.showdown,
                final_equity=snap.final_equity,
                preflop_equity=snap.preflop_equity,
                flop_equity=snap.flop_equity,
                turn_equity=snap.turn_equity,
                river_equity=snap.river_equity,
            )
        )
    seen = {r.player_id for r in hand.results}
    for pid, snap in eq_map.items():
        if pid in seen:
            continue
        pos = next((p.position for p in hand.players if p.player_id == pid), "?")
        new_results.append(
            ParsedResult(
                player_id=pid,
                position=pos,
                cards="",
                net_result=0.0,
                won_pot=0.0,
                showdown=False,
                final_equity=snap.final_equity,
                preflop_equity=snap.preflop_equity,
                flop_equity=snap.flop_equity,
                turn_equity=snap.turn_equity,
                river_equity=snap.river_equity,
            )
        )
    return ParsedHand(
        hand_id=hand.hand_id,
        stakes=hand.stakes,
        game_type=hand.game_type,
        num_players=hand.num_players,
        small_blind=hand.small_blind,
        big_blind=hand.big_blind,
        hero_position=hand.hero_position,
        hero_cards=hand.hero_cards,
        board_cards=hand.board_cards,
        pot_preflop=hand.pot_preflop,
        pot_flop=hand.pot_flop,
        pot_turn=hand.pot_turn,
        pot_river=hand.pot_river,
        antes=hand.antes,
        players=hand.players,
        actions=hand.actions,
        results=tuple(new_results),
        ingest_source=hand.ingest_source,
        external_ref=hand.external_ref,
    )


def hero_street_equity_from_hand(hand: ParsedHand, *, street: str) -> float | None:
    """Read backfilled hero equity for a street label (Replayer / Drill)."""
    hero_pid = next((p.player_id for p in hand.players if p.is_hero), None)
    if hero_pid is None:
        return None
    r = next((x for x in hand.results if x.player_id == hero_pid), None)
    if r is None:
        return None
    key = street.strip().lower()
    if key == "preflop":
        return r.preflop_equity
    if key == "flop":
        return r.flop_equity
    if key == "turn":
        return r.turn_equity
    if key in ("river", "showdown"):
        return r.river_equity or r.final_equity
    return r.final_equity


async def _result_needs_backfill(session: AsyncSession, hand_id: int) -> bool:
    stmt = select(Result.preflop_equity).where(Result.hand_id == hand_id).limit(1)
    val = await session.scalar(stmt)
    return val is None


async def _persist_equities(session: AsyncSession, hand: ParsedHand) -> int:
    enriched = enrich_hand_results(hand)
    updated = 0
    for r in enriched.results:
        if r.preflop_equity is None and r.final_equity is None:
            continue
        pid = r.player_id
        values = {
            "preflop_equity": r.preflop_equity,
            "flop_equity": r.flop_equity,
            "turn_equity": r.turn_equity,
            "river_equity": r.river_equity,
            "final_equity": r.final_equity,
        }

        async def _update_row(
            *,
            player_id: int = pid,
            vals: dict[str, float | None] = values,
        ) -> None:
            await session.execute(
                update(Result)
                .where(Result.hand_id == hand.hand_id, Result.player_id == player_id)
                .values(**vals)
            )

        await with_sqlite_retry(_update_row)
        updated += 1
    return updated


async def backfill_equities_async(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    since: datetime | None = None,
    limit: int | None = None,
    skip_existing: bool = True,
    mc_samples: int = 6000,
    progress: ProgressFn | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> BackfillStats:
    """Scan stored hands and write MC equities into ``results`` rows."""
    scanned = 0
    updated_hands = 0
    seats = 0
    skipped = 0
    pending_ids: list[int] = []

    async with session_factory() as session:
        async for hand in iter_parsed_hands_since(session, since=since):
            if cancel_check and cancel_check():
                break
            if limit is not None and scanned >= limit:
                break
            scanned += 1
            if skip_existing and not await _result_needs_backfill(session, hand.hand_id):
                continue
            if not hand.hero_cards and not any(r.cards.strip() for r in hand.results):
                skipped += 1
                continue
            pending_ids.append(int(hand.hand_id))

    total = len(pending_ids)
    for idx, hand_id in enumerate(pending_ids, start=1):
        if cancel_check and cancel_check():
            break

        async def _write_one() -> int:
            async with session_factory() as write_session:
                hand = await load_parsed_hand_by_id(write_session, hand_id)
                if hand is None:
                    return 0
                n = await _persist_equities(write_session, hand)
                if n > 0:
                    await write_session.commit()
                return n

        n = await with_sqlite_retry(_write_one)
        if n > 0:
            updated_hands += 1
            seats += n
        if progress and (idx % 25 == 0 or idx == total):
            progress(
                {
                    "pct": min(99, int(100 * idx / max(1, total))),
                    "msg": f"Equity backfill — {updated_hands} hands, {seats} seats",
                    "detail": {"scanned": scanned, "updated": updated_hands, "pending": total},
                }
            )

    if progress:
        progress({"pct": 100, "msg": f"Equity backfill complete — {updated_hands} hands"})

    return BackfillStats(
        hands_scanned=scanned,
        hands_updated=updated_hands,
        seats_enriched=seats,
        skipped_no_cards=skipped,
    )


def backfill_equities_sync(
    session_factory: async_sessionmaker[AsyncSession],
    **kwargs: object,
) -> BackfillStats:
    import asyncio

    return asyncio.run(backfill_equities_async(session_factory, **kwargs))  # type: ignore[arg-type]
