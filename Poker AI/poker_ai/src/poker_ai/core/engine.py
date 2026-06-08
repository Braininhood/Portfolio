"""NLH step function, legal actions, and table bootstrapping (Phase 2)."""

from __future__ import annotations

from collections.abc import Sequence

from poker_ai.core.cards import cards_from_space_separated, parse_card
from poker_ai.core.game import EngineAction, EngineActionKind, GameState, Street
from poker_ai.ingest.positions import POSITION_RING, ring_slot_candidates
from poker_ai.ingest.records import ParsedHand, ParsedPlayer


class IllegalActionError(ValueError):
    """Raised when a step would violate NLH rules."""


def money_to_chips(x: float) -> int:
    """Convert currency (two-decimal floats from the store) to integer chips."""
    return round(float(x) * 100.0)


def chips_to_money(x: int) -> float:
    return x / 100.0


def _active_seats(state: GameState) -> list[int]:
    return [i for i in range(state.num_seats) if not state.folded[i]]


def _max_street_commit(state: GameState) -> int:
    act = _active_seats(state)
    if not act:
        return 0
    return max(state.street_commit[i] for i in act)


def _needs_to_add_chips(state: GameState, seat: int) -> int:
    """Extra chips this seat must add to match ``current_max`` (capped by stack)."""
    if state.folded[seat]:
        return 0
    gap = state.current_max - state.street_commit[seat]
    if gap <= 0:
        return 0
    return min(gap, state.stacks[seat])


def _preflop_first_seat(bb_seat: int, n: int) -> int:
    return (bb_seat + 1) % n


def _first_postflop_actor(state: GameState) -> int:
    """Heads-up postflop follows ingested OHH order (BTN / dealer acts first)."""
    if state.num_seats == 2:
        return state.button_seat
    return state.sb_seat


def _next_seat_needing_chips(state: GameState, start_after: int) -> int | None:
    """First clockwise seat strictly after ``start_after`` that must add chips to match max."""
    mx = _max_street_commit(state)
    if mx == 0:
        return None
    for k in range(1, state.num_seats + 1):
        s = (start_after + k) % state.num_seats
        if state.folded[s]:
            continue
        if state.stacks[s] == 0:
            continue
        if state.street_commit[s] < mx:
            return s
    return None


def _everyone_matched_or_all_in(state: GameState) -> bool:
    mx = _max_street_commit(state)
    if mx == 0:
        return False
    for s in _active_seats(state):
        if state.street_commit[s] < mx and state.stacks[s] > 0:
            return False
    return True


def _reveal_board_for_current_street(state: GameState) -> None:
    fb = state.full_board
    if state.street == Street.PREFLOP:
        state.board = []
    elif state.street == Street.FLOP:
        state.board = list(fb[:3])
    elif state.street == Street.TURN:
        state.board = list(fb[:4])
    elif state.street == Street.RIVER:
        state.board = list(fb[:5])
    elif state.street == Street.SHOWDOWN:
        state.board = list(fb[:5])


def _first_live_from(state: GameState, start: int) -> int | None:
    for k in range(state.num_seats):
        s = (start + k) % state.num_seats
        if not state.folded[s] and state.stacks[s] > 0:
            return s
    return None


def _advance_street(state: GameState) -> None:
    if state.street == Street.PREFLOP:
        state.street = Street.FLOP
    elif state.street == Street.FLOP:
        state.street = Street.TURN
    elif state.street == Street.TURN:
        state.street = Street.RIVER
    else:
        return
    for i in range(state.num_seats):
        state.street_commit[i] = 0
    state.current_max = 0
    state.raise_count_street = 0
    state.last_aggressor_seat = None
    state.acted_this_round = [False] * state.num_seats
    _reveal_board_for_current_street(state)
    start = _first_postflop_actor(state)
    state.acting_seat = _first_live_from(state, start)
    state.bb_checked_preflop = False


