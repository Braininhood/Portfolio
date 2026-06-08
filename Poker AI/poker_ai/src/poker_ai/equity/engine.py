"""Live equity API — warm board once, query many ranges in milliseconds."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from poker_ai.equity._runout_cache import cacheable_board, runout_rank_cache
from poker_ai.equity.cache import EquityCache
from poker_ai.equity.exact import exact_equity_range_vs_range
from poker_ai.equity.mc import mc_equity_range_vs_range


class EquityEngine:
    """Postflop exact equity with an in-RAM runout table; preflop falls back to Monte Carlo."""

    def __init__(self, *, cache_dir: str | Path | None = None) -> None:
        self._runout = runout_rank_cache()
        self._disk: EquityCache | None = EquityCache(cache_dir) if cache_dir is not None else None

    def warm_board(self, board: Sequence[int]) -> None:
        """Precompute ranks for all runouts on ``board`` (do once per flop/turn/river)."""
        self._runout.warm(board)

    def equity(
        self,
        range_a: Sequence[float],
        range_b: Sequence[float],
        board: Sequence[int] = (),
        *,
        use_disk_cache: bool = True,
    ) -> float:
        """Hero equity of ``range_a`` vs ``range_b`` on ``board``."""
        if cacheable_board(board):
            if self._disk is not None and use_disk_cache:
                return self._disk.lookup_or_compute(
                    range_a,
                    range_b,
                    board,
                    exact_equity_range_vs_range,
                    persist=False,
                )
            return exact_equity_range_vs_range(range_a, range_b, board)
        return mc_equity_range_vs_range(range_a, range_b, board, n_samples=80_000, seed=42)
