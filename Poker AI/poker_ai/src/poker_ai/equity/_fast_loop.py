"""Runout aggregation — Numba triple loop (default) with NumPy fallback."""

from __future__ import annotations

import os

import numpy as np

_USE_NUMBA = os.environ.get("POKER_AI_EQUITY_NO_NUMBA", "").lower() not in ("1", "true", "yes")


def _accumulate_numpy_sliced(
    ra: np.ndarray,
    rb: np.ndarray,
    base_w: np.ndarray,
    alive_a: np.ndarray,
    alive_b: np.ndarray,
) -> tuple[float, float]:
    """2-D slice per runout (avoids huge ``(na, nb, n_run)`` temporaries)."""
    n_run = ra.shape[1]
    win_mass = 0.0
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
        outcome = better.astype(np.float64) + tied.astype(np.float64) * 0.5
        mass += float(w.sum())
        win_mass += float((w * outcome).sum())
    return win_mass, mass


if _USE_NUMBA:
    from numba import njit

    @njit(cache=False, fastmath=True)
    def _accumulate_numba(
        ra: np.ndarray,
        rb: np.ndarray,
        base_w: np.ndarray,
        alive_a: np.ndarray,
        alive_b: np.ndarray,
    ) -> tuple[float, float]:
        na, n_run = ra.shape
        nb = rb.shape[0]
        win_mass = 0.0
        mass = 0.0
        for k in range(n_run):
            for i in range(na):
                if not alive_a[i, k]:
                    continue
                rai = ra[i, k]
                for j in range(nb):
                    if not alive_b[j, k]:
                        continue
                    w = base_w[i, j]
                    if w == 0.0:
                        continue
                    mass += w
                    rbj = rb[j, k]
                    if rai < rbj:
                        win_mass += w
                    elif rai == rbj:
                        win_mass += 0.5 * w
        return win_mass, mass

    _numba_warmed = False

    def _warm_numba() -> None:
        global _numba_warmed
        if _numba_warmed:
            return
        ra = np.array([[1, 2]], dtype=np.int32)
        rb = np.array([[3, 4]], dtype=np.int32)
        bw = np.ones((1, 1), dtype=np.float64)
        aa = np.ones((1, 2), dtype=np.bool_)
        ab = np.ones((1, 2), dtype=np.bool_)
        _accumulate_numba(ra, rb, bw, aa, ab)
        _numba_warmed = True


def accumulate_runout_equity(
    ra: np.ndarray,
    rb: np.ndarray,
    base_w: np.ndarray,
    alive_a: np.ndarray,
    alive_b: np.ndarray,
) -> tuple[float, float]:
    """Sum weighted win/tie mass over all runouts (``ra``/``rb`` shape ``(n, n_runouts)``)."""
    if _USE_NUMBA:
        _warm_numba()
        return _accumulate_numba(ra, rb, base_w, alive_a, alive_b)
    return _accumulate_numpy_sliced(ra, rb, base_w, alive_a, alive_b)
