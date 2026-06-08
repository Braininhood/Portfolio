"""Abstracted preflop game for tabular CFR (Phase 6)."""

from __future__ import annotations

from dataclasses import dataclass

from poker_ai.solver.preflop_equity import EquityMode, PreflopDeal, build_chance_deals
from poker_ai.solver.preflop_showdown import showdown_payoffs

FOLD = 0
CALL = 1
RAISE = 2
ALLIN = 3

POSITIONS_6MAX: tuple[str, ...] = ("UTG", "HJ", "CO", "BTN", "SB", "BB")
MAX_PLAYERS = 10


@dataclass(frozen=True, slots=True)
class PreflopState:
    num_players: int
    buckets: tuple[int, ...]
    combos: tuple[int, ...] | None
    history: tuple[int, ...]
    pot: int
    street_bets: tuple[int, ...]
    current_max: int
    acting_seat: int
    active: tuple[bool, ...]
    pending: tuple[bool, ...]
    raise_count: int
    terminal: bool
    payoffs: tuple[float, ...] | None


def _encode_action(seat: int, action: int) -> int:
    return seat * 4 + action


class PreflopAbstractionGame:
    """Sequential preflop with bucket showdown EV and abstract raise sizes."""

    num_players: int
    big_blind: int
    small_blind: int
    ante: int
    raise_bb: int
    max_raises: int
    chance_samples: int
    equity_mode: EquityMode
    equity_mc_samples: int
    _deals: tuple[PreflopDeal, ...]

    def __init__(
        self,
        *,
        num_players: int = 6,
        big_blind: int = 100,
        small_blind: int = 50,
        ante: int = 0,
        raise_bb: int = 250,
        max_raises: int = 1,
        chance_samples: int = 256,
        seed: int = 0,
        equity_mode: EquityMode = "random",
        equity_mc_samples: int = 2000,
    ) -> None:
        if num_players < 2 or num_players > MAX_PLAYERS:
            msg = f"num_players must be 2..{MAX_PLAYERS}"
            raise ValueError(msg)
        self.num_players = num_players
        self.big_blind = big_blind
        self.small_blind = small_blind
        self.ante = ante
        self.raise_bb = raise_bb
        self.max_raises = max(0, max_raises)
        self.chance_samples = max(1, chance_samples)
        self.equity_mode = equity_mode
        self.equity_mc_samples = max(100, equity_mc_samples)
        self._deals = build_chance_deals(
            num_players=num_players,
            chance_samples=self.chance_samples,
            seed=seed,
            equity_mode=equity_mode,
            mc_samples=self.equity_mc_samples,
        )

    def initial_chance_outcomes(self) -> tuple[tuple[float, PreflopState], ...]:
        p = 1.0 / float(len(self._deals))
        stacks = self._initial_street_bets()
        pot = sum(stacks) + self.ante * self.num_players
        n = self.num_players
        return tuple(
            (
                p,
                PreflopState(
                    num_players=n,
                    buckets=deal.buckets,
                    combos=deal.combos,
                    history=(),
                    pot=pot,
                    street_bets=stacks,
                    current_max=max(stacks),
                    acting_seat=0,
                    active=tuple(True for _ in range(n)),
                    pending=tuple(True for _ in range(n)),
                    raise_count=0,
                    terminal=False,
                    payoffs=None,
                ),
            )
            for deal in self._deals
        )

    def current_player(self, state: object) -> int | None:
        state = _as_preflop(state)
        if state.terminal:
            return -1
        return state.acting_seat

    def legal_actions(self, state: object) -> tuple[int, ...]:
        state = _as_preflop(state)
        if state.terminal:
            return ()
        seat = state.acting_seat
        if not state.active[seat]:
            msg = f"acting seat {seat} is not active"
            raise RuntimeError(msg)
        acts: list[int] = [FOLD, CALL]
        can_raise = (
            state.raise_count < self.max_raises
            and state.street_bets[seat] < self.raise_bb
            and state.street_bets[seat] < self._starting_stack()
        )
        if can_raise:
            acts.append(RAISE)
        if state.street_bets[seat] < self._starting_stack():
            acts.append(ALLIN)
        return tuple(dict.fromkeys(acts))

    def next_state(self, state: object, action: int) -> object:
        state = _as_preflop(state)
        if action not in self.legal_actions(state):
            msg = f"illegal action {action}"
            raise ValueError(msg)
        seat = state.acting_seat
        h = (*state.history, _encode_action(seat, action))
        active = list(state.active)
        pending = list(state.pending)
        bets = list(state.street_bets)
        pot = state.pot
        current_max = state.current_max
        raise_count = state.raise_count

        if action == FOLD:
            active[seat] = False
            pending[seat] = False
        elif action == CALL:
            gap = current_max - bets[seat]
            pot += gap
            bets[seat] = current_max
            pending[seat] = False
        elif action == RAISE:
            add = self.raise_bb - bets[seat]
            pot += add
            bets[seat] = self.raise_bb
            current_max = max(current_max, self.raise_bb)
            raise_count += 1
            pending = [a and i != seat for i, a in enumerate(active)]
        elif action == ALLIN:
            stack = self._starting_stack()
            add = stack - bets[seat]
            pot += add
            bets[seat] = stack
            current_max = max(current_max, stack)
            pending = [a and i != seat for i, a in enumerate(active)]

        live = [i for i, a in enumerate(active) if a]
        if len(live) == 1:
            payoffs = showdown_payoffs(
                num_players=state.num_players,
                active=active,
                bets=bets,
                pot=pot,
                buckets=state.buckets,
                combos=state.combos,
                use_combos=self.equity_mode == "real",
            )
            return self._terminal(
                state, h, pot, bets, current_max, seat, active, pending, raise_count, payoffs
            )

        if _betting_closed(active, pending, bets, current_max):
            payoffs = showdown_payoffs(
                num_players=state.num_players,
                active=active,
                bets=bets,
                pot=pot,
                buckets=state.buckets,
                combos=state.combos,
                use_combos=self.equity_mode == "real",
            )
            return self._terminal(
                state, h, pot, bets, current_max, seat, active, pending, raise_count, payoffs
            )

        next_seat = _next_active_seat(active, seat)
        if next_seat is None:
            payoffs = showdown_payoffs(
                num_players=state.num_players,
                active=active,
                bets=bets,
                pot=pot,
                buckets=state.buckets,
                combos=state.combos,
                use_combos=self.equity_mode == "real",
            )
            return self._terminal(
                state, h, pot, bets, current_max, seat, active, pending, raise_count, payoffs
            )

        return PreflopState(
            num_players=state.num_players,
            buckets=state.buckets,
            combos=state.combos,
            history=h,
            pot=pot,
            street_bets=tuple(bets),
            current_max=current_max,
            acting_seat=next_seat,
            active=tuple(active),
            pending=tuple(pending),
            raise_count=raise_count,
            terminal=False,
            payoffs=None,
        )

    def chance_outcomes(self, state: object) -> tuple[tuple[float, object], ...]:
        _ = state
        return ()

    def terminal_utility(self, state: object, player: int) -> float:
        state = _as_preflop(state)
        if state.payoffs is None:
            return 0.0
        return state.payoffs[player]

    def information_set_key(self, state: object, player: int) -> str:
        state = _as_preflop(state)
        hist = ",".join(str(x) for x in state.history)
        return f"n{state.num_players}|p{player}|b{state.buckets[player]}|h{hist}"

    def _starting_stack(self) -> int:
        return 100 * self.big_blind

    def _initial_street_bets(self) -> tuple[int, ...]:
        bets = [self.ante] * self.num_players
        if self.num_players >= 2:
            bets[-2] += self.small_blind
            bets[-1] += self.big_blind
        return tuple(bets)

    def _terminal(
        self,
        state: PreflopState,
        history: tuple[int, ...],
        pot: int,
        bets: list[int],
        current_max: int,
        seat: int,
        active: list[bool],
        pending: list[bool],
        raise_count: int,
        payoffs: tuple[float, ...],
    ) -> PreflopState:
        return PreflopState(
            num_players=state.num_players,
            buckets=state.buckets,
            combos=state.combos,
            history=history,
            pot=pot,
            street_bets=tuple(bets),
            current_max=current_max,
            acting_seat=seat,
            active=tuple(active),
            pending=tuple(pending),
            raise_count=raise_count,
            terminal=True,
            payoffs=payoffs,
        )


def _as_preflop(state: object) -> PreflopState:
    if not isinstance(state, PreflopState):
        msg = "expected PreflopState"
        raise TypeError(msg)
    return state


def _next_active_seat(active: list[bool], after: int) -> int | None:
    n = len(active)
    for k in range(1, n + 1):
        s = (after + k) % n
        if active[s]:
            return s
    return None


def _betting_closed(
    active: list[bool],
    pending: list[bool],
    bets: list[int],
    current_max: int,
) -> bool:
    """True when every active seat has matched the current max and acted this street."""
    for i, is_active in enumerate(active):
        if not is_active:
            continue
        if pending[i]:
            return False
        if bets[i] < current_max:
            return False
    return True
