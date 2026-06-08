"""Stacked policy — delegates to :class:`~poker_ai.policy.router_policy.RouterPolicy` (Phase 7b)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from poker_ai.core.game import GameState
from poker_ai.core.profiles import PlayerProfile
from poker_ai.policy.base import ActionDist, Policy
from poker_ai.policy.router_policy import RouterPolicy


class StackedPolicy:
    """Backward-compatible name; runtime routing is HU vs multi-way by ``n_active``."""

    name: str = "stacked"
    version: str = "0.4.0"

    def __init__(self, router: Policy | None = None, **_legacy: object) -> None:
        _ = _legacy
        self._router = router or RouterPolicy.from_artifacts()

    @classmethod
    def from_artifacts(
        cls,
        *,
        preflop_hu: Path = Path("artifacts/solver/preflop_hu_real.json"),
        preflop_6: Path = Path("artifacts/solver/preflop_cfr.json"),
        embed_jsonl: Path | None = Path("data/processed/hhformer_embeddings.jsonl"),
        student_dir: Path = Path("artifacts/student/v1"),
        multiway_student_dir: Path = Path("artifacts/student/multiway_v1"),
        hhformer_dir: Path = Path("artifacts/hhformer/v1"),
        monker_export_dir: Path = Path("artifacts/solver/monker_exports"),
    ) -> StackedPolicy:
        _ = embed_jsonl  # reserved for Phase 8 style / embed nudges
        return cls(
            router=RouterPolicy.from_artifacts(
                preflop_hu=preflop_hu,
                preflop_6=preflop_6,
                hu_student_dir=student_dir,
                multiway_student_dir=multiway_student_dir,
                hhformer_dir=hhformer_dir,
                monker_export_dir=monker_export_dir,
            ),
        )

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
        hand_id: str | None = None,
    ) -> ActionDist:
        _ = hand_id
        return self._router.propose(
            state,
            profile,
            opponent_styles=opponent_styles,
            thinking_ms=thinking_ms,
        )

    def explain(self, state: GameState, decision: ActionDist) -> str:
        return self._router.explain(state, decision)


def load_runtime_policy() -> Policy:
    from poker_ai.policy.distilled_policy import load_best_policy

    return load_best_policy()