def _return_uncalled_bet(state: GameState) -> None:
    """Return excess from the largest commitment when shorter stacks matched lower."""
    active = _active_seats(state)
    if len(active) <= 1:
        return
    mx = max(state.street_commit[i] for i in active)
    commits_sorted = sorted({state.street_commit[i] for i in active}, reverse=True)
    second = commits_sorted[1] if len(commits_sorted) >= 2 else commits_sorted[0]
    for s in active:
        extra = state.street_commit[s] - second
        if extra > 0 and state.street_commit[s] == mx:
            state.street_commit[s] -= extra
            state.stacks[s] += extra
            state.pot -= extra


def _award_fold_win(state: GameState) -> None:
    alive = [i for i in range(state.num_seats) if not state.folded[i]]
    if len(alive) != 1:
        return
    w = alive[0]
    state.hand_over = True
    state.winner_seat = w
    state.stacks[w] += state.pot
    state.pot = 0
    state.acting_seat = None


def _close_betting_round(state: GameState) -> None:
    _return_uncalled_bet(state)
    alive = [i for i in range(state.num_seats) if not state.folded[i]]
    if len(alive) <= 1:
        _award_fold_win(state)
        return
    elif state.street == Street.RIVER:
        state.street = Street.SHOWDOWN
        state.acting_seat = None
        _reveal_board_for_current_street(state)
        return
    _advance_street(state)


def _next_checkdown_seat(state: GameState, last_actor: int) -> int | None:
    """Next active seat with chips that has not acted on a checked-through street."""
    for k in range(1, state.num_seats + 1):
        s = (last_actor + k) % state.num_seats
        if state.folded[s]:
            continue
        if state.stacks[s] == 0:
            continue
        if not state.acted_this_round[s]:
            return s
    return None


def _compute_next_acting(state: GameState, last_actor: int) -> None:
    if state.hand_over:
        state.acting_seat = None
        return
    alive = _active_seats(state)
    if len(alive) <= 1:
        _award_fold_win(state)
        return

    nxt = _next_seat_needing_chips(state, last_actor)
    if nxt is not None:
        state.acting_seat = nxt
        return

    if state.current_max > 0 and _everyone_matched_or_all_in(state):
        if (
            state.street == Street.PREFLOP
            and state.raise_count_street == 0
            and not state.bb_checked_preflop
        ):
            state.acting_seat = state.bb_seat
            return
        _close_betting_round(state)
        return

    if state.current_max == 0:
        nxt2 = _next_checkdown_seat(state, last_actor)
        if nxt2 is not None:
            state.acting_seat = nxt2
            return
        _close_betting_round(state)


def ring_player_ids(players: Sequence[ParsedPlayer], n: int) -> list[int]:
    """Map canonical ring labels to ``player_id`` values (``POSITION_RING`` order)."""
    pos_to_pid = {p.position: p.player_id for p in players}
    ring = POSITION_RING[n]
    used: set[int] = set()
    seat_pids: list[int] = []
    missing: list[str] = []
    for lbl in ring:
        pid: int | None = None
        for candidate in ring_slot_candidates(lbl, n):
            if candidate not in pos_to_pid:
                continue
            cand_pid = pos_to_pid[candidate]
            if cand_pid in used:
                continue
            pid = cand_pid
            break
        if pid is None:
            missing.append(lbl)
        else:
            used.add(pid)
            seat_pids.append(pid)
    if missing:
        remaining = [p.player_id for p in players if p.player_id not in used]
        if len(seat_pids) + len(remaining) == n and remaining:
            seat_pids.extend(remaining[: len(missing)])
            missing = []
    if missing:
        msg = f"missing positions for {n}-max ring: {missing!r} (have {list(pos_to_pid)!r})"
        raise ValueError(msg)
    return seat_pids


def pid_to_seat(seat_pid: Sequence[int], pid: int) -> int:
    return list(seat_pid).index(pid)


def _ante_chips_by_pid(hand: ParsedHand) -> dict[int, int]:
    """Map ``player_id`` → ante chips; ``hand.antes`` is parallel to ``hand.players``."""
    out = {p.player_id: 0 for p in hand.players}
    if len(hand.antes) == 0:
        return out
    if len(hand.antes) != len(hand.players):
        msg = f"antes length {len(hand.antes)} must match players ({len(hand.players)})"
        raise ValueError(msg)
    for p, a in zip(hand.players, hand.antes, strict=True):
        out[p.player_id] = money_to_chips(float(a))
    return out


