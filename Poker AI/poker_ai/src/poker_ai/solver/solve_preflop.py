"""Preflop CFR+ driver used by the CLI (Phase 6)."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import cast

import numpy as np

log = logging.getLogger(__name__)

from poker_ai.policy.cfr_policy import CFRPolicy, TabularStrategy
from poker_ai.runtime.workers import resolve_worker_count
from poker_ai.solver.cfr import CFRPlusSolver, ExternalSamplingMCCFRSolver
from poker_ai.solver.exploitability import exploitability_mbb_per_game
from poker_ai.solver.game import ExtensiveGame
from poker_ai.solver.parallel_cfr import _iterations_per_shard, solve_preflop_parallel
from poker_ai.solver.preflop import PreflopAbstractionGame
from poker_ai.runtime.progress import ProgressFn
from poker_ai.solver.preflop_equity import EquityMode, warm_combo_equity_table


@dataclass(frozen=True, slots=True)
class ResolvedSolveConfig:
    """Effective options after ``--production`` overrides."""

    equity_mode: EquityMode
    iterations: int
    chance_samples: int
    prune_min_mass: float


def parse_table_seats(positions: str) -> int:
    """Map CLI ``--positions`` to player count (2–10)."""
    p = positions.strip().lower().replace("_", "").replace("-", "")
    if p in {"hu", "headsup", "2max"}:
        return 2
    for n in (10, 9, 8, 6):
        if p in {f"{n}max", str(n)}:
            return n
    return 6


def resolve_solve_config(
    *,
    num_players: int,
    iterations: int,
    chance_samples: int,
    equity_mode: EquityMode,
    prune_min_mass: float,
    production: bool,
) -> ResolvedSolveConfig:
    eq = equity_mode
    it = iterations
    cs = chance_samples
    prune = prune_min_mass
    if production:
        eq = "real"
        prune = max(prune, 10.0)
        if num_players <= 2:
            it = max(it, 50_000)
            cs = max(cs, 32)
        else:
            it = max(it, 25_000)
            cs = min(cs, 32)
    return ResolvedSolveConfig(
        equity_mode=eq,
        iterations=it,
        chance_samples=cs,
        prune_min_mass=prune,
    )


@dataclass(frozen=True, slots=True)
class SolveResult:
    iterations: int
    exploitability_mbb: float | None
    num_info_sets: int
    strategy: TabularStrategy
    workers: int
    equity_mode: EquityMode
    equity_mc_samples: int


def _run_solver(
    *,
    num_players: int,
    iterations: int,
    chance_samples: int,
    seed: int,
    max_raises: int,
    equity_mode: EquityMode,
    equity_mc_samples: int,
    prune_min_mass: float = 0.0,
) -> dict[str, np.ndarray]:
    game = PreflopAbstractionGame(
        num_players=num_players,
        chance_samples=chance_samples,
        seed=seed,
        max_raises=max_raises,
        equity_mode=equity_mode,
        equity_mc_samples=equity_mc_samples,
    )
    ext_game = cast(ExtensiveGame, game)
    if num_players > 2:
        solver = ExternalSamplingMCCFRSolver(ext_game, seed=seed)
    else:
        solver = CFRPlusSolver(ext_game, seed=seed)

    batch = max(1, min(iterations, 5000))
    done = 0
    while done < iterations:
        step = min(batch, iterations - done)
        solver.run(step)
        done += step
    return solver.average_strategy(min_mass=prune_min_mass)


def solve_preflop(
    *,
    num_players: int = 6,
    iterations: int = 100_000,
    chance_samples: int = 64,
    seed: int = 42,
    log_every: int = 0,
    max_raises: int = 1,
    workers: int | None = None,
    measure_exploitability: bool = False,
    equity_mode: EquityMode = "random",
    equity_mc_samples: int = 2000,
    prune_min_mass: float = 5.0,
    production: bool = False,
    progress: ProgressFn = None,
) -> SolveResult:
    """Run CFR on the abstracted preflop tree and return the average strategy."""
    cfg = resolve_solve_config(
        num_players=num_players,
        iterations=iterations,
        chance_samples=chance_samples,
        equity_mode=equity_mode,
        prune_min_mass=prune_min_mass,
        production=production,
    )
    equity_mode = cfg.equity_mode
    iterations = cfg.iterations
    chance_samples = cfg.chance_samples
    prune_min_mass = cfg.prune_min_mass

    log.info(
        "solve_preflop num_players=%s iterations=%s chance_samples=%s equity_mode=%s production=%s",
        num_players,
        iterations,
        chance_samples,
        equity_mode,
        production,
    )

    explicit_workers = workers
    n_workers = resolve_worker_count(workers)
    if sys.platform == "win32" and explicit_workers is None and n_workers > 1:
        n_workers = 1
        log.info(
            "Windows: Auto uses single-process CFR (pick workers 2–10 in Tasks for parallel; win32 = Windows OS tag, not 32-bit)"
        )
        if progress:
            progress(
                {
                    "pct": 1,
                    "msg": "Windows: single-process CFR (pick 8–10 CPU workers in Configure for parallel)",
                    "detail": {"workers": 1, "platform": "win32"},
                }
            )
    if equity_mode == "real":
        if progress:
            progress(
                {
                    "pct": 2,
                    "msg": f"Building preflop equity table (MC samples={equity_mc_samples})…",
                    "detail": {"equity_mode": equity_mode, "equity_mc_samples": equity_mc_samples},
                }
            )
        log.info(
            "equity_mode=real mc_samples=%s (CPU Numba; cache under artifacts/solver/cache/)",
            equity_mc_samples,
        )
        warm_combo_equity_table(equity_mc_samples)
        if progress:
            progress({"pct": 5, "msg": "Equity table ready — starting CFR…", "detail": {}})
    game = PreflopAbstractionGame(
        num_players=num_players,
        chance_samples=chance_samples,
        seed=seed,
        max_raises=max_raises,
        equity_mode=equity_mode,
        equity_mc_samples=equity_mc_samples,
    )
    ext_game = cast(ExtensiveGame, game)

    if n_workers > 1:
        per = _iterations_per_shard(iterations, n_workers)
        if progress:
            progress(
                {
                    "pct": 6,
                    "msg": f"Starting parallel preflop CFR ({n_workers} workers, ~{per[0]} iters/shard)",
                    "detail": {"workers": n_workers, "iterations": iterations},
                }
            )
        log.info(
            "parallel workers=%s (~%s iters/shard; JSON after all shards finish)",
            n_workers,
            per[0],
        )
        raw = solve_preflop_parallel(
            num_players=num_players,
            iterations=iterations,
            chance_samples=chance_samples,
            seed=seed,
            max_raises=max_raises,
            workers=n_workers,
            equity_mode=equity_mode,
            equity_mc_samples=equity_mc_samples,
            prune_min_mass=prune_min_mass,
            progress=progress,
        )
    else:
        log.info("single-process preflop CFR (%s iterations)", iterations)
        if log_every > 0:
            log.info("single-process solve (log_every=%s)", log_every)
        done = 0
        batch = max(1, min(iterations, 500 if progress else 5000))
        if num_players > 2:
            solver = ExternalSamplingMCCFRSolver(ext_game, seed=seed)
        else:
            solver = CFRPlusSolver(ext_game, seed=seed)
        while done < iterations:
            step = min(batch, iterations - done)
            solver.run(step)
            done += step
            if progress:
                progress(
                    {
                        "pct": min(99, max(6, int(100 * done / iterations))),
                        "msg": f"Preflop CFR {done:,}/{iterations:,} iterations",
                        "detail": {"iterations_done": done, "iterations_total": iterations},
                    }
                )
            if log_every > 0 and done % log_every == 0:
                strat_np = solver.average_strategy()
                log.info("iter=%s info_sets=%s", done, len(strat_np))
        raw = solver.average_strategy(min_mass=prune_min_mass)
    strategy = _to_action_lists(raw)
    exp: float | None = None
    if measure_exploitability:
        max_roots = 24 if num_players > 2 else None
        exp = exploitability_mbb_per_game(
            ext_game,
            raw,
            big_blind=float(game.big_blind),
            max_chance_roots=max_roots,
        )
    return SolveResult(
        iterations=iterations,
        exploitability_mbb=exp,
        num_info_sets=len(strategy),
        strategy=strategy,
        workers=n_workers,
        equity_mode=equity_mode,
        equity_mc_samples=equity_mc_samples,
    )


def _to_action_lists(raw: dict[str, np.ndarray]) -> TabularStrategy:
    return {k: tuple(float(x) for x in v) for k, v in raw.items()}


def build_policy(result: SolveResult) -> CFRPolicy:
    return CFRPolicy(
        strategy=result.strategy,
        equity_mode=result.equity_mode,
        equity_mc_samples=result.equity_mc_samples,
    )
