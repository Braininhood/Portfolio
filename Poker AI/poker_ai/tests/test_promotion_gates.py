"""Promotion gate evaluation (Phase 11)."""

from __future__ import annotations

from poker_ai.learn.promotion_gates import evaluate_promotion_gates


def test_promotion_gates_unknown_model_has_checks() -> None:
    report = evaluate_promotion_gates("student_hu", skip_drift=True)
    assert report.model_name == "student_hu"
    assert len(report.checks) >= 3
