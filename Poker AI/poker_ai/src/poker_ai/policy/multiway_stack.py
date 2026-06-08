"""Multi-way policy stack — ring CFR / heuristic preflop + multi-way postflop (Phase 7b)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from poker_ai.core.context import is_multiway_context
from poker_ai.core.game import GameState, Street
from poker_ai.core.profiles import PlayerProfile
from poker_ai.policy.base import ActionDist, Policy
from poker_ai.policy.cfr_policy import CFRPolicy
from poker_ai.policy.heuristic import HeuristicPolicy
from poker_ai.policy.multiway_postflop import MultiwayPostflopPolicy
from poker_ai.solver.preflop_artifacts import resolve_preflop_cfr_path

# Tabular preflop CFR supports 2–10 seats when matching artifact exists.
_CFR_MAX_SEATS = 10


class MultiwayStackPolicy:
    """Used when ``count_active_players(state) >= 3``."""

    name: str = "multiway_stack"
    version: str = "1.0.0"

    def __init__(
        self,
        *,
        preflop_6: Path | None = None,
        student_dir: Path | None = None,
        hhformer_dir: Path | None = None,
        monker_export_dir: Path | None = None,
        monker_blend: float = 0.15,
    ) -> None:
        p6 = preflop_6 or Path("artifacts/solver/preflop_cfr.json")
        self._cfr_default_path = p6
        self._cfr_cache: dict[int, CFRPolicy | None] = {}
        if p6.is_file():
            self._cfr_cache[6] = CFRPolicy.load_json(p6)
        self._postflop: Policy = MultiwayPostflopPolicy(
            student_dir=student_dir,
            hhformer_dir=hhformer_dir,
            monker_export_dir=monker_export_dir,
            monker_blend=monker_blend,
        )
        self._heuristic = HeuristicPolicy()

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> ActionDist:
        if not is_multiway_context(state):
            return ActionDist((), ())

        if state.street != Street.PREFLOP and not state.hand_over:
            dist = self._postflop.propose(
                state, profile, opponent_styles=opponent_styles, thinking_ms=thinking_ms
            )
            if dist.actions:
                return dist

        cfr = self._cfr_for_seats(state.num_seats)
        if (
            cfr is not None
            and state.street == Street.PREFLOP
            and state.num_seats <= _CFR_MAX_SEATS
        ):
            dist = cfr.propose(
                state, profile, opponent_styles=opponent_styles, thinking_ms=thinking_ms
            )
            if dist.actions:
                return dist

        return self._heuristic.propose(
            state, profile, opponent_styles=opponent_styles, thinking_ms=thinking_ms
        )

    def _cfr_for_seats(self, num_seats: int) -> CFRPolicy | None:
        if num_seats in self._cfr_cache:
            return self._cfr_cache[num_seats]
        path = resolve_preflop_cfr_path(num_seats) or (
            self._cfr_default_path if self._cfr_default_path.is_file() else None
        )
        policy: CFRPolicy | None = None
        if path is not None and path.is_file():
            policy = CFRPolicy.load_json(path)
        self._cfr_cache[num_seats] = policy
        return policy

    def explain(self, state: GameState, decision: ActionDist) -> str:
        return f"brain=multiway seats={state.num_seats} {self._postflop.explain(state, decision)}"
