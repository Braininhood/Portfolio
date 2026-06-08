"""Frozen baseline policies — poker archetypes (Phase 9).

Archetype targets (live VPIP/PFR vary by stakes; used as design knobs):
- TAG: VPIP ~15–22%, PFR ~12–18% — tight-aggressive ([Pokerology](https://www.pokerology.com/poker/strategy/playing-styles/))
- LAG: VPIP ~25–35%, PFR ~20–28% — loose-aggressive
- NIT/Rock: VPIP <14%, passive postflop — tight-passive
- Calling station / Fish: VPIP 40%+, low PFR — loose-passive
- Maniac: extreme LAG — hyper-aggressive
"""

from __future__ import annotations

import random

import numpy as np

from poker_ai.core.engine import legal_actions
from poker_ai.core.game import EngineActionKind, GameState
from poker_ai.core.profiles import PlayerProfile
from poker_ai.policy.base import ActionDist
from poker_ai.policy.heuristic import HeuristicPolicy


def _reweight_dist(
    dist: ActionDist,
    *,
    fold_mul: float = 1.0,
    call_mul: float = 1.0,
    aggro_mul: float = 1.0,
) -> ActionDist:
    keys = list(dist.actions)
    probs = [float(p) for p in dist.probs]
    for i, k in enumerate(keys):
        if k[0] == "Fold":
            probs[i] *= fold_mul
        elif k[0] in ("Call", "Check"):
            probs[i] *= call_mul
        elif k[0] in ("Bet", "Raise"):
            probs[i] *= aggro_mul
    s = sum(probs)
    if s <= 0:
        return dist.normalized()
    return ActionDist(tuple(keys), tuple(p / s for p in probs)).normalized()


class _HeuristicArchetypePolicy:
    """Shared wrapper: heuristic core + action reweighting."""

    name: str = "archetype"
    version: str = "1.0.0"

    def __init__(
        self,
        *,
        fold_mul: float = 1.0,
        call_mul: float = 1.0,
        aggro_mul: float = 1.0,
    ) -> None:
        self._inner = HeuristicPolicy()
        self._fold_mul = fold_mul
        self._call_mul = call_mul
        self._aggro_mul = aggro_mul

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> ActionDist:
        dist = self._inner.propose(
            state, profile, opponent_styles=opponent_styles, thinking_ms=thinking_ms
        )
        if not dist.actions:
            return dist
        return _reweight_dist(
            dist,
            fold_mul=self._fold_mul,
            call_mul=self._call_mul,
            aggro_mul=self._aggro_mul,
        )

    def explain(self, state: GameState, decision: ActionDist) -> str:
        return self.name


class RandomPolicy:
    name = "random"
    version = "1.0.0"

    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> ActionDist:
        _ = profile, opponent_styles, thinking_ms
        legal = legal_actions(state)
        if not legal:
            return ActionDist((), ())
        i = self._rng.randrange(len(legal))
        probs = [0.0] * len(legal)
        probs[i] = 1.0
        keys = [(a.kind.value, a.amount_chips, a.seat) for a in legal]
        return ActionDist(tuple(keys), tuple(probs))

    def explain(self, state: GameState, decision: ActionDist) -> str:
        return "random uniform legal action"


class CallStationPolicy:
    """Loose-passive: calls wide, rarely raises (classic fish / station)."""

    name = "call_station"
    version = "1.0.0"

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> ActionDist:
        _ = profile, opponent_styles, thinking_ms
        legal = legal_actions(state)
        if not legal:
            return ActionDist((), ())
        keys: list[tuple[str, int, int]] = []
        probs: list[float] = []
        for a in legal:
            keys.append((a.kind.value, a.amount_chips, a.seat))
            if a.kind == EngineActionKind.FOLD:
                probs.append(0.02)
            elif a.kind in (EngineActionKind.CALL, EngineActionKind.CHECK):
                probs.append(0.85)
            else:
                probs.append(0.13)
        s = sum(probs)
        return ActionDist(tuple(keys), tuple(p / s for p in probs))

    def explain(self, state: GameState, decision: ActionDist) -> str:
        return "call_station"


class FishPolicy:
    """Loose-passive+ : even wider calls, almost never folds (VPIP 40%+ style)."""

    name = "fish"
    version = "1.0.0"

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> ActionDist:
        _ = profile, opponent_styles, thinking_ms
        legal = legal_actions(state)
        if not legal:
            return ActionDist((), ())
        keys: list[tuple[str, int, int]] = []
        probs: list[float] = []
        for a in legal:
            keys.append((a.kind.value, a.amount_chips, a.seat))
            if a.kind == EngineActionKind.FOLD:
                probs.append(0.005)
            elif a.kind in (EngineActionKind.CALL, EngineActionKind.CHECK):
                probs.append(0.92)
            else:
                probs.append(0.075)
        s = sum(probs)
        return ActionDist(tuple(keys), tuple(p / s for p in probs))

    def explain(self, state: GameState, decision: ActionDist) -> str:
        return "fish"


class NitPolicy(_HeuristicArchetypePolicy):
    """Tight-passive rock: few hands, check/call > bet (VPIP <14% style)."""

    name = "nit"
    version = "1.0.0"

    def __init__(self) -> None:
        super().__init__(fold_mul=2.2, call_mul=1.35, aggro_mul=0.3)


class RockPolicy(NitPolicy):
    """Alias for nit — same tight-passive profile."""

    name = "rock"
    version = "1.0.0"


class TagPolicy(_HeuristicArchetypePolicy):
    """Tight-aggressive reg: selective preflop, solid aggression when in."""

    name = "tag"
    version = "1.0.0"

    def __init__(self) -> None:
        super().__init__(fold_mul=1.35, call_mul=0.85, aggro_mul=1.2)


class LAGPolicy(_HeuristicArchetypePolicy):
    """Loose-aggressive: wider range, more barrels."""

    name = "lag"
    version = "1.0.0"

    def __init__(self) -> None:
        super().__init__(fold_mul=0.65, call_mul=0.95, aggro_mul=1.45)


class ManiacPolicy(_HeuristicArchetypePolicy):
    """Ultra-LAG: raises constantly (Phase 8 exploit target)."""

    name = "maniac"
    version = "1.0.0"

    def __init__(self) -> None:
        super().__init__(fold_mul=0.3, call_mul=1.2, aggro_mul=2.2)


class PassiveRegPolicy(_HeuristicArchetypePolicy):
    """Weak-tight reg: plays few pots, rarely applies pressure postflop."""

    name = "passive_reg"
    version = "1.0.0"

    def __init__(self) -> None:
        super().__init__(fold_mul=1.6, call_mul=1.25, aggro_mul=0.55)
