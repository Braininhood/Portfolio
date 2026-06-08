"""Multi-way equity (Phase 7b)."""

from __future__ import annotations

from poker_ai.core.cards import parse_card
from poker_ai.equity.multiway import hero_equity_vs_n_uniform


def test_aa_vs_two_uniform_preflop() -> None:
    aa = (parse_card("As"), parse_card("Ah"))
    eq = hero_equity_vs_n_uniform(aa, (), n_opponents=2, n_samples=12_000, seed=1)
    assert eq > 0.55


def test_weak_hand_vs_three_opponents_lower() -> None:
    weak = (parse_card("7c"), parse_card("2d"))
    eq = hero_equity_vs_n_uniform(weak, (), n_opponents=3, n_samples=12_000, seed=2)
    assert eq < 0.20
