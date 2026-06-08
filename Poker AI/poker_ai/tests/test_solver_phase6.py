"""Phase 6 — CFR solvers, abstractions, and policies."""

from __future__ import annotations

import time

import pytest

from hand_fixture import make_six_max_hand
from poker_ai.core.engine import initial_state_from_parsed_hand, legal_actions
from poker_ai.core.profiles import PlayerProfile
from poker_ai.policy.cfr_policy import CFRPolicy
from poker_ai.policy.heuristic import HeuristicPolicy
from poker_ai.solver.abstraction import equity_bucket, nearest_bet_fraction, pot_fraction_chips
from poker_ai.solver.cfr import CFRPlusSolver, CFRSolver, ExternalSamplingMCCFRSolver
from poker_ai.solver.games.kuhn import KuhnPoker
from poker_ai.solver.preflop import FOLD, PreflopAbstractionGame
from poker_ai.solver.solve_preflop import solve_preflop


@pytest.mark.slow
def test_kuhn_cfr_plus_converges() -> None:
    from poker_ai.solver.validate import OpenSpielKuhnBridge, openspiel_exploitability_mbb

    game = OpenSpielKuhnBridge()
    solver = CFRPlusSolver(game, seed=1)
    solver.run(30_000)
    strat = solver.average_strategy()
    exp = openspiel_exploitability_mbb(strat, big_blind=1.0)
    assert exp < 1.0, f"Kuhn exploitability too high: {exp:.4f} mbb/g"


def test_kuhn_native_game_tree() -> None:
    game = KuhnPoker()
    _, root = game.initial_chance_outcomes()[0]
    assert game.legal_actions(root) == (0, 1)


def test_kuhn_vanilla_improves() -> None:
    from poker_ai.solver.validate import OpenSpielKuhnBridge, openspiel_exploitability_mbb

    game = OpenSpielKuhnBridge()
    solver = CFRSolver(game, mode="vanilla", seed=2)
    solver.run(5_000)
    strat = solver.average_strategy()
    exp = openspiel_exploitability_mbb(strat, big_blind=1.0)
    assert exp < 200.0


def test_abstraction_helpers() -> None:
    assert nearest_bet_fraction(0.35) == 0.33
    assert pot_fraction_chips(100, 0.33) == 33
    assert 0 <= equity_bucket(0.5) < 50


def test_heuristic_propose_valid_distribution() -> None:
    hand = make_six_max_hand(
        hand_id=1,
        hero_seat=0,
        hero_cards="AhKd",
        hero_position="BTN",
    )
    state = initial_state_from_parsed_hand(hand)
    policy = HeuristicPolicy()
    profile = PlayerProfile(profile_id="hero")
    dist = policy.propose(state, profile)
    legal = legal_actions(state)
    assert len(dist.actions) == len(legal)
    assert sum(dist.probs) == pytest.approx(1.0, abs=1e-6)
    assert all(p >= 0.0 for p in dist.probs)


def test_cfr_policy_propose_fast() -> None:
    hand = make_six_max_hand(
        hand_id=2,
        hero_seat=3,
        hero_cards="QsQh",
        hero_position="CO",
    )
    state = initial_state_from_parsed_hand(hand)
    strat = {"n6|p3|b25|h": (0.1, 0.2, 0.5, 0.2)}
    policy = CFRPolicy(strategy=strat)
    profile = PlayerProfile(profile_id="hero")
    dist = policy.propose(state, profile)
    t0 = time.perf_counter()
    for _ in range(199):
        policy.propose(state, profile)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0 / 199.0
    assert elapsed_ms < 5.0
    assert sum(dist.probs) == pytest.approx(1.0, abs=1e-6)


@pytest.mark.slow
def test_preflop_hu_solve_runs() -> None:
    result = solve_preflop(
        num_players=2,
        iterations=500,
        chance_samples=32,
        seed=0,
        measure_exploitability=True,
    )
    assert result.num_info_sets > 0
    assert result.exploitability_mbb is not None
    assert result.exploitability_mbb >= 0.0


