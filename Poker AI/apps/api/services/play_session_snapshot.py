"""Serialize / deserialize PlaySession + GameState for DB resume (W7 Day 28)."""

from __future__ import annotations

from typing import Any

from poker_ai.core.game import EngineAction, EngineActionKind, GameState, Street


SNAPSHOT_VERSION = 1


def _engine_action_to_dict(action: EngineAction) -> dict[str, Any]:
    return {
        "seat": action.seat,
        "kind": action.kind.value,
        "amount_chips": action.amount_chips,
    }


def _engine_action_from_dict(raw: dict[str, Any]) -> EngineAction:
    return EngineAction(
        seat=int(raw["seat"]),
        kind=EngineActionKind(str(raw["kind"])),
        amount_chips=int(raw.get("amount_chips") or 0),
    )


def game_state_to_dict(state: GameState) -> dict[str, Any]:
    holes = state.seat_holes
    hole_payload: list[list[int] | None] | None = None
    if holes is not None:
        hole_payload = []
        for h in holes:
            if h is None:
                hole_payload.append(None)
            else:
                lo, hi = h
                hole_payload.append([lo, hi])
    return {
        "num_seats": state.num_seats,
        "stacks": list(state.stacks),
        "folded": list(state.folded),
        "street": state.street.value,
        "board": list(state.board),
        "full_board": list(state.full_board),
        "pot": state.pot,
        "button_seat": state.button_seat,
        "sb_seat": state.sb_seat,
        "bb_seat": state.bb_seat,
        "seat_pid": list(state.seat_pid),
        "street_commit": list(state.street_commit),
        "current_max": state.current_max,
        "big_blind": state.big_blind,
        "small_blind": state.small_blind,
        "acting_seat": state.acting_seat,
        "hand_over": state.hand_over,
        "winner_seat": state.winner_seat,
        "seed": state.seed,
        "last_aggressor_seat": state.last_aggressor_seat,
        "bb_checked_preflop": state.bb_checked_preflop,
        "raise_count_street": state.raise_count_street,
        "action_log": [_engine_action_to_dict(a) for a in state.action_log],
        "acted_this_round": list(state.acted_this_round),
        "seat_holes": hole_payload,
        "hand_id": state.hand_id,
    }


def game_state_from_dict(raw: dict[str, Any]) -> GameState:
    holes_raw = raw.get("seat_holes")
    holes: list[tuple[int, int] | None] | None = None
    if holes_raw is not None:
        holes = []
        for h in holes_raw:
            if h is None:
                holes.append(None)
            else:
                holes.append((int(h[0]), int(h[1])))
    return GameState(
        num_seats=int(raw["num_seats"]),
        stacks=[int(x) for x in raw["stacks"]],
        folded=[bool(x) for x in raw["folded"]],
        street=Street(str(raw["street"])),
        board=[int(x) for x in raw.get("board") or []],
        full_board=tuple(int(x) for x in raw.get("full_board") or []),
        pot=int(raw["pot"]),
        button_seat=int(raw["button_seat"]),
        sb_seat=int(raw["sb_seat"]),
        bb_seat=int(raw["bb_seat"]),
        seat_pid=[int(x) for x in raw["seat_pid"]],
        street_commit=[int(x) for x in raw["street_commit"]],
        current_max=int(raw["current_max"]),
        big_blind=int(raw["big_blind"]),
        small_blind=int(raw["small_blind"]),
        acting_seat=raw.get("acting_seat") if raw.get("acting_seat") is None else int(raw["acting_seat"]),
        hand_over=bool(raw["hand_over"]),
        winner_seat=raw.get("winner_seat") if raw.get("winner_seat") is None else int(raw["winner_seat"]),
        seed=int(raw.get("seed") or 0),
        last_aggressor_seat=(
            raw.get("last_aggressor_seat")
            if raw.get("last_aggressor_seat") is None
            else int(raw["last_aggressor_seat"])
        ),
        bb_checked_preflop=bool(raw.get("bb_checked_preflop")),
        raise_count_street=int(raw.get("raise_count_street") or 0),
        action_log=[_engine_action_from_dict(a) for a in raw.get("action_log") or []],
        acted_this_round=[bool(x) for x in raw.get("acted_this_round") or []],
        seat_holes=holes,
        hand_id=raw.get("hand_id"),
    )


