"""Targeted branches for full coverage on text / OHH parsers."""

from __future__ import annotations

from poker_ai.ingest import ohh_json as ohh_mod
from poker_ai.ingest import pokerstars_text as ps_mod
from poker_ai.ingest.ohh_json import parse_ohh_dict, parse_ohh_json_bytes
from poker_ai.ingest.pokerstars_text import parse_text


def test_resolve_hand_id_cross_format_uniqueness() -> None:
    from poker_ai.ingest.canonical_id import INGEST_NORMALIZED_TXT, INGEST_OHH_JSON, resolve_hand_id

    assert resolve_hand_id(INGEST_NORMALIZED_TXT, "900006") == 900006
    assert resolve_hand_id(INGEST_OHH_JSON, "900006") != 900006


def test_convert_amount_none_branch() -> None:
    assert ps_mod._convert_amount(None) == 0.0


def test_comma_action_fragments_skips_street_and_seat_lines() -> None:
    assert ps_mod._comma_separated_action_fragments(
        "Flop: ($1) Ah Kh 2d (2 players)", is_seat_line=False
    ) == ["Flop: ($1) Ah Kh 2d (2 players)"]
    assert ps_mod._comma_separated_action_fragments(
        "SB: $1 (50 bb), BB: $2 (100 bb)", is_seat_line=True
    ) == ["SB: $1 (50 bb), BB: $2 (100 bb)"]


def test_normalized_fold_check_singular_and_comma_preflop() -> None:
    from pathlib import Path

    fx = Path(__file__).resolve().parent / "fixtures" / "hands" / "hand_900006.txt"
    h = parse_text(fx.read_text(encoding="utf-8"), hand_id=900006, uid_secret="s")
    assert h is not None
    folds = [a for a in h.actions if a.action_type == "Fold"]
    raises = [a for a in h.actions if a.action_type == "Raise"]
    assert len(folds) == 5
    assert len(raises) == 1

    check_hand = """$0.01/$0.02, NLH, 2 Players
SB: $1 (50 bb)
Hero (BB): $2 (100 bb)
Preflop: Hero Ah Kh
Flop: ($0.03) 2c 3d 4h (2 players)
SB check
Hero checks
"""
    hc = parse_text(check_hand, hand_id=800030, uid_secret="s")
    assert hc is not None
    assert [a.action_type for a in hc.actions] == ["Check", "Check"]

    pre_actions = (
        "UTG calls $0.05, MP raises to $0.20, CO folds, Hero raises to $0.70, 3 folds, "
        "MP raises to $1.45, Hero calls $0.75\n"
    )
    comma = f"""Poker Stars, $0.02/$0.05 No Limit Hold'em Cash, 6 Players
SB: $5 (100 bb)
BB: $5 (100 bb)
UTG: $5 (100 bb)
Hero (BTN): $5 (100 bb)
CO: $5 (100 bb)
MP: $5 (100 bb)
Preflop: Hero is BTN with Kc Ah
{pre_actions}Flop: ($3.02) Ac 9h 8s (2 players)
MP bets $1.45, Hero calls $1.45
"""
    h2 = parse_text(comma, hand_id=800031, uid_secret="s")
    assert h2 is not None
    types = [a.action_type for a in h2.actions]
    assert types.count("Fold") >= 1
    assert "Call" in types and "Raise" in types


def test_normalized_header_requires_nlh_token() -> None:
    bad = "$0.01/$0.02, PLO, 6 Players\nSB: $1 (50 bb)\nBB: $1 (50 bb)\n"
    assert parse_text(bad, hand_id=1, uid_secret="k") is None


def test_normalized_header_rejects_plo_substring_even_with_nlh() -> None:
    bad = "$0.01/$0.02, NLH PLO promo, 6 Players\nSB: $1 (50 bb)\nBB: $1 (50 bb)\n"
    assert parse_text(bad, hand_id=1, uid_secret="k") is None


def test_parse_text_rejects_omaha_raw_header() -> None:
    txt = "PokerStars Hand #9: Omaha Pot Limit ($0.01/$0.02 USD) - 2020/01/01\n"
    assert parse_text(txt, hand_id=1, uid_secret="k") is None


def test_parse_text_raw_no_limit_but_no_stakes_returns_none() -> None:
    txt = "PokerStars Hand #1: Hold'em No Limit - 2020/01/01\nTable 'x' 6-max\n"
    assert parse_text(txt, hand_id=1, uid_secret="k") is None


