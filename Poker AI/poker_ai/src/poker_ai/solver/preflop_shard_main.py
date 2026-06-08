"""Subprocess entry: one CFR shard. Must stay import-light; env vars set before poker imports."""

from __future__ import annotations

import json
import sys


def main() -> None:
    cfg: dict = json.load(sys.stdin)
    out_path = str(cfg.pop("out_path"))

    from poker_ai.solver.preflop_shard import run_shard

    result = run_shard(
        num_players=int(cfg["num_players"]),
        iterations=int(cfg["iterations"]),
        chance_samples=int(cfg["chance_samples"]),
        seed=int(cfg["seed"]),
        max_raises=int(cfg["max_raises"]),
        shard_id=int(cfg["shard_id"]),
        num_shards=int(cfg["num_shards"]),
        equity_mode=cfg["equity_mode"],
        equity_mc_samples=int(cfg["equity_mc_samples"]),
    )
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh)
    sys.stdout.write(out_path)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
