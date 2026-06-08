"""Filter parsed hands before persisting — keeps the training store high-signal."""

from __future__ import annotations

from poker_ai.ingest.canonical_id import INGEST_OHH_JSON, INGEST_PHH
from poker_ai.ingest.records import ParsedHand


def parsed_hand_passes_store_gate(hand: ParsedHand, *, require_complete: bool) -> bool:
    """Return True when ``hand`` meets minimum completeness for the SQLite store.

    When ``require_complete`` is False, only obviously broken rows are rejected
    (single-player, zero BB, no actions).
    """
    if hand.num_players < 2:
        return False
    if len(hand.players) != hand.num_players:
        return False
    if hand.big_blind <= 0:
        return False
    if len(hand.actions) < 1:
        return False
    if sorted(p.player_id for p in hand.players) != list(range(1, hand.num_players + 1)):
        return False
    if not require_complete:
        return True
    if hand.ingest_source == INGEST_PHH:
        return len(hand.results) == hand.num_players
    if hand.ingest_source == INGEST_OHH_JSON:
        return len(hand.results) >= 1
    return True
