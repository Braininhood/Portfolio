"""Playbook orchestrator — queue DB-heavy jobs; monitor long-running tasks.

Runs equity backfill after multiway train exits (avoids SQLite lock vs API/ingest).
Logs to reports/playbook_logs/playbook_orchestrator.log
"""
from __future__ import annotations

import json
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


def log(msg: str) -> None:
    line = f"{datetime.now(UTC).isoformat()} {msg}"
    for name in ("playbook_orchestrator.log", "playbook_full.log"):
        path = LOG_DIR / name
        try:
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass
    print(line, flush=True)


def write_status(**fields: object) -> None:
    data: dict[str, object] = {}
    if STATUS.is_file():
        data = json.loads(STATUS.read_text(encoding="utf-8"))
    data.update(fields)
    data["updated_at"] = datetime.now(UTC).isoformat()
    STATUS.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run_cmd(args: list[str], log_name: str) -> int:
    out = LOG_DIR / log_name
    err = LOG_DIR / log_name.replace(".log", ".err.log")
    with out.open("a", encoding="utf-8") as fo, err.open("a", encoding="utf-8") as fe:
        fo.write(f"\n=== {' '.join(args)} ===\n")
        fo.flush()
        return subprocess.call([str(PY), *args], cwd=str(ROOT), stdout=fo, stderr=fe)


def _matching_pids(pattern: str) -> list[int]:
    if sys.platform == "win32":
        ps = (
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" "
            f"| Where-Object {{ $_.CommandLine -match '{pattern}' }} "
            "| Select-Object -ExpandProperty ProcessId"
        )
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            check=False,
        )
        return [int(x) for x in out.stdout.split() if x.strip().isdigit()]
    try:
        import psutil  # type: ignore[import-untyped]

        return [
            int(p.info["pid"])
            for p in psutil.process_iter(["pid", "cmdline"])
            if p.info.get("cmdline") and pattern in " ".join(p.info["cmdline"])
        ]
    except ImportError:
        return []


def wait_for_pattern_gone(pattern: str, *, label: str, timeout_sec: float = 86400.0) -> None:
    t0 = time.time()
    empty_streak = 0
    while time.time() - t0 < timeout_sec:
        pids = _matching_pids(pattern)
        if not pids:
            empty_streak += 1
            if empty_streak >= 3:
                log(f"{label} finished (3 empty polls)")
                return
        else:
            empty_streak = 0
            log(f"waiting for {label} pids={pids[:5]}")
        time.sleep(60)
    log(f"{label} wait timeout — proceeding anyway")


def main() -> int:
    write_status(phase="orchestrator_started")
    log("orchestrator: wait for multiway train, then equity backfill")
    wait_for_pattern_gone("multiway-student", label="multiway train")
    write_status(equity_backfill="running")
    rc = run_cmd(["-m", "poker_ai", "equity", "backfill"], "equity_backfill.log")
    write_status(equity_backfill="done" if rc == 0 else f"failed_exit_{rc}")
    log(f"equity backfill exit {rc}")
    if rc != 0:
        return rc
    # 9/10-max preflop after 8-max parent exits
    log("orchestrator: waiting for 8max preflop, then 9max/10max")
    wait_for_pattern_gone("preflop.*8max|positions 8max", label="preflop 8max")
    for fmt in ("9max", "10max"):
        write_status(**{f"preflop_{fmt}": "running"})
        rc = run_cmd(
            ["-m", "poker_ai", "solve", "preflop", "--positions", fmt, "--production"],
            f"preflop_{fmt}.log",
        )
        write_status(**{f"preflop_{fmt}": "done" if rc == 0 else f"failed_{rc}"})
        if rc != 0:
            return rc
    write_status(phase="orchestrator_complete")
    log("orchestrator complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
