"""Plain-English spot notes for the equity calculator UI."""

from __future__ import annotations

from collections.abc import Sequence

from poker_ai.core.cards import card_from_int


def _rank(c: int) -> int:
    return c // 4


def _suit(c: int) -> int:
    return c % 4


def _format(c: int) -> str:
    r, s = card_from_int(c)
    suits = {"c": "clubs", "d": "diamonds", "h": "hearts", "s": "spades"}
    return f"{r} of {suits[s]}"


def spot_insight(
    hero: tuple[int, int],
    board: Sequence[int],
) -> str | None:
    """Short hint about draws / made hands on the current board."""
    if len(board) < 3:
        return None

    h0, h1 = hero
    all_cards = [h0, h1, *board]
    ranks = sorted({_rank(c) for c in all_cards}, reverse=True)
    hero_ranks = {_rank(h0), _rank(h1)}
    board_ranks = [_rank(c) for c in board]
    board_suits = [_suit(c) for c in board]

    parts: list[str] = []

    # Flush draw
    suit_counts: dict[int, int] = {}
    for c in all_cards:
        s = _suit(c)
        suit_counts[s] = suit_counts.get(s, 0) + 1
    hero_suits = {_suit(h0), _suit(h1)}
    for s, cnt in suit_counts.items():
        if cnt == 4 and s in hero_suits:
            parts.append("you have a four-card flush draw")
            break

    # Straight draws (simplified)
    unique = sorted(set(board_ranks + list(hero_ranks)))
    # Wheel ace low
    extended = unique[:]
    if 12 in unique:
        extended = sorted(set(unique + [-1]))

    def has_oesd(vals: list[int]) -> bool:
        for i in range(len(vals) - 3):
            window = vals[i : i + 4]
            if window[-1] - window[0] == 3 and len(set(window)) == 4:
                return True
        return False

    if has_oesd(extended):
        parts.append("an open-ended straight draw")
    elif len(unique) >= 4:
        for i in range(len(extended) - 3):
            w = extended[i : i + 4]
            if w[-1] - w[0] == 4 and len(set(w)) == 4:
                parts.append("a gutshot straight draw")
                break

    # Pair / set hints
    if _rank(h0) == _rank(h1):
        pr = _rank(h0)
        if pr in board_ranks:
            parts.insert(0, "you flopped a set")
        elif any(r == pr for r in board_ranks):
            parts.insert(0, "you paired your pocket pair")
    else:
        matches = [r for r in hero_ranks if r in board_ranks]
        if len(matches) == 2:
            parts.insert(0, "both hole cards pair the board")
        elif len(matches) == 1:
            parts.insert(0, "top pair or middle pair depending on kickers")

    board_str = " ".join(_format(c) for c in board[:5])
    if not parts:
        return f"With board {board_str}, equity depends heavily on villain range and runouts."

    joined = ", ".join(parts)
    return f"With board {board_str} — {joined.capitalize()}."
