"""Heads-up policy stack — HU preflop CFR + distilled postflop (Phase 7b)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from poker_ai.core.context import is_heads_up_context
from poker_ai.core.game import GameState, Street
from poker_ai.core.profiles import PlayerProfile
from poker_ai.policy.base import ActionDist, Policy
from poker_ai.policy.cfr_policy import CFRPolicy
from poker_ai.policy.distilled_policy import DistilledPolicy
from poker_ai.policy.heuristic import HeuristicPolicy


class HuStackPolicy:
    """Used only when ``count_active_players(state) == 2``."""

    name: str = "hu_stack"
    version: str = "1.0.0"

    def __init__(
        self,
        *,
        preflop_hu: Path | None = None,
        student_dir: Path | None = None,
        hhformer_dir: Path | None = None,
    ) -> None:
        hu = preflop_hu or Path("artifacts/solver/preflop_hu_real.json")
        self._cfr = CFRPolicy.load_json(hu) if hu.is_file() else None
        sd = student_dir or Path("artifacts/student/v1")
        self._postflop: Policy = DistilledPolicy.from_artifacts(
            student_dir=sd,
            hhformer_dir=hhformer_dir or Path("artifacts/hhformer/v1"),
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
        if not is_heads_up_context(state):
            return ActionDist((), ())

        if state.street != Street.PREFLOP and not state.hand_over:
            dist = self._postflop.propose(
                state, profile, opponent_styles=opponent_styles, thinking_ms=thinking_ms
            )
            if dist.actions:
                return dist

        if self._cfr is not None and state.street == Street.PREFLOP:
            dist = self._cfr.propose(
                state, profile, opponent_styles=opponent_styles, thinking_ms=thinking_ms
            )
            if dist.actions:
                return dist

        return self._heuristic.propose(
            state, profile, opponent_styles=opponent_styles, thinking_ms=thinking_ms
        )

    def explain(self, state: GameState, decision: ActionDist) -> str:
        return f"brain=hu {self._postflop.explain(state, decision)}"
