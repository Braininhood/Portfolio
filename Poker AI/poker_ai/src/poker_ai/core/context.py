"""Table context helpers — active player count for policy routing (Phase 7b)."""

from __future__ import annotations

from poker_ai.core.game import GameState


def active_seat_indices(state: GameState) -> tuple[int, ...]:
    """Seats still in the hand (not folded)."""
    return tuple(i for i in range(state.num_seats) if not state.folded[i])


def count_active_players(state: GameState) -> int:
    """Number of players still contesting the pot (router uses this, not ``num_seats``)."""
    return len(active_seat_indices(state))


def is_heads_up_context(state: GameState) -> bool:
    """True when exactly two players remain — use HU brain."""
    return count_active_players(state) == 2


def is_multiway_context(state: GameState) -> bool:
    """True when three or more players remain — use multi-way brain."""
    return count_active_players(state) >= 3
