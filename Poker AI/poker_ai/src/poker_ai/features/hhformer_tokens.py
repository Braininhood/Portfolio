"""Hand-history tokenisation for HHFormer (Phase 5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from poker_ai.core.cards import cards_from_space_separated
from poker_ai.features.info_set import _hero_preflop_id
from poker_ai.features.sequence import pack_action_token, unpack_action_token
from poker_ai.ingest.records import ParsedHand

_STREET_TO_I = {"Preflop": 0, "Flop": 1, "Turn": 2, "River": 3}
_KIND_TO_I = {"Fold": 0, "Check": 1, "Call": 2, "Bet": 3, "Raise": 4}

# Reserved token ids (single shared embedding table).
TOK_PAD: Final = 0
TOK_CLS: Final = 1
TOK_MASK: Final = 2

# token_kind values (parallel array; drives MAP / MCP masking).
KIND_META: Final = 0
KIND_ACTION: Final = 1
KIND_CARD: Final = 2

VOCAB_SIZE: Final = 1536
MAX_SEQ_LEN: Final = 128

_META_PLAYERS_BASE: Final = 3
_STAKES_BASE: Final = 14
_STAKES_BUCKETS: Final = 12
_ACTION_VOCAB_BASE: Final = 32
_ACTION_VOCAB_SIZE: Final = 512
_CARD_VOCAB_BASE: Final = 576
_MAX_WINNER_SEATS: Final = 10


@dataclass(frozen=True, slots=True)
class HandSequence:
    """Fixed-length hand sequence for HHFormer training / inference."""

    token_ids: tuple[int, ...]
    token_kinds: tuple[int, ...]
    num_players: int
    winner_seat: int | None
    hero_strength_class: int
    length: int


def _stakes_bucket(stakes: str) -> int:
    s = stakes.strip().lower()
    if not s:
        return 0
    if "/" in s:
        parts = s.split("/", 1)
        try:
            bb = float(parts[-1])
        except ValueError:
            bb = 1.0
    else:
        try:
            bb = float(s)
        except ValueError:
            bb = 1.0
    if bb <= 0.25:
        return 0
    if bb <= 0.5:
        return 1
    if bb <= 1.0:
        return 2
    if bb <= 2.0:
        return 3
    if bb <= 5.0:
        return 4
    if bb <= 10.0:
        return 5
    if bb <= 25.0:
        return 6
    if bb <= 50.0:
        return 7
    if bb <= 100.0:
        return 8
    if bb <= 200.0:
        return 9
    return 10


def meta_players_token(num_players: int) -> int:
    n = min(max(2, num_players), 10)
    return _META_PLAYERS_BASE + (n - 2)


def meta_stakes_token(stakes: str) -> int:
    return _STAKES_BASE + min(_STAKES_BUCKETS - 1, _stakes_bucket(stakes))


def packed_to_action_vocab(packed: int, *, num_players: int) -> int:
    """Map a packed action int into a compact action-vocab slot."""
    street, _pos, kind, bpr = unpack_action_token(packed, num_players=num_players)
    st = _STREET_TO_I.get(street, 0)
    kind_i = _KIND_TO_I.get(kind, 0)
    cent = 0 if bpr is None else min(15, round(float(bpr) * 15.0))
    slot = (st << 7) | (kind_i << 3) | (cent & 0x7)
    return _ACTION_VOCAB_BASE + (slot % _ACTION_VOCAB_SIZE)


def card_token(card_int: int) -> int:
    if card_int < 0 or card_int > 51:
        msg = f"card out of range: {card_int}"
        raise ValueError(msg)
    return _CARD_VOCAB_BASE + card_int


def winner_seat_index(hand: ParsedHand) -> int | None:
    """Winning seat index ``0..num_players-1``, or ``None`` if unknown."""
    if not hand.results:
        return None
    from poker_ai.features.sequence import position_index

    best: tuple[float, int] | None = None
    for r in hand.results:
        score = float(r.won_pot) if r.won_pot > 0 else float(r.net_result)
        if score <= 1e-9:
            continue
        seat = position_index(hand.num_players, r.position)
        if best is None or score > best[0]:
            best = (score, seat)
    return None if best is None else best[1]


def encode_hand_sequence(
    hand: ParsedHand,
    *,
    max_len: int = MAX_SEQ_LEN,
) -> HandSequence:
    """Build ``[CLS] + meta + actions/cards`` token sequence (truncated)."""
    ids: list[int] = [TOK_CLS]
    kinds: list[int] = [KIND_META]

    ids.append(meta_players_token(hand.num_players))
    kinds.append(KIND_META)
    ids.append(meta_stakes_token(hand.stakes))
    kinds.append(KIND_META)

    board = cards_from_space_separated(hand.board_cards)
    _street_board_len = {"Preflop": 0, "Flop": 3, "Turn": 4, "River": 5}
    emitted_board = 0

    for pa in hand.actions:
        if len(ids) >= max_len:
            break
        target = _street_board_len.get(pa.street, emitted_board)
        while emitted_board < target and emitted_board < len(board):
            if len(ids) >= max_len:
                break
            ids.append(card_token(board[emitted_board]))
            kinds.append(KIND_CARD)
            emitted_board += 1

        packed = pack_action_token(pa, num_players=hand.num_players)
        ids.append(packed_to_action_vocab(packed, num_players=hand.num_players))
        kinds.append(KIND_ACTION)

    length = len(ids)
    while len(ids) < max_len:
        ids.append(TOK_PAD)
        kinds.append(KIND_META)

    return HandSequence(
        token_ids=tuple(ids),
        token_kinds=tuple(kinds),
        num_players=hand.num_players,
        winner_seat=winner_seat_index(hand),
        hero_strength_class=_hero_preflop_id(hand),
        length=length,
    )
