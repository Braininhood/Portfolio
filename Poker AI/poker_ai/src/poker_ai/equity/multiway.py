"""Multi-way equity: hero vs independent uniform opponents (Phase 4 / 7b)."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from poker_ai.core.evaluator import hand_rank_value_int
from poker_ai.equity._tables import COMBO_CARDS, COMBO_MASK, board_mask
from poker_ai.equity.mc import _rng, _sample_combo
from poker_ai.features.range import uniform_range


def _seven_card_rank(hole: tuple[int, int], board5: tuple[int, ...]) -> int | None:
    """Best hand rank for hole + five board/runout cards; ``None`` if duplicate cards."""
    cards = (hole[0], hole[1], *board5)
    if len(set(cards)) != len(cards):
        return None
    try:
        return hand_rank_value_int(*cards)
    except (ValueError, IndexError):
        return None


def _sample_opponent_ranks(
    b5: tuple[int, ...],
    *,
    uniform: np.ndarray,
    dead: np.uint64,
    rng: np.random.Generator,
    n_opponents: int,
) -> list[int] | None:
    """Draw ``n_opponents`` non-overlapping uniform combos and return their ranks."""
    d = dead
    ranks: list[int] = []
    for _ in range(n_opponents):
        idx = _sample_combo(uniform, d, rng)
        if idx is None:
            return None
        lo, hi = int(COMBO_CARDS[idx, 0]), int(COMBO_CARDS[idx, 1])
        r = _seven_card_rank((lo, hi), b5)
        if r is None:
            return None
        ranks.append(r)
        d |= COMBO_MASK[idx]
    return ranks


def _showdown_equity_share(hero_rank: int, opponent_ranks: list[int]) -> float:
    """Win mass (1.0) or split mass when hero ties for best hand."""
    if all(hero_rank < r for r in opponent_ranks):
        return 1.0
    if hero_rank == min(opponent_ranks):
        n_top = 1 + sum(1 for r in opponent_ranks if r == hero_rank)
        return 1.0 / float(n_top)
    return 0.0


def mc_equity_hole_vs_uniform_opponents(
    hole: tuple[int, int],
    board: Sequence[int] = (),
    *,
    n_opponents: int,
    n_samples: int = 40_000,
    seed: int | None = None,
) -> float:
    """Monte Carlo: P(hero wins) + 0.5 * P(hero ties) at showdown vs ``n_opponents``.

    Each opponent is drawn from a uniform range with card removal. This is a standard
    population approximation when villain ranges are unknown (not full multi-way CFR).
    """
    if n_opponents < 1:
        msg = "n_opponents must be >= 1"
        raise ValueError(msg)
    if hole[0] == hole[1]:
        msg = "hole cards must be distinct"
        raise ValueError(msg)

    dead = board_mask(board)
    hero_mask = np.uint64(1) << np.uint64(hole[0]) | np.uint64(1) << np.uint64(hole[1])
    if (hero_mask & dead) != 0:
        msg = "hole cards overlap the board"
        raise ValueError(msg)
    dead |= hero_mask

    need = 5 - len(board)
    if need < 0:
        msg = f"board has more than five cards: {len(board)}"
        raise ValueError(msg)

    uniform = np.asarray(uniform_range(), dtype=np.float64)
    rng = _rng(seed)
    wins = 0.0
    valid = 0

    if need == 0:
        b5 = tuple(int(c) for c in board)
        hero_rank = _seven_card_rank(hole, b5)
        if hero_rank is None:
            return 0.0
        for _ in range(n_samples):
            opponent_ranks = _sample_opponent_ranks(
                b5, uniform=uniform, dead=dead, rng=rng, n_opponents=n_opponents
            )
            if opponent_ranks is None:
                continue
            valid += 1
            wins += _showdown_equity_share(hero_rank, opponent_ranks)
        return wins / float(max(1, valid))

    deck = np.array([c for c in range(52) if (dead >> np.uint64(c)) & 1 == 0], dtype=np.int16)
    for _ in range(n_samples):
        if len(deck) < need:
            break
        runout = rng.choice(deck, size=need, replace=False)
        b5 = tuple(int(c) for c in board) + tuple(int(c) for c in runout)
        hero_rank = _seven_card_rank(hole, b5)
        if hero_rank is None:
            continue
        opponent_ranks = _sample_opponent_ranks(
            b5, uniform=uniform, dead=dead, rng=rng, n_opponents=n_opponents
        )
        if opponent_ranks is None:
            continue
        valid += 1
        wins += _showdown_equity_share(hero_rank, opponent_ranks)
    return wins / float(max(1, valid))


def hero_equity_vs_n_uniform(
    hole: tuple[int, int],
    board: Sequence[int],
    n_opponents: int,
    *,
    n_samples: int = 40_000,
    seed: int | None = None,
) -> float:
    """Alias used by policies."""
    return mc_equity_hole_vs_uniform_opponents(
        hole, board, n_opponents=n_opponents, n_samples=n_samples, seed=seed
    )
