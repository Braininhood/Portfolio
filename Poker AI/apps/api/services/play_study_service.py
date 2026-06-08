"""Play-vs-AI study data — DB status and training manifest (Phase W7)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from poker_ai.learn.play_study_loader import (
    collect_play_study_stats,
    sqlite_db_path,
    write_play_study_manifest,
)


def get_play_study_status() -> dict[str, Any]:
    """Training-ready stats; data lives in ``play_hands`` table."""
    stats = collect_play_study_stats()
    manifest_path = Path("artifacts/play_study/manifest.json")
    manifest: dict[str, Any] | None = None
    if manifest_path.is_file():
        import json

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = None

    return {
        **stats,
        "ready_for_training": stats["hands"] > 0,
        "manifest_path": str(manifest_path.resolve()) if manifest_path.is_file() else None,
        "manifest": manifest,
        "note": (
            "Hands are stored in play_hands.summary_json (full action logs, showdowns, bot lineups). "
            "Run play_study_materialize to refresh the training manifest — no file export required."
        ),
    }


def materialize_play_study(*, output_dir: str = "artifacts/play_study") -> dict[str, Any]:
    """Register DB play hands for training pipelines (writes manifest only)."""
    out = Path(output_dir)
    result = write_play_study_manifest(out, db_path=sqlite_db_path())
    return result
