"""Phase 4 — Monte Carlo, exact, and range-vs-range equity."""

from __future__ import annotations

from poker_ai.equity.cache import EquityCache
from poker_ai.equity.engine import EquityEngine
from poker_ai.equity.breakdown import (
    EquityBreakdown,
    equity_breakdown,
    exact_equity_breakdown,
    mc_equity_breakdown,
)
from poker_ai.equity.exact import exact_equity_hands, exact_equity_range_vs_range
from poker_ai.equity.mc import mc_equity_hands, mc_equity_range_vs_range
from poker_ai.equity.range_notation import range_from_notation
from poker_ai.equity.spot_insight import spot_insight
from poker_ai.equity.backfill import (
    BackfillStats,
    compute_seat_equities,
    enrich_hand_results,
    hero_street_equity_from_hand,
)
from poker_ai.equity.live import hero_equity_from_state
from poker_ai.equity.multiway import hero_equity_vs_n_uniform, mc_equity_hole_vs_uniform_opponents
from poker_ai.equity.range_vs_range import (
    aa_vs_random_preflop_equity,
    combo_equity_vs_range,
    equity_range_vs_range,
    fft_equity_distribution_convolution,
    mixed_range_equity,
    nonzero_combo_indices,
    per_combo_equity_histogram,
)

__all__ = [
    "BackfillStats",
    "EquityCache",
    "EquityEngine",
    "aa_vs_random_preflop_equity",
    "combo_equity_vs_range",
    "compute_seat_equities",
    "enrich_hand_results",
    "EquityBreakdown",
    "equity_breakdown",
    "equity_range_vs_range",
    "exact_equity_breakdown",
    "exact_equity_hands",
    "hero_equity_from_state",
    "hero_street_equity_from_hand",
    "mc_equity_breakdown",
    "range_from_notation",
    "spot_insight",
    "exact_equity_range_vs_range",
    "fft_equity_distribution_convolution",
    "hero_equity_vs_n_uniform",
    "mc_equity_hands",
    "mc_equity_hole_vs_uniform_opponents",
    "mc_equity_range_vs_range",
    "mixed_range_equity",
    "nonzero_combo_indices",
    "per_combo_equity_histogram",
]
