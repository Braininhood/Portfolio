"""Showdown resolution with side-pot support."""

from __future__ import annotations

from collections import defaultdict

from poker_ai.core.evaluator import hand_rank_value_int
from poker_ai.core.game import GameState, Street


def seat_contributions(state: GameState, start_totals: list[int]) -> list[int]:
    """Chips each seat put into the pot this hand (including folded seats)."""
    n = state.num_seats
    out: list[int] = []
    for seat in range(n):
        end = state.stacks[seat] + state.street_commit[seat]
        out.append(max(0, start_totals[seat] - end))
    return out


def _hand_rank(state: GameState, seat: int, board: list[int]) -> int:
    holes = state.seat_holes
    if holes is None:
        return 10**9
    hole = holes[seat]
    if hole is None or len(board) < 5:
        return 10**9
    lo, hi = hole
    return hand_rank_value_int(lo, hi, board[0], board[1], board[2], board[3], board[4])


def award_showdown_pots(
    state: GameState,
    *,
    start_totals: list[int],
) -> dict[int, int]:
    """Award ``state.pot`` using side-pot layers; returns chips won per seat."""
    n = state.num_seats
    contributions = seat_contributions(state, start_totals)
    pot_remaining = state.pot
    thresholds = sorted({c for c in contributions if c > 0})
    awards: dict[int, int] = defaultdict(int)
    prev = 0

    for threshold in thresholds:
        layer = threshold - prev
        if layer <= 0:
            continue
        contributors = [s for s in range(n) if contributions[s] >= threshold]
        pot_layer = layer * len(contributors)
        if pot_layer <= 0:
            prev = threshold
            continue
        eligible = [s for s in contributors if not state.folded[s]]
        if not eligible:
            prev = threshold
            continue

        board = list(state.full_board)
        ranks = {s: _hand_rank(state, s, board) for s in eligible}
        best_rank = min(ranks.values())
        winners = sorted(s for s, r in ranks.items() if r == best_rank)
        share, remainder = divmod(pot_layer, len(winners))
        for i, seat in enumerate(winners):
            awards[seat] += share + (1 if i < remainder else 0)
        pot_remaining -= pot_layer
        prev = threshold

    if pot_remaining > 0:
        alive = [s for s in range(n) if not state.folded[s]]
        if len(alive) == 1:
            awards[alive[0]] += pot_remaining
        elif alive:
            board = list(state.full_board)
            ranks = {s: _hand_rank(state, s, board) for s in alive}
            best_rank = min(ranks.values())
            winners = sorted(s for s, r in ranks.items() if r == best_rank)
            share, remainder = divmod(pot_remaining, len(winners))
            for i, seat in enumerate(winners):
                awards[seat] += share + (1 if i < remainder else 0)

    for seat, chips in awards.items():
        state.stacks[seat] += chips
    state.pot = 0
    return dict(awards)


def resolve_showdown(
    state: GameState,
    *,
    start_totals: list[int] | None = None,
) -> None:
    """Resolve a showdown — single pot or side pots when ``start_totals`` is given."""
    alive = [i for i in range(state.num_seats) if not state.folded[i]]

    if len(alive) == 1:
        w = alive[0]
        state.stacks[w] += state.pot
        state.pot = 0
        state.hand_over = True
        state.winner_seat = w
        state.acting_seat = None
        return

    if len(alive) < 2:
        return

    board = list(state.full_board)
    holes = state.seat_holes

    if start_totals is not None and len(start_totals) == state.num_seats and state.pot > 0:
        awards = award_showdown_pots(state, start_totals=start_totals)
        if awards:
            best_award = max(awards.values())
            top = [s for s, c in awards.items() if c == best_award]
            state.winner_seat = top[0] if len(top) == 1 else top[0]
        else:
            state.winner_seat = alive[0]
        state.hand_over = True
        state.acting_seat = None
        state.street = Street.SHOWDOWN
        return

    best_seat = alive[0]
    best_rank = 10**9

    for seat in alive:
        if holes is None:
            continue
        hole_cards = holes[seat]
        if hole_cards is None:
            continue
        lo, hi = hole_cards
        rank = hand_rank_value_int(lo, hi, board[0], board[1], board[2], board[3], board[4])
        if rank < best_rank:
            best_rank = rank
            best_seat = seat

    state.stacks[best_seat] += state.pot
    state.pot = 0
    state.hand_over = True
    state.winner_seat = best_seat
    state.acting_seat = None
    state.street = Street.SHOWDOWN
