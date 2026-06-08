"""Nightly retrain scheduling — Windows Task Scheduler / cron (Phase W8 Day 35)."""

from __future__ import annotations

import json
import platform
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

Frequency = Literal["daily", "weekly"]

# CLI args after ``python -m poker_ai`` (must match Typer commands).
JOB_CLI_ARGS: dict[str, str] = {
    "features_build": "features build",
    "train_hhformer": "train hhformer",
    "train_multiway_student": "train multiway-student",
    "train_student": "train student",
    "league_run": "league run",
}

SCHEDULABLE_JOB_TYPES = frozenset(JOB_CLI_ARGS.keys())

NIGHTLY_BUNDLE: list[tuple[str, str, Frequency, str | None]] = [
    ("features_build", "00:00", "daily", None),
    ("train_hhformer", "00:15", "daily", None),
    ("train_multiway_student", "00:45", "daily", None),
    ("train_student", "01:00", "weekly", "SUN"),
    ("league_run", "02:00", "daily", None),
]

_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
_DOW = frozenset({"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"})


@dataclass
class ScheduleEntry:
    job_type: str
    enabled: bool
    time_local: str
    frequency: Frequency
    day_of_week: str | None = None
    os_task_name: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _poker_ai_root() -> Path:
    # runtime/job_schedule.py → poker_ai package → src → project root (pyproject.toml)
    return Path(__file__).resolve().parents[3]


def _schedule_dir() -> Path:
    d = _poker_ai_root() / "data" / "schedule"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _config_path() -> Path:
    return _schedule_dir() / "config.json"


def _tasks_dir() -> Path:
    d = _schedule_dir() / "tasks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _logs_dir() -> Path:
    d = _schedule_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def task_name(job_type: str) -> str:
    return f"PokerAI_{job_type}"


def _validate_time(time_local: str) -> str:
    m = _TIME_RE.match(time_local.strip())
    if not m:
        raise ValueError("time_local must be HH:MM (24-hour)")
    return f"{int(m.group(1)):02d}:{m.group(2)}"


def _validate_frequency(freq: str) -> Frequency:
    f = freq.strip().lower()
    if f not in ("daily", "weekly"):
        raise ValueError("frequency must be 'daily' or 'weekly'")
    return f  # type: ignore[return-value]


def _validate_dow(day: str | None) -> str | None:
    if day is None:
        return None
    d = day.strip().upper()
    if d not in _DOW:
        raise ValueError(f"day_of_week must be one of {sorted(_DOW)}")
    return d


def load_config() -> dict[str, Any]:
    path = _config_path()
    if not path.is_file():
        return {"entries": [], "nightly_enabled": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"entries": [], "nightly_enabled": False}
    if not isinstance(data, dict):
        return {"entries": [], "nightly_enabled": False}
    return data


def save_config(data: dict[str, Any]) -> None:
    data["updated_at"] = datetime.now(UTC).isoformat()
    _config_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def _entry_from_dict(raw: dict[str, Any]) -> ScheduleEntry:
    return ScheduleEntry(
        job_type=str(raw["job_type"]),
        enabled=bool(raw.get("enabled", False)),
        time_local=str(raw.get("time_local", "00:00")),
        frequency=_validate_frequency(str(raw.get("frequency", "daily"))),
        day_of_week=raw.get("day_of_week"),
        os_task_name=raw.get("os_task_name") or task_name(str(raw["job_type"])),
        updated_at=raw.get("updated_at"),
    )


def _entries_from_config(data: dict[str, Any]) -> dict[str, ScheduleEntry]:
    out: dict[str, ScheduleEntry] = {}
    for raw in data.get("entries", []):
        if not isinstance(raw, dict) or "job_type" not in raw:
            continue
        jt = str(raw["job_type"])
        if jt not in SCHEDULABLE_JOB_TYPES:
            continue
        out[jt] = _entry_from_dict(raw)
    return out


def platform_name() -> str:
    return platform.system().lower()


def scheduler_available() -> bool:
    from shutil import which

    if platform_name() == "windows":
        return which("schtasks") is not None
    return which("crontab") is not None


