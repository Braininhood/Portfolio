"""Range-vs-range equity (exact kernel + FFT equity-bucket convolution)."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from poker_ai.equity._runout_cache import cacheable_board
from poker_ai.equity.exact import exact_equity_range_vs_range
from poker_ai.features.range import NUM_HOLE_COMBOS, l1_sum, normalize_l1


def equity_range_vs_range(
    range_a: Sequence[float],
    range_b: Sequence[float],
    board: Sequence[int] = (),
) -> float:
    """Exact equity of ``range_a`` vs ``range_b`` (hero perspective)."""
    return exact_equity_range_vs_range(range_a, range_b, board)


def nonzero_combo_indices(
    weights: Sequence[float],
    dead_cards: Sequence[int] | None = None,
) -> np.ndarray:
    """Combo indices with positive weight that do not overlap ``dead_cards``."""
    from poker_ai.equity._tables import COMBO_MASK, board_mask

    w = np.asarray(weights, dtype=np.float64)
    idx = np.flatnonzero(w > 0.0)
    if dead_cards is None or len(dead_cards) == 0:
        return idx
    dm = board_mask(dead_cards)
    return idx[(COMBO_MASK[idx] & dm) == 0]


def combo_equity_vs_range(
    combo_idx: int,
    opp_range: Sequence[float],
    board: Sequence[int] = (),
) -> float:
    """Exact equity of one combo vs a range on ``board``."""
    from poker_ai.equity._tables import COMBO_CARDS
    from poker_ai.features.range import one_hot_range

    lo = int(COMBO_CARDS[combo_idx, 0])
    hi = int(COMBO_CARDS[combo_idx, 1])
    hero = one_hot_range(lo, hi)
    if not cacheable_board(board):
        from poker_ai.equity.mc import mc_equity_range_vs_range

        return mc_equity_range_vs_range(hero, opp_range, board, n_samples=30_000, seed=42)
    return exact_equity_range_vs_range(hero, opp_range, board)


def per_combo_equity_histogram(
    hero_range: Sequence[float],
    opp_range: Sequence[float],
    board: Sequence[int] = (),
    *,
    n_buckets: int = 101,
) -> np.ndarray:
    """Histogram of hero combo equities vs ``opp_range`` (``n_buckets`` bins on [0, 1])."""
    from poker_ai.equity._tables import COMBO_MASK, board_mask

    hist = np.zeros(n_buckets, dtype=np.float64)
    if l1_sum(hero_range) <= 0.0:
        return hist

    hr = np.asarray(normalize_l1(hero_range), dtype=np.float64)
    idx = nonzero_combo_indices(hr, board)
    if idx.size == 0:
        return hist

    # Cap work for wide ranges (histogram is approximate by nature).
    max_combos = 64
    if idx.size > max_combos:
        top = np.argsort(-hr[idx])[:max_combos]
        idx = idx[top]
        scale = float(hr[idx].sum())
        if scale > 0.0:
            hr = hr.copy()
            hr[idx] /= scale

    dm = board_mask(board)
    for i in idx:
        if (COMBO_MASK[int(i)] & dm) != 0:
            continue
        eq = combo_equity_vs_range(int(i), opp_range, board)
        b = min(n_buckets - 1, int(eq * float(n_buckets - 1) + 0.5))
        hist[b] += hr[int(i)]
    s = hist.sum()
    if s > 0.0:
        hist /= s
    return hist


def fft_equity_distribution_convolution(
    dist_a: np.ndarray,
    dist_b: np.ndarray,
) -> np.ndarray:
    """Convolve two equity histograms via FFT (mixed-strategy overlay)."""
    if dist_a.ndim != 1 or dist_b.ndim != 1:
        msg = "distributions must be one-dimensional"
        raise ValueError(msg)
    if dist_a.size != dist_b.size:
        msg = "distributions must have the same bucket count"
        raise ValueError(msg)
    n = int(dist_a.size)
    fa = np.fft.rfft(dist_a, n=2 * n - 1)
    fb = np.fft.rfft(dist_b, n=2 * n - 1)
    out = np.fft.irfft(fa * fb, n=2 * n - 1)[:n]
    s = float(out.sum())
    if s > 0.0:
        out /= s
    return out


def mixed_range_equity(
    alpha: float,
    range_value: Sequence[float],
    range_bluff: Sequence[float],
    opp_range: Sequence[float],
    board: Sequence[int] = (),
    *,
    n_buckets: int = 101,
) -> float:
    """Equity of mixed range vs ``opp_range`` via bucket convolution."""
    if not (0.0 <= alpha <= 1.0):
        msg = "alpha must be in [0, 1]"
        raise ValueError(msg)
    rv = np.asarray(normalize_l1(range_value), dtype=np.float64)
    rb = np.asarray(normalize_l1(range_bluff), dtype=np.float64)
    mixed = alpha * rv + (1.0 - alpha) * rb
    mixed = np.asarray(normalize_l1(mixed), dtype=np.float64)

    hist_v = per_combo_equity_histogram(mixed, opp_range, board, n_buckets=n_buckets)
    # Opp distribution under uniform equity buckets (identity proxy for overlay).
    buckets = np.linspace(0.0, 1.0, n_buckets)
    return float(np.dot(buckets, hist_v))


def aa_vs_random_preflop_equity(*, use_exact: bool = False) -> float:
    """AA (uniform over six combos) vs a uniform random range (literature ~0.852)."""
    from poker_ai.core.cards import parse_card
    from poker_ai.features.range import combo_index, uniform_range

    aa_indices = [
        combo_index(parse_card("As"), parse_card("Ah")),
        combo_index(parse_card("As"), parse_card("Ad")),
        combo_index(parse_card("As"), parse_card("Ac")),
        combo_index(parse_card("Ah"), parse_card("Ad")),
        combo_index(parse_card("Ah"), parse_card("Ac")),
        combo_index(parse_card("Ad"), parse_card("Ac")),
    ]
    ra = [0.0] * NUM_HOLE_COMBOS
    for i in aa_indices:
        ra[i] = 1.0 / 6.0
    rb = uniform_range()
    if use_exact:
        return exact_equity_range_vs_range(ra, rb, ())
    from poker_ai.equity.mc import mc_equity_range_vs_range

    return mc_equity_range_vs_range(ra, rb, (), n_samples=100_000, seed=42)