def initial_state_from_parsed_hand(
    hand: ParsedHand,
    *,
    seed: int = 0,
) -> GameState:
    """Build table state after antes (if any) and blinds.

    Ready for the first voluntary preflop action.
    """
    n = hand.num_players
    if not (2 <= n <= 10):
        msg = f"num_players out of range: {n}"
        raise ValueError(msg)
    seat_pid = ring_player_ids(hand.players, n)
    sb_amt = money_to_chips(hand.small_blind)
    bb_amt = money_to_chips(hand.big_blind)
    pid_stack = {p.player_id: money_to_chips(p.stack_size) for p in hand.players}
    stacks = [pid_stack[pid] for pid in seat_pid]

    btn, sb_s, bb_s = 0, 1 % n, 2 % n
    if n == 2:
        sb_s, bb_s = 0, 1

    street_commit = [0] * n
    ante_by_pid = _ante_chips_by_pid(hand)
    ante_ring = [ante_by_pid[pid] for pid in seat_pid]
    pot = 0
    for s in range(n):
        ac = ante_ring[s]
        if ac < 0:
            msg = "negative ante"
            raise ValueError(msg)
        if stacks[s] < ac:
            msg = "stack smaller than ante"
            raise ValueError(msg)
        stacks[s] -= ac
        pot += ac

    if stacks[sb_s] < sb_amt or stacks[bb_s] < bb_amt:
        msg = "stack smaller than blinds"
        raise ValueError(msg)
    stacks[sb_s] -= sb_amt
    stacks[bb_s] -= bb_amt
    street_commit[sb_s] = sb_amt
    street_commit[bb_s] = bb_amt

    pot += sb_amt + bb_amt
    current_max = bb_amt
    full_board = tuple(cards_from_space_separated(hand.board_cards))
    seat_holes: list[tuple[int, int] | None] = [None] * n
    if hand.hero_cards and hand.hero_cards.strip():
        hero_seat = next((i for i, p in enumerate(hand.players) if p.is_hero), 0)
        try:
            toks = hand.hero_cards.strip().split()
            if len(toks) == 2:
                c0, c1 = parse_card(toks[0]), parse_card(toks[1])
                seat_holes[hero_seat] = (c0, c1)
        except ValueError:
            pass

    return GameState(
        num_seats=n,
        stacks=stacks,
        folded=[False] * n,
        street=Street.PREFLOP,
        board=[],
        full_board=full_board,
        pot=pot,
        button_seat=btn,
        sb_seat=sb_s,
        bb_seat=bb_s,
        seat_pid=list(seat_pid),
        street_commit=street_commit,
        current_max=current_max,
        big_blind=bb_amt,
        small_blind=sb_amt,
        acting_seat=_preflop_first_seat(bb_s, n),
        hand_over=False,
        winner_seat=None,
        seed=seed,
        last_aggressor_seat=None,
        bb_checked_preflop=False,
        raise_count_street=0,
        action_log=[],
        acted_this_round=[False] * n,
        seat_holes=seat_holes,
        hand_id=str(hand.hand_id),
    )


