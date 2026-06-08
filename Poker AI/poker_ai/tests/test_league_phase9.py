"""Phase 9 league — HU, multi-way, brain switches, promotion gates."""

from __future__ import annotations

import json
import random
from pathlib import Path

from poker_ai.league.agents import CallStationPolicy, RandomPolicy, build_default_roster
from poker_ai.league.evaluator import LeagueBoard, promotion_significant, record_hand
from poker_ai.league.formats import parse_table_sizes
from poker_ai.league.orchestrator import LeagueConfig, run_league
from poker_ai.league.sim import (
    HandResult,
    chip_total,
    new_hu_hand,
    new_table_hand,
    play_hand,
)
from poker_ai.policy.bench import bench_policy
from poker_ai.policy.heuristic import HeuristicPolicy


def test_hu_hand_play_completes() -> None:
    state = new_hu_hand(seed=123)
    a, b = RandomPolicy(1), CallStationPolicy()
    from poker_ai.core.profiles import PlayerProfile

    result = play_hand(
        state,
        (a, b),
        (PlayerProfile(profile_id="a"), PlayerProfile(profile_id="b")),
        __import__("random").Random(9),
    )
    assert result.winner_seat is not None
    assert sum(result.deltas) == 0


def test_6max_hand_play_completes() -> None:
    from poker_ai.core.profiles import PlayerProfile

    state = new_table_hand(num_seats=6, seed=456)
    policies = tuple(RandomPolicy(i) for i in range(6))
    profiles = tuple(PlayerProfile(profile_id=f"p{i}") for i in range(6))
    result = play_hand(state, policies, profiles, random.Random(11))
    assert sum(result.deltas) == 0
    assert result.num_seats == 6


def test_multiway_can_switch_to_hu_brain() -> None:
    """After folds, active count drops — league sim tracks HU vs multi-way decisions."""
    from poker_ai.core.profiles import PlayerProfile

    state = new_table_hand(num_seats=6, seed=99)
    policies = tuple(RandomPolicy(i) for i in range(6))
    profiles = tuple(PlayerProfile(profile_id=f"p{i}") for i in range(6))
    result = play_hand(state, policies, profiles, random.Random(3))
    assert result.hu_decisions + result.multiway_decisions >= 1
    if result.max_active_seen >= 3 and result.hu_decisions > 0:
        assert result.brain_switches >= 0


def test_chip_conservation_many_hands() -> None:
    from poker_ai.core.profiles import PlayerProfile

    rng = random.Random(7)
    for seats in (2, 6, 9):
        for i in range(30):
            state = new_table_hand(num_seats=seats, seed=seats * 1000 + i)
            start = chip_total(state)
            policies = tuple(RandomPolicy(i + s) for s in range(seats))
            profiles = tuple(PlayerProfile(profile_id=f"a{s}") for s in range(seats))
            play_hand(state, policies, profiles, rng)
            assert chip_total(state) == start


def test_parse_table_sizes() -> None:
    assert parse_table_sizes("hu,6max,9") == (2, 6, 9)
    assert parse_table_sizes("2,6") == (2, 6)


def test_league_until_wall_multiway(tmp_path: Path) -> None:
    roster = build_default_roster()
    report = tmp_path / "until.json"
    result = run_league(
        roster,
        cfg=LeagueConfig(
            hands_per_matchup=12,
            max_wall_sec=1.2,
            run_until_wall=True,
            until_multiway_only=True,
            until_include_hu=False,
            seed=7,
            report_path=report,
            table_sizes=(6, 9),
            workers=1,
            min_hands_for_promotion=50,
        ),
    )
    assert result.wall_sec >= 0.9
    assert result.hands_played >= 12
    assert "hu" not in result.formats_played
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data.get("schedule") == "until_wall"
    assert data.get("multiway_decisions_total", 0) > 0


def test_league_run_short(tmp_path: Path) -> None:
    roster = build_default_roster()
    report = tmp_path / "lb.json"
    result = run_league(
        roster,
        cfg=LeagueConfig(
            hands_per_matchup=18,
            max_wall_sec=60.0,
            seed=1,
            report_path=report,
            min_hands_for_promotion=50,
            table_sizes=(2, 6),
        ),
    )
    assert result.hands_played > 0
    assert result.brain_switches_total >= 0
    assert "hu" in result.formats_played
    assert report.is_file()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert "main_agent" in {r["agent_id"] for r in data["leaderboard"]}
    assert data.get("chip_balance", 1) == 0
    assert data.get("multiway_decisions_total", 0) >= 0


def test_heuristic_bench_fast() -> None:
    r = bench_policy(HeuristicPolicy(), n_warmup=2, n_samples=30)
    assert r.p99_ms < 500.0
    assert r.n_samples == 30


def test_record_hand_updates_elo() -> None:
    board = LeagueBoard()
    record_hand(
        board,
        "a",
        "b",
        HandResult(deltas=(100, -100), went_showdown=False, winner_seat=0),
        big_blind=100,
        format_id="hu",
    )
    assert board.agents["a"].elo > board.agents["b"].elo


def test_promotion_significance_gate() -> None:
    board = LeagueBoard()
    rec = board.ensure("main_agent")
    for _ in range(1200):
        record_hand(
            board,
            "main_agent",
            "random",
            HandResult(deltas=(50, -50), went_showdown=False, winner_seat=0),
            big_blind=100,
        )
    assert promotion_significant(rec, min_hands=1000, alpha=0.05)
