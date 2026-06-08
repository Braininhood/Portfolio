"""Symbolic explanation engine tests."""

from __future__ import annotations

from poker_ai.explain.engine import explain_decision
from poker_ai.policy.base import ActionDist
from poker_ai.policy.bench import _postflop_state


def test_explain_returns_non_empty() -> None:
    state = _postflop_state()
    dist = ActionDist((("Check", 0, 0),), (1.0,))
    text = explain_decision(state, dist, policy_name="test")
    assert "test" in text
    assert len(text) > 10