def test_ohh_rejects_non_nl_bet_type() -> None:
    h = parse_ohh_dict(
        {
            "ohh": {
                "game_number": "42",
                "small_blind_amount": 0.01,
                "big_blind_amount": 0.02,
                "bet_limit": {"bet_type": "PL"},
                "players": [{"name": "A", "id": 0, "starting_stack": 1.0, "seat": 1}],
                "rounds": [
                    {
                        "street": "Preflop",
                        "actions": [{"player_id": 0, "action": "Fold", "amount": 0.0}],
                    }
                ],
                "pots": [],
            }
        },
        uid_secret="k",
    )
    assert h is None


def test_numeric_folds_and_all_fold_and_aliases() -> None:
    text = """$0.01/$0.02, NLH, 3 Players
SB: $1 (50 bb)
BB: $1 (50 bb)
Hero (BTN): $2 (100 bb)
Preflop: Hero Ah Kh
2 folds
All fold
"""
    h = parse_text(text, hand_id=800002, uid_secret="s")
    assert h is not None
    assert len([a for a in h.actions if a.action_type == "Fold"]) >= 2

    text2 = """$0.01/$0.02, NLH, 2 Players
SB: $1 (50 bb)
Hero (BB): $2 (100 bb)
Preflop: Hero Ah Kh
1 raises to $0.06
Hero folds
"""
    h2 = parse_text(text2, hand_id=800003, uid_secret="s")
    assert h2 is not None

    text3 = """$0.01/$0.02, NLH, 2 Players
SB: $1 (50 bb)
Hero (BB): $2 (100 bb)
Preflop: Hero Ah Kh
SB showed As Ks and lost (-$0.50 net)
"""
    h3 = parse_text(text3, hand_id=800004, uid_secret="s")
    assert h3 is not None

    text4 = """$0.01/$0.02, NLH, 2 Players
SB: $1 (50 bb)
Hero (BTN): $2 (100 bb)
Preflop: Hero Ah Kh
"""
    h4 = parse_text(
        text4,
        hand_id=800005,
        uid_secret="s",
        default_screen_names={"BTN": "ScreenHero"},
    )
    assert h4 is not None
    assert h4.players[-1].screen_name == "ScreenHero"


def test_ohh_branches_for_coverage() -> None:
    assert parse_ohh_dict({"ohh": "x"}, uid_secret="k") is None
    h0 = parse_ohh_dict(
        {
            "ohh": {
                "game_number": "scan1",
                "small_blind_amount": 0.01,
                "big_blind_amount": 0.02,
                "bet_limit": {"bet_type": "NL"},
                "players": [
                    {"name": "A", "id": 0, "starting_stack": 1.0, "seat": 1},
                    {"name": "B", "id": 1, "starting_stack": 1.0, "seat": 2},
                ],
                "rounds": [
                    {"street": "Flop", "actions": []},
                    {
                        "street": "Preflop",
                        "actions": [
                            "not-a-dict",
                            {"action": "Post SB", "amount": 0.01, "is_allin": False},
                            {
                                "player_id": 0,
                                "action": "Post SB",
                                "amount": 0.01,
                                "is_allin": False,
                            },
                            {
                                "player_id": 1,
                                "action": "Post BB",
                                "amount": 0.02,
                                "is_allin": False,
                            },
                            {
                                "player_id": 99,
                                "action": "Post BB",
                                "amount": 0.02,
                                "is_allin": False,
                            },
                        ],
                    },
                ],
                "pots": [],
            }
        },
        uid_secret="k",
    )
    assert h0 is not None and h0.players[0].position == "BTN"
    h1 = parse_ohh_dict(
        {
            "ohh": {
                "game_number": "not-an-int-id",
                "small_blind_amount": 0.01,
                "big_blind_amount": 0.02,
                "bet_limit": {"bet_type": "NL"},
                "players": [{"name": "A", "id": 0, "starting_stack": 1.0, "seat": 1}],
                "rounds": [
                    {
                        "street": "Preflop",
                        "cards": [123, "Ah"],
                        "actions": [
                            {"action": "Fold", "amount": 0.0},
                            "bad",
                            {"action": "Unknown", "player_id": 0, "amount": 0.0},
                            {"action": "Dealt Cards", "cards": ["Kd", "Qd"]},
                            {"action": "Dealt Cards", "player_id": 0, "cards": ["As", "Ks"]},
                        ],
                    }
                ],
                "pots": [{"player_wins": [{"player_id": 99, "win_amount": 1.0}]}],
            }
        },
        uid_secret="k",
    )
    assert h1 is not None
    assert h1.game_type == "NLH"

    h2 = parse_ohh_dict(
        {
            "ohh": {
                "game_number": "2",
                "small_blind_amount": 0.01,
                "big_blind_amount": 0.02,
                "players": [
                    {"name": "A", "id": 0, "starting_stack": 1.0, "seat": 1},
                    {"name": "B", "id": 1, "starting_stack": 1.0, "seat": 2},
                ],
                "rounds": [
                    {
                        "street": "Preflop",
                        "actions": [
                            {"action": "Shows Cards", "player_id": 0, "cards": ["2h", "3h"]},
                        ],
                    }
                ],
                "pots": [{"player_wins": [{"player_id": 0, "win_amount": 0.5}]}],
            }
        },
        uid_secret="k",
    )
    assert h2 is not None

    h3 = parse_ohh_dict(
        {
            "ohh": {
                "game_number": "3",
                "small_blind_amount": 0.01,
                "big_blind_amount": 0.02,
                "players": [{"name": "A", "id": 0, "starting_stack": 1.0, "seat": 1}],
                "rounds": [],
                "pots": [{"player_wins": [{"player_id": 0, "win_amount": 0.25}]}],
            }
        },
        uid_secret="k",
    )
    assert h3 is not None

    assert parse_ohh_json_bytes(b"not-json", uid_secret="k") is None