def apply_action(state: GameState, action: EngineAction, *, strict_actor: bool = True) -> GameState:
    """Return a new state with ``action`` applied (does not mutate ``state``)."""
    s = state.clone()
    if s.hand_over:
        msg = "hand is already over"
        raise IllegalActionError(msg)
    if strict_actor and s.acting_seat is not None and action.seat != s.acting_seat:
        msg = f"wrong actor: expected seat {s.acting_seat}, got {action.seat}"
        raise IllegalActionError(msg)

    seat = action.seat
    if s.folded[seat]:
        msg = "seat has already folded"
        raise IllegalActionError(msg)

    last_actor = seat
    s.acted_this_round[seat] = True

    if action.kind == EngineActionKind.FOLD:
        if action.amount_chips != 0:
            msg = "fold must have zero amount"
            raise IllegalActionError(msg)
        s.folded[seat] = True
    elif action.kind == EngineActionKind.CHECK:
        if action.amount_chips != 0:
            msg = "check must have zero amount"
            raise IllegalActionError(msg)
        if _needs_to_add_chips(s, seat) > 0:
            msg = "illegal check facing a bet"
            raise IllegalActionError(msg)
        if s.street == Street.PREFLOP and seat == s.bb_seat and s.raise_count_street == 0:
            s.bb_checked_preflop = True
    elif action.kind == EngineActionKind.CALL:
        add = action.amount_chips
        need = _needs_to_add_chips(s, seat)
        if add != need:
            msg = f"call amount mismatch: need {need}, got {add}"
            raise IllegalActionError(msg)
        s.stacks[seat] -= add
        s.pot += add
        s.street_commit[seat] += add
        if s.street == Street.PREFLOP and seat == s.bb_seat and s.raise_count_street == 0:
            s.bb_checked_preflop = True
    elif action.kind == EngineActionKind.BET:
        if s.current_max > 0:
            msg = "bet illegal when a bet already exists on this street"
            raise IllegalActionError(msg)
        add = action.amount_chips
        if add <= 0 or add > s.stacks[seat]:
            msg = "illegal bet size"
            raise IllegalActionError(msg)
        s.stacks[seat] -= add
        s.pot += add
        s.street_commit[seat] += add
        s.current_max = s.street_commit[seat]
        s.raise_count_street += 1
        s.last_aggressor_seat = seat
    elif action.kind == EngineActionKind.RAISE:
        target = action.amount_chips
        cur = s.street_commit[seat]
        if target <= cur:
            msg = "raise-to must exceed current street commitment"
            raise IllegalActionError(msg)
        add = target - cur
        if add > s.stacks[seat]:
            msg = "raise exceeds stack"
            raise IllegalActionError(msg)
        s.stacks[seat] -= add
        s.pot += add
        s.street_commit[seat] = target
        if target > s.current_max:
            s.current_max = target
        s.raise_count_street += 1
        s.last_aggressor_seat = seat
    else:  # pragma: no cover — EngineActionKind is exhaustive
        msg = f"unknown action {action.kind!r}"
        raise IllegalActionError(msg)

    s.action_log.append(action)
    _compute_next_acting(s, last_actor)
    return s


def step(state: GameState, action: EngineAction) -> GameState:
    """``(state, action) -> state'`` with actor enforcement."""
    return apply_action(state, action, strict_actor=True)


def legal_actions(state: GameState) -> tuple[EngineAction, ...]:
    """Enumerate legal actions for ``state.acting_seat`` (empty if none)."""
    if state.hand_over or state.acting_seat is None:
        return ()
    seat = state.acting_seat
    if state.folded[seat]:
        return ()

    out: list[EngineAction] = [EngineAction(seat, EngineActionKind.FOLD, 0)]
    need = _needs_to_add_chips(state, seat)
    if need > 0:
        out.append(EngineAction(seat, EngineActionKind.CALL, need))
    else:
        out.append(EngineAction(seat, EngineActionKind.CHECK, 0))

    if state.stacks[seat] > 0:
        if state.current_max == 0:
            for frac in (0.5, 1.0):
                bet = min(state.stacks[seat], max(1, int(state.pot * frac)))
                out.append(EngineAction(seat, EngineActionKind.BET, bet))
        else:
            min_raise = state.big_blind
            target = min(
                state.street_commit[seat] + state.stacks[seat],
                state.current_max + min_raise,
            )
            if target > state.street_commit[seat]:
                out.append(EngineAction(seat, EngineActionKind.RAISE, target))
            allin_target = state.street_commit[seat] + state.stacks[seat]
            if allin_target > state.current_max and allin_target != target:
                out.append(EngineAction(seat, EngineActionKind.RAISE, allin_target))

    uniq: dict[tuple[int, EngineActionKind, int], EngineAction] = {}
    for a in out:
        uniq[(a.seat, a.kind, a.amount_chips)] = a
    return tuple(uniq.values())
