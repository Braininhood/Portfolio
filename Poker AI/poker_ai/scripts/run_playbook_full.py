"""Run the full production playbook sequentially (with league in parallel).

Order:
  1. Wait for / finish equity backfill
  2. Full multiway student train
  3. League 6 h (background subprocess)
  4. Preflop 8 / 9 / 10-max production solves (skip if artifact exists)
  5. Phase 1 ingest perf gate (when prior steps released CPU)

Status: reports/playbook_logs/playbook_status.json
Logs:   reports/playbook_logs/*.log
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "reports" / "playbook_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
PY = ROOT / ".venv" / "Scripts" / "python.exe"
STATUS = LOG_DIR / "playbook_status.json"

# Import shared helpers from orchestrator module
sys.path.insert(0, str(ROOT / "scripts"))
from playbook_orchestrator import (  # noqa: E402
    _matching_pids,
    log,
    run_cmd,
    wait_for_pattern_gone,
    write_status,
)


def _artifact(path: str) -> Path:
    return ROOT / path


def _log_mtime(path: Path) -> float | None:
    return path.stat().st_mtime if path.is_file() else None


def wait_for_log_progress(log_path: Path, *, stall_sec: float = 1800.0, poll_sec: float = 60.0) -> None:
    """Wait while log file keeps growing; abort wait if stalled ``stall_sec``."""
    log(f"monitor {log_path.name} (stall={stall_sec}s)")
    last_size = -1
    last_change = time.time()
    while True:
        pids = _matching_pids("equity backfill")
        if not pids:
            log(f"{log_path.name}: no backfill process")
            return
        size = log_path.stat().st_size if log_path.is_file() else 0
        if size != last_size:
            last_size = size
            last_change = time.time()
        elif time.time() - last_change > stall_sec:
            log(f"{log_path.name}: stalled — continuing pipeline")
            return
        time.sleep(poll_sec)


def start_league_background() -> subprocess.Popen[bytes] | None:
    log_path = LOG_DIR / "league_6h.log"
    err_path = LOG_DIR / "league_6h.err.log"
    if _matching_pids("until-hours"):
        log("league 6h already running")
        return None
    fo = log_path.open("a", encoding="utf-8")
    fe = err_path.open("a", encoding="utf-8")
    fo.write(f"\n=== league run --until-hours 6 ({datetime.now(UTC).isoformat()}) ===\n")
    fo.flush()
    proc = subprocess.Popen(
        [
            str(PY),
            "-u",
            "-m",
            "poker_ai",
            "league",
            "run",
            "--until-hours",
            "6",
            "--hands-per-matchup",
            "200",
            "--workers",
            "16",
            "--until-hu",
            "--table-sizes",
            "hu,6max,9max",
        ],
        cwd=str(ROOT),
        stdout=fo,
        stderr=fe,
    )
    log(f"league 6h started pid={proc.pid}")
    write_status(phase9_league_6h="running", league_pid=proc.pid)
    return proc


def run_preflop(fmt: str) -> int:
    art = _artifact(f"artifacts/solver/preflop_{fmt}.json")
    if art.is_file() and art.stat().st_size > 1000:
        log(f"preflop {fmt} artifact exists — skip")
        write_status(**{f"preflop_{fmt}": "done_skipped"})
        return 0
    write_status(**{f"preflop_{fmt}": "running"})
    rc = run_cmd(
        ["-m", "poker_ai", "solve", "preflop", "--positions", fmt, "--production"],
        f"preflop_{fmt}.log",
    )
    write_status(**{f"preflop_{fmt}": "done" if rc == 0 else f"failed_{rc}"})
    return rc


def run_phase1_perf() -> int:
    write_status(phase1_ingest_perf="running")
    env = os.environ.copy()
    env["POKER_AI_PERF_INGEST"] = "1"
    env["POKER_AI_CORPUS_ROOT"] = str(ROOT.parent / "hand" / "6")
    env["POKER_AI_PERF_BUDGET_SEC"] = "90"
    out = LOG_DIR / "phase1_perf.log"
    err = LOG_DIR / "phase1_perf.err.log"
    with out.open("a", encoding="utf-8") as fo, err.open("a", encoding="utf-8") as fe:
        fo.write(f"\n=== phase1 perf ({datetime.now(UTC).isoformat()}) ===\n")
        rc = subprocess.call(
            [str(PY), "-m", "pytest", "tests/test_ingest_perf.py", "-v", "--tb=line"],
            cwd=str(ROOT),
            stdout=fo,
            stderr=fe,
            env=env,
        )
    write_status(phase1_ingest_perf="done" if rc == 0 else f"failed_{rc}")
    return rc


def main() -> int:
    write_status(phase="playbook_full_started", started_at=datetime.now(UTC).isoformat())

    # --- 1. Equity backfill ---
    if _matching_pids("equity backfill"):
        log("step 1: waiting for in-flight equity backfill")
        write_status(production_equity_backfill="running_wait")
        wait_for_log_progress(LOG_DIR / "equity_backfill.log")
        wait_for_pattern_gone("equity backfill", label="equity backfill")
    write_status(production_equity_backfill="running")
    rc = run_cmd(["-m", "poker_ai", "equity", "backfill"], "equity_backfill.log")
    write_status(production_equity_backfill="done" if rc == 0 else f"failed_{rc}")
    log(f"equity backfill exit {rc}")
    if rc != 0:
        log("backfill failed — continuing with remaining steps")

    # --- 2. Multiway train ---
    write_status(phase7b_multiway_train="running")
    rc = run_cmd(
        [
            "-m",
            "poker_ai",
            "train",
            "multiway-student",
            "--epochs",
            "25",
            "--row-limit",
            "500000",
            "--device",
            "cuda",
            "--batch-size",
            "64",
        ],
        "multiway_train.log",
    )
    write_status(phase7b_multiway_train="done" if rc == 0 else f"failed_{rc}")
    log(f"multiway train exit {rc}")

    # --- 3. League 6 h (background) ---
    start_league_background()

    # --- 4. Preflop ring solves ---
    for fmt in ("8max", "9max", "10max"):
        wait_for_pattern_gone("preflop_shard", label="orphan preflop shards")
        rc = run_preflop(fmt)
        if rc != 0:
            log(f"preflop {fmt} failed exit {rc}")

    # --- 5. Phase 1 perf (CPU idle-ish) ---
    rc = run_phase1_perf()
    log(f"phase1 perf exit {rc}")

    write_status(phase="playbook_full_finished", finished_at=datetime.now(UTC).isoformat())
    log("playbook full pipeline finished (league may still run in background)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
