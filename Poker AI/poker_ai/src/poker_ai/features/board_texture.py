"""Board texture flags and a fixed 16-dimensional embedding (Phase 3)."""

from __future__ import annotations

import math
from collections.abc import Sequence

# Deterministic extra dimensions (beyond explicit flags) from sorted board ranks.
_EMBED_SEED = 0x9E3779B97F4A7C15


def _rank_idx(card_int: int) -> int:
    return card_int // 4


def _suit_idx(card_int: int) -> int:
    return card_int % 4


def board_rank_histogram(board: Sequence[int]) -> tuple[int, ...]:
    """13-bin histogram (deuce..ace) for cards currently on the board."""
    hist = [0] * 13
    for c in board:
        hist[_rank_idx(int(c))] += 1
    return tuple(hist)


def compute_board_flags(board: Sequence[int]) -> dict[str, bool | float]:
    """Boolean / scalar texture tags for the current board (0..5 cards)."""
    cards = [int(c) for c in board]
    n = len(cards)
    ranks = sorted(_rank_idx(c) for c in cards)
    suits = [_suit_idx(c) for c in cards]
    hist = board_rank_histogram(cards)

    paired = any(h >= 2 for h in hist)
    trips_on_board = any(h >= 3 for h in hist)
    monotone = n >= 3 and len({suits[i] for i in range(n)}) == 1
    unique_suits = len(set(suits)) if n else 0
    two_tone_flop = n >= 3 and unique_suits == 2
    rainbow_flop = n >= 3 and unique_suits == 3

    connected_flop = False
    if n >= 3:
        r3 = sorted({_rank_idx(cards[i]) for i in range(3)})
        connected_flop = len(r3) == 3 and (r3[2] - r3[0]) <= 4

    dynamic_wetness = 0.0
    if n >= 3:
        dynamic_wetness = float(paired) + float(monotone) + float(connected_flop)
        dynamic_wetness = min(3.0, dynamic_wetness) / 3.0

    high_card_norm = 0.0
    if ranks:
        high_card_norm = max(ranks) / 12.0

    return {
        "paired": paired,
        "trips_on_board": trips_on_board,
        "monotone": monotone,
        "two_tone_flop": two_tone_flop,
        "rainbow_flop": rainbow_flop,
        "connected_flop": connected_flop,
        "dynamic_wetness": dynamic_wetness,
        "high_card_norm": high_card_norm,
    }


def texture_embedding_16(board: Sequence[int]) -> tuple[float, ...]:
    """16 floats: 8 interpretable flags + 8 deterministic rank-based channels."""
    flags = compute_board_flags(board)
    ordered_keys = (
        "paired",
        "trips_on_board",
        "monotone",
        "two_tone_flop",
        "rainbow_flop",
        "connected_flop",
        "dynamic_wetness",
        "high_card_norm",
    )
    head = tuple(float(flags[k]) for k in ordered_keys)
    hist = board_rank_histogram(board)
    tail: list[float] = []
    acc = sum(hist)
    for i in range(8):
        h = hist[i] + hist[i + 5] if i + 5 < 13 else hist[i]
        v = float(h) / float(max(1, acc))
        mix = (_EMBED_SEED >> (i * 7)) ^ (hist[(i * 3) % 13] << 2)
        raw = math.sin(v * 3.14159 + float(mix & 0xFFFF) * 1e-4)
        tail.append((raw + 1.0) * 0.5)
    return head + tuple(tail)


def texture_int16(board: Sequence[int]) -> tuple[int, ...]:
    """Discrete 0..255 texture channels for lossless round-trips with scaling."""
    emb = texture_embedding_16(board)
    return tuple(max(0, min(255, round(float(x) * 255.0))) for x in emb)


def texture_from_int16(vals: Sequence[int]) -> tuple[float, ...]:
    return tuple(max(0.0, min(1.0, float(x) / 255.0)) for x in vals)
