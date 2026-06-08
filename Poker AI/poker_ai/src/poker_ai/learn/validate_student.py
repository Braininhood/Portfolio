"""Phase 7 exit-criteria validation (MSE + inference latency)."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from poker_ai.learn.train_student import TrainStudentConfig, run_train_student
from poker_ai.solver.bridge.batch import solve_grid


@dataclass(frozen=True, slots=True)
class StudentGateResult:
    n_spots: int
    mse_val: float
    mse_ok: bool
    p99_sec: float
    latency_ok: bool
    student_dir: Path
    cache_dir: Path


def _p99_max_sec() -> float:
    raw = os.environ.get("POKER_AI_STUDENT_P99_MAX_SEC", "0.01")
    try:
        return max(0.001, float(raw))
    except ValueError:
        return 0.01


def measure_student_p99_latency(
    *,
    student_dir: Path,
    hhformer_dir: Path,
    cache_dir: Path,
    n_iters: int = 50,
) -> float:
    from poker_ai.core.cards import cards_from_space_separated
    from poker_ai.core.engine import initial_state_from_parsed_hand
    from poker_ai.core.game import Street
    from poker_ai.core.profiles import PlayerProfile
    from poker_ai.ingest.records import ParsedHand, ParsedPlayer
    from poker_ai.policy.distilled_policy import DistilledPolicy

    hand = ParsedHand(
        hand_id=99,
        stakes="0.01/0.02",
        game_type="NLH",
        num_players=6,
        small_blind=0.01,
        big_blind=0.02,
        hero_position="BTN",
        hero_cards="Ah Kd",
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=tuple(
            ParsedPlayer(
                player_id=i + 1,
                position=p,
                stack_size=2.0,
                bb_size=100.0,
                is_hero=(i == 0),
                player_uid=f"u{i}",
            )
            for i, p in enumerate(("BTN", "SB", "BB", "UTG", "MP", "CO"))
        ),
    )
    policy = DistilledPolicy.from_artifacts(
        student_dir=student_dir,
        hhformer_dir=hhformer_dir,
        cache_dir=cache_dir,
    )
    # Warm cache path (same state repeated in loop).
    state = initial_state_from_parsed_hand(hand)
    state.street = Street.FLOP
    state.board = list(cards_from_space_separated("Qs Jh 2h"))
    state.acting_seat = 0
    profile = PlayerProfile(profile_id="hero")
    _ = policy.propose(state, profile)
    times: list[float] = []
    for _ in range(n_iters):
        t0 = time.perf_counter()
        dist = policy.propose(state, profile)
        times.append(time.perf_counter() - t0)
        if not dist.actions:
            msg = "DistilledPolicy returned empty distribution during latency probe"
            raise RuntimeError(msg)
    return float(np.percentile(times, 99))


def run_student_gates(
    *,
    n_spots: int = 1000,
    cache_dir: Path,
    hhformer_dir: Path,
    student_dir: Path,
    backend: str = "mock",
    seed: int = 42,
    train_epochs: int = 30,
    train_batch: int = 128,
) -> StudentGateResult:
    """Solve teacher grid, train student, and check roadmap Phase 7 gates."""
    solve_grid(
        n_spots=n_spots,
        cache_dir=cache_dir,
        backend=backend,  # type: ignore[arg-type]
        seed=seed,
    )
    metrics = run_train_student(
        cache_dir=cache_dir,
        hhformer_dir=hhformer_dir,
        artifact_dir=student_dir,
        cfg=TrainStudentConfig(epochs=train_epochs, batch_size=train_batch, seed=seed),
    )
    p99 = measure_student_p99_latency(
        student_dir=student_dir,
        hhformer_dir=hhformer_dir,
        cache_dir=cache_dir,
    )
    mse_limit = 0.05
    p99_limit = _p99_max_sec()
    return StudentGateResult(
        n_spots=n_spots,
        mse_val=float(metrics.mse_val),
        mse_ok=float(metrics.mse_val) <= mse_limit,
        p99_sec=p99,
        latency_ok=p99 < p99_limit,
        student_dir=student_dir,
        cache_dir=cache_dir,
    )
