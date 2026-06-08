"""Tests for :func:`poker_ai.ingest.hero_viewpoint.ensure_hero_viewpoint`."""

from __future__ import annotations

from dataclasses import replace

from poker_ai.ingest.canonical_id import INGEST_PHH
from poker_ai.ingest.hero_viewpoint import ensure_hero_viewpoint
from poker_ai.ingest.phh_text import parse_phh_block_dict
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer, ParsedResult


def _hand(
    *,
    hero_position: str | None = None,
    hero_cards: str | None = None,
    players: tuple[ParsedPlayer, ...],
    results: tuple[ParsedResult, ...],
) -> ParsedHand:
    return ParsedHand(
        hand_id=1,
        stakes="1/2",
        game_type="NLH",
        num_players=len(players),
        small_blind=1.0,
        big_blind=2.0,
        hero_position=hero_position,
        hero_cards=hero_cards,
        board_cards=None,
        pot_preflop=3.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=players,
        actions=(ParsedAction(1, "SB", "Preflop", "Fold", 0.0, False, 100.0, 3.0, 3.0, None),),
        results=results,
        ingest_source=INGEST_PHH,
        external_ref="x",
    )


def test_ensure_hero_empty_players() -> None:
    h = replace(
        _hand(
            players=(),
            results=(),
        ),
        num_players=0,
    )
    assert ensure_hero_viewpoint(h) is h


def test_ensure_hero_defaults_to_lowest_seat_without_cards() -> None:
    uid = "a" * 64
    uid2 = "b" * 64
    p1 = ParsedPlayer(1, "SB", 100.0, 50.0, False, uid)
    p2 = ParsedPlayer(2, "BB", 100.0, 50.0, False, uid2)
    h = _hand(
        players=(p1, p2),
        results=(
            ParsedResult(1, "SB", "", 0.0, 0.0, False),
            ParsedResult(2, "BB", "", 0.0, 0.0, False),
        ),
    )
    out = ensure_hero_viewpoint(h)
    assert out.hero_position == "SB"
    assert out.hero_cards is None
    assert sum(1 for p in out.players if p.is_hero) == 1
    assert next(p for p in out.players if p.is_hero).player_id == 1


def test_ensure_hero_prefers_lowest_seat_with_known_cards() -> None:
    uid = "c" * 64
    uid2 = "d" * 64
    p1 = ParsedPlayer(1, "SB", 100.0, 50.0, False, uid)
    p2 = ParsedPlayer(2, "BB", 100.0, 50.0, False, uid2)
    h = _hand(
        players=(p1, p2),
        results=(
            ParsedResult(1, "SB", "2d 3c", 0.0, 0.0, False),
            ParsedResult(2, "BB", "ah kh", 0.0, 0.0, False),
        ),
    )
    out = ensure_hero_viewpoint(h)
    assert out.hero_position == "SB"
    assert out.hero_cards == "2d 3c"


def test_ensure_hero_fills_cards_when_position_preset() -> None:
    uid = "e" * 64
    uid2 = "f" * 64
    p1 = ParsedPlayer(1, "SB", 100.0, 50.0, False, uid)
    p2 = ParsedPlayer(2, "BB", 100.0, 50.0, False, uid2)
    h = _hand(
        players=(p1, p2),
        hero_position="BB",
        hero_cards=None,
        results=(
            ParsedResult(1, "SB", "", 0.0, 0.0, False),
            ParsedResult(2, "BB", "qs qc", 0.0, 0.0, False),
        ),
    )
    out = ensure_hero_viewpoint(h)
    assert out.hero_position == "BB"
    assert out.hero_cards == "qs qc"


def test_ensure_hero_keeps_existing_cards() -> None:
    uid = "g" * 64
    uid2 = "h" * 64
    p1 = ParsedPlayer(1, "SB", 100.0, 50.0, False, uid)
    p2 = ParsedPlayer(2, "BB", 100.0, 50.0, False, uid2)
    h = _hand(
        players=(p1, p2),
        hero_position="SB",
        hero_cards="As Ks",
        results=(
            ParsedResult(1, "SB", "2d 2c", 0.0, 0.0, False),
            ParsedResult(2, "BB", "", 0.0, 0.0, False),
        ),
    )
    out = ensure_hero_viewpoint(h)
    assert out.hero_cards == "as ks"


def test_ensure_hero_ignores_unknown_hero_position_string() -> None:
    uid = "i" * 64
    uid2 = "j" * 64
    p1 = ParsedPlayer(1, "SB", 100.0, 50.0, False, uid)
    p2 = ParsedPlayer(2, "BB", 100.0, 50.0, False, uid2)
    h = _hand(
        players=(p1, p2),
        hero_position="NOT_A_SEAT",
        results=(
            ParsedResult(1, "SB", "", 0.0, 0.0, False),
            ParsedResult(2, "BB", "9s 8s", 0.0, 0.0, False),
        ),
    )
    out = ensure_hero_viewpoint(h)
    assert out.hero_position == "BB"
    assert out.hero_cards == "9s 8s"


def test_phh_dict_gets_hero_after_ensure() -> None:
    h = parse_phh_block_dict(
        {
            "variant": "NT",
            "players": ["a", "b"],
            "starting_stacks": [200.0, 200.0],
            "blinds_or_straddles": [1, 2],
            "actions": ["d dh p1 AsKh", "d dh p2 QdQc", "p2 f"],
            "winnings": [2.0, -2.0],
        },
        external_ref="hero-t",
        uid_secret="k",
    )
    assert h is not None
    assert h.hero_position is None
    out = ensure_hero_viewpoint(h)
    assert out.hero_cards is not None
    assert "as" in out.hero_cards and "kh" in out.hero_cards
