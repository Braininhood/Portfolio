"""Policy protocol and action distributions (Phase 6)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np

from poker_ai.core.game import GameState
from poker_ai.core.profiles import PlayerProfile


@dataclass(frozen=True, slots=True)
class ActionDist:
    """Probability mass over legal :class:`~poker_ai.core.game.EngineAction` choices."""

    actions: tuple[tuple[str, int, int], ...]  # (kind, amount_chips, seat)
    probs: tuple[float, ...]

    def normalized(self) -> ActionDist:
        arr = np.asarray(self.probs, dtype=np.float64)
        s = float(arr.sum())
        if s <= 0.0:
            n = len(arr)
            return ActionDist(self.actions, tuple(1.0 / n for _ in range(n)))
        return ActionDist(self.actions, tuple(float(x / s) for x in arr))


@runtime_checkable
class Policy(Protocol):
    """Runtime decision contract for simulators and review tools."""

    name: str
    version: str

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> ActionDist: ...

    def explain(self, state: GameState, decision: ActionDist) -> str: ...
