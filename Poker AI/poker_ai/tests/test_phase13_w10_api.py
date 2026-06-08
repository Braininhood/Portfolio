"""Phase W10 — research extensions API and library modules."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from load_api_app import load_api_app
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer, ParsedResult
from poker_ai.opponents.causal_eval import evaluate_causal_leaks
from poker_ai.opponents.range_inference import infer_range_from_hands
from poker_ai.policy.deep_search import deep_search_enabled

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

app = load_api_app()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _sample_hand(*, hero_uid: str = "villain_1", show_ak: bool = True) -> ParsedHand:
    player = ParsedPlayer(
        2,
        "BTN",
        100.0,
        100.0,
        False,
        hero_uid,
        "Villain",
    )
    hero = ParsedPlayer(1, "BB", 100.0, 100.0, True, "hero_1", "Hero")
    actions = (
        ParsedAction(2, "BTN", "PREFLOP", "raise", 3.0, False, 97.0, 1.5, 4.5, 2.0),
        ParsedAction(1, "BB", "PREFLOP", "call", 2.0, False, 98.0, 4.5, 6.5, None),
        ParsedAction(1, "BB", "FLOP", "check", 0.0, False, 98.0, 6.5, 6.5, None),
        ParsedAction(2, "BTN", "FLOP", "bet", 4.0, False, 93.0, 6.5, 10.5, 0.66),
        ParsedAction(1, "BB", "FLOP", "call", 4.0, False, 94.0, 10.5, 14.5, None),
    )
    results = ()
    if show_ak:
        results = (
            ParsedResult(2, "BTN", "ah kh", -14.5, 0.0, True),
            ParsedResult(1, "BB", "7c 2d", 14.5, 14.5, True),
        )
    return ParsedHand(
        hand_id=42,
        stakes="0.50/1",
        game_type="NLH",
        num_players=2,
        small_blind=0.5,
        big_blind=1.0,
        hero_position="BB",
        hero_cards="7c 2d",
        board_cards="Qs Jh 2h",
        pot_preflop=6.5,
        pot_flop=14.5,
        pot_turn=14.5,
        pot_river=14.5,
        players=(hero, player),
        actions=actions,
        results=results,
    )


def test_range_inference_dirichlet_buckets() -> None:
    hand = _sample_hand()
    result = infer_range_from_hands("villain_1", [hand])
    assert result.observed_actions >= 2
    assert len(result.buckets) == 3
    assert abs(sum(b.mass_pct for b in result.buckets) - 100.0) < 2.0
    assert result.confidence_pct > 0


def test_causal_eval_detects_dry_board_calls() -> None:
    hands = [_sample_hand() for _ in range(25)]
    result = evaluate_causal_leaks("villain_1", hands)
    assert result.hands_analyzed == 25
    assert isinstance(result.total_leak_bb_per_100, (int, float))


def test_deep_search_enabled_threshold() -> None:
    assert deep_search_enabled(thinking_ms=0, deep_search=False) is False
    assert deep_search_enabled(thinking_ms=250, deep_search=False) is True
    assert deep_search_enabled(thinking_ms=0, deep_search=True) is True


def test_player_range_endpoint_404(client: TestClient) -> None:
    r = client.get("/players/nonexistent_uid_xyz/range")
    assert r.status_code == 404


def test_player_causal_endpoint_404(client: TestClient) -> None:
    r = client.get("/players/nonexistent_uid_xyz/causal")
    assert r.status_code == 404


def test_decide_accepts_thinking_ms_and_deep_search(client: TestClient) -> None:
    r = client.post(
        "/decide",
        json={"policy": "heuristic", "thinking_ms": 250, "deep_search": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["latency_ms"] >= 0
    assert len(body["actions"]) >= 1
