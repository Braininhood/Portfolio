"""Unit tests for ``nlh_validate`` (header + card integrity)."""

from __future__ import annotations

from pathlib import Path

import pytest

from poker_ai.ingest.nlh_validate import (
    is_normalized_nlh_header,
    normalized_nlh_card_integrity_ok,
)
from poker_ai.ingest.pokerstars_text import parse_text


def test_is_normalized_nlh_header_matrix() -> None:
    assert is_normalized_nlh_header("$0.01/$0.02, NLH, 6 Players") is True
    assert is_normalized_nlh_header("WPN, $5/$10 No Limit Hold'em Cash, 4 Players") is True
    assert is_normalized_nlh_header("$1/$2, Pot Limit Omaha, 6 Players") is False
    assert is_normalized_nlh_header("$1/$2, PLO, 6 Players") is False
    assert is_normalized_nlh_header("$2/$4 Limit Hold'em, 6 Players") is False
    assert is_normalized_nlh_header("NLH PLO Challenge, 6 Players") is False


def test_integrity_rejects_duplicate_card_anywhere() -> None:
    base = (Path(__file__).resolve().parent / "fixtures" / "hands" / "hand_900006.txt").read_text(
        encoding="utf-8"
    )
    bad = base + "\nFlop: ($1) Ah Ah 2d (2 players)\n"
    assert normalized_nlh_card_integrity_ok(base) is True
    assert normalized_nlh_card_integrity_ok(bad) is False


def test_parse_text_wpn_style_when_corpus_present() -> None:
    repo = Path(__file__).resolve().parents[2].parent
    sample = repo / "hand" / "6" / "hand_37936805.txt"
    if not sample.is_file():
        pytest.skip("hand/6 corpus not in checkout")
    text = sample.read_text(encoding="utf-8")
    h = parse_text(text, hand_id=37936805, uid_secret="k")
    assert h is not None
    assert h.hero_cards == "8s ah"
    assert h.game_type == "NLH"


def test_parse_text_duplicate_flop_when_strict_off() -> None:
    base = (Path(__file__).resolve().parent / "fixtures" / "hands" / "hand_900006.txt").read_text(
        encoding="utf-8"
    )
    bad = base + "\nFlop: ($1) Ah Ah 2d (2 players)\n"
    assert parse_text(bad, hand_id=1, uid_secret="k", enforce_card_integrity=True) is None
    assert parse_text(bad, hand_id=1, uid_secret="k", enforce_card_integrity=False) is not None


def test_integrity_allows_hero_show_line_repeating_preflop_hole_cards() -> None:
    ok = """$0.01/$0.02, NLH, 2 Players
SB: $1 (50 bb)
Hero (BB): $2 (100 bb)
Preflop: Hero Ks Qd
Flop: ($1) 2d 4s Td (2 players)
Hero showed Ks Qd and won ($1.00) ($0.50 net)
"""
    assert normalized_nlh_card_integrity_ok(ok) is True


def test_integrity_rejects_hero_without_two_hole_cards() -> None:
    bad = """$0.01/$0.02, NLH, 3 Players
SB: $1 (50 bb)
BB: $1 (50 bb)
Hero (BTN): $2 (100 bb)
Preflop: Hero Ah
UTG folds
"""
    assert normalized_nlh_card_integrity_ok(bad) is False
