"""52-card integer encoding (rank-major, suit 0..3)."""

from __future__ import annotations

RANKS = "23456789TJQKA"
SUITS = "cdhs"


def card_to_int(rank: str, suit: str) -> int:
    """Encode one card as ``0..51`` (deuce clubs = 0, ace spades = 51)."""
    r = RANKS.index(rank.upper())
    s = SUITS.index(suit.lower())
    return r * 4 + s


def card_from_int(c: int) -> tuple[str, str]:
    """Decode ``0..51`` to ``(rank_char, suit_char)``."""
    if c < 0 or c > 51:
        msg = f"card index out of range: {c}"
        raise ValueError(msg)
    return RANKS[c // 4], SUITS[c % 4]


def parse_card(token: str) -> int:
    """Parse ``\"Ah\"`` / ``\"TD\"`` style into an int."""
    t = token.strip()
    if len(t) != 2:
        msg = f"expected two-character card, got {token!r}"
        raise ValueError(msg)
    rank_raw, suit_raw = t[0], t[1]
    rank = "T" if rank_raw.lower() == "t" else rank_raw.upper()
    if rank not in RANKS:
        msg = f"invalid rank in {token!r}"
        raise ValueError(msg)
    return card_to_int(rank, suit_raw)


def cards_from_space_separated(s: str | None) -> tuple[int, ...]:
    """Split ``\"ah kh\"`` / ``\"2d 3d 4d\"`` into ints."""
    if not s or not s.strip():
        return ()
    out: list[int] = []
    for p in s.lower().split():
        if len(p) != 2:
            msg = f"expected two-character card token, got {p!r}"
            raise ValueError(msg)
        rank = "T" if p[0] == "t" else p[0].upper()
        out.append(card_to_int(rank, p[1]))
    return tuple(out)
