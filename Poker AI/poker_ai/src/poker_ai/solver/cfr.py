"""Vanilla CFR, CFR+, and external-sampling MCCFR (Phase 6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from poker_ai.solver.game import ExtensiveGame

CFRMode = Literal["vanilla", "cfr_plus", "external"]


@dataclass
class _InfoSetNode:
    regrets: np.ndarray
    strategy_sum: np.ndarray
    num_actions: int


@dataclass
class CFRSolver:
    """Tabular CFR / CFR+ / external-sampling MCCFR."""

    game: ExtensiveGame
    mode: CFRMode = "cfr_plus"
    seed: int = 42
    _nodes: dict[str, _InfoSetNode] = field(default_factory=dict, init=False, repr=False)
    _iter: int = field(default=0, init=False, repr=False)
    _rng: np.random.Generator = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = np.random.default_rng(self.seed)

    @property
    def iterations(self) -> int:
        return self._iter

    def run(self, iterations: int) -> None:
        for _ in range(iterations):
            self._iter += 1
            if self.mode == "external":
                for p in range(self.game.num_players):
                    for prob, root in self.game.initial_chance_outcomes():
                        reach = np.ones(self.game.num_players + 1, dtype=np.float64)
                        reach[-1] = prob
                        self._external_traverse(root, p, reach)
            else:
                for p in range(self.game.num_players):
                    for prob, root in self.game.initial_chance_outcomes():
                        reach = np.ones(self.game.num_players + 1, dtype=np.float64)
                        reach[-1] = prob
                        self._cfr_traverse(root, p, reach)
                    if self.mode == "cfr_plus":
                        self._apply_regret_matching_plus()

    def export_nodes(self) -> dict[str, tuple[np.ndarray, np.ndarray, int]]:
        """Regrets, strategy sum, and action count per info set (for parallel merge)."""
        return {
            key: (node.regrets.copy(), node.strategy_sum.copy(), node.num_actions)
            for key, node in self._nodes.items()
        }

    def average_strategy(self, *, min_mass: float = 0.0) -> dict[str, np.ndarray]:
        out: dict[str, np.ndarray] = {}
        for key, node in self._nodes.items():
            s = float(node.strategy_sum.sum())
            if min_mass > 0.0 and s < min_mass:
                continue
            if s <= 0.0:
                out[key] = np.full(node.num_actions, 1.0 / node.num_actions)
            else:
                out[key] = node.strategy_sum / s
        return out

    def _node(self, key: str, n_actions: int) -> _InfoSetNode:
        if key not in self._nodes:
            self._nodes[key] = _InfoSetNode(
                regrets=np.zeros(n_actions, dtype=np.float64),
                strategy_sum=np.zeros(n_actions, dtype=np.float64),
                num_actions=n_actions,
            )
        return self._nodes[key]

    def _strategy(self, key: str, n_actions: int) -> np.ndarray:
        node = self._node(key, n_actions)
        return _regret_matching(node.regrets)

    def _apply_regret_matching_plus(self) -> None:
        for node in self._nodes.values():
            node.regrets = np.maximum(node.regrets, 0.0)

    def _cfr_traverse(
        self,
        state: object,
        traverser: int,
        reach: np.ndarray,
    ) -> np.ndarray:
        player = self.game.current_player(state)
        if player == -1:
            u = np.zeros(self.game.num_players, dtype=np.float64)
            for p in range(self.game.num_players):
                u[p] = self.game.terminal_utility(state, p)
            return u

        if player is None:
            util = np.zeros(self.game.num_players, dtype=np.float64)
            for prob, child in self.game.chance_outcomes(state):
                child_reach = reach.copy()
                child_reach[-1] *= prob
                util += prob * self._cfr_traverse(child, traverser, child_reach)
            return util

        actions = self.game.legal_actions(state)
        n = len(actions)
        key = self.game.information_set_key(state, player)
        sigma = self._strategy(key, n)

        action_utils: list[np.ndarray] = []
        node_util = np.zeros(self.game.num_players, dtype=np.float64)
        for i, act in enumerate(actions):
            child = self.game.next_state(state, act)
            child_reach = reach.copy()
            child_reach[player] *= sigma[i]
            u = self._cfr_traverse(child, traverser, child_reach)
            action_utils.append(u)
            node_util += sigma[i] * u

        if player == traverser:
            cf_reach = float(np.prod(reach[:player]) * np.prod(reach[player + 1 :]))
            node = self._node(key, n)
            for i in range(n):
                regret = action_utils[i][player] - node_util[player]
                node.regrets[i] += cf_reach * regret
            weight = (
                float(self._iter * reach[player])
                if self.mode == "cfr_plus"
                else float(reach[player])
            )
            node.strategy_sum += weight * sigma

        return node_util

    def _external_traverse(
        self,
        state: object,
        traverser: int,
        reach: np.ndarray,
    ) -> float:
        player = self.game.current_player(state)
        if player == -1:
            return self.game.terminal_utility(state, traverser)

        if player is None:
            outcomes = self.game.chance_outcomes(state)
            r = self._rng.random()
            cum = 0.0
            for prob, child in outcomes:
                cum += prob
                if r <= cum:
                    child_reach = reach.copy()
                    child_reach[-1] *= prob
                    return self._external_traverse(child, traverser, child_reach)
            prob, child = outcomes[-1]
            child_reach = reach.copy()
            child_reach[-1] *= prob
            return self._external_traverse(child, traverser, child_reach)

        actions = self.game.legal_actions(state)
        n = len(actions)
        key = self.game.information_set_key(state, player)
        sigma = self._strategy(key, n)

        if player == traverser:
            util = 0.0
            action_vals = np.zeros(n, dtype=np.float64)
            for i, act in enumerate(actions):
                child = self.game.next_state(state, act)
                child_reach = reach.copy()
                child_reach[player] *= sigma[i]
                action_vals[i] = self._external_traverse(child, traverser, child_reach)
                util += sigma[i] * action_vals[i]
            cf_reach = float(np.prod(reach[:player]) * np.prod(reach[player + 1 :]))
            node = self._node(key, n)
            for i in range(n):
                node.regrets[i] += cf_reach * (action_vals[i] - util)
            node.strategy_sum += float(self._iter * reach[player]) * sigma
            return util

        idx = int(self._rng.choice(n, p=sigma))
        act = actions[idx]
        child = self.game.next_state(state, act)
        child_reach = reach.copy()
        child_reach[player] *= sigma[idx]
        return self._external_traverse(child, traverser, child_reach)


def _regret_matching(regrets: np.ndarray) -> np.ndarray:
    r = np.maximum(regrets, 0.0)
    s = float(r.sum())
    if s <= 0.0:
        n = len(r)
        return np.full(n, 1.0 / n, dtype=np.float64)
    return r / s


class CFRPlusSolver(CFRSolver):
    """CFR+ (alternating traversals, linear averaging, regret reset each iter)."""

    def __init__(self, game: ExtensiveGame, seed: int = 42) -> None:
        super().__init__(game=game, mode="cfr_plus", seed=seed)


class ExternalSamplingMCCFRSolver(CFRSolver):
    """External-sampling Monte Carlo CFR."""

    def __init__(self, game: ExtensiveGame, seed: int = 42) -> None:
        super().__init__(game=game, mode="external", seed=seed)
