"""Win / tie / loss breakdown for range-vs-range equity (exact postflop + MC fallback)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

import numpy as np

from poker_ai.equity._runout_cache import cacheable_board, runout_rank_cache
from poker_ai.equity._tables import COMBO_MASK, board_mask, rank_combo_on_board
from poker_ai.features.range import NUM_HOLE_COMBOS, l1_sum, normalize_l1


class EquityBreakdown(NamedTuple):
    """Hero share of the pot and outcome fractions (sum to 1.0)."""

    hero_equity: float
    hero_win: float
    tie: float
    villain_win: float


def _river_breakdown(
    wa: np.ndarray,
    wb: np.ndarray,
    board5: tuple[int, ...],
) -> EquityBreakdown:
    dm = board_mask(board5)
    valid_a = np.flatnonzero(wa > 0.0)
    valid_b = np.flatnonzero(wb > 0.0)
    ia = valid_a[(COMBO_MASK[valid_a] & dm) == 0]
    ib = valid_b[(COMBO_MASK[valid_b] & dm) == 0]
    if ia.size == 0 or ib.size == 0:
        return EquityBreakdown(0.5, 0.0, 1.0, 0.0)

    ranks_a = np.array([rank_combo_on_board(int(i), board5) for i in ia], dtype=np.int32)
    ranks_b = np.array([rank_combo_on_board(int(j), board5) for j in ib], dtype=np.int32)
    overlap = (COMBO_MASK[ia, None] & COMBO_MASK[ib]) != 0
    weight = wa[ia, None] * wb[ib]
    weight = np.where(overlap, 0.0, weight)
    mass = float(weight.sum())
    if mass <= 0.0:
        return EquityBreakdown(0.5, 0.0, 1.0, 0.0)

    win = (ranks_a[:, None] < ranks_b[None, :]).astype(np.float64)
    tie = (ranks_a[:, None] == ranks_b[None, :]).astype(np.float64)
    loss = (ranks_a[:, None] > ranks_b[None, :]).astype(np.float64)
    win_mass = float((weight * win).sum())
    tie_mass = float((weight * tie).sum())
    loss_mass = float((weight * loss).sum())
    hero_eq = (win_mass + 0.5 * tie_mass) / mass
    return EquityBreakdown(
        hero_eq,
        win_mass / mass,
        tie_mass / mass,
        loss_mass / mass,
    )


def _cached_breakdown(
    wa: np.ndarray,
    wb: np.ndarray,
    pre_a: np.ndarray,
    pre_b: np.ndarray,
    masks: np.ndarray,
    rank_tbl: np.ndarray,
) -> EquityBreakdown:
    ra = rank_tbl[pre_a, :]
    rb = rank_tbl[pre_b, :]
    static_overlap = (COMBO_MASK[pre_a, None] & COMBO_MASK[pre_b]) != 0
    base_w = np.where(static_overlap, 0.0, wa[pre_a][:, None] * wb[pre_b][None, :])
    alive_a = (COMBO_MASK[pre_a, None] & masks[None, :]) == 0
    alive_b = (COMBO_MASK[pre_b, None] & masks[None, :]) == 0

    n_run = ra.shape[1]
    win_mass = 0.0
    tie_mass = 0.0
    loss_mass = 0.0
    mass = 0.0
    for k in range(n_run):
        la = alive_a[:, k]
        lb = alive_b[:, k]
        if not la.any() or not lb.any():
            continue
        w = base_w * (la[:, None] & lb[None, :])
        if not w.any():
            continue
        rai = ra[:, k]
        rbj = rb[:, k]
        better = rai[:, None] < rbj[None, :]
        tied = rai[:, None] == rbj[None, :]
        worse = rai[:, None] > rbj[None, :]
        mass += float(w.sum())
        win_mass += float((w * better).sum())
        tie_mass += float((w * tied).sum())
        loss_mass += float((w * worse).sum())

    if mass <= 0.0:
        return EquityBreakdown(0.5, 0.0, 1.0, 0.0)
    return EquityBreakdown(
        (win_mass + 0.5 * tie_mass) / mass,
        win_mass / mass,
        tie_mass / mass,
        loss_mass / mass,
    )


def exact_equity_breakdown(
    range_a: Sequence[float],
    range_b: Sequence[float],
    board: Sequence[int] = (),
) -> EquityBreakdown:
    """Exact win/tie/loss breakdown on cacheable boards (flop/turn/river)."""
    if len(range_a) != NUM_HOLE_COMBOS or len(range_b) != NUM_HOLE_COMBOS:
        msg = f"ranges must have length {NUM_HOLE_COMBOS}"
        raise ValueError(msg)
    if l1_sum(range_a) <= 0.0 or l1_sum(range_b) <= 0.0:
        return EquityBreakdown(0.5, 0.0, 1.0, 0.0)

    board_tuple = tuple(int(c) for c in board)
    if not cacheable_board(board_tuple):
        msg = "board not cacheable for exact breakdown; use mc_equity_breakdown"
        raise ValueError(msg)

    wa = np.asarray(normalize_l1(range_a), dtype=np.float64)
    wb = np.asarray(normalize_l1(range_b), dtype=np.float64)
    dead0 = board_mask(board_tuple)
    valid_a = np.flatnonzero(wa > 0.0)
    valid_b = np.flatnonzero(wb > 0.0)
    if valid_a.size == 0 or valid_b.size == 0:
        return EquityBreakdown(0.5, 0.0, 1.0, 0.0)

    need = 5 - len(board_tuple)
    if need == 0:
        return _river_breakdown(wa, wb, board_tuple)

    pre_a = valid_a[(COMBO_MASK[valid_a] & dead0) == 0]
    pre_b = valid_b[(COMBO_MASK[valid_b] & dead0) == 0]
    if pre_a.size == 0 or pre_b.size == 0:
        return EquityBreakdown(0.5, 0.0, 1.0, 0.0)
    if pre_a.size * pre_b.size > 25_000:
        msg = "range too wide for exact breakdown"
        raise ValueError(msg)

    masks, rank_tbl = runout_rank_cache().get(board_tuple)
    return _cached_breakdown(wa, wb, pre_a, pre_b, masks, rank_tbl)


def mc_equity_breakdown(
    range_a: Sequence[float],
    range_b: Sequence[float],
    board: Sequence[int] = (),
    *,
    n_samples: int = 20_000,
    seed: int | None = 42,
) -> EquityBreakdown:
    """Monte Carlo breakdown (preflop or wide ranges)."""
    from poker_ai.equity.mc import _rng, _sample_combo
    from poker_ai.equity._tables import COMBO_CARDS
    from poker_ai.core.evaluator import hand_rank_value

    if len(range_a) != NUM_HOLE_COMBOS or len(range_b) != NUM_HOLE_COMBOS:
        msg = f"ranges must have length {NUM_HOLE_COMBOS}"
        raise ValueError(msg)

    wa = np.asarray(normalize_l1(range_a), dtype=np.float64)
    wb = np.asarray(normalize_l1(range_b), dtype=np.float64)
    dead = board_mask(board)
    rng = _rng(seed)
    need = 5 - len(board)

    wins = 0.0
    ties = 0.0
    losses = 0.0
    n = 0
    for _ in range(n_samples):
        ia = _sample_combo(wa, dead, rng)
        if ia is None:
            continue
        da = COMBO_MASK[ia]
        ib = _sample_combo(wb, dead | da, rng)
        if ib is None:
            continue
        lo_a, hi_a = int(COMBO_CARDS[ia, 0]), int(COMBO_CARDS[ia, 1])
        lo_b, hi_b = int(COMBO_CARDS[ib, 0]), int(COMBO_CARDS[ib, 1])
        d = dead | da | COMBO_MASK[ib]
        if need == 0:
            b5 = tuple(int(c) for c in board)
        else:
            deck = np.array([c for c in range(52) if (d >> np.uint64(c)) & 1 == 0], dtype=np.int16)
            runout = rng.choice(deck, size=need, replace=False)
            b5 = tuple(int(c) for c in board) + tuple(int(c) for c in runout)
        ra = hand_rank_value(lo_a, hi_a, *b5)
        rb = hand_rank_value(lo_b, hi_b, *b5)
        n += 1
        if ra < rb:
            wins += 1.0
        elif ra == rb:
            ties += 1.0
        else:
            losses += 1.0

    if n == 0:
        return EquityBreakdown(0.5, 0.0, 1.0, 0.0)
    w = wins / n
    t = ties / n
    lo = losses / n
    return EquityBreakdown(w + 0.5 * t, w, t, lo)


def equity_breakdown(
    range_a: Sequence[float],
    range_b: Sequence[float],
    board: Sequence[int] = (),
    *,
    mode: str = "auto",
    n_samples: int = 20_000,
    seed: int | None = 42,
) -> tuple[EquityBreakdown, str]:
    """Pick exact or MC; returns breakdown and ``mode_used``."""
    board_tuple = tuple(int(c) for c in board)
    use_exact = mode == "exact" or (mode == "auto" and cacheable_board(board_tuple))
    if use_exact:
        try:
            return exact_equity_breakdown(range_a, range_b, board_tuple), "exact"
        except (ValueError, TypeError):
            pass
    return mc_equity_breakdown(range_a, range_b, board_tuple, n_samples=n_samples, seed=seed), "mc"
