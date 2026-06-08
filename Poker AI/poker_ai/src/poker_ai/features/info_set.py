"""Info-set encoding: discrete parts, stable key, and a flat float tensor (Phase 3)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from poker_ai.core.cards import cards_from_space_separated, parse_card
from poker_ai.features.board_texture import texture_int16
from poker_ai.features.range import isomorphic_preflop_id
from poker_ai.features.sequence import pack_action_token, position_index
from poker_ai.ingest.records import ParsedHand

MAX_ACTION_SLOTS = 32
UNKNOWN_PREFLOP = 169


@dataclass(frozen=True, slots=True)
class InfoSetParts:
    """Discrete view of an info set (round-trips through :func:`parts_flat_ints`)."""

    preflop_id: int  # 0..168 class, or UNKNOWN_PREFLOP
    street: int  # 0..3
    hero_pos: int  # 0..9 (clamped to table size)
    stack_bb_milli: int  # min starting stack in thousandths of a big blind
    texture: tuple[int, ...]  # 16 x uint8
    action_tokens: tuple[int, ...]  # length MAX_ACTION_SLOTS packed ints


def _hero_preflop_id(hand: ParsedHand) -> int:
    hc = hand.hero_cards
    if not hc or not hc.strip():
        return UNKNOWN_PREFLOP
    s = hc.strip().lower().replace(" ", "")
    if len(s) != 4:
        return UNKNOWN_PREFLOP
    try:
        c0 = parse_card(s[:2])
        c1 = parse_card(s[2:])
    except ValueError:
        return UNKNOWN_PREFLOP
    return isomorphic_preflop_id(c0, c1)


def _max_street(hand: ParsedHand) -> int:
    m = 0
    mapping = {"Preflop": 0, "Flop": 1, "Turn": 2, "River": 3}
    for a in hand.actions:
        m = max(m, mapping.get(a.street, 0))
    n_board = len(cards_from_space_separated(hand.board_cards))
    if n_board >= 3:
        m = max(m, 1)
    if n_board >= 4:
        m = max(m, 2)
    if n_board >= 5:
        m = max(m, 3)
    return m


def _min_stack_bb_milli(hand: ParsedHand) -> int:
    if hand.big_blind <= 0:
        return 0
    raw = min(float(p.stack_size) / float(hand.big_blind) * 1000.0 for p in hand.players)
    return min(2_000_000, max(0, round(raw)))


def parts_from_hand(hand: ParsedHand) -> InfoSetParts:
    """Snapshot parts at the end of the stored hand (board + action line)."""
    board = cards_from_space_separated(hand.board_cards)
    tex = texture_int16(board)
    toks = [
        pack_action_token(a, num_players=hand.num_players) for a in hand.actions[:MAX_ACTION_SLOTS]
    ]
    while len(toks) < MAX_ACTION_SLOTS:
        toks.append(0)
    hp = 0
    if hand.hero_position:
        hp = position_index(hand.num_players, hand.hero_position)
    return InfoSetParts(
        preflop_id=_hero_preflop_id(hand),
        street=_max_street(hand),
        hero_pos=min(9, hp),
        stack_bb_milli=_min_stack_bb_milli(hand),
        texture=tex,
        action_tokens=tuple(toks),
    )


def parts_flat_ints(p: InfoSetParts) -> tuple[int, ...]:
    """Fixed-length integer wire format (bijective with :func:`parts_from_flat_ints`)."""
    if len(p.texture) != 16 or len(p.action_tokens) != MAX_ACTION_SLOTS:
        msg = "invalid parts shape"
        raise ValueError(msg)
    head = (p.preflop_id, p.street, p.hero_pos, p.stack_bb_milli)
    return head + p.texture + p.action_tokens


def parts_from_flat_ints(vals: Sequence[int]) -> InfoSetParts:
    if len(vals) != 4 + 16 + MAX_ACTION_SLOTS:
        msg = f"expected {4 + 16 + MAX_ACTION_SLOTS} ints, got {len(vals)}"
        raise ValueError(msg)
    head = vals[:4]
    tex = vals[4:20]
    act = vals[20 : 20 + MAX_ACTION_SLOTS]
    return InfoSetParts(
        preflop_id=int(head[0]),
        street=int(head[1]),
        hero_pos=int(head[2]),
        stack_bb_milli=int(head[3]),
        texture=tuple(int(x) for x in tex),
        action_tokens=tuple(int(x) for x in act),
    )


def info_set_key(hand: ParsedHand) -> str:
    """Stable ASCII key (sorted integer tuple)."""
    p = parts_from_hand(hand)
    return "v1|" + ",".join(str(x) for x in parts_flat_ints(p))


def parts_to_tensor(p: InfoSetParts) -> tuple[float, ...]:
    """Float view of :func:`parts_flat_ints` (exact integers below ``2**53``)."""
    return tuple(float(x) for x in parts_flat_ints(p))


def parts_from_tensor(t: Sequence[float]) -> InfoSetParts:
    wire = tuple(round(float(x)) for x in t)
    return parts_from_flat_ints(wire)


def encode_hand_tensor(hand: ParsedHand) -> tuple[float, ...]:
    """Public helper: tensor for one :class:`~poker_ai.ingest.records.ParsedHand`."""
    return parts_to_tensor(parts_from_hand(hand))