def _write_task_script(job_type: str) -> Path:
    root = _poker_ai_root()
    python = Path(sys.executable).resolve()
    cli = JOB_CLI_ARGS[job_type]
    log_file = _logs_dir() / f"{job_type}.log"
    tasks = _tasks_dir()
    tname = task_name(job_type)

    if platform_name() == "windows":
        script = tasks / f"{tname}.cmd"
        content = (
            "@echo off\r\n"
            f'cd /d "{root}"\r\n'
            f'"{python}" -m poker_ai {cli} >> "{log_file}" 2>&1\r\n'
        )
        script.write_text(content, encoding="utf-8")
        return script

    script = tasks / f"{tname}.sh"
    content = (
        "#!/bin/sh\n"
        f'cd "{root}" || exit 1\n'
        f'"{python}" -m poker_ai {cli} >> "{log_file}" 2>&1\n'
    )
    script.write_text(content, encoding="utf-8", newline="\n")
    script.chmod(script.stat().st_mode | 0o111)
    return script


def _run_os_command(args: list[str]) -> None:
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(err or f"Command failed: {' '.join(args)}")


def _install_windows(entry: ScheduleEntry) -> None:
    script = _write_task_script(entry.job_type)
    time_local = _validate_time(entry.time_local)
    args = [
        "schtasks",
        "/create",
        "/tn",
        entry.os_task_name or task_name(entry.job_type),
        "/tr",
        str(script),
        "/sc",
        "weekly" if entry.frequency == "weekly" else "daily",
        "/st",
        time_local,
        "/f",
    ]
    if entry.frequency == "weekly":
        dow = _validate_dow(entry.day_of_week) or "SUN"
        args.extend(["/d", dow])
    _run_os_command(args)


def _remove_windows(task_name: str) -> None:
    try:
        _run_os_command(["schtasks", "/delete", "/tn", task_name, "/f"])
    except RuntimeError as exc:
        msg = str(exc).lower()
        if "cannot find" not in msg and "does not exist" not in msg:
            raise


def _cron_line(entry: ScheduleEntry, script: Path) -> str:
    hh, mm = _validate_time(entry.time_local).split(":")
    if entry.frequency == "weekly":
        dow = (_validate_dow(entry.day_of_week) or "SUN").upper()
        dow_map = {"SUN": "0", "MON": "1", "TUE": "2", "WED": "3", "THU": "4", "FRI": "5", "SAT": "6"}
        cron_dow = dow_map.get(dow, "0")
        schedule = f"{mm} {hh} * * {cron_dow}"
    else:
        schedule = f"{mm} {hh} * * *"
    name = entry.os_task_name or task_name(entry.job_type)
    return f"{schedule} {script} # {name}"


def _sync_crontab_from_config() -> None:
    data = load_config()
    entries = _entries_from_config(data)
    lines: list[str] = [
        "# Poker AI nightly retrain — managed by POST /jobs/schedule",
        "# Edit via Setup wizard, not by hand.",
        "",
    ]
    for entry in entries.values():
        if not entry.enabled:
            continue
        script = _tasks_dir() / f"{task_name(entry.job_type)}.sh"
        if not script.is_file():
            _write_task_script(entry.job_type)
        lines.append(_cron_line(entry, script))
    cron_file = _schedule_dir() / "crontab.txt"
    cron_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not scheduler_available():
        return
    proc = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
    existing = proc.stdout if proc.returncode == 0 else ""
    kept = [
        ln
        for ln in existing.splitlines()
        if ln.strip() and not ln.strip().startswith("# Poker AI") and "# PokerAI_" not in ln
    ]
    merged = kept + ([""] if kept else []) + lines
    install = _schedule_dir() / "crontab.install.txt"
    install.write_text("\n".join(merged) + "\n", encoding="utf-8")
    _run_os_command(["crontab", str(install)])


