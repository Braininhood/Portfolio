"""Benchmark equity latency (warm board → repeated queries)."""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np

from poker_ai.core.cards import parse_card
from poker_ai.equity import EquityEngine
from poker_ai.features.range import NUM_HOLE_COMBOS, normalize_l1


def _sparse(n: int, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    w = np.zeros(NUM_HOLE_COMBOS, dtype=np.float64)
    w[rng.choice(NUM_HOLE_COMBOS, n, replace=False)] = 1.0
    return list(normalize_l1(w.tolist()))


def main() -> None:
    flop = (parse_card("Ah"), parse_card("Kd"), parse_card("7c"))
    eng = EquityEngine()
    ra = _sparse(100, 1)
    rb = _sparse(100, 2)

    t0 = time.perf_counter()
    eng.warm_board(flop)
    warm_ms = (time.perf_counter() - t0) * 1000.0

    times: list[float] = []
    eq = 0.0
    for _ in range(20):
        t0 = time.perf_counter()
        eq = eng.equity(ra, rb, flop, use_disk_cache=False)
        times.append((time.perf_counter() - t0) * 1000.0)

    print(
        f"equity={eq:.4f}  warm_ms={warm_ms:.1f}  query_ms min/median/max="
        f"{min(times):.2f}/{sorted(times)[len(times) // 2]:.2f}/{max(times):.2f}"
    )


if __name__ == "__main__":
    main()
