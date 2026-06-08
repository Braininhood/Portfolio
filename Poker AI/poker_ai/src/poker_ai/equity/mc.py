"""Monte Carlo equity (legacy path) with a seedable RNG."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from poker_ai.core.evaluator import hand_rank_value
from poker_ai.equity._tables import COMBO_CARDS, COMBO_MASK, board_mask
from poker_ai.features.range import NUM_HOLE_COMBOS, normalize_l1


def _rng(seed: int | None) -> np.random.Generator:
    return np.random.default_rng(seed)


def _sample_combo(
    weights: np.ndarray,
    dead: np.uint64,
    rng: np.random.Generator,
) -> int | None:
    """Sample a combo index proportional to ``weights``, respecting ``dead`` mask."""
    mask = COMBO_MASK & dead == 0
    w = weights * mask.astype(np.float64)
    total = float(w.sum())
    if total <= 0.0:
        return None
    probs = w / total
    idx = int(rng.choice(NUM_HOLE_COMBOS, p=probs))
    return idx


def mc_equity_hands(
    hole_a: tuple[int, int],
    hole_b: tuple[int, int],
    board: Sequence[int] = (),
    *,
    n_samples: int = 20_000,
    seed: int | None = None,
) -> float:
    """Heads-up equity of ``hole_a`` vs ``hole_b`` (Monte Carlo over runouts)."""
    if hole_a[0] == hole_a[1] or hole_b[0] == hole_b[1]:
        msg = "hole cards must be two distinct cards"
        raise ValueError(msg)
    dead = board_mask(board)
    ha = np.uint64(1) << np.uint64(hole_a[0]) | np.uint64(1) << np.uint64(hole_a[1])
    hb = np.uint64(1) << np.uint64(hole_b[0]) | np.uint64(1) << np.uint64(hole_b[1])
    if (ha & hb) != 0 or (ha & dead) != 0 or (hb & dead) != 0:
        msg = "hole cards overlap each other or the board"
        raise ValueError(msg)
    dead |= ha | hb

    need = 5 - len(board)
    if need < 0:
        msg = f"board has more than five cards: {len(board)}"
        raise ValueError(msg)
    if need == 0:
        ra = hand_rank_value(hole_a[0], hole_a[1], *board)
        rb = hand_rank_value(hole_b[0], hole_b[1], *board)
        if ra < rb:
            return 1.0
        if ra == rb:
            return 0.5
        return 0.0

    deck = np.array([c for c in range(52) if (dead >> np.uint64(c)) & 1 == 0], dtype=np.int16)
    rng = _rng(seed)
    wins = 0.0
    for _ in range(n_samples):
        runout = rng.choice(deck, size=need, replace=False)
        b5 = tuple(int(c) for c in board) + tuple(int(c) for c in runout)
        ra = hand_rank_value(hole_a[0], hole_a[1], *b5)
        rb = hand_rank_value(hole_b[0], hole_b[1], *b5)
        if ra < rb:
            wins += 1.0
        elif ra == rb:
            wins += 0.5
    return wins / float(n_samples)


def mc_equity_range_vs_range(
    range_a: Sequence[float],
    range_b: Sequence[float],
    board: Sequence[int] = (),
    *,
    n_samples: int = 50_000,
    seed: int | None = None,
) -> float:
    """Monte Carlo range-vs-range equity (card-removal aware)."""
    if len(range_a) != NUM_HOLE_COMBOS or len(range_b) != NUM_HOLE_COMBOS:
        msg = f"ranges must have length {NUM_HOLE_COMBOS}"
        raise ValueError(msg)
    wa = np.asarray(normalize_l1(range_a), dtype=np.float64)
    wb = np.asarray(normalize_l1(range_b), dtype=np.float64)
    dead = board_mask(board)
    rng = _rng(seed)

    need = 5 - len(board)
    if need < 0:
        msg = f"board has more than five cards: {len(board)}"
        raise ValueError(msg)

    wins = 0.0
    for _ in range(n_samples):
        ia = _sample_combo(wa, dead, rng)
        if ia is None:
            continue
        da = COMBO_MASK[ia]
        ib = _sample_combo(wb, dead | da, rng)
        if ib is None:
            continue
        lo_a, hi_a = int(COMBO_CARDS[ia, 0]), int(COMBO_CARDS[ia, 1])
        lo_b, hi_b = int(COMBO_CARDS[ib, 0]), int(COMBO_CARDS[ib, 1])
        d = dead | da | COMBO_MASK[ib]
        if need == 0:
            b5 = tuple(int(c) for c in board)
        else:
            deck = np.array([c for c in range(52) if (d >> np.uint64(c)) & 1 == 0], dtype=np.int16)
            runout = rng.choice(deck, size=need, replace=False)
            b5 = tuple(int(c) for c in board) + tuple(int(c) for c in runout)
        ra = hand_rank_value(lo_a, hi_a, *b5)
        rb = hand_rank_value(lo_b, hi_b, *b5)
        if ra < rb:
            wins += 1.0
        elif ra == rb:
            wins += 0.5
    return wins / float(n_samples)
