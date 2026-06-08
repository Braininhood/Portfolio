"""Equity / zero baselines for AIVAT chance correction."""

from __future__ import annotations

from poker_ai.ingest.records import ParsedHand


def hero_equity_at_showdown(hand: ParsedHand) -> float | None:
    """Return hero final equity (0–1) from backfilled results, if available."""
    hero_pid = _hero_player_id(hand)
    if hero_pid is None:
        return None
    for r in hand.results:
        if r.player_id == hero_pid and r.showdown:
            if r.final_equity is not None:
                return float(r.final_equity)
            if r.river_equity is not None:
                return float(r.river_equity)
    return None


def expected_showdown_share(
    delta_chips: int,
    *,
    equity: float | None,
    pot_chips: int,
    big_blind: int,
) -> float:
    """Expected chip delta at showdown given hero equity vs pot."""
    if equity is None or pot_chips <= 0:
        return float(delta_chips)
    # Zero-sum: hero share ≈ equity * pot - invested; use residual as luck
    expected = equity * float(pot_chips) - (float(pot_chips) * (1.0 - equity)) * 0.0
    return expected


def _hero_player_id(hand: ParsedHand) -> int | None:
    for p in hand.players:
        if p.is_hero:
            return p.player_id
    if hand.hero_position:
        for p in hand.players:
            if p.position == hand.hero_position:
                return p.player_id
    return hand.players[0].player_id if hand.players else None
