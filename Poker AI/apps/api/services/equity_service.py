"""Compute equity for POST /equity (Phase W5)."""

from __future__ import annotations

import os
import time
from typing import Any

# Serial runout tables avoid Windows ProcessPool pickling issues on first flop query.
os.environ.setdefault("POKER_AI_EQUITY_WORKERS", "1")

from poker_ai.core.cards import card_from_int, cards_from_space_separated, parse_card
from poker_ai.equity.breakdown import equity_breakdown
from poker_ai.equity.engine import EquityEngine
from poker_ai.equity.range_notation import range_from_notation
from poker_ai.equity.spot_insight import spot_insight
from poker_ai.features.range import one_hot_range_from_hole_string


def _format_cards(cards: tuple[int, ...]) -> str:
    return " ".join(f"{card_from_int(c)[0]}{card_from_int(c)[1]}" for c in cards)


def _parse_hero(hero_cards: str) -> tuple[int, int]:
    s = hero_cards.strip()
    if not s:
        msg = "hero_cards is required (e.g. 'Ah Kd')"
        raise ValueError(msg)
    parts = s.split()
    if len(parts) == 1 and len(parts[0]) == 4:
        c0, c1 = parse_card(parts[0][:2]), parse_card(parts[0][2:])
    elif len(parts) == 2:
        c0, c1 = parse_card(parts[0]), parse_card(parts[1])
    else:
        msg = "hero_cards must be two cards, e.g. 'Ah Kd'"
        raise ValueError(msg)
    if c0 == c1:
        msg = "hero cards must be distinct"
        raise ValueError(msg)
    return c0, c1


def compute_equity(
    *,
    hero_cards: str,
    board_cards: str = "",
    villain_range: str = "random",
    mode: str = "exact",
    num_samples: int = 5000,
) -> dict[str, Any]:
    """Run equity and return a dict matching ``EquityResponse``."""
    t0 = time.perf_counter()
    hero_hole = _parse_hero(hero_cards)
    board = cards_from_space_separated(board_cards or None)
    if len(board) > 5:
        msg = "board cannot have more than five cards"
        raise ValueError(msg)
    for c in board:
        if c in hero_hole:
            msg = "board overlaps hero hole cards"
            raise ValueError(msg)

    dead = hero_hole + board
    hero_range = one_hot_range_from_hole_string(
        f"{card_from_int(hero_hole[0])[0]}{card_from_int(hero_hole[0])[1]} "
        f"{card_from_int(hero_hole[1])[0]}{card_from_int(hero_hole[1])[1]}"
    )
    villain = range_from_notation(villain_range, dead_cards=dead)

    mode_norm = mode.strip().lower()
    if mode_norm not in ("exact", "mc", "auto"):
        msg = "mode must be 'exact', 'mc', or 'auto'"
        raise ValueError(msg)

    pick = "mc" if mode_norm == "mc" else ("exact" if mode_norm == "exact" else "auto")
    bd, mode_used = equity_breakdown(
        hero_range,
        villain,
        board,
        mode=pick,
        n_samples=max(1000, int(num_samples)),
    )

    # Warm engine cache for repeat queries on same board (library path).
    if board and mode_used == "exact":
        eng = EquityEngine()
        eng.warm_board(board)

    hero_eq = bd.hero_equity
    villain_eq = 1.0 - hero_eq
    tie_eq = bd.tie

    breakdown: dict[str, float] = {}
    if len(board) >= 3:
        for n, label in ((3, "flop"), (4, "turn"), (5, "river")):
            if len(board) >= n:
                sub, _ = equity_breakdown(
                    hero_range,
                    villain,
                    board[:n],
                    mode="auto",
                    n_samples=max(2000, num_samples // 2),
                )
                breakdown[label] = round(sub.hero_equity, 4)

    insight = spot_insight(hero_hole, board)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "hero_equity": round(hero_eq, 6),
        "villain_equity": round(villain_eq, 6),
        "tie_equity": round(tie_eq, 6),
        "hero_cards": _format_cards(hero_hole),
        "board_cards": _format_cards(board) if board else None,
        "villain_range": villain_range.strip() or "random",
        "mode_used": mode_used,
        "latency_ms": round(latency_ms, 2),
        "breakdown": breakdown,
        "insight": insight,
    }
