"""Human-readable Hold'em hand descriptions for the play UI."""

from __future__ import annotations

from itertools import combinations

from poker_ai.core.cards import card_from_int
from poker_ai.core.evaluator import hand_rank_value_int
from poker_ai.core.game import GameState

_RANK_NAMES = {
    "2": "Twos",
    "3": "Threes",
    "4": "Fours",
    "5": "Fives",
    "6": "Sixes",
    "7": "Sevens",
    "8": "Eights",
    "9": "Nines",
    "T": "Tens",
    "J": "Jacks",
    "Q": "Queens",
    "K": "Kings",
    "A": "Aces",
}

_RANK_ORDER = "23456789TJQKA"


def _rank_char(c: int) -> str:
    return card_from_int(c)[0]


def _rank_name(r: str) -> str:
    return _RANK_NAMES.get(r, r)


def _category_from_rank(rank: int) -> str:
    if rank <= 10:
        return "straight_flush"
    if rank <= 166:
        return "four_of_a_kind"
    if rank <= 322:
        return "full_house"
    if rank <= 1599:
        return "flush"
    if rank <= 1609:
        return "straight"
    if rank <= 2467:
        return "three_of_a_kind"
    if rank <= 3325:
        return "two_pair"
    if rank <= 6185:
        return "one_pair"
    return "high_card"


def _describe_five(cards: tuple[int, ...], rank: int) -> str:
    ranks = [_rank_char(c) for c in cards]
    counts: dict[str, int] = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    by_count = sorted(counts.items(), key=lambda x: (-x[1], -_RANK_ORDER.index(x[0])))

    cat = _category_from_rank(rank)
    if cat == "straight_flush":
        return f"Straight flush ({_rank_name(ranks[0])} high)"
    if cat == "four_of_a_kind":
        quad = by_count[0][0]
        kicker = by_count[1][0]
        return f"Four of a kind ({_rank_name(quad)}) · {_rank_name(kicker)} kicker"
    if cat == "full_house":
        trip, pair = by_count[0][0], by_count[1][0]
        return f"Full house ({_rank_name(trip)} full of {_rank_name(pair)})"
    if cat == "flush":
        return f"Flush ({_rank_name(max(ranks, key=lambda r: _RANK_ORDER.index(r)))} high)"
    if cat == "straight":
        high = max(ranks, key=lambda r: _RANK_ORDER.index(r))
        return f"Straight ({_rank_name(high)} high)"
    if cat == "three_of_a_kind":
        trip = by_count[0][0]
        return f"Three of a kind ({_rank_name(trip)})"
    if cat == "two_pair":
        p1, p2 = by_count[0][0], by_count[1][0]
        kicker = by_count[2][0] if len(by_count) > 2 else ""
        base = f"Two pair ({_rank_name(p1)} and {_rank_name(p2)})"
        return f"{base} · {_rank_name(kicker)} kicker" if kicker else base
    if cat == "one_pair":
        pair = by_count[0][0]
        return f"Pair of {_rank_name(pair)}"
    high = max(ranks, key=lambda r: _RANK_ORDER.index(r))
    return f"{_rank_name(high)} high"


def _preflop_label(lo: int, hi: int) -> str:
    r1, r2 = _rank_char(lo), _rank_char(hi)
    suited = (lo % 4) == (hi % 4)
    ordered = sorted([r1, r2], key=lambda r: -_RANK_ORDER.index(r))
    if r1 == r2:
        return f"Pocket {_rank_name(r1)}"
    s = "suited" if suited else "offsuit"
    return f"{ordered[0]}{ordered[1]} {s}"


def rank_for_hole_board(*, hole: tuple[int, int] | None, board: list[int]) -> int:
    """Lower is stronger (phevaluator). Requires 5 board cards."""
    if hole is None or len(board) < 5:
        return 10**9
    lo, hi = hole
    return hand_rank_value_int(lo, hi, board[0], board[1], board[2], board[3], board[4])


def best_hand_description(*, hole: tuple[int, int] | None, board: list[int]) -> dict[str, str]:
    """Best current 5-card hand from hole + board (or preflop label)."""
    if hole is None:
        return {"category": "unknown", "name": "Unknown", "detail": ""}
    lo, hi = hole
    if len(board) < 3:
        name = _preflop_label(lo, hi)
        return {"category": "preflop", "name": name, "detail": name}
    cards = [lo, hi, *board]
    best_rank = 10**9
    best_combo: tuple[int, ...] = ()
    for combo in combinations(cards, 5):
        rank = hand_rank_value_int(*combo)
        if rank < best_rank:
            best_rank = rank
            best_combo = combo
    if not best_combo:
        return {"category": "unknown", "name": "Unknown", "detail": ""}
    cat = _category_from_rank(best_rank)
    name = _describe_five(best_combo, best_rank)
    return {"category": cat, "name": name, "detail": name}


def hero_hand_payload(state: GameState, hero_seat: int) -> dict[str, str] | None:
    if state.seat_holes is None:
        return None
    hole = state.seat_holes[hero_seat]
    if hole is None:
        return None
    return best_hand_description(hole=hole, board=list(state.board))
