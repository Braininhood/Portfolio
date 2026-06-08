"""Route HU vs multi-way brains by active player count (Phase 7b)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from poker_ai.core.context import count_active_players, is_heads_up_context, is_multiway_context
from poker_ai.core.game import GameState
from poker_ai.core.profiles import PlayerProfile
from poker_ai.policy.base import ActionDist, Policy
from poker_ai.policy.heuristic import HeuristicPolicy
from poker_ai.policy.hu_stack import HuStackPolicy
from poker_ai.policy.multiway_stack import MultiwayStackPolicy


class RouterPolicy:
    """Single runtime entry: ``n_active == 2`` → HU, ``n_active >= 3`` → multi-way."""

    name: str = "router"
    version: str = "1.0.0"

    def __init__(
        self,
        *,
        hu: Policy | None = None,
        multiway: Policy | None = None,
        fallback: Policy | None = None,
    ) -> None:
        self._hu = hu or HuStackPolicy()
        self._multiway = multiway or MultiwayStackPolicy()
        self._fallback = fallback or HeuristicPolicy()
        self._last_brain: str = "fallback"

    @classmethod
    def from_artifacts(
        cls,
        *,
        preflop_hu: Path = Path("artifacts/solver/preflop_hu_real.json"),
        preflop_6: Path = Path("artifacts/solver/preflop_cfr.json"),
        hu_student_dir: Path = Path("artifacts/student/v1"),
        multiway_student_dir: Path = Path("artifacts/student/multiway_v1"),
        hhformer_dir: Path = Path("artifacts/hhformer/v1"),
        monker_export_dir: Path = Path("artifacts/solver/monker_exports"),
        monker_blend: float = 0.15,
    ) -> RouterPolicy:
        return cls(
            hu=HuStackPolicy(
                preflop_hu=preflop_hu,
                student_dir=hu_student_dir,
                hhformer_dir=hhformer_dir,
            ),
            multiway=MultiwayStackPolicy(
                preflop_6=preflop_6,
                student_dir=multiway_student_dir,
                hhformer_dir=hhformer_dir,
                monker_export_dir=monker_export_dir,
                monker_blend=monker_blend,
            ),
        )

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> ActionDist:
        n = count_active_players(state)
        if is_heads_up_context(state):
            self._last_brain = "hu"
            dist = self._hu.propose(
                state, profile, opponent_styles=opponent_styles, thinking_ms=thinking_ms
            )
            if dist.actions:
                return dist
        elif is_multiway_context(state):
            self._last_brain = "multiway"
            dist = self._multiway.propose(
                state, profile, opponent_styles=opponent_styles, thinking_ms=thinking_ms
            )
            if dist.actions:
                return dist

        self._last_brain = "fallback"
        _ = n
        return self._fallback.propose(
            state, profile, opponent_styles=opponent_styles, thinking_ms=thinking_ms
        )

    def explain(self, state: GameState, decision: ActionDist) -> str:
        n = count_active_players(state)
        return f"router brain={self._last_brain} n_active={n} seats={state.num_seats}"
