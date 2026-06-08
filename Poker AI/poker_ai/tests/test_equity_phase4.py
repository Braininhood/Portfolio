"""Phase 4 — equity exit criteria and unit tests.

Fast default run (no multi-minute preflop enumeration)::

  $env:POKER_AI_SKIP_PERF = "1"
  python -m pytest tests/test_equity_phase4.py -q --no-cov

Full MC + literature check (slower)::

  python -m pytest tests/test_equity_phase4.py -q --no-cov -m slow
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np
import pytest

from poker_ai.core.cards import parse_card
from poker_ai.equity import (
    EquityCache,
    aa_vs_random_preflop_equity,
    equity_range_vs_range,
    exact_equity_hands,
    exact_equity_range_vs_range,
    fft_equity_distribution_convolution,
    mc_equity_hands,
    mc_equity_range_vs_range,
    mixed_range_equity,
    nonzero_combo_indices,
    per_combo_equity_histogram,
)
from poker_ai.features.range import NUM_HOLE_COMBOS, combo_index, normalize_l1, uniform_range

# Serial table build in tests (ProcessPool + pytest on Windows can hang on teardown).
os.environ.setdefault("POKER_AI_EQUITY_WORKERS", "1")


def _aa_range() -> list[float]:
    aa = [
        combo_index(parse_card("As"), parse_card("Ah")),
        combo_index(parse_card("As"), parse_card("Ad")),
        combo_index(parse_card("As"), parse_card("Ac")),
        combo_index(parse_card("Ah"), parse_card("Ad")),
        combo_index(parse_card("Ah"), parse_card("Ac")),
        combo_index(parse_card("Ad"), parse_card("Ac")),
    ]
    r = [0.0] * NUM_HOLE_COMBOS
    for i in aa:
        r[i] = 1.0 / 6.0
    return r


def _sparse_range(n: int, *, seed: int = 7) -> list[float]:
    rng = np.random.default_rng(seed)
    idx = rng.choice(NUM_HOLE_COMBOS, size=n, replace=False)
    w = [0.0] * NUM_HOLE_COMBOS
    for i in idx:
        w[int(i)] = 1.0
    return list(normalize_l1(w))


@pytest.mark.slow
@pytest.mark.skipif(os.environ.get("POKER_AI_SKIP_PERF") == "1", reason="slow MC skipped")
def test_aa_vs_random_preflop_literature() -> None:
    eq = aa_vs_random_preflop_equity()
    assert eq == pytest.approx(0.852, abs=1e-3)


def test_exact_aces_vs_kings_on_flop() -> None:
    """Preflop exact enumeration is ~1.7M runouts; use a flop for a fast regression."""
    aa = (parse_card("As"), parse_card("Ah"))
    kk = (parse_card("Ks"), parse_card("Kh"))
    flop = (parse_card("2c"), parse_card("3d"), parse_card("4h"))
    eq = exact_equity_hands(aa, kk, flop)
    assert eq > 0.85


def test_mc_reproducible_with_seed() -> None:
    aa = (parse_card("As"), parse_card("Ah"))
    kk = (parse_card("Ks"), parse_card("Kh"))
    e1 = mc_equity_hands(aa, kk, (), n_samples=5_000, seed=99)
    e2 = mc_equity_hands(aa, kk, (), n_samples=5_000, seed=99)
    assert e1 == e2


def test_exact_matches_mc_on_river() -> None:
    board = (
        parse_card("2c"),
        parse_card("3d"),
        parse_card("4h"),
        parse_card("5s"),
        parse_card("9c"),
    )
    ha = (parse_card("As"), parse_card("Ah"))
    hb = (parse_card("Kd"), parse_card("Kc"))
    ex = exact_equity_hands(ha, hb, board)
    mc = mc_equity_hands(ha, hb, board, n_samples=5_000, seed=1)
    assert ex == pytest.approx(mc, abs=0.02)


@pytest.mark.skipif(os.environ.get("POKER_AI_SKIP_PERF") == "1", reason="perf skipped")
def test_range_vs_range_flop_performance() -> None:
    flop = (parse_card("Ah"), parse_card("Kd"), parse_card("7c"))
    ra = _sparse_range(100, seed=1)
    rb = _sparse_range(100, seed=2)
    _ = equity_range_vs_range(ra, rb, flop)
    t0 = time.perf_counter()
    eq = equity_range_vs_range(ra, rb, flop)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert 0.0 <= eq <= 1.0
    assert elapsed_ms < 50.0, f"cached flop range-vs-range took {elapsed_ms:.1f} ms"


def test_equity_cache_hit_fast(tmp_path: Path) -> None:
    flop = (parse_card("2h"), parse_card("3d"), parse_card("4c"))
    ra = _sparse_range(50, seed=3)
    rb = _sparse_range(50, seed=4)
    cache = EquityCache(tmp_path / "eq_cache")

    eq = cache.lookup_or_compute(ra, rb, flop, equity_range_vs_range, persist=True)
    assert 0.0 <= eq <= 1.0

    t0 = time.perf_counter()
    for _ in range(200):
        hit = cache.get(ra, rb, flop)
        assert hit is not None
        _ = hit + 0.0
    per_lookup_us = (time.perf_counter() - t0) / 200.0 * 1e6
    assert per_lookup_us < 1000.0, f"cache lookup {per_lookup_us:.0f} µs"


def test_fft_convolution_normalizes() -> None:
    a = np.array([0.0, 0.5, 0.5])
    b = np.array([1.0, 0.0, 0.0])
    out = fft_equity_distribution_convolution(a, b)
    assert out.sum() == pytest.approx(1.0)
    assert out[0] == pytest.approx(0.0)
    assert out[2] == pytest.approx(0.5)


def test_nonzero_combo_indices_respects_board() -> None:
    board = [parse_card("As"), parse_card("Ah")]
    u = uniform_range()
    idx = nonzero_combo_indices(u, board)
    from poker_ai.equity._tables import COMBO_MASK

    dm = np.uint64(0)
    for c in board:
        dm |= np.uint64(1) << np.uint64(c)
    assert np.all((COMBO_MASK[idx] & dm) == 0)


def test_mixed_range_equity_in_unit_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid 40× nested exact solves in CI; smoke-test the mixer only."""
    import poker_ai.equity.range_vs_range as rvr

    fake_hist = np.zeros(11, dtype=np.float64)
    fake_hist[8] = 1.0
    monkeypatch.setattr(rvr, "per_combo_equity_histogram", lambda *_a, **_k: fake_hist)
    ra = _sparse_range(10, seed=10)
    rb = _sparse_range(10, seed=11)
    flop = (parse_card("Tc"), parse_card("9d"), parse_card("2s"))
    eq = mixed_range_equity(0.7, ra, rb, rb, flop, n_buckets=11)
    assert eq == pytest.approx(0.8, abs=1e-9)


