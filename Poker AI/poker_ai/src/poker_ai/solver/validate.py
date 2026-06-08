"""Validation helpers (OpenSpiel ground truth for tiny games)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from poker_ai.solver.game import ExtensiveGame

    _State = Any
else:
    _State = object


class OpenSpielKuhnBridge:
    """Wrap OpenSpiel ``kuhn_poker`` as :class:`~poker_ai.solver.game.ExtensiveGame`."""

    num_players: int = 2

    def __init__(self) -> None:
        import pyspiel

        self._game = pyspiel.load_game("kuhn_poker")

    def initial_chance_outcomes(self) -> tuple[tuple[float, object], ...]:
        root = self._game.new_initial_state()
        return ((1.0, root),)

    def current_player(self, state: _State) -> int | None:
        st: Any = state
        if st.is_terminal():
            return -1
        if st.is_chance_node():
            return None
        return st.current_player()

    def legal_actions(self, state: _State) -> tuple[int, ...]:
        st: Any = state
        if st.is_chance_node():
            return tuple(a for a, _ in st.chance_outcomes())
        return tuple(st.legal_actions())

    def next_state(self, state: _State, action: int) -> _State:
        return state.child(action)

    def chance_outcomes(self, state: _State) -> tuple[tuple[float, _State], ...]:
        st: Any = state
        return tuple((float(p), st.child(a)) for a, p in st.chance_outcomes())

    def terminal_utility(self, state: _State, player: int) -> float:
        st: Any = state
        return float(st.returns()[player])

    def information_set_key(self, state: _State, player: int) -> str:
        st: Any = state
        return str(st.information_state_string(player))


def openspiel_exploitability(game: ExtensiveGame, strategy: dict[str, np.ndarray]) -> float:
    """OpenSpiel exploitability (utility units; scale by 1000/BB for mbb/g)."""
    from open_spiel.python import policy as policy_lib
    from open_spiel.python.algorithms import exploitability as os_exp

    if not isinstance(game, OpenSpielKuhnBridge):
        msg = "openspiel_exploitability requires OpenSpielKuhnBridge"
        raise TypeError(msg)

    py_game = game._game

    class _Tabular(policy_lib.Policy):
        def __init__(self) -> None:
            super().__init__(py_game, list(range(py_game.num_distinct_actions())))
            self._strat = strategy

        def action_probabilities(
            self, state: object, player_id: int | None = None
        ) -> dict[int, float]:
            st: Any = state
            if st.is_chance_node():
                return dict(st.chance_outcomes())
            p = st.current_player()
            legal = st.legal_actions()
            key = st.information_state_string(p)
            sigma = self._strat.get(key)
            if sigma is None or len(sigma) != len(legal):
                return {a: 1.0 / len(legal) for a in legal}
            return {legal[i]: float(sigma[i]) for i in range(len(legal))}

    return float(os_exp.exploitability(py_game, _Tabular()))


def openspiel_exploitability_mbb(
    strategy: dict[str, np.ndarray], *, big_blind: float = 1.0
) -> float:
    """Kuhn exploitability in mbb/g via OpenSpiel."""
    bridge = OpenSpielKuhnBridge()
    exp = openspiel_exploitability(bridge, strategy)
    return exp / big_blind * 1000.0
