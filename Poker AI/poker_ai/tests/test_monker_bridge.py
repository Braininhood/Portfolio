"""Monker / multi-way teacher bridge stub (Phase 7c)."""

from __future__ import annotations

from poker_ai.solver.bridge.monker import MultiwaySpotSpec, solve_multiway_spot


def test_monker_mock_teacher_normalized() -> None:
    spec = MultiwaySpotSpec(board="Qs,Jh,2h", n_active=4, num_seats=6)
    spot = solve_multiway_spot(spec, backend="mock")
    assert spot.backend == "monker_mock"
    assert abs(sum(spot.frequencies) - 1.0) < 1e-5
