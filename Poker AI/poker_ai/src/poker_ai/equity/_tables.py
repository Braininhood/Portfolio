"""Precomputed combo cards and 52-bit masks for equity kernels."""

from __future__ import annotations

import itertools
from collections.abc import Iterator, Sequence

import numpy as np

from poker_ai.features.range import NUM_HOLE_COMBOS, combo_at_index

# (1326, 2) hole card ints
COMBO_CARDS: np.ndarray = np.zeros((NUM_HOLE_COMBOS, 2), dtype=np.int16)
for _i in range(NUM_HOLE_COMBOS):
    lo, hi = combo_at_index(_i)
    COMBO_CARDS[_i, 0] = lo
    COMBO_CARDS[_i, 1] = hi

# 52-bit mask per combo (uint64)
COMBO_MASK: np.ndarray = np.zeros(NUM_HOLE_COMBOS, dtype=np.uint64)
_one = np.uint64(1)
for _i in range(NUM_HOLE_COMBOS):
    lo = int(COMBO_CARDS[_i, 0])
    hi = int(COMBO_CARDS[_i, 1])
    COMBO_MASK[_i] = (_one << np.uint64(lo)) | (_one << np.uint64(hi))


def board_mask(board: Sequence[int]) -> np.uint64:
    m = np.uint64(0)
    for c in board:
        m |= _one << np.uint64(int(c))
    return m


def iter_runout_completions(
    board: Sequence[int],
    extra_dead: np.uint64 | None = None,
) -> Iterator[tuple[int, ...]]:
    """Yield ``need``-card completions so ``board + completion`` has five cards."""
    need = 5 - len(board)
    if need < 0:
        msg = f"board has more than five cards: {len(board)}"
        raise ValueError(msg)
    if need == 0:
        yield ()
        return
    dm = board_mask(board)
    if extra_dead is not None:
        dm |= extra_dead
    deck = [c for c in range(52) if (dm >> np.uint64(c)) & np.uint64(1) == 0]
    if need == 1:
        for c in deck:
            yield (c,)
        return
    yield from itertools.combinations(deck, need)


def rank_combo_on_board(combo_idx: int, board5: Sequence[int]) -> int:
    """Seven-card ``phevaluator`` rank for one hole combo and a five-card board."""
    from poker_ai.core.evaluator import hand_rank_value_int

    lo = int(COMBO_CARDS[combo_idx, 0])
    hi = int(COMBO_CARDS[combo_idx, 1])
    return hand_rank_value_int(lo, hi, *board5)


def fill_ranks_on_board(
    combo_indices: np.ndarray,
    board5: Sequence[int],
    out: np.ndarray,
) -> None:
    """Write ``phevaluator`` ranks into ``out[: len(combo_indices)]``."""
    from poker_ai.core.evaluator import hand_rank_value_int

    b0, b1, b2, b3, b4 = (
        int(board5[0]),
        int(board5[1]),
        int(board5[2]),
        int(board5[3]),
        int(board5[4]),
    )
    ev = hand_rank_value_int
    cc = COMBO_CARDS
    for k, idx in enumerate(combo_indices):
        i = int(idx)
        out[k] = ev(int(cc[i, 0]), int(cc[i, 1]), b0, b1, b2, b3, b4)
