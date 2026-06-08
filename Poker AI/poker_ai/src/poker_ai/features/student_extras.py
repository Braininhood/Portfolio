"""Student training extras bundle — SPR, pot odds, board texture (blueprint v2)."""

from __future__ import annotations

from poker_ai.core.cards import cards_from_space_separated
from poker_ai.features.board_texture import texture_int16
from poker_ai.ingest.records import ParsedAction, ParsedHand


def _hero_result(hand: ParsedHand) -> tuple[float, bool]:
    """Hero net result in BB and whether hero showed down."""
    hero_pid = None
    for p in hand.players:
        if p.is_hero:
            hero_pid = p.player_id
            break
    if hero_pid is None and hand.hero_position:
        for p in hand.players:
            if p.position == hand.hero_position:
                hero_pid = p.player_id
                break
    if hero_pid is None:
        return 0.0, False
    bb = max(hand.big_blind, 1e-9)
    for r in hand.results:
        if r.player_id == hero_pid:
            return float(r.net_result) / bb, bool(r.showdown)
    return 0.0, False


def _last_hero_action(hand: ParsedHand) -> ParsedAction | None:
    hero_pid = None
    for p in hand.players:
        if p.is_hero:
            hero_pid = p.player_id
            break
    if hero_pid is None:
        return None
    last = None
    for a in hand.actions:
        if a.player_id == hero_pid:
            last = a
    return last


def encode_student_extras(hand: ParsedHand) -> tuple[float, ...]:
    """Fixed-length extras: SPR, pot_odds, stack_bb, n_active_norm, texture[0:4]."""
    board = cards_from_space_separated(hand.board_cards)
    tex = texture_int16(board)
    la = _last_hero_action(hand)
    eff_stack = float(la.effective_stack) if la else min(
        (float(p.stack_size) for p in hand.players), default=100.0
    )
    pot = float(la.pot_before) if la else float(hand.pot_river or hand.pot_flop or hand.pot_preflop)
    bb = max(float(hand.big_blind), 1e-9)
    spr = eff_stack / max(pot, bb)
    pot_odds = pot / max(eff_stack + pot, bb)
    stack_bb = eff_stack / bb
    n_active = float(hand.num_players) / 10.0
    head = (min(50.0, spr), min(1.0, pot_odds), min(500.0, stack_bb), n_active)
    tail = tuple(float(x) / 255.0 for x in tex[:4])
    return head + tail


def hero_aivat_bb(hand: ParsedHand) -> float:
    """Hero net BB/100 with full AIVAT when enabled and equity backfill present."""
    from poker_ai.core.engine import money_to_chips
    from poker_ai.eval.aivat import aivat_adjust_delta

    hero_pid = None
    for p in hand.players:
        if p.is_hero:
            hero_pid = p.player_id
            break
    if hero_pid is None:
        bb, _ = _hero_result(hand)
        return bb
    bb_chips = max(1, money_to_chips(hand.big_blind))
    delta_chips = 0
    sd = False
    hero_seat = 0
    for i, p in enumerate(hand.players):
        if p.player_id == hero_pid:
            hero_seat = i
    for r in hand.results:
        if r.player_id == hero_pid:
            delta_chips = money_to_chips(float(r.net_result))
            sd = bool(r.showdown)
    winner_seat: int | None = None
    for r in hand.results:
        if r.won_pot > 0:
            for i, p in enumerate(hand.players):
                if p.player_id == r.player_id:
                    winner_seat = i
                    break
            break
    adj = aivat_adjust_delta(
        delta_chips,
        went_showdown=sd,
        winner_seat=winner_seat,
        seat=hero_seat,
        big_blind=bb_chips,
        hand=hand,
    )
    return adj / bb_chips * 100.0
