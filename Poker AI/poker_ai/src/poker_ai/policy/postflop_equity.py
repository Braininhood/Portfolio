"""Postflop policy via Phase 4 range-vs-range equity (Phase 6 bridge)."""

from __future__ import annotations

import numpy as np

from poker_ai.core.context import is_multiway_context
from poker_ai.core.engine import legal_actions
from poker_ai.core.game import EngineAction, EngineActionKind, GameState, Street
from poker_ai.core.profiles import PlayerProfile
from poker_ai.equity import EquityEngine
from poker_ai.features.range import one_hot_range, uniform_range
from poker_ai.policy.base import ActionDist
from poker_ai.policy.heuristic import HeuristicPolicy


class PostflopEquityPolicy:
    """Equity-aware bet/raise/call/fold from hero range vs uniform (postflop streets)."""

    name: str = "postflop_equity"
    version: str = "0.1.0"

    def __init__(self) -> None:
        self._engine = EquityEngine()
        self._fallback = HeuristicPolicy()

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> ActionDist:
        _ = profile, opponent_styles, thinking_ms
        if state.hand_over or state.street == Street.PREFLOP:
            return self._fallback.propose(state, profile)
        if is_multiway_context(state):
            return ActionDist((), ())

        legal = legal_actions(state)
        if not legal or state.acting_seat is None:
            return ActionDist((), ())

        hero = state.acting_seat
        holes = getattr(state, "seat_holes", None)
        if holes is None or hero >= len(holes) or holes[hero] is None:
            return self._fallback.propose(state, profile)

        lo, hi = holes[hero]
        hero_range = one_hot_range(lo, hi)
        board = tuple(state.board)
        if len(board) >= 3:
            self._engine.warm_board(board)
        eq = float(self._engine.equity(hero_range, uniform_range(), board))

        return self._dist_from_equity(eq, legal)

    def explain(self, state: GameState, decision: ActionDist) -> str:
        return "postflop_equity policy"

    def _dist_from_equity(
        self,
        eq: float,
        legal: tuple[EngineAction, ...],
    ) -> ActionDist:
        fold_p, call_p, raise_p = 0.05, 0.35, 0.60
        if eq < 0.35:
            fold_p, call_p, raise_p = 0.55, 0.40, 0.05
        elif eq < 0.55:
            fold_p, call_p, raise_p = 0.20, 0.55, 0.25
        keys = [(a.kind.value, a.amount_chips, a.seat) for a in legal]
        mass = [0.0] * len(legal)
        for i, a in enumerate(legal):
            if a.kind == EngineActionKind.FOLD:
                mass[i] = fold_p
            elif a.kind in (EngineActionKind.CALL, EngineActionKind.CHECK):
                mass[i] = call_p
            else:
                mass[i] = raise_p
        s = sum(mass)
        if s <= 0:
            mass = [1.0 / len(legal)] * len(legal)
        else:
            mass = [m / s for m in mass]
        return ActionDist(tuple(keys), tuple(mass))
