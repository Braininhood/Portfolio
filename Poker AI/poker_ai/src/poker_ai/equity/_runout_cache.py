"""Per-board runout rank tables — amortises flop/turn equity across range queries."""

from __future__ import annotations

import math
import os
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from typing import NamedTuple

import numpy as np

from poker_ai.equity._tables import (
    COMBO_MASK,
    board_mask,
    fill_ranks_on_board,
    iter_runout_completions,
)
from poker_ai.features.range import NUM_HOLE_COMBOS

# Preflop has C(52,5) ≈ 2.6M runouts (~5 GB table). Never build that in RAM.
MAX_CACHED_RUNOUTS = 2_000

_INVALID_RANK = np.int32(1_000_000)


class _RunoutSliceResult(NamedTuple):
    start: int
    masks: np.ndarray
    alive_indices: list[np.ndarray]
    rank_values: list[np.ndarray]


def _worker_count() -> int:
    raw = int(os.environ.get("POKER_AI_EQUITY_WORKERS", "0"))
    if raw > 0:
        return raw
    cpu = os.cpu_count() or 4
    return max(1, min(4, cpu))


def _process_runout_slice(
    board_tuple: tuple[int, ...],
    runouts: list[tuple[int, ...]],
    start_ri: int,
) -> _RunoutSliceResult:
    dead0 = board_mask(board_tuple)
    n = len(runouts)
    masks = np.empty(n, dtype=np.uint64)
    alive_indices: list[np.ndarray] = []
    rank_values: list[np.ndarray] = []
    all_idx = np.arange(NUM_HOLE_COMBOS, dtype=np.int32)
    buf = np.empty(NUM_HOLE_COMBOS, dtype=np.int32)

    for offset, runout in enumerate(runouts):
        b5 = board_tuple + runout
        dm = dead0
        for c in runout:
            dm |= np.uint64(1) << np.uint64(int(c))
        masks[offset] = dm
        alive = all_idx[(COMBO_MASK & dm) == 0]
        fill_ranks_on_board(alive, b5, buf)
        alive_indices.append(alive.copy())
        rank_values.append(buf[: alive.size].copy())
    return _RunoutSliceResult(start_ri, masks, alive_indices, rank_values)


def _build_table_serial(
    board_tuple: tuple[int, ...],
    runouts: list[tuple[int, ...]],
) -> tuple[np.ndarray, np.ndarray]:
    dead0 = board_mask(board_tuple)
    n = len(runouts)
    ranks = np.full((NUM_HOLE_COMBOS, n), _INVALID_RANK, dtype=np.int32)
    masks = np.empty(n, dtype=np.uint64)
    all_idx = np.arange(NUM_HOLE_COMBOS, dtype=np.int32)
    buf = np.empty(NUM_HOLE_COMBOS, dtype=np.int32)

    for ri, runout in enumerate(runouts):
        b5 = board_tuple + runout
        dm = dead0
        for c in runout:
            dm |= np.uint64(1) << np.uint64(int(c))
        masks[ri] = dm
        alive = all_idx[(COMBO_MASK & dm) == 0]
        fill_ranks_on_board(alive, b5, buf)
        ranks[alive, ri] = buf[: alive.size]
    return masks, ranks


def _build_table_parallel(
    board_tuple: tuple[int, ...],
    runouts: list[tuple[int, ...]],
    workers: int,
) -> tuple[np.ndarray, np.ndarray]:
    n = len(runouts)
    ranks = np.full((NUM_HOLE_COMBOS, n), _INVALID_RANK, dtype=np.int32)
    masks = np.empty(n, dtype=np.uint64)
    chunk = max(1, (n + workers - 1) // workers)
    tasks: list[tuple[tuple[int, ...], list[tuple[int, ...]], int]] = []
    for start in range(0, n, chunk):
        tasks.append((board_tuple, runouts[start : start + chunk], start))

    with ProcessPoolExecutor(max_workers=workers) as pool:
        for slice_result in pool.map(_process_runout_slice, tasks):
            for offset, alive in enumerate(slice_result.alive_indices):
                ri = slice_result.start + offset
                masks[ri] = slice_result.masks[offset]
                ranks[alive, ri] = slice_result.rank_values[offset]
    return masks, ranks


def _build_table(board: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
    runouts = list(iter_runout_completions(board))
    workers = _worker_count()
    if workers > 1 and len(runouts) >= 64:
        return _build_table_parallel(board, runouts, workers)
    return _build_table_serial(board, runouts)


class RunoutRankCache:
    """Maps ``board`` -> ``(runout_masks, rank_table[combo, runout])``."""

    __slots__ = ("_store",)

    def __init__(self) -> None:
        self._store: dict[tuple[int, ...], tuple[np.ndarray, np.ndarray]] = {}

    def get(self, board: Sequence[int]) -> tuple[np.ndarray, np.ndarray]:
        key = tuple(int(c) for c in board)
        hit = self._store.get(key)
        if hit is not None:
            return hit
        built = _build_table(key)
        self._store[key] = built
        return built

    def warm(self, board: Sequence[int]) -> None:
        """Pre-build the rank table for ``board`` (call once per fixed board in live tooling)."""
        self.get(board)

    def clear(self) -> None:
        self._store.clear()


_GLOBAL_RUNOUT_CACHE = RunoutRankCache()


def runout_rank_cache() -> RunoutRankCache:
    return _GLOBAL_RUNOUT_CACHE


def count_runouts(board: Sequence[int]) -> int:
    """Number of board completions (``C(deck_remaining, cards_to_deal)``)."""
    need = 5 - len(board)
    if need <= 0:
        return 1
    deck = 52 - len(board)
    return math.comb(deck, need)


def cacheable_board(board: Sequence[int]) -> bool:
    """True when building a rank table for ``board`` is small enough to keep in RAM."""
    return count_runouts(board) <= MAX_CACHED_RUNOUTS
