"""Replay canonical :class:`~poker_ai.ingest.records.ParsedHand` rows through the engine."""

from __future__ import annotations

from dataclasses import dataclass

from poker_ai.core.engine import (
    IllegalActionError,
    apply_action,
    initial_state_from_parsed_hand,
    money_to_chips,
    pid_to_seat,
    step,
)
from poker_ai.core.game import EngineAction, EngineActionKind, GameState
from poker_ai.ingest.records import ParsedAction, ParsedHand


@dataclass(frozen=True, slots=True)
class ReplayResult:
    final_state: GameState
    pot_trace_ok: bool
    action_sequence_ok: bool


def _kind_from_store(action_type: str) -> EngineActionKind:
    try:
        return EngineActionKind(action_type)
    except ValueError as e:
        msg = f"unsupported action_type {action_type!r}"
        raise ValueError(msg) from e


def parsed_action_to_engine(state: GameState, pa: ParsedAction) -> EngineAction:
    seat = pid_to_seat(state.seat_pid, pa.player_id)
    kind = _kind_from_store(pa.action_type)
    return EngineAction(seat, kind, money_to_chips(pa.amount))


def state_after_actions(hand: ParsedHand, n_actions: int, *, lenient: bool = False) -> GameState:
    """Replay the first ``n_actions`` stored actions (0 = blinds posted, ready to act).

    ``lenient=True`` skips strict actor checks (for AI overlay on imported HH).
    """
    s = initial_state_from_parsed_hand(hand)
    for pa in hand.actions[: max(0, n_actions)]:
        act = parsed_action_to_engine(s, pa)
        if lenient:
            s = apply_action(s, act, strict_actor=False)
        else:
            s = step(s, act)
    return s


def replay_parsed_hand(hand: ParsedHand) -> ReplayResult:
    """Apply stored actions in order.

    Verifies ``pot`` matches ``pot_after`` while the pot remains in play.
    """
    s = initial_state_from_parsed_hand(hand)
    pot_ok = True
    seq_ok = True
    for pa in hand.actions:
        try:
            act = parsed_action_to_engine(s, pa)
            s = step(s, act)
        except IllegalActionError:
            seq_ok = False
            break
        exp = money_to_chips(pa.pot_after)
        if not s.hand_over and abs(s.pot - exp) > 1:
            pot_ok = False
    return ReplayResult(final_state=s, pot_trace_ok=pot_ok, action_sequence_ok=seq_ok)
