"""Policy inference latency benchmarks (Phase 7)."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.core.cards import cards_from_space_separated
from poker_ai.core.engine import initial_state_from_parsed_hand, legal_actions
from poker_ai.core.game import Street
from poker_ai.core.profiles import PlayerProfile
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer
from poker_ai.policy.base import Policy


@dataclass(frozen=True, slots=True)
class BenchResult:
    policy_name: str
    policy_version: str
    n_samples: int
    street: str
    device: str
    mean_ms: float
    p50_ms: float
    p99_ms: float
    max_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _hu_flop_hand() -> ParsedHand:
    actions = (
        ParsedAction(1, "BTN", "Preflop", "Raise", 20.0, False, 100.0, 10.0, 30.0, 2.0),
        ParsedAction(2, "BB", "Preflop", "Call", 20.0, False, 100.0, 30.0, 50.0, None),
        ParsedAction(2, "BB", "Flop", "Check", 0.0, False, 100.0, 50.0, 50.0, None),
    )
    return ParsedHand(
        hand_id=42,
        stakes="0.05/0.10",
        game_type="NLH",
        num_players=2,
        small_blind=5.0,
        big_blind=10.0,
        hero_position="BTN",
        hero_cards="As Kh",
        board_cards="Qs Jh 2h",
        pot_preflop=50.0,
        pot_flop=50.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(
            ParsedPlayer(1, "BTN", 100.0, 100.0, True, "hero", None),
            ParsedPlayer(2, "BB", 100.0, 100.0, False, "villain", None),
        ),
        actions=actions,
    )


def _postflop_state() -> Any:

    hand = _hu_flop_hand()
    state = initial_state_from_parsed_hand(hand)
    state.street = Street.FLOP
    state.board = list(cards_from_space_separated(hand.board_cards))
    state.acting_seat = 0
    holes = state.seat_holes or [None, None]
    if holes[0] is None:
        from poker_ai.core.cards import parse_card

        state.seat_holes = [(parse_card("As"), parse_card("Kh")), None]
    return state


def bench_policy(
    policy: Policy,
    *,
    n_warmup: int = 10,
    n_samples: int = 500,
    profile: PlayerProfile | None = None,
) -> BenchResult:
    """Time ``policy.propose`` on a fixed HU flop decision point."""
    prof = profile or PlayerProfile(profile_id="bench")
    state = _postflop_state()
    legal = legal_actions(state)
    if not legal:
        msg = "bench fixture has no legal actions"
        raise RuntimeError(msg)

    for _ in range(n_warmup):
        _ = policy.propose(state, prof)

    times_ms: list[float] = []
    for _ in range(n_samples):
        t0 = time.perf_counter()
        dist = policy.propose(state, prof)
        times_ms.append((time.perf_counter() - t0) * 1000.0)
        if not dist.actions:
            msg = f"{policy.name} returned empty action dist"
            raise RuntimeError(msg)

    arr = np.asarray(times_ms, dtype=np.float64)
    device = getattr(policy, "_device", "cpu")
    return BenchResult(
        policy_name=policy.name,
        policy_version=policy.version,
        n_samples=n_samples,
        street="Flop",
        device=str(device),
        mean_ms=float(arr.mean()),
        p50_ms=float(np.percentile(arr, 50)),
        p99_ms=float(np.percentile(arr, 99)),
        max_ms=float(arr.max()),
    )


def write_bench_report(results: list[BenchResult], path: Path) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([r.to_dict() for r in results], indent=2),
        encoding="utf-8",
    )
