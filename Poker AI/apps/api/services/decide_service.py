"""Shared /decide logic for replay, drill, and play hints (W7 Day 27)."""

from __future__ import annotations

from typing import Any

from poker_ai.core.engine import legal_actions
from poker_ai.core.game import GameState
from poker_ai.core.profiles import PlayerProfile
from poker_ai.equity.live import hero_equity_from_state
from poker_ai.explain.engine import explain_decision

from services.drill_service import format_action_label
from services.policy_service import get_policy, propose_with_timing
from state_codec import action_dist_to_probs


def run_decide_for_state(
    state: GameState,
    *,
    profile_id: str = "hero",
    policy_name: str = "best",
    thinking_ms: int = 0,
    deep_search: bool = False,
    include_equity: bool = False,
) -> dict[str, Any]:
    """Run policy propose + explanation on a live engine state."""
    if state.hand_over:
        msg = "hand is over at this step"
        raise ValueError(msg)
    legal = legal_actions(state)
    if not legal:
        msg = "no legal actions at this node"
        raise ValueError(msg)

    profile = PlayerProfile(profile_id=profile_id, display_name=profile_id)
    policy = get_policy(policy_name)
    dist, latency_ms = propose_with_timing(
        policy,
        state,
        profile,
        thinking_ms=thinking_ms,
        deep_search=deep_search,
    )
    explanation = explain_decision(state, dist, policy_name=policy.name)
    try:
        policy_explain = policy.explain(state, dist)
        if policy_explain and policy_explain not in explanation:
            explanation = f"{explanation}\n{policy_explain}"
    except Exception:
        pass

    from poker_ai.policy.deep_search import deep_search_enabled

    if deep_search_enabled(thinking_ms=thinking_ms, deep_search=deep_search):
        explanation = f"{explanation}\nDeep search: solver blend active (thinking_ms={thinking_ms})."

    bb = max(float(state.big_blind), 1.0)
    pot = int(state.pot)
    raw = action_dist_to_probs(dist.actions, dist.probs)
    actions: list[dict[str, Any]] = []
    for row in raw:
        kind = str(row["kind"])
        amount = int(row["amount_chips"])
        actions.append(
            {
                "kind": kind,
                "amount_chips": amount,
                "seat": int(row["seat"]),
                "prob": float(row["prob"]),
                "label": format_action_label(kind, amount, pot=pot, bb=bb),
            }
        )
    return {
        "policy_name": policy.name,
        "policy_version": policy.version,
        "latency_ms": latency_ms,
        "actions": actions,
        "explanation": explanation,
        "street": state.street.value,
        "acting_seat": state.acting_seat,
        "hero_equity": hero_equity_from_state(state) if include_equity else None,
    }
