"""Serialize :class:`~poker_ai.core.game.GameState` for JSON APIs."""

from __future__ import annotations

from typing import Any

from poker_ai.core.cards import card_from_int
from poker_ai.core.game import EngineAction, GameState


def _card_str(c: int) -> str:
    r, s = card_from_int(c)
    return f"{r}{s}"


def state_to_dict(state: GameState) -> dict[str, Any]:
    return {
        "num_seats": state.num_seats,
        "stacks": state.stacks,
        "folded": state.folded,
        "street": state.street.value,
        "board": [_card_str(c) for c in state.board],
        "pot": state.pot,
        "acting_seat": state.acting_seat,
        "hand_over": state.hand_over,
        "big_blind": state.big_blind,
        "small_blind": state.small_blind,
    }


def action_dist_to_probs(
    actions: tuple[tuple[str, int, int], ...],
    probs: tuple[float, ...],
) -> list[dict[str, float | int | str]]:
    out: list[dict[str, float | int | str]] = []
    for (kind, amount, seat), p in zip(actions, probs, strict=True):
        out.append(
            {
                "kind": kind,
                "amount_chips": amount,
                "seat": seat,
                "prob": float(p),
            }
        )
    return out


def engine_action_label(action: EngineAction) -> tuple[str, int, int]:
    return (action.kind.value, action.amount_chips, action.seat)
