"""Batch solve spots into the disk cache (Phase 7)."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from poker_ai.solver.bridge.cache import SolverCache, cache_key
from poker_ai.solver.bridge.grid import generate_spot_grid
from poker_ai.solver.bridge.schemas import SolvedSpot, SpotSpec
from poker_ai.runtime.progress import ProgressFn
from poker_ai.solver.bridge.texas import Backend, TexasSolverDriver, solve_spot


@dataclass(frozen=True, slots=True)
class GridSolveResult:
    requested: int
    solved: int
    cache_hits: int
    failed: int
    backends: dict[str, int]
    failed_spots_path: Path | None = None


def solve_grid(
    *,
    n_spots: int,
    cache_dir: Path = Path("artifacts/solver_cache"),
    backend: Backend = "auto",
    seed: int = 42,
    skip_cached: bool = True,
    continue_on_error: bool = False,
    texas_threads: int = 2,
    progress: ProgressFn = None,
) -> GridSolveResult:
    cache = SolverCache(cache_dir)
    driver = TexasSolverDriver()
    specs = generate_spot_grid(n_spots=n_spots, seed=seed)
    solved = 0
    hits = 0
    failed = 0
    backends: dict[str, int] = {}
    fail_log = cache_dir / "failed_spots.jsonl"
    fail_rows: list[dict[str, str]] = []
    n_specs = len(specs)
    for i, spec in enumerate(specs):
        if progress and n_specs > 0:
            progress(
                {
                    "pct": min(99, int(100 * i / n_specs)),
                    "msg": f"Solving spot {i + 1}/{n_specs} ({spec.normalized_board()})",
                    "detail": {"spot_index": i, "spots_total": n_specs, "solved": solved, "cache_hits": hits},
                }
            )
        key = cache_key(spec)
        if skip_cached and cache.contains(key):
            hits += 1
            existing = cache.get(key)
            if existing is not None:
                backends[existing.backend] = backends.get(existing.backend, 0) + 1
            continue
        run_spec = spec
        if backend == "texas" and texas_threads > 0 and spec.thread_num != texas_threads:
            run_spec = SpotSpec(
                board=spec.board,
                pot_chips=spec.pot_chips,
                effective_stack=spec.effective_stack,
                range_oop=spec.range_oop,
                range_ip=spec.range_ip,
                bet_sizes=spec.bet_sizes,
                thread_num=texas_threads,
                max_iteration=spec.max_iteration,
                accuracy=spec.accuracy,
                allin_threshold=spec.allin_threshold,
                sizing_tree_id=spec.sizing_tree_id,
            )
        try:
            spot = solve_spot(run_spec, backend=backend, driver=driver)
        except (FileNotFoundError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            if not continue_on_error:
                raise
            failed += 1
            fail_rows.append(
                {
                    "index": str(i),
                    "board": spec.normalized_board(),
                    "cache_key": key,
                    "error": str(exc)[:500],
                }
            )
            continue
        spot = _enrich_spot(spot, spec)
        cache.put(spot)
        solved += 1
        backends[spot.backend] = backends.get(spot.backend, 0) + 1
    if fail_rows:
        fail_log.parent.mkdir(parents=True, exist_ok=True)
        with fail_log.open("a", encoding="utf-8") as fh:
            for row in fail_rows:
                fh.write(json.dumps(row) + "\n")
    return GridSolveResult(
        requested=len(specs),
        solved=solved,
        cache_hits=hits,
        failed=failed,
        backends=backends,
        failed_spots_path=fail_log if fail_rows else None,
    )


def _enrich_spot(spot: SolvedSpot, spec: SpotSpec) -> SolvedSpot:
    meta = dict(spot.meta or {})
    meta.setdefault("pot_chips", spec.pot_chips)
    meta.setdefault("effective_stack", spec.effective_stack)
    return SolvedSpot(
        cache_key=spot.cache_key,
        board=spot.board,
        sizing_tree_id=spot.sizing_tree_id,
        ranges_hash=spot.ranges_hash,
        action_labels=spot.action_labels,
        frequencies=spot.frequencies,
        backend=spot.backend,
        meta=meta,
    )
