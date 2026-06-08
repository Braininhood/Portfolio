"""1326 starting-hand combo indexing and range vectors (Phase 3)."""

from __future__ import annotations

from collections.abc import Sequence

from poker_ai.core.cards import parse_card

NUM_HOLE_COMBOS = 1326  # C(52, 2)


def _rank_value(card_int: int) -> int:
    return card_int // 4


def _suit(card_int: int) -> int:
    return card_int % 4


def combo_index(card_a: int, card_b: int) -> int:
    """Stable index in ``0 .. 1325`` for an unordered hole pair (int card encoding)."""
    if card_a == card_b:
        msg = "hole cards must be two distinct cards"
        raise ValueError(msg)
    lo, hi = (card_a, card_b) if card_a < card_b else (card_b, card_a)
    # C(52,2) with lo < hi: index pairs (lo, hi) in lex order on lo then hi.
    # Count pairs with first card < lo: sum_{i=0}^{lo-1} (51 - i) = lo*52 - lo*(lo+1)/2
    return lo * 52 - (lo * (lo + 1)) // 2 + (hi - lo - 1)


def combo_at_index(idx: int) -> tuple[int, int]:
    """Inverse of :func:`combo_index` (returns ``(lo, hi)`` with ``lo < hi``)."""
    if idx < 0 or idx >= NUM_HOLE_COMBOS:
        msg = f"combo index out of range: {idx}"
        raise ValueError(msg)
    lo = 0
    while True:
        row_start = lo * 52 - (lo * (lo + 1)) // 2
        row_len = 51 - lo
        if idx < row_start + row_len:
            hi = lo + 1 + (idx - row_start)
            return lo, hi
        lo += 1


def combo_index_from_string(hole: str) -> int:
    """Parse ``\"Ah Kd\"`` / ``\"AhKd\"`` style (two cards) into a combo index."""
    s = hole.strip().lower().replace(" ", "")
    if len(s) != 4:
        msg = f"expected four character hole string, got {hole!r}"
        raise ValueError(msg)
    c0 = parse_card(s[:2])
    c1 = parse_card(s[2:])
    return combo_index(c0, c1)


def uniform_range() -> tuple[float, ...]:
    """Uniform distribution over all 1326 combos (L1 norm = 1)."""
    w = 1.0 / float(NUM_HOLE_COMBOS)
    return tuple(w for _ in range(NUM_HOLE_COMBOS))


def one_hot_range(card_a: int, card_b: int) -> tuple[float, ...]:
    """Delta range (exact hole) as a one-hot vector over 1326 combos."""
    idx = combo_index(card_a, card_b)
    return tuple(1.0 if i == idx else 0.0 for i in range(NUM_HOLE_COMBOS))


def one_hot_range_from_hole_string(hole: str) -> tuple[float, ...]:
    """One-hot from a two-card space-separated or concatenated string."""
    idx = combo_index_from_string(hole)
    lo, hi = combo_at_index(idx)
    return one_hot_range(lo, hi)


def combo_from_index(idx: int) -> tuple[int, int]:
    """Return the two card ints (unordered) for combo ``idx``."""
    lo, hi = combo_at_index(idx)
    return lo, hi


def normalize_l1(weights: Sequence[float], *, eps: float = 1e-12) -> tuple[float, ...]:
    """Project onto the probability simplex (non-negative, sum = 1); zeros stay zero."""
    if len(weights) == 0:
        return ()
    s = sum(max(0.0, float(x)) for x in weights)
    if s <= eps:
        return uniform_range()
    return tuple(max(0.0, float(x)) / s for x in weights)


def l1_sum(weights: Sequence[float]) -> float:
    return float(sum(float(x) for x in weights))


def _tri(n: int) -> int:
    return n * (n + 1) // 2


def isomorphic_preflop_id(card_a: int, card_b: int) -> int:
    """Index in ``0..168`` for the 169 isomorphic NLH preflop classes (pair / suited / offsuit)."""
    r0, r1 = _rank_value(card_a), _rank_value(card_b)
    s0, s1 = _suit(card_a), _suit(card_b)
    hi_r, lo_r = (r0, r1) if r0 >= r1 else (r1, r0)
    suited = s0 == s1
    if hi_r == lo_r:
        return 12 - hi_r
    # Non-pairs: same (high, low) shell index for suited vs offsuit.
    core = _tri(12) - _tri(hi_r) + (hi_r - 1 - lo_r)
    if suited:
        return 13 + core
    return 13 + 78 + core
