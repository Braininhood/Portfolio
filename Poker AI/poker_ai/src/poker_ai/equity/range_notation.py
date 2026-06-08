"""Parse common poker range strings (TT+, AKs, AhKd, random) into 1326 combo weights."""

from __future__ import annotations

import re
from collections.abc import Sequence

from poker_ai.core.cards import parse_card
from poker_ai.equity._tables import COMBO_CARDS, COMBO_MASK, board_mask
from poker_ai.features.range import NUM_HOLE_COMBOS, combo_index, normalize_l1, uniform_range

_RANKS = "23456789TJQKA"
_PAIR_RE = re.compile(r"^([2-9TJQKA])\1$")
_PAIR_PLUS_RE = re.compile(r"^([2-9TJQKA])\1\+$")
_PAIR_RANGE_RE = re.compile(r"^([2-9TJQKA])\1-([2-9TJQKA])\2$")
_SUITED_PLUS_RE = re.compile(r"^([2-9TJQKA])([2-9TJQKA])s\+$")
_HAND_RE = re.compile(r"^([2-9TJQKA])([2-9TJQKA])([so]?)(\+)?$", re.IGNORECASE)


def _rank_idx(ch: str) -> int:
    c = ch.upper()
    if c == "T":
        return _RANKS.index("T")
    return _RANKS.index(c)


def _combo_class(lo: int, hi: int) -> tuple[int, int, bool, bool]:
    """Return (high_rank, low_rank, is_pair, is_suited) for a combo."""
    r0, r1 = lo // 4, hi // 4
    s0, s1 = lo % 4, hi % 4
    if r0 == r1:
        return r0, r0, True, False
    hi_r, lo_r = (r0, r1) if r0 >= r1 else (r1, r0)
    return hi_r, lo_r, False, s0 == s1


def _empty_weights() -> list[float]:
    return [0.0] * NUM_HOLE_COMBOS


def _mark_combo(weights: list[float], idx: int, dead: int) -> None:
    if (COMBO_MASK[idx] & dead) != 0:
        return
    weights[idx] = 1.0


def _mark_pair(weights: list[float], rank: int, dead: int) -> None:
    for i in range(NUM_HOLE_COMBOS):
        lo, hi = int(COMBO_CARDS[i, 0]), int(COMBO_CARDS[i, 1])
        hr, lr, is_pair, _ = _combo_class(lo, hi)
        if is_pair and hr == rank:
            _mark_combo(weights, i, dead)


def _mark_suited(weights: list[float], hi: int, lo: int, dead: int) -> None:
    for i in range(NUM_HOLE_COMBOS):
        c_lo, c_hi = int(COMBO_CARDS[i, 0]), int(COMBO_CARDS[i, 1])
        hr, lr, is_pair, suited = _combo_class(c_lo, c_hi)
        if not is_pair and suited and hr == hi and lr == lo:
            _mark_combo(weights, i, dead)


def _mark_offsuit(weights: list[float], hi: int, lo: int, dead: int) -> None:
    for i in range(NUM_HOLE_COMBOS):
        c_lo, c_hi = int(COMBO_CARDS[i, 0]), int(COMBO_CARDS[i, 1])
        hr, lr, is_pair, suited = _combo_class(c_lo, c_hi)
        if not is_pair and not suited and hr == hi and lr == lo:
            _mark_combo(weights, i, dead)


def _mark_any(weights: list[float], hi: int, lo: int, dead: int) -> None:
    _mark_suited(weights, hi, lo, dead)
    _mark_offsuit(weights, hi, lo, dead)


def _parse_token(token: str, weights: list[float], dead: int) -> None:
    t = token.strip()
    if not t:
        return
    low = t.lower()
    if low in ("random", "any", "*"):
        for i in range(NUM_HOLE_COMBOS):
            if (COMBO_MASK[i] & dead) == 0:
                weights[i] = 1.0
        return

  # Specific hole cards: "Ah Kd" or "AhKd"
    compact = low.replace(" ", "")
    if len(compact) == 4:
        try:
            c0, c1 = parse_card(compact[:2]), parse_card(compact[2:])
            idx = combo_index(c0, c1)
            _mark_combo(weights, idx, dead)
            return
        except ValueError:
            pass

    m = _PAIR_PLUS_RE.match(t.upper())
    if m:
        r0 = _rank_idx(m.group(1))
        for r in range(r0, len(_RANKS)):
            _mark_pair(weights, r, dead)
        return

    m = _PAIR_RANGE_RE.match(t.upper())
    if m:
        r0, r1 = _rank_idx(m.group(1)), _rank_idx(m.group(2))
        lo_r, hi_r = (r0, r1) if r0 <= r1 else (r1, r0)
        for r in range(lo_r, hi_r + 1):
            _mark_pair(weights, r, dead)
        return

    m = _PAIR_RE.match(t.upper())
    if m:
        _mark_pair(weights, _rank_idx(m.group(1)), dead)
        return

    m = _SUITED_PLUS_RE.match(t.upper())
    if m:
        hi, lo = _rank_idx(m.group(1)), _rank_idx(m.group(2))
        if hi <= lo:
            msg = f"invalid suited+ token: {token!r}"
            raise ValueError(msg)
        for lr in range(lo, hi):
            _mark_suited(weights, hi, lr, dead)
        return

    m = _HAND_RE.match(t.upper())
    if m:
        hi, lo = _rank_idx(m.group(1)), _rank_idx(m.group(2))
        if hi == lo:
            _mark_pair(weights, hi, dead)
            return
        if hi < lo:
            hi, lo = lo, hi
        suffix = (m.group(3) or "").lower()
        plus = m.group(4) == "+"
        if suffix == "s":
            if plus:
                for lr in range(lo, hi):
                    _mark_suited(weights, hi, lr, dead)
            else:
                _mark_suited(weights, hi, lo, dead)
        elif suffix == "o":
            if plus:
                for lr in range(lo, hi):
                    _mark_offsuit(weights, hi, lr, dead)
            else:
                _mark_offsuit(weights, hi, lo, dead)
        else:
            if plus:
                for lr in range(lo, hi):
                    _mark_any(weights, hi, lr, dead)
            else:
                _mark_any(weights, hi, lo, dead)
        return

    msg = f"unrecognized range token: {token!r}"
    raise ValueError(msg)


def range_from_notation(
    notation: str,
    *,
    dead_cards: Sequence[int] = (),
) -> tuple[float, ...]:
    """Build a normalized 1326-vector from ``random``, ``TT+,AKs``, or ``AhKd`` style input."""
    raw = notation.strip()
    if not raw or raw.lower() in ("random", "any", "*"):
        w = list(uniform_range())
        dead = board_mask(dead_cards)
        if dead:
            w = [0.0 if (COMBO_MASK[i] & dead) else w[i] for i in range(NUM_HOLE_COMBOS)]
        return normalize_l1(w)

    dead = board_mask(dead_cards)
    weights = _empty_weights()
    for part in raw.split(","):
        part = part.strip()
        if part:
            _parse_token(part, weights, dead)

    if sum(weights) <= 0.0:
        msg = f"range has no valid combos after card removal: {notation!r}"
        raise ValueError(msg)
    return normalize_l1(weights)
