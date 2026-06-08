"""Ante parsing for OHH and normalized PokerStars text."""

from __future__ import annotations

import json
from pathlib import Path

from poker_ai.ingest.ohh_json import parse_ohh_dict
from poker_ai.ingest.pokerstars_text import parse_text
from poker_ai.ingest.records import hand_uses_antes, total_ante_amount

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hands"


def test_ohh_top_level_antes_list() -> None:
    raw = json.loads((FIXTURES / "sample_ohh_ante.json").read_text(encoding="utf-8"))
    hand = parse_ohh_dict(raw, uid_secret="ante-secret")
    assert hand is not None
    assert hand.antes == (0.25, 0.25, 0.25)
    assert hand_uses_antes(hand)
    assert abs(total_ante_amount(hand) - 0.75) < 1e-9


def test_ohh_post_ante_actions_only() -> None:
    data = {
        "ohh": {
            "game_number": "1",
            "small_blind_amount": 1.0,
            "big_blind_amount": 2.0,
            "bet_limit": {"bet_type": "NL"},
            "players": [
                {"name": "A", "id": 0, "starting_stack": 200.0, "seat": 1},
                {"name": "B", "id": 1, "starting_stack": 200.0, "seat": 2},
            ],
            "rounds": [
                {
                    "street": "Preflop",
                    "actions": [
                        {"player_id": 0, "action": "Post Ante", "amount": 2.0},
                        {"player_id": 1, "action": "Post Ante", "amount": 2.0},
                        {"player_id": 0, "action": "Post SB", "amount": 1.0},
                        {"player_id": 1, "action": "Post BB", "amount": 2.0},
                        {"player_id": 0, "action": "Fold", "amount": 0.0},
                    ],
                }
            ],
            "pots": [],
        }
    }
    hand = parse_ohh_dict(data, uid_secret="k")
    assert hand is not None
    assert hand.antes == (2.0, 2.0)


def test_normalized_text_posts_ante() -> None:
    text = """$1/$2, NLH, 3 Players
Hero (BTN): $200 (100 bb)
SB: $200 (100 bb)
BB: $200 (100 bb)
Preflop
BTN: posts ante $2
SB: posts the ante $2
BB: posts the ante $2
Hero (BTN): Ah Kh
BTN: raises to $6
SB: folds
BB: folds
"""
    hand = parse_text(text, hand_id=88001, uid_secret="k", enforce_card_integrity=False)
    assert hand is not None
    assert hand_uses_antes(hand)
    assert hand.antes == (2.0, 2.0, 2.0)
