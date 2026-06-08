"""W8 drift + model registry smoke tests."""

from __future__ import annotations

from pathlib import Path

import json

from poker_ai.learn.model_registry import get_model_info, list_models
from poker_ai.observability.drift import list_drift_reports, run_drift_check


def test_run_drift_check_writes_report(tmp_path: Path) -> None:
    meta = run_drift_check(output_dir=tmp_path)
    assert (tmp_path / meta.filename).is_file()
    reports = list_drift_reports(tmp_path)
    assert len(reports) >= 1
    assert reports[0].status in ("green", "yellow", "red")


def test_hand_id_shift_does_not_affect_status(tmp_path: Path) -> None:
    feat = tmp_path / "features.jsonl"
    lines = [json.dumps({"hand_id": i, "range_l1": 1.0}) for i in range(120)]
    feat.write_text("\n".join(lines) + "\n", encoding="utf-8")
    meta = run_drift_check(output_dir=tmp_path, features_path=feat)
    assert meta.features_flagged == 0
    assert meta.status == "green"


def test_range_l1_shift_flags(tmp_path: Path) -> None:
    feat = tmp_path / "features.jsonl"
    lines = [json.dumps({"hand_id": i, "range_l1": 1.0}) for i in range(60)]
    lines += [json.dumps({"hand_id": i, "range_l1": 0.3}) for i in range(60, 120)]
    feat.write_text("\n".join(lines) + "\n", encoding="utf-8")
    meta = run_drift_check(output_dir=tmp_path, features_path=feat)
    assert meta.features_flagged >= 1
    detail_path = tmp_path / f"drift_{meta.date}.json"
    detail = json.loads(detail_path.read_text(encoding="utf-8"))
    hand_row = next(r for r in detail["features"] if r["feature"] == "hand_id")
    assert hand_row["counts_toward_status"] is False
    assert hand_row["flagged"] is False


def test_list_models_returns_core_names() -> None:
    names = {m.name for m in list_models()}
    assert "student_hu" in names
    assert "student_multiway" in names
    assert get_model_info("hhformer").name == "hhformer"
