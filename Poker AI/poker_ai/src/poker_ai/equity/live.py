"""Live hero equity from engine state (HUD, drill, play hints)."""

from __future__ import annotations

import os

from poker_ai.core.context import count_active_players
from poker_ai.core.game import GameState
from poker_ai.equity.multiway import hero_equity_vs_n_uniform


def hero_equity_from_state(
    state: GameState,
    *,
    mc_samples: int | None = None,
    seed: int | None = None,
) -> float | None:
    """Monte Carlo pot-equity for the acting seat vs uniform remaining villains."""
    seat = state.acting_seat
    if seat is None or state.seat_holes is None:
        return None
    hole = state.seat_holes[seat]
    if hole is None:
        return None
    n_opp = count_active_players(state) - 1
    if n_opp < 1:
        return None
    samples = mc_samples
    if samples is None:
        samples = int(os.environ.get("POKER_AI_HUD_EQUITY_SAMPLES", "4000"))
    seed_val = seed if seed is not None else int(state.seed or 0)
    return float(
        hero_equity_vs_n_uniform(
            hole,
            state.board,
            n_opp,
            n_samples=max(500, samples),
            seed=seed_val,
        )
    )
