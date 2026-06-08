"""Exact equity by enumerating all remaining board runouts."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from poker_ai.core.evaluator import hand_rank_value, hand_rank_value_int
from poker_ai.equity._fast_loop import accumulate_runout_equity
from poker_ai.equity._runout_cache import (
    MAX_CACHED_RUNOUTS,
    cacheable_board,
    count_runouts,
    runout_rank_cache,
)
from poker_ai.equity._tables import (
    COMBO_MASK,
    board_mask,
    iter_runout_completions,
    rank_combo_on_board,
)
from poker_ai.features.range import NUM_HOLE_COMBOS, l1_sum, normalize_l1


def exact_equity_hands(
    hole_a: tuple[int, int],
    hole_b: tuple[int, int],
    board: Sequence[int] = (),
) -> float:
    """Exact heads-up equity for two known hole pairs."""
    dead = board_mask(board)
    ha = np.uint64(1) << np.uint64(hole_a[0]) | np.uint64(1) << np.uint64(hole_a[1])
    hb = np.uint64(1) << np.uint64(hole_b[0]) | np.uint64(1) << np.uint64(hole_b[1])
    if (ha & hb) != 0 or (ha & dead) != 0 or (hb & dead) != 0:
        msg = "hole cards overlap each other or the board"
        raise ValueError(msg)

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

    if not cacheable_board(board):
        msg = (
            f"exact_equity_hands: too many runouts ({count_runouts(board)}); "
            "use a postflop board or mc_equity_hands"
        )
        raise ValueError(msg)

    extra_dead = ha | hb
    wins = 0.0
    n = 0
    for runout in iter_runout_completions(board, extra_dead):
        b5 = tuple(int(c) for c in board) + runout
        ra = hand_rank_value_int(hole_a[0], hole_a[1], *b5)
        rb = hand_rank_value_int(hole_b[0], hole_b[1], *b5)
        n += 1
        if ra < rb:
            wins += 1.0
        elif ra == rb:
            wins += 0.5
    return wins / float(n) if n else 0.5


def exact_equity_range_vs_range(
    range_a: Sequence[float],
    range_b: Sequence[float],
    board: Sequence[int] = (),
) -> float:
    """Exact range-vs-range equity (cached postflop runout table + vectorised aggregation)."""
    if len(range_a) != NUM_HOLE_COMBOS or len(range_b) != NUM_HOLE_COMBOS:
        msg = f"ranges must have length {NUM_HOLE_COMBOS}"
        raise ValueError(msg)
    if l1_sum(range_a) <= 0.0 or l1_sum(range_b) <= 0.0:
        return 0.5

    board_tuple = tuple(int(c) for c in board)
    if not cacheable_board(board_tuple):
        n_run = count_runouts(board_tuple)
        msg = (
            f"exact equity needs ≤{MAX_CACHED_RUNOUTS} runouts (got {n_run} on this board); "
            "use mc_equity_range_vs_range for preflop"
        )
        raise ValueError(msg)

    wa = np.asarray(normalize_l1(range_a), dtype=np.float64)
    wb = np.asarray(normalize_l1(range_b), dtype=np.float64)
    dead0 = board_mask(board_tuple)

    valid_a = np.flatnonzero(wa > 0.0)
    valid_b = np.flatnonzero(wb > 0.0)
    if valid_a.size == 0 or valid_b.size == 0:
        return 0.5

    need = 5 - len(board_tuple)
    if need < 0:
        msg = f"board has more than five cards: {len(board_tuple)}"
        raise ValueError(msg)
    if need == 0:
        return _river_equity_matrix(wa, wb, valid_a, valid_b, board_tuple)

    pre_a = valid_a[(COMBO_MASK[valid_a] & dead0) == 0]
    pre_b = valid_b[(COMBO_MASK[valid_b] & dead0) == 0]
    if pre_a.size == 0 or pre_b.size == 0:
        return 0.5

    if pre_a.size * pre_b.size > 25_000:
        msg = (
            f"too many active combo pairs ({pre_a.size} x {pre_b.size}); "
            "narrow ranges or use mc_equity_range_vs_range"
        )
        raise ValueError(msg)

    masks, rank_tbl = runout_rank_cache().get(board_tuple)
    return _cached_runout_equity(wa, wb, pre_a, pre_b, masks, rank_tbl)


def _cached_runout_equity(
    wa: np.ndarray,
    wb: np.ndarray,
    pre_a: np.ndarray,
    pre_b: np.ndarray,
    masks: np.ndarray,
    rank_tbl: np.ndarray,
) -> float:
    """Range-vs-range using a pre-built ``(combo, runout)`` rank table."""
    ra = rank_tbl[pre_a, :]
    rb = rank_tbl[pre_b, :]
    static_overlap = (COMBO_MASK[pre_a, None] & COMBO_MASK[pre_b]) != 0
    base_w = np.where(static_overlap, 0.0, wa[pre_a][:, None] * wb[pre_b][None, :])
    alive_a = (COMBO_MASK[pre_a, None] & masks[None, :]) == 0
    alive_b = (COMBO_MASK[pre_b, None] & masks[None, :]) == 0
    win_mass, mass = accumulate_runout_equity(ra, rb, base_w, alive_a, alive_b)
    if mass <= 0.0:
        return 0.5
    return win_mass / mass


def _river_equity_matrix(
    wa: np.ndarray,
    wb: np.ndarray,
    valid_a: np.ndarray,
    valid_b: np.ndarray,
    board5: tuple[int, ...],
) -> float:
    dm = board_mask(board5)
    ia = valid_a[(COMBO_MASK[valid_a] & dm) == 0]
    ib = valid_b[(COMBO_MASK[valid_b] & dm) == 0]
    if ia.size == 0 or ib.size == 0:
        return 0.5

    ranks_a = np.array([rank_combo_on_board(int(i), board5) for i in ia], dtype=np.int32)
    ranks_b = np.array([rank_combo_on_board(int(j), board5) for j in ib], dtype=np.int32)

    overlap = (COMBO_MASK[ia, None] & COMBO_MASK[ib]) != 0
    weight = wa[ia, None] * wb[ib]
    weight = np.where(overlap, 0.0, weight)
    mass = float(weight.sum())
    if mass <= 0.0:
        return 0.5

    win = (ranks_a[:, None] < ranks_b[None, :]).astype(np.float64)
    tie = (ranks_a[:, None] == ranks_b[None, :]).astype(np.float64) * 0.5
    return float((weight * (win + tie)).sum() / mass)
