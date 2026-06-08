"""Stratified sampling of DB hands for replay league (v2)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from poker_ai.ingest.records import ParsedHand
from poker_ai.learn.multiway_dataset import _count_active_before_action, _hero_player_id


@dataclass(frozen=True, slots=True)
class ReplaySample:
    hand: ParsedHand
    format_id: str  # "hu" | "mw"


def classify_hand(hand: ParsedHand) -> str:
    """Return hu or mw based on max active players postflop."""
    max_active = hand.num_players
    for i, _pa in enumerate(hand.actions):
        active = _count_active_before_action(hand, i)
        max_active = max(max_active, active)
    return "mw" if max_active >= 3 else "hu"


def hero_has_decisions(hand: ParsedHand) -> bool:
    hero_pid = _hero_player_id(hand)
    if hero_pid is None:
        return False
    return any(pa.player_id == hero_pid for pa in hand.actions)


async def iter_replay_samples(
    session,
    *,
    limit: int = 500,
    strata: frozenset[str] | None = None,
    since=None,
) -> AsyncIterator[ReplaySample]:
    """Yield stratified hands until ``limit`` reached."""
    from poker_ai.store.loader import iter_parsed_hands_since

    want = strata or frozenset({"hu", "mw"})
    counts = {k: 0 for k in want}
    target_per = max(1, limit // max(1, len(want)))
    total = 0

    async for hand in iter_parsed_hands_since(session, since=since):
        if total >= limit:
            break
        if not hero_has_decisions(hand):
            continue
        fmt = classify_hand(hand)
        if fmt not in want:
            continue
        if counts.get(fmt, 0) >= target_per and total >= limit // 2:
            continue
        counts[fmt] = counts.get(fmt, 0) + 1
        total += 1
        yield ReplaySample(hand=hand, format_id=fmt)
