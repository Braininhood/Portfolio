"""Disk-backed equity cache (parquet rows keyed by xxhash)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import xxhash

from poker_ai.features.range import NUM_HOLE_COMBOS, normalize_l1

_CACHE_SCHEMA_VERSION = 1


def _cache_key(
    range_a: Sequence[float],
    range_b: Sequence[float],
    board: Sequence[int],
) -> str:
    h = xxhash.xxh64()
    h.update(_CACHE_SCHEMA_VERSION.to_bytes(2, "little"))
    board_arr = np.asarray([int(c) for c in board], dtype=np.int16)
    h.update(board_arr.tobytes())
    a = np.asarray(normalize_l1(range_a), dtype=np.float32)
    b = np.asarray(normalize_l1(range_b), dtype=np.float32)
    h.update(a.tobytes())
    h.update(b.tobytes())
    return h.hexdigest()


def _read_parquet(path: Path) -> dict[str, float]:
    try:
        import pyarrow.parquet as pq

        table = pq.read_table(path)
        keys = table.column("key").to_pylist()
        vals = table.column("equity").to_pylist()
        return {str(k): float(v) for k, v in zip(keys, vals, strict=True)}
    except ImportError:
        import duckdb

        rows = duckdb.execute(
            "SELECT key, equity FROM read_parquet(?)",
            [path.as_posix()],
        ).fetchall()
        return {str(k): float(v) for k, v in rows}


def _write_parquet(path: Path, mem: dict[str, float]) -> None:
    keys = list(mem.keys())
    vals = [mem[k] for k in keys]
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        table = pa.table({"key": keys, "equity": vals})
        pq.write_table(table, path)
        return
    except ImportError:
        import duckdb

        con = duckdb.connect()
        con.execute("CREATE TEMP TABLE _eq_cache (key VARCHAR, equity DOUBLE)")
        con.executemany(
            "INSERT INTO _eq_cache VALUES (?, ?)",
            list(zip(keys, vals, strict=True)),
        )
        con.execute("COPY _eq_cache TO ? (FORMAT PARQUET)", [path.as_posix()])


class EquityCache:
    """Parquet-backed store mapping xxhash keys to scalar equities."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._file = self.path / "equity_cache.parquet"
        self._mem: dict[str, float] = {}
        self._load()

    def _load(self) -> None:
        if not self._file.is_file():
            return
        self._mem = _read_parquet(self._file)

    def _flush(self) -> None:
        _write_parquet(self._file, self._mem)

    def get(
        self,
        range_a: Sequence[float],
        range_b: Sequence[float],
        board: Sequence[int] = (),
    ) -> float | None:
        key = _cache_key(range_a, range_b, board)
        return self._mem.get(key)

    def set(
        self,
        range_a: Sequence[float],
        range_b: Sequence[float],
        board: Sequence[int],
        equity: float,
        *,
        persist: bool = True,
    ) -> str:
        if len(range_a) != NUM_HOLE_COMBOS or len(range_b) != NUM_HOLE_COMBOS:
            msg = f"ranges must have length {NUM_HOLE_COMBOS}"
            raise ValueError(msg)
        key = _cache_key(range_a, range_b, board)
        self._mem[key] = float(equity)
        if persist:
            self._flush()
        return key

    def lookup_or_compute(
        self,
        range_a: Sequence[float],
        range_b: Sequence[float],
        board: Sequence[int],
        compute_fn: Any,
        *,
        persist: bool = True,
    ) -> float:
        """Return cached equity or call ``compute_fn(range_a, range_b, board)``."""
        hit = self.get(range_a, range_b, board)
        if hit is not None:
            return hit
        eq = float(compute_fn(range_a, range_b, board))
        self.set(range_a, range_b, board, eq, persist=persist)
        return eq