def os_task_installed(name: str) -> bool:
    if platform_name() == "windows":
        proc = subprocess.run(
            ["schtasks", "/query", "/tn", name],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode == 0
    cron_file = _schedule_dir() / "crontab.txt"
    if not cron_file.is_file():
        return False
    return name in cron_file.read_text(encoding="utf-8")


def install_os_schedule(entry: ScheduleEntry) -> None:
    if not entry.enabled:
        remove_os_schedule(entry.os_task_name or task_name(entry.job_type))
        return
    if platform_name() == "windows":
        _install_windows(entry)
    elif platform_name() in ("linux", "darwin"):
        _write_task_script(entry.job_type)
        _sync_crontab_from_config()
    else:
        raise RuntimeError(f"Scheduling not supported on {platform.system()}")


def remove_os_schedule(name: str) -> None:
    if platform_name() == "windows":
        _remove_windows(name)
    elif platform_name() in ("linux", "darwin"):
        _sync_crontab_from_config()


def upsert_schedule_entry(
    *,
    job_type: str,
    enabled: bool,
    time_local: str = "00:00",
    frequency: str = "daily",
    day_of_week: str | None = None,
) -> ScheduleEntry:
    if job_type not in SCHEDULABLE_JOB_TYPES:
        raise ValueError(
            f"Unknown schedulable job '{job_type}'. Allowed: {', '.join(sorted(SCHEDULABLE_JOB_TYPES))}"
        )

    freq = _validate_frequency(frequency)
    entry = ScheduleEntry(
        job_type=job_type,
        enabled=enabled,
        time_local=_validate_time(time_local),
        frequency=freq,
        day_of_week=_validate_dow(day_of_week) if freq == "weekly" else None,
        os_task_name=task_name(job_type),
        updated_at=datetime.now(UTC).isoformat(),
    )

    data = load_config()
    entries = _entries_from_config(data)
    entries[job_type] = entry
    data["entries"] = [e.to_dict() for e in sorted(entries.values(), key=lambda x: x.job_type)]
    save_config(data)

    if scheduler_available():
        install_os_schedule(entry)
    return entry


def set_nightly_bundle(*, enabled: bool, start_time: str = "00:00") -> list[ScheduleEntry]:
    base_h, base_m = map(int, _validate_time(start_time).split(":"))
    base_minutes = base_h * 60 + base_m
    offsets = [0, 15, 45, 60, 120]
    results: list[ScheduleEntry] = []

    data = load_config()
    entries = _entries_from_config(data)

    for (job_type, _default_time, frequency, dow), offset in zip(NIGHTLY_BUNDLE, offsets, strict=True):
        total = base_minutes + offset
        hh = (total // 60) % 24
        mm = total % 60
        time_local = f"{hh:02d}:{mm:02d}"
        entry = ScheduleEntry(
            job_type=job_type,
            enabled=enabled,
            time_local=time_local,
            frequency=frequency,
            day_of_week=dow if frequency == "weekly" else None,
            os_task_name=task_name(job_type),
            updated_at=datetime.now(UTC).isoformat(),
        )
        entries[job_type] = entry
        results.append(entry)
        if scheduler_available():
            install_os_schedule(entry)

    data["entries"] = [e.to_dict() for e in sorted(entries.values(), key=lambda x: x.job_type)]
    data["nightly_enabled"] = enabled
    data["nightly_start_time"] = _validate_time(start_time)
    save_config(data)
    return results


def list_schedule_entries() -> tuple[list[ScheduleEntry], bool, str | None]:
    data = load_config()
    entries_map = _entries_from_config(data)
    out: list[ScheduleEntry] = []
    for jt in sorted(SCHEDULABLE_JOB_TYPES):
        if jt in entries_map:
            out.append(entries_map[jt])
        else:
            out.append(
                ScheduleEntry(
                    job_type=jt,
                    enabled=False,
                    time_local="00:00",
                    frequency="daily",
                    os_task_name=task_name(jt),
                )
            )
    nightly = bool(data.get("nightly_enabled", False))
    msg: str | None = None
    if not scheduler_available():
        msg = (
            "OS scheduler not found (schtasks on Windows, crontab on Linux/macOS). "
            "Schedule config is saved; install tasks manually from data/schedule/."
        )
    return out, nightly, msg
