"""Bet-tree and equity-bucket abstractions for NLH solvers (Phase 6)."""

from __future__ import annotations

BET_FRACTIONS: tuple[float, ...] = (0.0, 0.33, 0.66, 1.5)  # + all-in handled separately
NUM_EQUITY_BUCKETS = 50


def nearest_bet_fraction(pot_fraction: float) -> float:
    """Map an observed pot fraction to the nearest abstract size (excluding all-in)."""
    if pot_fraction <= 0.0:
        return 0.0
    best = BET_FRACTIONS[1]
    best_dist = abs(pot_fraction - best)
    for frac in BET_FRACTIONS[1:]:
        d = abs(pot_fraction - frac)
        if d < best_dist:
            best, best_dist = frac, d
    return best


def pot_fraction_chips(pot: int, fraction: float, *, min_bet: int = 1) -> int:
    """Chips for ``fraction * pot`` (at least ``min_bet`` when fraction > 0)."""
    if fraction <= 0.0:
        return 0
    return max(min_bet, round(pot * fraction))


def equity_bucket(equity: float, n_buckets: int = NUM_EQUITY_BUCKETS) -> int:
    """Map hero equity in ``[0, 1]`` to ``0 .. n_buckets-1``."""
    e = min(1.0, max(0.0, float(equity)))
    if n_buckets <= 1:
        return 0
    return min(n_buckets - 1, int(e * float(n_buckets)))


def bucket_midpoint(bucket: int, n_buckets: int = NUM_EQUITY_BUCKETS) -> float:
    """Representative equity for a bucket (cell centre)."""
    if n_buckets <= 0:
        return 0.5
    b = min(n_buckets - 1, max(0, bucket))
    return (b + 0.5) / float(n_buckets)
