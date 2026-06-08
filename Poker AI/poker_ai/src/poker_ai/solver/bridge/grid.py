"""Curated postflop spot grids for overnight teacher runs (Phase 7)."""

from __future__ import annotations

import random
from itertools import product

from poker_ai.solver.bridge.schemas import SpotSpec

# Benchmark-style ranges (TexasSolver syntax).
_DEFAULT_OOP = (
    "AA,KK,QQ,JJ,TT,99:0.75,88:0.75,77:0.5,AK,AQs,AJs,ATs,KQs,QJs,JTs,T9s,98s,87s,76s,65s"
)
_DEFAULT_IP = (
    "QQ:0.5,JJ:0.75,TT,99,88,77,66,55,44,33,22,"
    "AQs,AQo:0.75,AJs,ATs,KQs,KJs,QJs,JTs,T9s,98s,87s,76s,65s,54s"
)

_FLOP_BOARDS: tuple[str, ...] = (
    "Qs,Jh,2h",
    "As,Kd,7c",
    "9h,8h,3d",
    "Tc,Td,4s",
    "Kh,Qh,5h",
    "2c,2d,9s",
    "Jc,7d,3s",
    "Ad,6c,2s",
)

_SPR_BUCKETS: tuple[tuple[int, int], ...] = (
    (10, 40),
    (10, 95),
    (20, 60),
    (15, 120),
    (8, 25),
)

_DEFAULT_BET_SIZES: tuple[tuple[str, str, str, str], ...] = (
    ("oop", "flop", "bet", "100"),
    ("oop", "flop", "raise", "50"),
    ("oop", "flop", "allin", "allin"),
    ("ip", "flop", "bet", "100"),
    ("ip", "flop", "raise", "50"),
    ("ip", "flop", "allin", "allin"),
    ("oop", "turn", "bet", "100"),
    ("ip", "turn", "bet", "100"),
    ("oop", "river", "bet", "100"),
    ("ip", "river", "bet", "100"),
)


def default_bet_sizes() -> tuple[tuple[str, str, str, str], ...]:
    return _DEFAULT_BET_SIZES


def generate_spot_grid(
    *,
    n_spots: int,
    seed: int = 42,
    range_oop: str = _DEFAULT_OOP,
    range_ip: str = _DEFAULT_IP,
) -> list[SpotSpec]:
    """Build ``n_spots`` diverse HU postflop spots (board × SPR × tree id)."""
    from poker_ai.solver.bridge.cache import cache_key

    rng = random.Random(seed)
    combos = list(product(_FLOP_BOARDS, _SPR_BUCKETS, ("default_v1", "aggro_v1")))
    rng.shuffle(combos)
    specs: list[SpotSpec] = []
    seen: set[str] = set()
    for board, (pot, eff), tree_id in combos:
        bet_sizes = _DEFAULT_BET_SIZES
        if tree_id == "aggro_v1":
            extra = (("ip", "flop", "bet", "66"), ("oop", "turn", "raise", "75"))
            bet_sizes = (*_DEFAULT_BET_SIZES, *extra)
        spec = SpotSpec(
            board=board,
            pot_chips=pot,
            effective_stack=eff,
            range_oop=range_oop,
            range_ip=range_ip,
            bet_sizes=bet_sizes,
            sizing_tree_id=tree_id,
        )
        key = cache_key(spec)
        if key in seen:
            continue
        seen.add(key)
        specs.append(spec)
        if len(specs) >= n_spots:
            return specs
    attempt = 0
    while len(specs) < n_spots and attempt < n_spots * 20:
        attempt += 1
        board = rng.choice(_FLOP_BOARDS)
        pot, eff = rng.choice(_SPR_BUCKETS)
        spec = SpotSpec(
            board=board,
            pot_chips=pot + (attempt % 3),
            effective_stack=eff + (attempt % 5),
            range_oop=range_oop,
            range_ip=range_ip,
            bet_sizes=_DEFAULT_BET_SIZES,
            sizing_tree_id=f"random_v1_{attempt}",
        )
        key = cache_key(spec)
        if key in seen:
            continue
        seen.add(key)
        specs.append(spec)
    return specs
