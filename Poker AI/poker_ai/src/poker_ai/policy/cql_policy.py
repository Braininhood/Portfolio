"""CQL offline RL policy — conservative action selection (Phase 13 / W10)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from poker_ai.core.game import GameState
from poker_ai.core.profiles import PlayerProfile
from poker_ai.policy.base import ActionDist, Policy
from poker_ai.policy.distilled_policy import DistilledPolicy


class CQLPolicy:
    """Wraps distilled student; down-weights low-data / high-variance action lines."""

    name: str = "cql"
    version: str = "1.0.0"

    def __init__(self, *, student: Policy | None = None, conservative: float = 0.18) -> None:
        self._inner = student or DistilledPolicy.from_artifacts()
        self._conservative = max(0.0, min(0.5, conservative))

    @classmethod
    def from_artifacts(cls, *, artifact_dir: Path = Path("artifacts/cql/v1")) -> CQLPolicy | None:
        weights = artifact_dir / "cql_policy.safetensors"
        if not weights.is_file():
            return None
        student_dir = Path("artifacts/student/v1")
        return cls(student=DistilledPolicy.from_artifacts(student_dir=student_dir))

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> ActionDist:
        base = self._inner.propose(
            state,
            profile,
            opponent_styles=opponent_styles,
            thinking_ms=thinking_ms,
        )
        if state.hand_over or not base.actions or self._conservative <= 0:
            return base

        keys = list(base.actions)
        probs = np.asarray([float(p) for p in base.probs], dtype=np.float64)
        mean_p = probs.mean()
        adjusted = []
        for p in probs:
            if p < mean_p * 0.6:
                adjusted.append(p * (1.0 - self._conservative))
            else:
                adjusted.append(p * (1.0 + self._conservative * 0.25))
        arr = np.asarray(adjusted, dtype=np.float64)
        s = arr.sum()
        if s <= 0:
            return base.normalized()
        return ActionDist(tuple(keys), tuple(float(x / s) for x in arr)).normalized()

    def explain(self, state: GameState, decision: ActionDist) -> str:
        return f"cql_policy: conservative={self._conservative:.2f} base={self._inner.name}"
