"""Run a full ``solve_preflop`` job in an isolated process (Windows API parity with CLI).

The FastAPI job queue runs work in a ``asyncio.to_thread`` worker. On Windows,
``ProcessPoolExecutor`` deadlocks in that context. The CLI works because it runs
in a normal main process.

Usage (from job_runner)::

    python -m poker_ai.solver.preflop_job_isolated <config.json>

Config JSON fields match ``_job_solve_preflop`` params plus:
  - ``progress_path``: NDJSON file (one progress event per line)
  - ``result_path``: JSON file written on success
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def _param_bool(val: Any, default: bool = False) -> bool:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in ("1", "true", "yes", "on"):
        return True
    if s in ("0", "false", "no", "off", ""):
        return False
    return default


def run_from_config(cfg: dict[str, Any]) -> dict[str, Any]:
    """Execute solve + save policy; append progress events to ``progress_path``."""
    from poker_ai.policy.cfr_policy import CFRPolicy
    from poker_ai.solver.preflop_equity import EquityMode
    from poker_ai.solver.solve_preflop import resolve_solve_config, solve_preflop

    progress_path = Path(str(cfg["progress_path"]))
    result_path = Path(str(cfg["result_path"]))
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text("", encoding="utf-8")

    def emit(event: dict[str, Any]) -> None:
        with progress_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, separators=(",", ":")) + "\n")

    from poker_ai.solver.solve_preflop import parse_table_seats, resolve_solve_config

    positions = str(cfg.get("positions", "6max"))
    num_players = parse_table_seats(positions)
    eq_raw = str(cfg.get("equity_mode", "random")).lower()
    eq_mode: EquityMode = "real" if eq_raw == "real" else "random"
    production = _param_bool(cfg.get("production"), False)
    requested_iters = int(cfg.get("iters", 20_000))
    resolved = resolve_solve_config(
        num_players=num_players,
        iterations=requested_iters,
        chance_samples=int(cfg.get("chance_samples", 64)),
        equity_mode=eq_mode,
        prune_min_mass=float(cfg.get("prune_min_mass", 5.0)),
        production=production,
    )
    if production and resolved.iterations != requested_iters:
        emit(
            {
                "pct": 1,
                "msg": (
                    f"production=True: CFR iterations {requested_iters:,} → "
                    f"{resolved.iterations:,}"
                ),
                "detail": {
                    "requested_iters": requested_iters,
                    "effective_iters": resolved.iterations,
                },
            }
        )

    output = Path(str(cfg.get("output", "artifacts/solver/preflop_cfr.json")))
    if num_players == 2 and output.name == "preflop_cfr.json":
        output = Path(
            str(
                cfg.get(
                    "output_hu",
                    "artifacts/solver/preflop_hu_real.json"
                    if eq_mode == "real"
                    else "artifacts/solver/preflop_hu.json",
                )
            )
        )

    workers = int(cfg.get("workers", 1))
    emit(
        {
            "pct": 2,
            "msg": f"Isolated preflop job (CLI-equivalent process, {workers} workers)",
            "detail": {"workers": workers, "isolated": True},
        }
    )

    result = solve_preflop(
        num_players=num_players,
        iterations=resolved.iterations,
        chance_samples=resolved.chance_samples,
        seed=int(cfg.get("seed", 42)),
        max_raises=int(cfg.get("max_raises", 1)),
        workers=workers,
        measure_exploitability=_param_bool(cfg.get("measure_exploitability"), False),
        equity_mode=resolved.equity_mode,
        equity_mc_samples=int(cfg.get("equity_mc_samples", 2000)),
        production=production,
        prune_min_mass=resolved.prune_min_mass,
        progress=emit,
    )

    policy = CFRPolicy(
        strategy=result.strategy,
        equity_mode=result.equity_mode,
        equity_mc_samples=result.equity_mc_samples,
    )
    exp = result.exploitability_mbb if result.exploitability_mbb is not None else -1.0
    policy.save_json(
        output,
        iterations=result.iterations,
        exploitability_mbb=exp,
        equity_mode=result.equity_mode,
        equity_mc_samples=result.equity_mc_samples,
    )

    out = {
        "output": str(output.resolve()),
        "info_sets": result.num_info_sets,
        "iterations": result.iterations,
        "workers": result.workers,
    }
    result_path.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    emit({"pct": 100, "msg": "Complete", "detail": out})
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m poker_ai.solver.preflop_job_isolated <config.json>", file=sys.stderr)
        raise SystemExit(2)
    os.environ["POKER_AI_PREFLOP_ISOLATED"] = "1"
    cfg_path = Path(sys.argv[1])
    cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
    try:
        run_from_config(cfg)
    except Exception as exc:
        err_path = cfg_path.with_suffix(".error.txt")
        err_path.write_text(str(exc), encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
