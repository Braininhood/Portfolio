"""Typed structures produced by ingest parsers before ORM mapping."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ParsedPlayer:
    player_id: int
    position: str
    stack_size: float
    bb_size: float
    is_hero: bool
    player_uid: str
    screen_name: str | None = None


@dataclass(frozen=True, slots=True)
class ParsedAction:
    player_id: int
    position: str
    street: str
    action_type: str
    amount: float
    is_all_in: bool
    effective_stack: float
    pot_before: float
    pot_after: float
    bet_to_pot_ratio: float | None


@dataclass(frozen=True, slots=True)
class ParsedResult:
    player_id: int
    position: str
    cards: str
    net_result: float
    won_pot: float
    showdown: bool
    final_equity: float | None = None
    preflop_equity: float | None = None
    flop_equity: float | None = None
    turn_equity: float | None = None
    river_equity: float | None = None


@dataclass(frozen=True, slots=True)
class ParsedHand:
    hand_id: int
    stakes: str
    game_type: str
    num_players: int
    small_blind: float
    big_blind: float
    hero_position: str | None
    hero_cards: str | None
    board_cards: str | None
    pot_preflop: float
    pot_flop: float
    pot_turn: float
    pot_river: float
    # Posted antes in **players tuple order** (same index as ``players[i]``), not ring seat order.
    # Engine maps by ``player_id`` when building per-seat stacks. Empty means no antes.
    antes: tuple[float, ...] = ()
    players: tuple[ParsedPlayer, ...] = field(default_factory=tuple)
    actions: tuple[ParsedAction, ...] = field(default_factory=tuple)
    results: tuple[ParsedResult, ...] = field(default_factory=tuple)
    # Provenance: unique per (ingest_source, external_ref) across poker rooms / formats.
    ingest_source: str = "normalized_txt"
    external_ref: str = ""


def total_ante_amount(hand: ParsedHand) -> float:
    """Sum of per-player antes in currency units (same as ``small_blind`` / ``big_blind``).

    ``ParsedHand.antes`` is parallel to ``players``; empty or all-zero means no antes.
    """

    if not hand.antes:
        return 0.0
    return float(sum(float(x or 0.0) for x in hand.antes))


def hand_uses_antes(hand: ParsedHand) -> bool:
    """True when the parsed hand carries a positive total ante (training / SQL filters)."""

    return total_ante_amount(hand) > 1e-9
