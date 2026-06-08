"""NLH self-play simulator — HU and 3–10 seats (Phase 9).



Policies route HU vs multi-way on every decision via ``count_active_players``

(Phase 7b ``RouterPolicy``), so a single 6-max hand can use the multi-way brain

preflop and switch to HU postflop after folds.

"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from poker_ai.core.context import count_active_players, is_heads_up_context, is_multiway_context
from poker_ai.core.engine import apply_action, legal_actions, money_to_chips
from poker_ai.core.game import EngineAction, GameState, Street
from poker_ai.core.profiles import PlayerProfile
from poker_ai.core.showdown import resolve_showdown as _resolve_showdown
from poker_ai.policy.base import ActionDist, Policy


@dataclass(frozen=True, slots=True)
class SimActionStep:
    """One betting line for live-sim / dashboard replay."""

    street: str
    seat: int
    kind: str
    amount_chips: int


@dataclass(frozen=True, slots=True)
class HandResult:
    """Per-seat net chips vs that seat's stack at deal (zero-sum; positive = won)."""

    deltas: tuple[int, ...]

    went_showdown: bool

    winner_seat: int | None

    hands_played: int = 1

    starting_stacks: tuple[int, ...] = ()

    num_seats: int = 2

    hu_decisions: int = 0

    multiway_decisions: int = 0

    brain_switches: int = 0

    max_active_seen: int = 2

    timeline: tuple[SimActionStep, ...] = ()


def chip_total(state: GameState) -> int:
    """Chips in play (stacks + pot)."""

    return sum(state.stacks) + state.pot


def assert_hand_conservation(
    state: GameState,
    start_total: int,
    deltas: tuple[int, ...],
) -> None:
    """Zero-sum check: constant chip mass and ``sum(deltas) == 0``."""

    end_total = chip_total(state)

    if end_total != start_total:
        msg = f"chip mass changed: start={start_total} end={end_total}"

        raise ValueError(msg)

    if state.pot != 0:
        msg = f"pot not cleared after finalize: pot={state.pot}"

        raise ValueError(msg)

    if sum(deltas) != 0:
        msg = f"non-zero-sum deltas: {deltas}"

        raise ValueError(msg)


def _fresh_deck(rng: random.Random) -> list[int]:

    deck = list(range(52))

    rng.shuffle(deck)

    return deck


def _preflop_first_seat(bb_seat: int, n: int) -> int:

    return (bb_seat + 1) % n


def _brain_label(state: GameState) -> str:

    if is_heads_up_context(state):
        return "hu"

    if is_multiway_context(state):
        return "multiway"

    return "idle"


def _policy_brain(policy: Policy) -> str | None:

    last = getattr(policy, "_last_brain", None)

    if isinstance(last, str) and last:
        return last

    return None


def new_table_hand(
    *,
    num_seats: int,
    seed: int,
    stack_bb: float = 100.0,
    sb_bb: float = 0.5,
    bb_bb: float = 1.0,
    ante_bb: float = 0.0,
) -> GameState:
    """Deal a fresh ring hand (2–10 seats): antes, blinds posted, preflop first to act."""

    if not (2 <= num_seats <= 10):
        msg = f"num_seats out of range: {num_seats}"

        raise ValueError(msg)

    rng = random.Random(seed)

    deck = _fresh_deck(rng)

    holes: list[tuple[int, int] | None] = [(deck.pop(), deck.pop()) for _ in range(num_seats)]

    board = (deck.pop(), deck.pop(), deck.pop(), deck.pop(), deck.pop())

    bb = money_to_chips(bb_bb)

    sb = money_to_chips(sb_bb)

    ante = money_to_chips(ante_bb)

    stack = money_to_chips(stack_bb)

    n = num_seats

    stacks = [stack] * n

    street_commit = [0] * n

    pot = 0

    if ante > 0:
        for s in range(n):
            post = min(ante, stacks[s])
            stacks[s] -= post
            pot += post

    if n == 2:
        btn, sb_s, bb_s = 0, 0, 1

        stacks[sb_s] -= sb

        stacks[bb_s] -= bb

        street_commit[sb_s] = sb

        street_commit[bb_s] = bb

    else:
        btn, sb_s, bb_s = 0, 1 % n, 2 % n

        stacks[sb_s] -= sb

        stacks[bb_s] -= bb

        street_commit[sb_s] = sb

        street_commit[bb_s] = bb

    pot += sum(street_commit)

    return GameState(
        num_seats=n,
        stacks=stacks,
        folded=[False] * n,
        street=Street.PREFLOP,
        board=[],
        full_board=board,
        pot=pot,
        button_seat=btn,
        sb_seat=sb_s,
        bb_seat=bb_s,
        seat_pid=list(range(1, n + 1)),
        street_commit=street_commit,
        current_max=bb,
        big_blind=bb,
        small_blind=sb,
        acting_seat=_preflop_first_seat(bb_s, n),
        hand_over=False,
        winner_seat=None,
        seed=seed,
        last_aggressor_seat=None,
        bb_checked_preflop=False,
        raise_count_street=0,
        action_log=[],
        acted_this_round=[False] * n,
        seat_holes=holes,
        hand_id=str(seed),
    )


