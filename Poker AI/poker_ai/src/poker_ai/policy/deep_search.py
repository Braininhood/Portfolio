"""Depth-limited re-solver blend when thinking_ms > 200 (Phase 13 / W10)."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from poker_ai.core.game import GameState, Street
from poker_ai.policy.base import ActionDist
from poker_ai.policy.distilled_policy import _format_card
from poker_ai.solver.bridge.cache import SolverCache, cache_key
from poker_ai.solver.bridge.schemas import SpotSpec


def _spot_from_state(state: GameState) -> SpotSpec:
    board = ",".join(_format_card(c) for c in state.board)
    return SpotSpec(
        board=board,
        pot_chips=max(1, state.pot),
        effective_stack=max(1, max(state.stacks)),
        range_oop="",
        range_ip="",
        sizing_tree_id="deep_search_v1",
    )


def deep_search_enabled(*, thinking_ms: int = 0, deep_search: bool = False) -> bool:
    return deep_search or thinking_ms > 200


def blend_with_solver(
    state: GameState,
    base: ActionDist,
    *,
    thinking_ms: int = 0,
    cache_dir: Path | str = Path("artifacts/solver_cache"),
) -> tuple[ActionDist, bool]:
    """Blend base policy with cached solver frequencies when deep search is on."""
    if state.hand_over or not base.actions:
        return base, False
    if state.street == Street.PREFLOP:
        return base, False

    budget_ms = max(0, thinking_ms - 50)
    t0 = time.perf_counter()
    cache = SolverCache(Path(cache_dir))
    spec = _spot_from_state(state)
    key = cache_key(spec)
    cached = cache.get(key)
    used = False

    if cached is None and budget_ms > 100:
        try:
            from poker_ai.solver.bridge.texas import solve_spot

            if (time.perf_counter() - t0) * 1000.0 < budget_ms:
                spot = solve_spot(spec, backend="auto")
                cache.put(spot)
                cached = spot
        except Exception:
            cached = None

    if cached is None or not cached.frequencies:
        return base, False

    labels = list(cached.action_labels or [])
    freqs = list(cached.frequencies)
    if not labels or len(freqs) != len(labels):
        return base, False

    label_to_solver: dict[str, float] = {}
    for lab, f in zip(labels, freqs, strict=True):
        k = lab.lower().replace("_", "")
        label_to_solver[k] = float(f)

    keys = list(base.actions)
    base_probs = np.asarray([float(p) for p in base.probs], dtype=np.float64)
    solver_probs = np.zeros(len(keys), dtype=np.float64)
    for i, k in enumerate(keys):
        kind = k[0].lower()
        if kind == "fold":
            solver_probs[i] = label_to_solver.get("fold", 0.0)
        elif kind in ("check", "call"):
            solver_probs[i] = label_to_solver.get("checkcall", label_to_solver.get("check", 0.0))
        elif kind in ("bet", "raise"):
            solver_probs[i] = (
                label_to_solver.get("bet33", 0.0)
                + label_to_solver.get("bet66", 0.0)
                + label_to_solver.get("allin", 0.0)
            )
    s = solver_probs.sum()
    if s <= 0:
        return base, False
    solver_probs /= s

    # More thinking time → heavier solver weight (DeepStack-lite knob).
    w = 0.35 if thinking_ms <= 300 else 0.55
    blended = (1.0 - w) * base_probs + w * solver_probs
    blended = blended / blended.sum()
    used = True
    return ActionDist(tuple(keys), tuple(float(x) for x in blended)).normalized(), used