def test_per_combo_histogram_sums_to_one() -> None:
    hero = [0.0] * NUM_HOLE_COMBOS
    hero[combo_index(parse_card("As"), parse_card("Ah"))] = 1.0
    rb = _sparse_range(15, seed=12)
    flop = (parse_card("Qs"), parse_card("Jd"), parse_card("2c"))
    hist = per_combo_equity_histogram(hero, rb, flop, n_buckets=21)
    assert hist.sum() == pytest.approx(1.0, abs=1e-9)


def test_exact_range_bad_length() -> None:
    with pytest.raises(ValueError):
        exact_equity_range_vs_range([1.0], [1.0], ())


@pytest.mark.slow
@pytest.mark.skipif(os.environ.get("POKER_AI_SKIP_PERF") == "1", reason="perf skipped")
def test_mc_range_vs_range_aa_random_smoke() -> None:
    eq = mc_equity_range_vs_range(_aa_range(), uniform_range(), (), n_samples=50_000, seed=42)
    assert eq == pytest.approx(0.852, abs=5e-3)


def test_equity_known_flop_spot() -> None:
    flop = (parse_card("2c"), parse_card("3d"), parse_card("4h"))
    hero = [0.0] * NUM_HOLE_COMBOS
    hero[combo_index(parse_card("As"), parse_card("Ah"))] = 1.0
    villain = [0.0] * NUM_HOLE_COMBOS
    villain[combo_index(parse_card("Ks"), parse_card("Kh"))] = 1.0
    eq = equity_range_vs_range(hero, villain, flop)
    assert eq > 0.85