def new_hu_hand(
    *,
    seed: int,
    stack_bb: float = 100.0,
    sb_bb: float = 0.5,
    bb_bb: float = 1.0,
) -> GameState:
    """Deal a new HU hand (alias for ``new_table_hand(num_seats=2, ...)``)."""

    return new_table_hand(
        num_seats=2,
        seed=seed,
        stack_bb=stack_bb,
        sb_bb=sb_bb,
        bb_bb=bb_bb,
    )


def finalize_hand(state: GameState, *, start_totals: list[int] | None = None) -> bool:
    """Award any remaining pot; return whether showdown was used."""

    if state.hand_over:
        if state.pot > 0 and state.winner_seat is not None:
            w = state.winner_seat

            state.stacks[w] += state.pot

            state.pot = 0

        return state.street == Street.SHOWDOWN

    alive = [i for i in range(state.num_seats) if not state.folded[i]]

    if len(alive) == 1:
        w = alive[0]

        state.stacks[w] += state.pot

        state.pot = 0

        state.hand_over = True

        state.winner_seat = w

        state.acting_seat = None

        return False

    if state.pot > 0:
        _resolve_showdown(state, start_totals=start_totals)

        return True

    return False


def _pick_action(
    dist: ActionDist, legal: tuple[EngineAction, ...], rng: random.Random
) -> EngineAction:

    if not legal:
        msg = "no legal actions"

        raise RuntimeError(msg)

    keys = [(a.kind.value, a.amount_chips, a.seat) for a in legal]

    probs = list(dist.probs)

    if len(probs) != len(legal):
        probs = [1.0 / len(legal)] * len(legal)

    s = sum(probs)

    if s <= 0:
        probs = [1.0 / len(legal)] * len(legal)

    else:
        probs = [p / s for p in probs]

    idx = rng.choices(range(len(legal)), weights=probs, k=1)[0]

    for a in legal:
        if (a.kind.value, a.amount_chips, a.seat) == keys[idx]:
            return a

    return legal[idx]


def play_hand(
    state: GameState,
    policies: Sequence[Policy],
    profiles: Sequence[PlayerProfile],
    rng: random.Random,
    *,
    max_actions: int = 256,
    opponent_styles_by_seat: Sequence[dict[str, np.ndarray] | None] | None = None,
    record_timeline: bool = False,
) -> HandResult:
    """Play one hand; ``policies[seat]`` acts for that seat."""

    n = state.num_seats

    if len(policies) != n or len(profiles) != n:
        msg = f"expected {n} policies/profiles, got {len(policies)}/{len(profiles)}"

        raise ValueError(msg)

    start_total = chip_total(state)

    starting_stacks = tuple(state.stacks[s] + state.street_commit[s] for s in range(n))

    went_showdown = False

    actions = 0

    hu_decisions = 0

    multiway_decisions = 0

    brain_switches = 0

    max_active_seen = count_active_players(state)

    last_brain: str | None = None

    timeline_steps: list[SimActionStep] = []

    while not state.hand_over and actions < max_actions:
        if state.street == Street.SHOWDOWN:
            _resolve_showdown(state, start_totals=list(starting_stacks))

            went_showdown = True

            break

        seat = state.acting_seat

        if seat is None:
            break

        legal = legal_actions(state)

        if not legal:
            break

        ctx_brain = _brain_label(state)

        max_active_seen = max(max_active_seen, count_active_players(state))

        if ctx_brain == "hu":
            hu_decisions += 1

        elif ctx_brain == "multiway":
            multiway_decisions += 1

        if last_brain is not None and ctx_brain != "idle" and last_brain != ctx_brain:
            brain_switches += 1

        if ctx_brain != "idle":
            last_brain = ctx_brain

        opp_styles = opponent_styles_by_seat[seat] if opponent_styles_by_seat is not None else None

        dist = policies[seat].propose(
            state,
            profiles[seat],
            opponent_styles=opp_styles,
        )

        routed = _policy_brain(policies[seat])

        if routed and routed != ctx_brain and ctx_brain != "idle":
            brain_switches += 1

        action = _pick_action(dist, legal, rng)

        if record_timeline:
            timeline_steps.append(
                SimActionStep(
                    street=state.street.value,
                    seat=action.seat,
                    kind=action.kind.value,
                    amount_chips=action.amount_chips,
                )
            )

        state = apply_action(state, action)

        actions += 1

        if state.street == Street.SHOWDOWN and not state.hand_over:
            _resolve_showdown(state, start_totals=list(starting_stacks))

            went_showdown = True

    if finalize_hand(state, start_totals=list(starting_stacks)):
        went_showdown = True

    deltas = tuple(state.stacks[s] - starting_stacks[s] for s in range(n))

    assert_hand_conservation(state, start_total, deltas)

    return HandResult(
        deltas=deltas,
        went_showdown=went_showdown,
        winner_seat=state.winner_seat,
        starting_stacks=starting_stacks,
        num_seats=n,
        hu_decisions=hu_decisions,
        multiway_decisions=multiway_decisions,
        brain_switches=brain_switches,
        max_active_seen=max_active_seen,
        timeline=tuple(timeline_steps),
    )
