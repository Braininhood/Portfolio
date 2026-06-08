"""Monker export import (Phase 7c)."""

from __future__ import annotations

import json
from pathlib import Path

from poker_ai.learn.monker_rows import load_monker_training_rows
from poker_ai.solver.bridge.monker import parse_monker_export_file


def test_parse_monker_export_file(tmp_path: Path) -> None:
    path = tmp_path / "spot.json"
    path.write_text(
        json.dumps(
            {
                "board": "As,Kd,7c",
                "n_active": 4,
                "num_seats": 9,
                "strategy": {"fold": 0.2, "check": 0.5, "bet": 0.3},
            }
        ),
        encoding="utf-8",
    )
    spot = parse_monker_export_file(path)
    assert spot.backend == "monker"
    assert spot.meta["n_active"] == 4
    assert abs(sum(spot.frequencies) - 1.0) < 1e-5


def test_load_monker_training_rows(tmp_path: Path) -> None:
    path = tmp_path / "mw.json"
    path.write_text(
        json.dumps(
            {
                "board": "Qs,Jh,2h",
                "n_active": 3,
                "num_seats": 6,
                "strategy": {"fold": 0.1, "check_call": 0.6, "bet_33": 0.3},
            }
        ),
        encoding="utf-8",
    )
    rows = load_monker_training_rows(tmp_path)
    assert len(rows) == 1
    assert len(rows[0].target_freqs) == 5
