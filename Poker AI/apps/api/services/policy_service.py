"""Lazy-loaded runtime policies for /decide."""

from __future__ import annotations

import time
from functools import lru_cache

from poker_ai.core.profiles import PlayerProfile
from poker_ai.policy.base import ActionDist, Policy
from poker_ai.policy.distilled_policy import DistilledPolicy, load_best_policy
from poker_ai.policy.heuristic import HeuristicPolicy


@lru_cache(maxsize=4)
def get_policy(name: str) -> Policy:
    key = name.strip().lower()
    if key == "best":
        return load_best_policy()
    if key == "heuristic":
        return HeuristicPolicy()
    return DistilledPolicy.from_artifacts()


def propose_with_timing(
    policy: Policy,
    state: object,
    profile: PlayerProfile,
    *,
    thinking_ms: int = 0,
    deep_search: bool = False,
) -> tuple[ActionDist, float]:
    from poker_ai.policy.deep_search import blend_with_solver, deep_search_enabled

    t0 = time.perf_counter()
    dist = policy.propose(state, profile, thinking_ms=thinking_ms)  # type: ignore[arg-type]
    if deep_search_enabled(thinking_ms=thinking_ms, deep_search=deep_search):
        dist, _ = blend_with_solver(state, dist, thinking_ms=thinking_ms)  # type: ignore[arg-type]
    ms = (time.perf_counter() - t0) * 1000.0
    return dist, ms
