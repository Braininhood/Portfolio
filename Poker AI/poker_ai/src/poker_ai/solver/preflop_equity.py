"""Preflop deal sampling: random buckets vs Phase-4 MC equity buckets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

from poker_ai.features.range import (
    NUM_HOLE_COMBOS,
    combo_at_index,
    combo_index,
    one_hot_range,
    uniform_range,
)
from poker_ai.solver.abstraction import NUM_EQUITY_BUCKETS, equity_bucket

EquityMode = Literal["random", "real"]

_UNIFORM = uniform_range()
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_COMBO_CACHE_DIR = _PROJECT_ROOT / "artifacts" / "solver" / "cache"


@dataclass(frozen=True, slots=True)
class PreflopDeal:
    """Root deal: per-seat equity buckets and optional combo indices (real mode)."""

    buckets: tuple[int, ...]
    combos: tuple[int, ...] | None = None


def sample_random_deals(
    num_players: int,
    chance_samples: int,
    seed: int,
) -> tuple[PreflopDeal, ...]:
    """Legacy abstraction: independent uniform buckets per seat."""
    rng = np.random.default_rng(seed)
    return tuple(
        PreflopDeal(
            buckets=tuple(int(rng.integers(0, NUM_EQUITY_BUCKETS)) for _ in range(num_players)),
            combos=None,
        )
        for _ in range(chance_samples)
    )


def _combo_cache_path(mc_samples: int) -> Path:
    return _COMBO_CACHE_DIR / f"combo_equity_vs_uniform_n{mc_samples}.npy"


def _load_combo_cache(mc_samples: int) -> tuple[float, ...] | None:
    path = _combo_cache_path(mc_samples)
    if not path.is_file():
        return None
    arr = np.load(path)
    if arr.shape != (NUM_HOLE_COMBOS,):
        return None
    return tuple(float(x) for x in arr)


def _save_combo_cache(mc_samples: int, table: tuple[float, ...]) -> None:
    path = _combo_cache_path(mc_samples)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.asarray(table, dtype=np.float64))


def _build_combo_equity_table(mc_samples: int) -> tuple[float, ...]:
    cached = _load_combo_cache(mc_samples)
    if cached is not None:
        return cached

    from poker_ai.equity.mc import mc_equity_range_vs_range

    print(
        f"Building preflop combo equity table ({NUM_HOLE_COMBOS} combos × "
        f"{mc_samples} MC samples; CPU — cached to {_combo_cache_path(mc_samples).name})..."
    )
    table: list[float] = []
    step = max(1, NUM_HOLE_COMBOS // 10)
    for idx in range(NUM_HOLE_COMBOS):
        if idx % step == 0 or idx == NUM_HOLE_COMBOS - 1:
            print(
                f"  equity table {idx + 1}/{NUM_HOLE_COMBOS} combos…",
                flush=True,
            )
        lo, hi = combo_at_index(idx)
        hero = one_hot_range(lo, hi)
        eq = float(
            mc_equity_range_vs_range(
                hero,
                _UNIFORM,
                (),
                n_samples=mc_samples,
                seed=10_000 + idx,
            )
        )
        table.append(eq)
    out = tuple(table)
    _save_combo_cache(mc_samples, out)
    return out


_COMBO_EQUITY: dict[int, tuple[float, ...]] = {}


def warm_combo_equity_table(mc_samples: int) -> None:
    """Load or build the 1326-combo preflop equity table once (before parallel workers)."""
    if mc_samples not in _COMBO_EQUITY:
        _COMBO_EQUITY[mc_samples] = _build_combo_equity_table(mc_samples)


def combo_preflop_equity(combo_idx: int, *, mc_samples: int) -> float:
    """Hero combo equity vs uniform random range (empty board, Monte Carlo)."""
    warm_combo_equity_table(mc_samples)
    return _COMBO_EQUITY[mc_samples][combo_idx]


def bucket_for_combo(combo_idx: int, *, mc_samples: int) -> int:
    return equity_bucket(combo_preflop_equity(combo_idx, mc_samples=mc_samples))


def sample_real_equity_deals(
    num_players: int,
    chance_samples: int,
    seed: int,
    *,
    mc_samples: int,
) -> tuple[PreflopDeal, ...]:
    """Deal disjoint hole combos; bucket each seat by preflop equity vs random range."""
    rng = np.random.default_rng(seed)
    cards_needed = 2 * num_players
    if cards_needed > 52:
        msg = f"cannot deal {num_players} players from 52 cards"
        raise ValueError(msg)

    deals: list[PreflopDeal] = []
    for _ in range(chance_samples):
        deck = np.arange(52, dtype=np.int16)
        rng.shuffle(deck)
        buckets: list[int] = []
        combos: list[int] = []
        for p in range(num_players):
            c0 = int(deck[2 * p])
            c1 = int(deck[2 * p + 1])
            lo, hi = (c0, c1) if c0 < c1 else (c1, c0)
            idx = combo_index(lo, hi)
            combos.append(idx)
            buckets.append(bucket_for_combo(idx, mc_samples=mc_samples))
        deals.append(PreflopDeal(buckets=tuple(buckets), combos=tuple(combos)))
    return tuple(deals)


def build_chance_deals(
    *,
    num_players: int,
    chance_samples: int,
    seed: int,
    equity_mode: EquityMode = "random",
    mc_samples: int = 2000,
) -> tuple[PreflopDeal, ...]:
    if equity_mode == "real":
        return sample_real_equity_deals(num_players, chance_samples, seed, mc_samples=mc_samples)
    return sample_random_deals(num_players, chance_samples, seed)
