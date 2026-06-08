"""Single CFR shard — imported by CLI pool workers and subprocess shard children."""

from __future__ import annotations

from typing import Any, cast

from poker_ai.solver.cfr import CFRPlusSolver, ExternalSamplingMCCFRSolver
from poker_ai.solver.game import ExtensiveGame
from poker_ai.solver.preflop import PreflopAbstractionGame
from poker_ai.solver.preflop_equity import EquityMode


def run_shard(
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
    per = max(1, chance_samples // num_shards)
    remainder = chance_samples - per * (num_shards - 1)
    samples = remainder if shard_id == num_shards - 1 else per
    game = PreflopAbstractionGame(
        num_players=num_players,
        chance_samples=samples,
        seed=seed + shard_id * 17_371,
        max_raises=max_raises,
        equity_mode=equity_mode,
        equity_mc_samples=equity_mc_samples,
    )
    ext = cast(ExtensiveGame, game)
    if num_players > 2:
        solver = ExternalSamplingMCCFRSolver(ext, seed=seed + shard_id)
    else:
        solver = CFRPlusSolver(ext, seed=seed + shard_id)
    solver.run(iterations)
    return {
        key: (reg.tolist(), ssum.tolist(), n_act)
        for key, (reg, ssum, n_act) in solver.export_nodes().items()
    }
