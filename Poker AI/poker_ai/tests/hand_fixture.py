"""Test helpers for :class:`ParsedHand` (explicit types for pyright)."""

from __future__ import annotations

from poker_ai.ingest.records import ParsedHand, ParsedPlayer

_POSITIONS_6 = ("BTN", "SB", "BB", "UTG", "MP", "CO")


def make_six_max_hand(
    *,
    hand_id: int,
    hero_seat: int,
    hero_cards: str,
    hero_position: str,
) -> ParsedHand:
    """Minimal 6-max NLH hand for policy / engine tests."""
    return ParsedHand(
        hand_id=hand_id,
        stakes="0.01/0.02",
        game_type="NLH",
        num_players=6,
        small_blind=0.01,
        big_blind=0.02,
        hero_position=hero_position,
        hero_cards=hero_cards,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=tuple(
            ParsedPlayer(
                i + 1,
                _POSITIONS_6[i],
                100.0,
                100.0,
                i == hero_seat,
                f"u{i}",
                None,
            )
            for i in range(6)
        ),
        actions=(),
    )
