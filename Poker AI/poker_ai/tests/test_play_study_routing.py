"""Play-study HU vs multi-way routing."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from poker_ai.learn.play_study_loader import (
    collect_play_study_stats,
    load_play_study_multiway_rows,
    load_play_study_student_rows,
    play_study_route,
)


def _seed_db(db: Path, *, summary: dict, seats: int = 6) -> None:
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE play_sessions (session_id TEXT PRIMARY KEY, table_config_json TEXT);
        CREATE TABLE play_hands (
            id INTEGER PRIMARY KEY, session_id TEXT, hand_no INTEGER,
            result_bb REAL, went_showdown INTEGER, board TEXT, hero_cards TEXT, summary_json TEXT
        );
        """
    )
    config = json.dumps({"user_seat": 0, "seats": seats})
    conn.execute(
        "INSERT INTO play_sessions VALUES (?, ?)",
        ("sess1", config),
    )
    conn.execute(
        "INSERT INTO play_hands VALUES (1, ?, 1, 0, 1, ?, ?, ?)",
        ("sess1", summary.get("board", "Ah Kh Qh"), "As Kd", json.dumps({"hand_record": summary})),
    )
    conn.commit()
    conn.close()


def test_play_study_routes_hu_and_multiway(tmp_path: Path) -> None:
    db = tmp_path / "play.db"
    summary = {
        "action_log": [
            {"seat": 1, "street": "preflop", "action": "raise", "label": "B1 raises", "pot_bb": 3},
            {"seat": 0, "street": "preflop", "action": "call", "label": "You call", "pot_bb": 6},
            {"seat": 2, "street": "preflop", "action": "call", "label": "B2 calls", "pot_bb": 9},
            {"seat": 0, "street": "flop", "action": "bet", "label": "You bet", "pot_bb": 12},
            {"seat": 2, "street": "flop", "action": "fold", "label": "B2 folds", "pot_bb": 12},
            {"seat": 0, "street": "turn", "action": "check", "label": "You check", "pot_bb": 12},
        ],
        "bot_lineup": {"1": "gto_bot", "2": "fish"},
    }
    _seed_db(db, summary=summary, seats=6)
    stats = collect_play_study_stats(db)
    assert stats["hero_decisions_hu"] == 1
    assert stats["hero_decisions_multiway"] == 1
    assert stats["hero_decisions_skipped"] == 1

    hu_rows = load_play_study_student_rows(db_path=db)
    mw_rows = load_play_study_multiway_rows(db_path=db)
    assert len(hu_rows) == 1
    assert len(mw_rows) == 1
    assert mw_rows[0].n_active >= 3


def test_play_study_route_skips_preflop_multiway(tmp_path: Path) -> None:
    db = tmp_path / "play.db"
    summary = {
        "action_log": [
            {"seat": 0, "street": "preflop", "action": "raise", "label": "You raise", "pot_bb": 3},
            {"seat": 1, "street": "preflop", "action": "call", "label": "B1", "pot_bb": 6},
            {"seat": 2, "street": "preflop", "action": "call", "label": "B2", "pot_bb": 9},
        ],
        "bot_lineup": {},
    }
    _seed_db(db, summary=summary, seats=6)
    from poker_ai.learn.play_study_loader import iter_play_study_decisions

    decs = list(iter_play_study_decisions(db))
    assert len(decs) == 1
    assert play_study_route(decs[0]) is None
    stats = collect_play_study_stats(db)
    assert stats["hero_decisions_skipped"] == 1