def session_snapshot_dict(session: Any) -> dict[str, Any]:
    """Build a JSON-serializable snapshot of live session state."""
    phase = "idle"
    if getattr(session, "_await_next_hand", False):
        phase = "await_next_hand"
    elif session.engine_state is not None and not session.engine_state.hand_over:
        phase = "in_hand"

    rng_state = list(session.rng.getstate())
    # JSON: inner state tuple -> list
    if len(rng_state) >= 2 and isinstance(rng_state[1], tuple):
        rng_state[1] = list(rng_state[1])

    seat_bot_ids = {str(k): v for k, v in session.seat_bot_ids.items()}

    snap: dict[str, Any] = {
        "version": SNAPSHOT_VERSION,
        "phase": phase,
        "hand_no": session.hand_no,
        "button_seat": session.button_seat,
        "stacks": list(session.stacks),
        "seat_bot_ids": seat_bot_ids,
        "hands_played": session.hands_played,
        "net_bb": session.net_bb,
        "vpip_count": session.vpip_count,
        "pfr_count": session.pfr_count,
        "total_decisions": session.total_decisions,
        "rng_state": rng_state,
        "hand_action_log": list(session._hand_action_log),
        "hand_start_totals": list(getattr(session, "_hand_start_totals", []) or []),
        "hero_voluntary_preflop": bool(getattr(session, "_hero_voluntary_preflop", False)),
        "hero_raised_preflop": bool(getattr(session, "_hero_raised_preflop", False)),
        "completed_hand_nos": [int(h["hand_no"]) for h in session.completed_hands],
    }
    if session.engine_state is not None:
        snap["engine"] = game_state_to_dict(session.engine_state)
    return snap


def apply_snapshot_to_session(session: Any, snap: dict[str, Any]) -> None:
    """Restore mutable session fields from a snapshot dict."""
    import random

    session.hand_no = int(snap.get("hand_no") or 0)
    session.button_seat = int(snap.get("button_seat") or 0)
    session.stacks = [int(x) for x in snap.get("stacks") or []]
    session.seat_bot_ids = {int(k): str(v) for k, v in (snap.get("seat_bot_ids") or {}).items()}
    session.hands_played = int(snap.get("hands_played") or 0)
    session.net_bb = float(snap.get("net_bb") or 0.0)
    session.vpip_count = int(snap.get("vpip_count") or 0)
    session.pfr_count = int(snap.get("pfr_count") or 0)
    session.total_decisions = int(snap.get("total_decisions") or 0)
    session._hand_action_log = list(snap.get("hand_action_log") or [])
    session._hand_start_totals = [int(x) for x in snap.get("hand_start_totals") or []]
    session._hero_voluntary_preflop = bool(snap.get("hero_voluntary_preflop"))
    session._hero_raised_preflop = bool(snap.get("hero_raised_preflop"))
    session._await_next_hand = snap.get("phase") == "await_next_hand"
    session._resume_mid_hand = snap.get("phase") == "in_hand"

    rng_state = snap.get("rng_state")
    if rng_state:
        rs = list(rng_state)
        if len(rs) >= 2 and isinstance(rs[1], list):
            rs[1] = tuple(rs[1])
        session.rng = random.Random()
        session.rng.setstate(tuple(rs))

    engine_raw = snap.get("engine")
    session.engine_state = game_state_from_dict(engine_raw) if engine_raw else None

    # Re-bind policies after bot lineup change
    from services.play_session import _policy_roster

    roster = _policy_roster()
    for seat in range(session.config.seats):
        if seat == session.config.user_seat:
            continue
        bot_id = session.seat_bot_ids.get(seat, "random")
        session.policies[seat] = roster.get(bot_id) or roster["random"]
