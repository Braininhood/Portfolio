"""Per-hand chance + decision event trace for AIVAT."""

from __future__ import annotations

from dataclasses import dataclass

from poker_ai.core.engine import money_to_chips
from poker_ai.ingest.records import ParsedAction, ParsedHand


@dataclass(frozen=True, slots=True)
class TraceEvent:
    kind: str  # "chance" | "decision"
    street: str
    player_id: int | None
    pot_after: float


def trace_hand_events(hand: ParsedHand) -> list[TraceEvent]:
    """Build a lightweight event list from stored actions."""
    events: list[TraceEvent] = []
    prev_street = "Preflop"
    seen_streets: set[str] = {prev_street}
    for pa in hand.actions:
        if pa.street not in seen_streets and pa.street in ("Flop", "Turn", "River"):
            events.append(
                TraceEvent(
                    kind="chance",
                    street=pa.street,
                    player_id=None,
                    pot_after=pa.pot_before,
                )
            )
            seen_streets.add(pa.street)
        events.append(
            TraceEvent(
                kind="decision",
                street=pa.street,
                player_id=pa.player_id,
                pot_after=pa.pot_after,
            )
        )
    return events


def pot_at_showdown(hand: ParsedHand) -> int:
    """Best-effort pot size in chips for showdown AIVAT."""
    pot = hand.pot_river or hand.pot_turn or hand.pot_flop or hand.pot_preflop
    return max(1, money_to_chips(float(pot)))
