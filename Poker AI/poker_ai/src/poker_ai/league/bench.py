"""League sim throughput benchmark (Phase 10 exit gate)."""

from __future__ import annotations

import random
import time
from typing import Any

from poker_ai.core.profiles import PlayerProfile
from poker_ai.league.agents.baselines import RandomPolicy
from poker_ai.league.sim import new_table_hand, play_hand
from poker_ai.policy.base import Policy


def measure_sim_throughput(
    *,
    wall_sec: float = 60.0,
    num_seats: int = 6,
    seed: int = 42,
    policies: tuple[Policy, Policy] | None = None,
) -> dict[str, Any]:
    """Play synthetic hands as fast as possible for ``wall_sec`` seconds."""
    pol_a, pol_b = policies or (RandomPolicy(seed=1), RandomPolicy(seed=2))
    rng = random.Random(seed)
    profiles = [PlayerProfile(profile_id=f"p{i}") for i in range(num_seats)]
    t0 = time.perf_counter()
    hands = 0
    while time.perf_counter() - t0 < wall_sec:
        state = new_table_hand(num_seats=num_seats, seed=rng.randint(0, 2**31 - 1))
        table_policies: list[Policy] = [pol_a] * num_seats
        table_policies[1] = pol_b
        play_hand(state, table_policies, profiles, rng, record_timeline=False)
        hands += 1
    elapsed = time.perf_counter() - t0
    hpm = hands / elapsed * 60.0 if elapsed > 0 else 0.0
    return {
        "hands": hands,
        "elapsed_sec": round(elapsed, 3),
        "hands_per_minute": round(hpm, 1),
        "num_seats": num_seats,
    }
