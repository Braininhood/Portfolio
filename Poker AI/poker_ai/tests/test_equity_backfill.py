"""Equity backfill and live HUD helpers."""

from __future__ import annotations

from pathlib import Path

from poker_ai.core.context import count_active_players
from poker_ai.core.engine import initial_state_from_parsed_hand
from poker_ai.equity.backfill import compute_seat_equities, enrich_hand_results
from poker_ai.equity.live import hero_equity_from_state
from poker_ai.ingest.ohh_json import parse_ohh_json_bytes

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hands"


def test_compute_seat_equities_sample_ohh() -> None:
    raw = (FIXTURES / "sample_ohh.json").read_bytes()
    hand = parse_ohh_json_bytes(raw, uid_secret="fixture-secret")
    assert hand is not None
    eq = compute_seat_equities(hand, mc_samples=800)
    assert 1 in eq
    assert eq[1].preflop_equity is not None
    assert 0.0 < eq[1].preflop_equity < 1.0


def test_enrich_hand_results_roundtrip() -> None:
    raw = (FIXTURES / "sample_ohh.json").read_bytes()
    hand = parse_ohh_json_bytes(raw, uid_secret="fixture-secret")
    assert hand is not None
    enriched = enrich_hand_results(hand, mc_samples=500)
    hero = next(r for r in enriched.results if r.player_id == 1)
    assert hero.preflop_equity is not None


def test_hero_equity_from_state_hu_flop() -> None:
    raw = (FIXTURES / "sample_ohh.json").read_bytes()
    hand = parse_ohh_json_bytes(raw, uid_secret="fixture-secret")
    assert hand is not None
    state = initial_state_from_parsed_hand(hand)
    assert count_active_players(state) >= 2
    eq = hero_equity_from_state(state, mc_samples=600, seed=1)
    assert eq is not None
    assert 0.0 <= eq <= 1.0