def test_cache_set_get_roundtrip(tmp_path: Path) -> None:
    cache = EquityCache(tmp_path / "c2")
    ra = _aa_range()
    rb = uniform_range()
    board = (parse_card("2c"), parse_card("3d"), parse_card("4h"))
    cache.set(ra, rb, board, 0.75, persist=False)
    assert cache.get(ra, rb, board) == pytest.approx(0.75)


def test_cache_persist_reload(tmp_path: Path) -> None:
    path = tmp_path / "persist"
    flop = (parse_card("5c"), parse_card("6d"), parse_card("7h"))
    ra = _sparse_range(20, seed=20)
    rb = _sparse_range(20, seed=21)
    c1 = EquityCache(path)
    eq1 = c1.lookup_or_compute(ra, rb, flop, equity_range_vs_range, persist=True)
    c2 = EquityCache(path)
    assert c2.get(ra, rb, flop) == pytest.approx(eq1)


def test_cache_bad_range_length(tmp_path: Path) -> None:
    cache = EquityCache(tmp_path / "bad")
    with pytest.raises(ValueError):
        cache.set([1.0], [1.0], (), 0.5)


def test_cache_parquet_duckdb_roundtrip(tmp_path: Path) -> None:
    from poker_ai.equity.cache import _read_parquet, _write_parquet

    path = tmp_path / "disk.parquet"
    _write_parquet(path, {"deadbeef": 0.42})
    loaded = _read_parquet(path)
    assert loaded["deadbeef"] == pytest.approx(0.42)


def test_hand_rank_value_int_bad_count() -> None:
    from poker_ai.core.evaluator import hand_rank_value_int

    with pytest.raises(ValueError):
        hand_rank_value_int(0, 1, 2, 3)


def test_mc_hands_errors() -> None:
    aa = (parse_card("As"), parse_card("As"))
    kk = (parse_card("Ks"), parse_card("Kh"))
    with pytest.raises(ValueError):
        mc_equity_hands(aa, kk, ())
    aa2 = (parse_card("As"), parse_card("Ah"))
    with pytest.raises(ValueError):
        mc_equity_hands(aa2, aa2, ())
    with pytest.raises(ValueError):
        mc_equity_hands(aa2, kk, (parse_card("As"),))
    six = tuple(parse_card(x) for x in ("2c", "3d", "4h", "5s", "9c", "th"))
    with pytest.raises(ValueError):
        mc_equity_hands(aa2, kk, six)


def test_mc_hands_river_win_tie_lose() -> None:
    board = tuple(parse_card(x) for x in ("2c", "3d", "4h", "5s", "9c"))
    nuts = (parse_card("As"), parse_card("Ah"))
    second = (parse_card("Kd"), parse_card("Kc"))
    assert mc_equity_hands(nuts, second, board, n_samples=1) == 1.0
    assert mc_equity_hands(second, nuts, board, n_samples=1) == 0.0
    chop_board = tuple(parse_card(x) for x in ("ah", "kh", "qh", "jh", "th"))
    assert (
        mc_equity_hands(
            (parse_card("2c"), parse_card("3d")),
            (parse_card("4c"), parse_card("5d")),
            chop_board,
            n_samples=1,
        )
        == 0.5
    )


def test_mc_range_errors_and_river() -> None:
    with pytest.raises(ValueError):
        mc_equity_range_vs_range([1.0], [1.0], ())
    six = tuple(parse_card(x) for x in ("2c", "3d", "4h", "5s", "9c", "th"))
    with pytest.raises(ValueError):
        mc_equity_range_vs_range(uniform_range(), uniform_range(), six)
    board = tuple(parse_card(x) for x in ("2c", "3d", "4h", "5s", "9c"))
    hero = [0.0] * NUM_HOLE_COMBOS
    hero[combo_index(parse_card("As"), parse_card("Ah"))] = 1.0
    villain = [0.0] * NUM_HOLE_COMBOS
    villain[combo_index(parse_card("Kd"), parse_card("Kc"))] = 1.0
    assert mc_equity_range_vs_range(hero, villain, board, n_samples=500, seed=1) > 0.9


