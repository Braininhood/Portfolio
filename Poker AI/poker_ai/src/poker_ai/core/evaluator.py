"""7-card (and shorter) Texas Hold'em strength via ``phevaluator``."""

from __future__ import annotations

from collections.abc import Sequence

from phevaluator.evaluator import _evaluate_cards, evaluate_cards

from poker_ai.core.cards import card_from_int


def _card_tokens(cards: Sequence[int | str]) -> list[str]:
    out: list[str] = []
    for c in cards:
        if isinstance(c, str):
            t = c.strip().lower()
            if len(t) != 2:
                msg = f"bad card token: {c!r}"
                raise ValueError(msg)
            rank = "T" if t[0] == "t" else t[0].upper()
            out.append(f"{rank}{t[1]}")
        else:
            rank, suit = card_from_int(int(c))
            out.append(f"{rank}{suit}")
    return out


def hand_rank_value_int(*cards: int) -> int:
    """Fast rank lookup for integer-encoded cards (same encoding as ``phevaluator``)."""
    n = len(cards)
    if not (5 <= n <= 7):
        msg = f"need 5..7 cards, got {n}"
        raise ValueError(msg)
    return int(_evaluate_cards(*cards))


def hand_rank_value(*cards: int | str) -> int:
    """Return ``phevaluator`` rank (lower value = stronger finished hand).

    Accepts 5-7 cards as ints or two-char strings.
    """
    toks = _card_tokens(cards)
    if not (5 <= len(toks) <= 7):
        msg = f"need 5..7 cards, got {len(toks)}"
        raise ValueError(msg)
    return int(evaluate_cards(*toks))


def evaluate_ohh_cards(*cards: int | str) -> int:
    """Alias for :func:`hand_rank_value` (explicit name for call sites)."""
    return hand_rank_value(*cards)
