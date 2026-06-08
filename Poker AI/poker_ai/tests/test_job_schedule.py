"""Tests for nightly job scheduling (W8 Day 35)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from poker_ai.runtime import job_schedule


@pytest.fixture
def schedule_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "poker_ai_pkg"
    root.mkdir()
    sched = root / "data" / "schedule"
    sched.mkdir(parents=True)
    monkeypatch.setattr(job_schedule, "_poker_ai_root", lambda: root)
    return root


def test_validate_time() -> None:
    assert job_schedule._validate_time("00:00") == "00:00"
    assert job_schedule._validate_time("9:05") == "09:05"
    with pytest.raises(ValueError):
        job_schedule._validate_time("25:00")


def test_upsert_saves_config(schedule_env: Path) -> None:
    entry = job_schedule.upsert_schedule_entry(
        job_type="features_build",
        enabled=True,
        time_local="01:30",
        frequency="daily",
    )
    assert entry.job_type == "features_build"
    cfg = json.loads((schedule_env / "data" / "schedule" / "config.json").read_text())
    assert len(cfg["entries"]) == 1
    assert cfg["entries"][0]["time_local"] == "01:30"


def test_set_nightly_bundle_stagger(schedule_env: Path) -> None:
    with patch.object(job_schedule, "scheduler_available", return_value=False):
        entries = job_schedule.set_nightly_bundle(enabled=True, start_time="00:00")
    assert len(entries) == 5
    times = {e.job_type: e.time_local for e in entries}
    assert times["features_build"] == "00:00"
    assert times["train_hhformer"] == "00:15"
    assert times["train_multiway_student"] == "00:45"
    assert times["train_student"] == "01:00"
    assert times["league_run"] == "02:00"
    cfg = job_schedule.load_config()
    assert cfg["nightly_enabled"] is True


def test_write_task_script_windows(schedule_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(job_schedule, "platform_name", lambda: "windows")
    path = job_schedule._write_task_script("features_build")
    assert path.suffix == ".cmd"
    text = path.read_text(encoding="utf-8")
    assert "features build" in text
    assert "-m poker_ai" in text


def test_install_windows_calls_schtasks(schedule_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(job_schedule, "platform_name", lambda: "windows")
    calls: list[list[str]] = []

    def fake_os_command(args: list[str]) -> None:
        calls.append(args)

    monkeypatch.setattr(job_schedule, "_run_os_command", fake_os_command)
    entry = job_schedule.ScheduleEntry(
        job_type="features_build",
        enabled=True,
        time_local="00:00",
        frequency="daily",
        os_task_name="PokerAI_features_build",
    )
    job_schedule.install_os_schedule(entry)
    assert any(c[0] == "schtasks" and "/create" in c for c in calls)


def test_unknown_job_type_rejected(schedule_env: Path) -> None:
    with pytest.raises(ValueError, match="Unknown schedulable"):
        job_schedule.upsert_schedule_entry(job_type="not_a_job", enabled=True)