def test_exact_hands_errors_and_tie() -> None:
    from poker_ai.core.evaluator import hand_rank_value_int

    aa = (parse_card("As"), parse_card("Ah"))
    with pytest.raises(ValueError):
        exact_equity_hands(aa, aa, ())
    with pytest.raises(ValueError):
        exact_equity_hands(aa, (parse_card("Ks"), parse_card("Kh")), (parse_card("As"),))
    chop_board = tuple(parse_card(x) for x in ("ah", "kh", "qh", "jh", "th"))
    chop_a = (parse_card("2c"), parse_card("3d"))
    chop_b = (parse_card("4c"), parse_card("5d"))
    assert exact_equity_hands(chop_a, chop_b, chop_board) == 0.5
    assert hand_rank_value_int(*chop_a, *chop_board) == hand_rank_value_int(*chop_b, *chop_board)


def test_exact_range_edge_cases() -> None:
    from poker_ai.equity._tables import fill_ranks_on_board, iter_runout_completions

    z = [0.0] * NUM_HOLE_COMBOS
    assert exact_equity_range_vs_range(z, uniform_range(), ()) == 0.5
    six = tuple(parse_card(x) for x in ("2c", "3d", "4h", "5s", "9c", "th"))
    with pytest.raises(ValueError):
        exact_equity_range_vs_range(uniform_range(), uniform_range(), six)
    with pytest.raises(ValueError):
        exact_equity_range_vs_range(uniform_range(), uniform_range(), ())
    turn = (parse_card("Ah"), parse_card("Kd"), parse_card("7c"), parse_card("2s"))
    eq = exact_equity_range_vs_range(_aa_range(), _sparse_range(20, seed=22), turn)
    assert 0.0 < eq < 1.0
    list(iter_runout_completions(turn[:4]))
    board5 = tuple(parse_card(x) for x in ("2c", "3d", "4h", "5s", "9c"))
    buf = np.empty(3, dtype=np.int32)
    fill_ranks_on_board(np.array([0, 1, 2], dtype=np.int32), board5, buf)
    assert buf[0] > 0


def test_range_helpers() -> None:
    from poker_ai.equity.range_vs_range import combo_equity_vs_range

    assert nonzero_combo_indices(uniform_range()).size == NUM_HOLE_COMBOS
    assert nonzero_combo_indices(uniform_range(), None).size == NUM_HOLE_COMBOS
    empty = [0.0] * NUM_HOLE_COMBOS
    assert per_combo_equity_histogram(empty, uniform_range(), ()).sum() == 0.0
    flop = (parse_card("2c"), parse_card("3d"), parse_card("4h"))
    eq = combo_equity_vs_range(0, _sparse_range(15, seed=13), flop)
    assert 0.0 <= eq <= 1.0
    with pytest.raises(ValueError):
        fft_equity_distribution_convolution(np.zeros((2, 2)), np.zeros(2))
    with pytest.raises(ValueError):
        fft_equity_distribution_convolution(np.zeros(3), np.zeros(2))
    with pytest.raises(ValueError, match="alpha"):
        mixed_range_equity(1.5, uniform_range(), uniform_range(), uniform_range(), flop)
    hist = np.array([1.0, 0.0])
    assert fft_equity_distribution_convolution(hist, hist).sum() == pytest.approx(1.0)


def test_cached_runout_zero_mass(monkeypatch: pytest.MonkeyPatch) -> None:
    from poker_ai.equity._fast_loop import accumulate_runout_equity
    from poker_ai.equity.exact import _cached_runout_equity

    n = 3
    ra = np.array([[1, 2, 3]], dtype=np.int32)
    rb = np.array([[4, 5, 6]], dtype=np.int32)
    base_w = np.ones((1, 1), dtype=np.float64)
    alive = np.ones((1, n), dtype=bool)
    win_mass, mass = accumulate_runout_equity(ra, rb, base_w, alive, alive)
    assert mass > 0.0
    assert 0.0 <= win_mass / mass <= 1.0

    monkeypatch.setattr(
        "poker_ai.equity.exact.accumulate_runout_equity",
        lambda *_a, **_k: (0.0, 0.0),
    )
    assert (
        _cached_runout_equity(
            np.array([1.0]),
            np.array([1.0]),
            np.array([0]),
            np.array([0]),
            np.zeros(n, dtype=np.uint64),
            np.zeros((1, n), dtype=np.int32),
        )
        == 0.5
    )
