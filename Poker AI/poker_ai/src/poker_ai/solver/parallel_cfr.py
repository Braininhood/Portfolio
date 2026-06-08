"""Process-parallel preflop CFR / MCCFR (Phase 6)."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, ThreadPoolExecutor, as_completed, wait
from pathlib import Path
from typing import Any

import numpy as np

log = logging.getLogger(__name__)

from poker_ai.solver.preflop_equity import EquityMode
from poker_ai.solver.preflop_shard import run_shard
from poker_ai.runtime.progress import ProgressFn

_SHARD_MODULE = "poker_ai.solver.preflop_shard_main"


def _package_root() -> Path:
    """``poker_ai/`` project dir (``pyproject.toml``, ``artifacts/solver/``)."""
    return Path(__file__).resolve().parents[3]


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    src = _package_root() / "src"
    parts = [str(src), env.get("PYTHONPATH", "")]
    env["PYTHONPATH"] = os.pathsep.join(p for p in parts if p)
    return env


def _shard_payload(
    *,
    num_players: int,
    iterations: int,
    chance_samples: int,
    seed: int,
    max_raises: int,
    shard_id: int,
    num_shards: int,
    equity_mode: EquityMode,
    equity_mc_samples: int,
) -> dict[str, Any]:
    return run_shard(
        num_players=num_players,
        iterations=iterations,
        chance_samples=chance_samples,
        seed=seed,
        max_raises=max_raises,
        shard_id=shard_id,
        num_shards=num_shards,
        equity_mode=equity_mode,
        equity_mc_samples=equity_mc_samples,
    )


def _cfr_shard_worker(args: tuple[Any, ...]) -> dict[str, Any]:
    return _shard_payload(**dict(zip(_SHARD_KEYS, args, strict=True)))


_SHARD_KEYS = (
    "num_players",
    "iterations",
    "chance_samples",
    "seed",
    "max_raises",
    "shard_id",
    "num_shards",
    "equity_mode",
    "equity_mc_samples",
)


def _iterations_per_shard(total: int, num_shards: int) -> list[int]:
    if num_shards <= 1:
        return [total]
    base, rem = divmod(total, num_shards)
    return [base + (1 if i < rem else 0) for i in range(num_shards)]


def merge_regret_shards(
    shards: list[dict[str, Any]],
    *,
    min_mass: float = 0.0,
) -> dict[str, np.ndarray]:
    merged_sum: dict[str, np.ndarray] = {}
    merged_n: dict[str, int] = {}
    for shard in shards:
        for key, value in shard.items():
            _reg_l, sum_l, n_act = value[0], value[1], int(value[2])
            ssum = np.asarray(sum_l, dtype=np.float64)
            if key not in merged_sum:
                merged_sum[key] = ssum.copy()
                merged_n[key] = n_act
            else:
                merged_sum[key] += ssum
    out: dict[str, np.ndarray] = {}
    for key, ssum in merged_sum.items():
        total = float(ssum.sum())
        if min_mass > 0.0 and total < min_mass:
            continue
        n = merged_n[key]
        if total <= 0.0:
            out[key] = np.full(n, 1.0 / n, dtype=np.float64)
        else:
            out[key] = ssum / total
    return out


def _solve_shards_subprocess(
    *,
    num_players: int,
    iterations: int,
    chance_samples: int,
    seed: int,
    max_raises: int,
    workers: int,
    equity_mode: EquityMode,
    equity_mc_samples: int,
    prune_min_mass: float,
    progress: ProgressFn,
) -> dict[str, np.ndarray]:
    """Windows-safe: one ``Popen`` per shard, results via temp files (no ProcessPool IPC)."""
    per_shard_iters = _iterations_per_shard(iterations, workers)
    env = _subprocess_env()
    cwd = str(_package_root())

    with tempfile.TemporaryDirectory(prefix="cfr_shards_") as td:
        td_path = Path(td)
        launched: list[tuple[int, subprocess.Popen[bytes], Path]] = []

        for shard_id in range(workers):
            out_path = td_path / f"shard_{shard_id}.json"
            cfg = {
                "num_players": num_players,
                "iterations": per_shard_iters[shard_id],
                "chance_samples": chance_samples,
                "seed": seed,
                "max_raises": max_raises,
                "shard_id": shard_id,
                "num_shards": workers,
                "equity_mode": equity_mode,
                "equity_mc_samples": equity_mc_samples,
                "out_path": str(out_path),
            }
            proc = subprocess.Popen(
                [sys.executable, "-m", _SHARD_MODULE],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                cwd=cwd,
            )
            assert proc.stdin is not None
            proc.stdin.write(json.dumps(cfg).encode())
            proc.stdin.close()
            launched.append((shard_id, proc, out_path))

        log.info("subprocess shards: %s processes started (Windows-safe)", workers)
        if progress:
            progress({
                "pct": 7,
                "msg": f"Preflop CFR: {workers} subprocess shards started",
                "detail": {
                    "workers": workers,
                    "shards_done": 0,
                    "workers_running": workers,
                    "parallel": True,
                },
            })

        def _join_one(item: tuple[int, subprocess.Popen[bytes], Path]) -> tuple[int, dict[str, Any]]:
            shard_id, proc, out_path = item
            rc = proc.wait()
            if rc != 0:
                raise RuntimeError(f"CFR shard {shard_id} failed (exit {rc})")
            if not out_path.is_file():
                raise RuntimeError(f"CFR shard {shard_id}: missing output {out_path}")
            return shard_id, json.loads(out_path.read_text(encoding="utf-8"))

        shards_by_id: dict[int, dict[str, Any]] = {}
        done = 0
        stop_heartbeat = threading.Event()

        def _heartbeat() -> None:
            while not stop_heartbeat.wait(20.0):
                finished = sum(1 for _, proc, _ in launched if proc.poll() is not None)
                running = workers - finished
                pct = 7 + int(83 * finished / workers)
                msg = (
                    f"Preflop CFR: {finished}/{workers} shards done "
                    f"({running} running, ~{per_shard_iters[0]:,} iters/shard)"
                )
                log.info(msg)
                if progress:
                    progress({
                        "pct": pct,
                        "msg": msg,
                        "detail": {
                            "workers": workers,
                            "shards_done": finished,
                            "workers_running": running,
                            "parallel": True,
                        },
                    })

        hb = threading.Thread(target=_heartbeat, daemon=True)
        hb.start()
        try:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(_join_one, item): item[0] for item in launched}
                for fut in as_completed(futures):
                    shard_id, data = fut.result()
                    shards_by_id[shard_id] = data
                    done += 1
                    pct = 7 + int(83 * done / workers)
                    msg = f"Preflop CFR: shard {done}/{workers} finished"
                    log.info(msg)
                    if progress:
                        progress({
                            "pct": pct,
                            "msg": msg,
                            "detail": {
                                "workers": workers,
                                "shards_done": done,
                                "workers_running": workers - done,
                                "parallel": True,
                            },
                        })
        finally:
            stop_heartbeat.set()
            hb.join(timeout=1.0)

        ordered = [shards_by_id[i] for i in range(workers)]

    if progress:
        progress({"pct": 96, "msg": "Merging regret tables…", "detail": {"shards_done": workers}})
    return merge_regret_shards(ordered, min_mass=prune_min_mass)


def _solve_shards_processpool(
    *,
    num_players: int,
    iterations: int,
    chance_samples: int,
    seed: int,
    max_raises: int,
    workers: int,
    equity_mode: EquityMode,
    equity_mc_samples: int,
    prune_min_mass: float,
    progress: ProgressFn,
) -> dict[str, np.ndarray]:
    per_shard_iters = _iterations_per_shard(iterations, workers)
    tasks = [
        (
            num_players,
            per_shard_iters[shard_id],
            chance_samples,
            seed,
            max_raises,
            shard_id,
            workers,
            equity_mode,
            equity_mc_samples,
        )
        for shard_id in range(workers)
    ]
    shards: list[dict[str, Any]] = []
    pool = ProcessPoolExecutor(max_workers=workers)
    futures = [pool.submit(_cfr_shard_worker, t) for t in tasks]
    pending = set(futures)
    done = 0
    if progress:
        progress({
            "pct": 7,
            "msg": f"Preflop CFR: {workers} workers started",
            "detail": {"workers": workers, "shards_done": 0},
        })
    try:
        while pending:
            finished, pending = wait(pending, timeout=120.0, return_when=FIRST_COMPLETED)
            for fut in finished:
                shards.append(fut.result())
                done += 1
                pct = min(95, int(95 * done / workers))
                msg = f"Preflop CFR: shard {done}/{workers} finished"
                log.info(msg)
                if progress:
                    progress({"pct": pct, "msg": msg, "detail": {"workers": workers, "shards_done": done}})
            if not finished and pending:
                wait_msg = f"Preflop CFR: still solving ({done}/{workers} shards done)"
                log.info(wait_msg)
                if progress:
                    progress({
                        "pct": max(7, int(95 * done / workers)),
                        "msg": wait_msg,
                        "detail": {"workers": workers, "shards_done": done},
                    })
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)
        raise
    pool.shutdown(wait=True)
    if progress:
        progress({"pct": 96, "msg": "Merging regret tables…", "detail": {"shards_done": done}})
    return merge_regret_shards(shards, min_mass=prune_min_mass)


def solve_preflop_parallel(
    *,
    num_players: int,
    iterations: int,
    chance_samples: int,
    seed: int,
    max_raises: int,
    workers: int,
    equity_mode: EquityMode = "random",
    equity_mc_samples: int = 2000,
    prune_min_mass: float = 0.0,
    progress: ProgressFn = None,
) -> dict[str, np.ndarray]:
    """Run ``workers`` independent CFR shards and merge tabular strategies."""
    if workers <= 1:
        from poker_ai.solver.solve_preflop import _run_solver

        return _run_solver(
            num_players=num_players,
            iterations=iterations,
            chance_samples=chance_samples,
            seed=seed,
            max_raises=max_raises,
            equity_mode=equity_mode,
            equity_mc_samples=equity_mc_samples,
            prune_min_mass=prune_min_mass,
        )

    # ProcessPoolExecutor deadlocks on Windows (spawn + 8× heavy re-import).
    # Subprocess-per-shard from a real main process (CLI or isolated job child) works.
    if sys.platform == "win32":
        log.info("Windows: subprocess-per-shard CFR (%s shards)", workers)
        return _solve_shards_subprocess(
            num_players=num_players,
            iterations=iterations,
            chance_samples=chance_samples,
            seed=seed,
            max_raises=max_raises,
            workers=workers,
            equity_mode=equity_mode,
            equity_mc_samples=equity_mc_samples,
            prune_min_mass=prune_min_mass,
            progress=progress,
        )

    return _solve_shards_processpool(
        num_players=num_players,
        iterations=iterations,
        chance_samples=chance_samples,
        seed=seed,
        max_raises=max_raises,
        workers=workers,
        equity_mode=equity_mode,
        equity_mc_samples=equity_mc_samples,
        prune_min_mass=prune_min_mass,
        progress=progress,
    )
