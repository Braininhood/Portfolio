"""Build human-readable sim hand detail for the dashboard."""

from __future__ import annotations

from typing import Any

from poker_ai.core.cards import card_from_int
from poker_ai.core.game import GameState, Street
from poker_ai.league.sim import HandResult, SimActionStep


def _card_str(c: int) -> str:
    r, s = card_from_int(c)
    return f"{r}{s}"


def _board_str(state: GameState) -> str:
    fb = state.full_board
    if len(fb) >= 5:
        return " ".join(_card_str(c) for c in fb[:5])
    if state.board:
        return " ".join(_card_str(c) for c in state.board)
    return "—"


def _why_won(
    *,
    went_showdown: bool,
    winner_seat: int | None,
    winner_name: str | None,
) -> str:
    if winner_seat is None or winner_name is None:
        return "Hand completed."
    if went_showdown:
        return (
            f"{winner_name} won at showdown — best five-card hand with the board cards shown below."
        )
    return f"{winner_name} won because everyone else folded."


def _format_action(step: SimActionStep, *, bb: int, seat_names: list[str]) -> dict[str, Any]:
    name = seat_names[step.seat] if step.seat < len(seat_names) else f"Seat {step.seat + 1}"
    amount_bb = round(step.amount_chips / bb, 1) if bb > 0 and step.amount_chips else 0.0
    label = step.kind
    if step.amount_chips > 0 and step.kind in ("Call", "Bet", "Raise"):
        label = f"{step.kind} {amount_bb:g} BB"
    return {
        "street": step.street,
        "seat": step.seat,
        "player": name,
        "action": label,
        "amount_bb": amount_bb,
    }


def build_sim_hand_detail(
    state: GameState,
    result: HandResult,
    *,
    seat_names: list[str],
    agent_a: str,
    agent_b: str,
) -> dict[str, Any]:
    bb = max(state.big_blind, 1)
    board = _board_str(state)
    winner = result.winner_seat
    winner_name = (
        seat_names[winner] if winner is not None and winner < len(seat_names) else None
    )

    players: list[dict[str, Any]] = []
    holes = state.seat_holes or [None] * state.num_seats
    for seat in range(state.num_seats):
        hole = holes[seat] if seat < len(holes) else None
        cards: str | None = None
        if hole is not None:
            lo, hi = hole
            cards = f"{_card_str(lo)} {_card_str(hi)}"
        else:
            cards = "—"
        delta_bb = round(result.deltas[seat] / bb, 1) if seat < len(result.deltas) else 0.0
        players.append(
            {
                "seat": seat + 1,
                "name": seat_names[seat],
                "cards": cards,
                "delta_bb": delta_bb,
            }
        )

    actions = [_format_action(s, bb=bb, seat_names=seat_names) for s in result.timeline]

    streets_seen: list[str] = []
    street_board: dict[str, str] = {}
    street_board[Street.PREFLOP.value] = "— (no board yet)"
    if len(state.full_board) >= 3:
        street_board[Street.FLOP.value] = " ".join(_card_str(c) for c in state.full_board[:3])
    if len(state.full_board) >= 4:
        street_board[Street.TURN.value] = " ".join(_card_str(c) for c in state.full_board[:4])
    if len(state.full_board) >= 5:
        street_board[Street.RIVER.value] = board

    for s in result.timeline:
        if s.street not in streets_seen:
            streets_seen.append(s.street)

    return {
        "board": board,
        "why_won": _why_won(
            went_showdown=result.went_showdown,
            winner_seat=winner,
            winner_name=winner_name,
        ),
        "players": players,
        "actions": actions,
        "streets": [
            {"name": st, "board": street_board.get(st, "—")} for st in streets_seen
        ],
    }