def test_map_ohh_unknown_action() -> None:
    assert ohh_mod._map_ohh_action("  Junk  ") is None
    assert ohh_mod._map_ohh_action("check") == "Check"


def test_raw_pokerstars_without_button_line() -> None:
    text = """PokerStars Hand #1:  Hold'em No Limit ($0.01/$0.02 USD) - 2021/01/01
"""
    h = parse_text(text, hand_id=99, uid_secret="z")
    assert h is not None


def test_raw_pokerstars_no_stakes_returns_none() -> None:
    assert parse_text("PokerStars Hand #1\nno stakes here", hand_id=1, uid_secret="z") is None


def test_fold_skip_hero_then_all_fold() -> None:
    text = """$0.01/$0.02, NLH, 2 Players
Hero (SB): $2 (100 bb)
BB: $1 (50 bb)
Preflop: Hero Ah Kh
1 folds
"""
    h = parse_text(text, hand_id=800010, uid_secret="s")
    assert h is not None
    assert any(a.action_type == "Fold" for a in h.actions)

    text2 = """$0.01/$0.02, NLH, 2 Players
SB: $1 (50 bb)
Hero (BB): $2 (100 bb)
Preflop: Hero Ah Kh
All fold
"""
    h2 = parse_text(text2, hand_id=800011, uid_secret="s")
    assert h2 is not None
    assert len([a for a in h2.actions if a.action_type == "Fold"]) >= 1

    text3 = """$0.01/$0.02, NLH, 3 Players
SB: $1 (50 bb)
BB: $1 (50 bb)
Hero (BTN): $2 (100 bb)
Preflop: Hero Ah Kh
SB raises to $0.06
1 folds
"""
    h3 = parse_text(text3, hand_id=800012, uid_secret="s")
    assert h3 is not None


def test_hero_preflop_with_pattern_and_skipped_unknown_result_positions() -> None:
    wpn_style = """$0.01/$0.02, NLH, 2 Players
SB: $1 (50 bb)
Hero (BB): $2 (100 bb)
Preflop: Hero with 9h 8c
SB showed As Ks and lost (-$0.50 net)
"""
    h = parse_text(wpn_style, hand_id=800020, uid_secret="s")
    assert h is not None
    assert h.hero_cards == "9h 8c"

    mixed = """$0.01/$0.02, NLH, 2 Players
SB: $1 (50 bb)
Hero (BB): $2 (100 bb)
Preflop: Hero Ah Kh
3 showed Jd Tc and lost ($0 net)
CO showed Qs Qc and lost ($0 net)
"""
    h2 = parse_text(mixed, hand_id=800021, uid_secret="s")
    assert h2 is not None
    assert len(h2.results) == 0
