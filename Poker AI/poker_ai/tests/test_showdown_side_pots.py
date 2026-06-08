"""Side-pot showdown resolution tests."""

from __future__ import annotations

import random

from poker_ai.core.engine import money_to_chips
from poker_ai.core.profiles import PlayerProfile
from poker_ai.core.showdown import award_showdown_pots, resolve_showdown
from poker_ai.league.agents.registry import build_default_roster
from poker_ai.league.sim import chip_total, new_table_hand, play_hand


def test_award_showdown_pots_clears_pot():
    state = new_table_hand(num_seats=2, seed=99, stack_bb=50.0)
    start = [state.stacks[s] + state.street_commit[s] for s in range(2)]
    pot = state.pot
    for seat in range(2):
        total = state.stacks[seat] + state.street_commit[seat]
        state.stacks[seat] = 0
        state.street_commit[seat] = total
        pot += total - start[seat] + state.street_commit[seat]
    state.pot = sum(start) - sum(state.stacks[s] + state.street_commit[s] for s in range(2))
    state.street = __import__("poker_ai.core.game", fromlist=["Street"]).Street.SHOWDOWN
    before = chip_total(state)
    award_showdown_pots(state, start_totals=start)
    assert state.pot == 0
    assert chip_total(state) == before


def test_play_hand_with_side_pots_conserves_chips():
    roster = build_default_roster()
    policies = [roster[0].policy] * 3
    profiles = [PlayerProfile(profile_id=f"p{i}") for i in range(3)]
    state = new_table_hand(num_seats=3, seed=7, stack_bb=30.0)
    rng = random.Random(7)
    result = play_hand(state, policies, profiles, rng, max_actions=400)
    assert sum(result.deltas) == 0


def test_ante_increases_pot():
    state = new_table_hand(num_seats=6, seed=7, stack_bb=100.0, ante_bb=1.0)
    ante = money_to_chips(1.0)
    expected_ante = ante * 6
    assert state.pot >= expected_ante
    start = chip_total(state)
    assert sum(state.stacks) + state.pot == start


def test_resolve_showdown_with_start_totals():
    state = new_table_hand(num_seats=2, seed=3, stack_bb=40.0)
    start = [state.stacks[s] + state.street_commit[s] for s in range(2)]
    from poker_ai.core.engine import apply_action, legal_actions
    from poker_ai.core.game import EngineActionKind, Street

    while state.street != Street.SHOWDOWN and not state.hand_over:
        seat = state.acting_seat
        if seat is None:
            break
        legal = legal_actions(state)
        action = legal[0]
        state = apply_action(state, action)
    if state.street == Street.SHOWDOWN:
        before = chip_total(state)
        resolve_showdown(state, start_totals=start)
        assert state.pot == 0
        assert chip_total(state) == before
