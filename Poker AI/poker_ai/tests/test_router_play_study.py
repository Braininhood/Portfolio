"""RouterPolicy play-study promotion (Phase W7 / W12)."""

from __future__ import annotations

from pathlib import Path

import pytest

from poker_ai.policy.router_sources import (
    get_router_status,
    play_study_artifact_dir,
    promote_play_study_to_router,
    resolve_router_student_dir,
    rollback_router_play_study,
)


def _write_student(dir_path: Path) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "student.safetensors").write_bytes(b"stub")


def test_resolve_router_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    student = tmp_path / "artifacts" / "student" / "v1"
    _write_student(student)
    assert resolve_router_student_dir("hu").resolve() == student.resolve()


def test_promote_play_study_to_router(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    hu = play_study_artifact_dir("hu")
    mw = play_study_artifact_dir("multiway")
    _write_student(hu)
    _write_student(mw)

    status = promote_play_study_to_router(hu=True, multiway=True, confirm=True)
    assert status.hu.play_study is True
    assert status.multiway.play_study is True
    assert resolve_router_student_dir("hu").resolve() == hu.resolve()
    assert resolve_router_student_dir("multiway").resolve() == mw.resolve()


def test_promote_requires_confirm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_student(play_study_artifact_dir("hu"))
    with pytest.raises(ValueError, match="confirm"):
        promote_play_study_to_router(hu=True, multiway=False, confirm=False)
