"""HU vs multi-way policy router (Phase 7b)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from poker_ai.core.cards import parse_card
from poker_ai.core.context import count_active_players
from poker_ai.core.game import GameState, Street
from poker_ai.core.profiles import PlayerProfile
from poker_ai.policy.base import ActionDist
from poker_ai.policy.distilled_policy import DistilledPolicy
from poker_ai.policy.multiway_postflop import MultiwayPostflopPolicy
from poker_ai.policy.router_policy import RouterPolicy


def _state(
    *,
    num_seats: int = 6,
    folded: list[bool] | None = None,
    street: Street = Street.FLOP,
) -> GameState:
    n = num_seats
    f = folded if folded is not None else [False] * n
    return GameState(
        num_seats=n,
        stacks=[1000] * n,
        folded=f,
        street=street,
        board=[
            parse_card("2c"),
            parse_card("7d"),
            parse_card("Jh"),
        ],
        full_board=(
            parse_card("2c"),
            parse_card("7d"),
            parse_card("Jh"),
        ),
        pot=300,
        button_seat=0,
        sb_seat=1,
        bb_seat=2,
        seat_pid=list(range(n)),
        street_commit=[0] * n,
        current_max=0,
        big_blind=10,
        small_blind=5,
        acting_seat=0,
        hand_over=False,
        winner_seat=None,
        seed=42,
        last_aggressor_seat=None,
        bb_checked_preflop=True,
        raise_count_street=0,
        action_log=[],
        acted_this_round=[False] * n,
        seat_holes=[(parse_card("As"), parse_card("Ah"))]
        + [(parse_card("Kd"), parse_card("Kc"))] * (n - 1),
    )


def _profile() -> PlayerProfile:
    return PlayerProfile(profile_id="hero")


def test_count_active_three_way() -> None:
    s = _state(folded=[False, False, False, True, True, True])
    assert count_active_players(s) == 3


def test_distilled_delegates_multiway_not_hu_student() -> None:
    """3-way pot: DistilledPolicy routes to multi-way brain (no HU student logits)."""
    s = _state(folded=[False, False, False, True, True, True])
    pol = DistilledPolicy.from_artifacts()
    dist = pol.propose(s, _profile())
    assert dist.actions
    assert sum(dist.probs) == pytest.approx(1.0, abs=1e-5)


def test_router_delegates_brains() -> None:
    hu = MagicMock()
    hu.propose.return_value = ActionDist((("Check", 0, 0),), (1.0,))
    mw = MagicMock()
    mw.propose.return_value = ActionDist((("Fold", 0, 0),), (1.0,))

    router = RouterPolicy(hu=hu, multiway=mw)
    s_hu = _state(num_seats=2, folded=[False, False])
    router.propose(s_hu, _profile())
    assert router._last_brain == "hu"
    hu.propose.assert_called()

    s_mw = _state(folded=[False, False, False, True, True, True])
    router.propose(s_mw, _profile())
    assert router._last_brain == "multiway"
    mw.propose.assert_called()


def test_multiway_postflop_equity_produces_dist() -> None:
    s = _state(folded=[False, False, False, True, True, True])
    pol = MultiwayPostflopPolicy()
    dist = pol.propose(s, _profile())
    assert dist.actions
    assert abs(sum(dist.probs) - 1.0) < 1e-6


@pytest.mark.parametrize("num_seats", [6, 9, 10])
def test_router_table_sizes(num_seats: int) -> None:
    folded = [False] * min(3, num_seats) + [True] * max(0, num_seats - 3)
    s = _state(num_seats=num_seats, folded=folded)
    assert count_active_players(s) >= 3
    pol = MultiwayPostflopPolicy()
    dist = pol.propose(s, _profile())
    assert dist.actions
