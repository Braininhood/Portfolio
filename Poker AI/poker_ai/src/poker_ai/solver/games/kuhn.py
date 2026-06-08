"""Kuhn poker — CFR validation game (OpenSpiel-compatible pass/bet tree)."""

from __future__ import annotations

from dataclasses import dataclass

PASS = 0
BET = 1

CARD_NAMES: tuple[str, ...] = ("J", "Q", "K")


@dataclass(frozen=True, slots=True)
class KuhnState:
    """Immutable Kuhn node."""

    cards: tuple[int, int]
    history: tuple[int, ...]
    pot: int
    p0_invested: int
    p1_invested: int
    acting: int
    terminal: bool
    winner: int | None


class KuhnPoker:
    """Two-player Kuhn poker (ante 1 each, optional bet of 1)."""

    num_players: int = 2
    ante: int = 1
    bet_size: int = 1

    def initial_chance_outcomes(self) -> tuple[tuple[float, KuhnState], ...]:
        deals = ((0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1))
        p = 1.0 / len(deals)
        return tuple(
            (
                p,
                KuhnState(
                    cards=(c0, c1),
                    history=(),
                    pot=2 * self.ante,
                    p0_invested=self.ante,
                    p1_invested=self.ante,
                    acting=0,
                    terminal=False,
                    winner=None,
                ),
            )
            for c0, c1 in deals
        )

    def current_player(self, state: KuhnState) -> int | None:
        if state.terminal:
            return -1
        return state.acting

    def legal_actions(self, state: KuhnState) -> tuple[int, ...]:
        if state.terminal:
            return ()
        h = state.history
        if len(h) == 0:
            return (PASS, BET)
        if len(h) == 1:
            return (PASS, BET)
        if h == (PASS, PASS):
            return ()
        if h == (PASS, BET):
            return (PASS, BET)
        if h in ((BET, PASS), (BET, BET), (PASS, BET, PASS), (PASS, BET, BET)):
            return ()
        return ()

    def next_state(self, state: KuhnState, action: int) -> KuhnState:
        if action not in self.legal_actions(state):
            msg = f"illegal action {action} at {state.history}"
            raise ValueError(msg)
        h = (*state.history, action)
        pot, p0, p1 = state.pot, state.p0_invested, state.p1_invested
        acting = state.acting
        terminal, winner = False, None

        if action == BET:
            if acting == 0:
                pot += self.bet_size
                p0 += self.bet_size
            else:
                pot += self.bet_size
                p1 += self.bet_size

        if h == (PASS, PASS):
            terminal, winner = True, self._showdown(state)
        elif h == (BET, PASS):
            terminal, winner = True, 0
        elif h in ((BET, BET), (PASS, BET, BET)):
            terminal, winner = True, self._showdown(state)
        elif h == (PASS, BET, PASS):
            terminal, winner = True, 1
        elif len(h) == 1:
            acting = 1
        elif h == (PASS, BET):
            acting = 0

        return KuhnState(
            cards=state.cards,
            history=h,
            pot=pot,
            p0_invested=p0,
            p1_invested=p1,
            acting=acting,
            terminal=terminal,
            winner=winner,
        )

    def chance_outcomes(self, state: KuhnState) -> tuple[tuple[float, KuhnState], ...]:
        _ = state
        return ()

    def terminal_utility(self, state: KuhnState, player: int) -> float:
        if not state.terminal or state.winner is None:
            return 0.0
        invested = state.p0_invested if player == 0 else state.p1_invested
        if state.winner == player:
            return float(state.pot - invested)
        return float(-invested)

    def information_set_key(self, state: KuhnState, player: int) -> str:
        card = CARD_NAMES[state.cards[player]]
        hist = ",".join(str(a) for a in state.history)
        return f"p{player}|{card}|{hist}"

    @staticmethod
    def _showdown(state: KuhnState) -> int:
        return 0 if state.cards[0] > state.cards[1] else 1
