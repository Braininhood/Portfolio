"""Tests for W8 dataset versioning and changepoint helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from poker_ai.learn.changepoint import (
    ChangepointAlert,
    changepoint_for_player,
    detect_changepoints,
    save_changepoints,
)
from poker_ai.learn.dataset_versioning import (
    list_snapshots,
    record_snapshot,
    set_active_version,
)


@pytest.fixture
def version_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "pkg"
    root.mkdir()
    monkeypatch.chdir(root)
    (root / "data" / "processed").mkdir(parents=True)
    (root / "data" / "drift").mkdir(parents=True)
    return root


def test_record_and_list_snapshot(version_env: Path) -> None:
    feat = version_env / "features.jsonl"
    feat.write_text('{"hand_id":1}\n{"hand_id":2}\n', encoding="utf-8")
    snap = record_snapshot(feat, version="2026-05-31")
    assert snap.num_features == 2
    assert any(s.version == "2026-05-31" for s in list_snapshots())


def test_set_active_version(version_env: Path) -> None:
    feat = version_env / "features.jsonl"
    feat.write_text("{}\n", encoding="utf-8")
    record_snapshot(feat, version="2026-05-30")
    active = set_active_version("2026-05-30")
    assert active.is_active


def test_changepoint_filter_by_player(version_env: Path) -> None:
    alerts = [
        ChangepointAlert("uid_a", "Alice", "2026-05-01", "shift", 0.8),
        ChangepointAlert("uid_b", "Bob", "2026-05-02", "shift", 0.7),
    ]
    save_changepoints(alerts)
    assert len(detect_changepoints(player_uid="uid_a")) == 1
    assert changepoint_for_player("uid_b") is not None
    assert changepoint_for_player("missing") is None
