"""Tests for play-vs-AI study loader."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from poker_ai.learn.play_study_loader import (
    collect_play_study_stats,
    iter_play_study_decisions,
    load_play_study_student_rows,
)


def test_play_study_loader_reads_hero_decisions(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE play_sessions (
            session_id TEXT PRIMARY KEY,
            table_config_json TEXT
        );
        CREATE TABLE play_hands (
            id INTEGER PRIMARY KEY,
            session_id TEXT,
            hand_no INTEGER,
            result_bb REAL,
            went_showdown INTEGER,
            board TEXT,
            hero_cards TEXT,
            summary_json TEXT
        );
        """
    )
    config = json.dumps({"user_seat": 0, "seats": 6})
    summary = json.dumps(
        {
            "hand_record": {
                "action_log": [
                    {"seat": 0, "street": "preflop", "action": "raise", "label": "You raise", "pot_bb": 3},
                    {"seat": 1, "street": "preflop", "action": "call", "label": "Bot calls", "pot_bb": 6},
                ],
                "bot_lineup": {"1": "fish"},
            }
        }
    )
    conn.execute(
        "INSERT INTO play_sessions (session_id, table_config_json) VALUES (?, ?)",
        ("sess1", config),
    )
    conn.execute(
        "INSERT INTO play_hands (session_id, hand_no, result_bb, went_showdown, board, hero_cards, summary_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("sess1", 1, 5.0, 1, "Ah Kh Qh", "As Kd", summary),
    )
    conn.commit()
    conn.close()

    stats = collect_play_study_stats(db)
    assert stats["hands"] == 1
    assert stats["hero_decisions"] >= 1
    rows = list(iter_play_study_decisions(db))
    assert len(rows) >= 1
    assert rows[0].action == "raise"

    student_rows = load_play_study_student_rows(db_path=db)
    assert len(student_rows) <= 1
    if student_rows:
        assert len(student_rows[0].target_freqs) == 5