def test_preflop_parallel_shard_merge() -> None:
    from poker_ai.solver.parallel_cfr import _iterations_per_shard, solve_preflop_parallel

    assert _iterations_per_shard(80, 2) == [40, 40]
    assert sum(_iterations_per_shard(81, 2)) == 81

    single = solve_preflop(num_players=2, iterations=80, chance_samples=16, seed=1, workers=1)
    parallel = solve_preflop_parallel(
        num_players=2,
        iterations=80,
        chance_samples=16,
        seed=1,
        max_raises=1,
        workers=2,
    )
    assert len(parallel) > 0
    assert single.num_info_sets > 0


def test_real_equity_deals_use_buckets() -> None:
    from poker_ai.solver.preflop_equity import build_chance_deals

    deals = build_chance_deals(
        num_players=2,
        chance_samples=4,
        seed=7,
        equity_mode="real",
        mc_samples=200,
    )
    assert len(deals) == 4
    for deal in deals:
        assert len(deal.buckets) == 2
        assert deal.combos is not None and len(deal.combos) == 2
        assert all(0 <= b < 50 for b in deal.buckets)


def test_showdown_payoffs_hu_combos() -> None:
    from poker_ai.solver.preflop_showdown import showdown_payoffs

    active = [True, True]
    bets = [50, 100]
    pot = 150
    buckets = (10, 40)
    combos = (100, 500)
    pay = showdown_payoffs(
        num_players=2,
        active=active,
        bets=bets,
        pot=pot,
        buckets=buckets,
        combos=combos,
        use_combos=True,
    )
    assert len(pay) == 2
    assert abs(sum(pay)) < 1e-5


def test_stacked_policy_from_artifacts() -> None:
    from poker_ai.policy.router_policy import RouterPolicy
    from poker_ai.policy.stacked import StackedPolicy

    p = StackedPolicy.from_artifacts()
    assert isinstance(p._router, RouterPolicy)
    assert p._router._fallback is not None


@pytest.mark.slow
def test_preflop_hu_real_equity_solve_smoke() -> None:
    result = solve_preflop(
        num_players=2,
        iterations=100,
        chance_samples=4,
        seed=3,
        workers=1,
        equity_mode="real",
        equity_mc_samples=200,
    )
    assert result.num_info_sets > 0
    assert result.equity_mode == "real"


@pytest.mark.slow
def test_hu_real_exploitability_under_5_mbb() -> None:
    result = solve_preflop(
        num_players=2,
        iterations=8_000,
        chance_samples=16,
        seed=4,
        workers=1,
        equity_mode="real",
        equity_mc_samples=300,
        measure_exploitability=True,
        prune_min_mass=20.0,
    )
    assert result.exploitability_mbb is not None
    assert result.exploitability_mbb < 5.0, (
        f"HU exploitability {result.exploitability_mbb:.2f} mbb/g"
    )


@pytest.mark.slow
def test_six_max_exploitability_under_5_mbb() -> None:
    result = solve_preflop(
        num_players=6,
        iterations=6_000,
        chance_samples=12,
        seed=5,
        workers=2,
        equity_mode="real",
        equity_mc_samples=300,
        max_raises=1,
        measure_exploitability=True,
        prune_min_mass=15.0,
    )
    assert result.exploitability_mbb is not None
    assert result.exploitability_mbb < 5.0, (
        f"6-max exploitability {result.exploitability_mbb:.2f} mbb/g"
    )


@pytest.mark.slow
def test_external_sampling_kuhn() -> None:
    from poker_ai.solver.validate import OpenSpielKuhnBridge, openspiel_exploitability_mbb

    game = OpenSpielKuhnBridge()
    solver = ExternalSamplingMCCFRSolver(game, seed=3)
    solver.run(50_000)
    strat = solver.average_strategy()
    exp = openspiel_exploitability_mbb(strat, big_blind=1.0)
    assert exp < 50.0


def test_preflop_game_legal_actions() -> None:
    game = PreflopAbstractionGame(num_players=2, chance_samples=4, seed=1)
    _, state = game.initial_chance_outcomes()[0]
    acts = game.legal_actions(state)
    assert FOLD in acts
