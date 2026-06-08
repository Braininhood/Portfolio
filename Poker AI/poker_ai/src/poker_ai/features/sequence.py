"""Action-sequence tokenization for transformer-style models (Phase 3)."""

from __future__ import annotations

from collections.abc import Sequence

from poker_ai.ingest.positions import POSITION_RING
from poker_ai.ingest.records import ParsedAction, ParsedHand

# Reserved vocabulary indices (keep clear of packed per-action tokens).
TOK_PAD = 0
TOK_BOS = 1

_STREET_TO_I = {"Preflop": 0, "Flop": 1, "Turn": 2, "River": 3}
_I_TO_STREET = {v: k for k, v in _STREET_TO_I.items()}

_KIND_TO_I = {"Fold": 0, "Check": 1, "Call": 2, "Bet": 3, "Raise": 4}
_I_TO_KIND = {v: k for k, v in _KIND_TO_I.items()}


def position_index(num_players: int, position_label: str) -> int:
    """Stable seat index ``0..n-1`` for canonical position text."""
    ring = POSITION_RING.get(num_players)
    if not ring:
        return 0
    try:
        return ring.index(position_label)
    except ValueError:
        return 0


def pack_action_token(pa: ParsedAction, *, num_players: int) -> int:
    """Single int token for one stored action (19 bits, reversible with same quantization)."""
    st = _STREET_TO_I.get(pa.street, 0)
    pos = position_index(num_players, pa.position) & 0xF
    kind = _KIND_TO_I.get(pa.action_type, 0)
    bpr = pa.bet_to_pot_ratio
    if bpr is None or bpr <= 0.0:
        cent = 0
    else:
        cent = min(999, max(0, round(float(bpr) * 100.0)))
    return st | (pos << 2) | (kind << 6) | (cent << 9)


def unpack_action_token(tok: int, *, num_players: int) -> tuple[str, str, str, float | None]:
    """Inverse of :func:`pack_action_token` (``bet_to_pot_ratio`` is cent-precision)."""
    st = tok & 0x3
    pos = (tok >> 2) & 0xF
    kind = (tok >> 6) & 0x7
    cent = (tok >> 9) & 0x3FF
    street = _I_TO_STREET.get(st, "Preflop")
    ring = POSITION_RING.get(num_players, ("BTN",))
    pos_label = ring[pos] if pos < len(ring) else ring[0]
    action_type = _I_TO_KIND.get(kind, "Fold")
    bpr = None if cent == 0 else cent / 100.0
    return street, pos_label, action_type, bpr


def encode_action_sequence(
    hand: ParsedHand,
    *,
    max_actions: int = 64,
    include_bos: bool = True,
) -> tuple[int, ...]:
    """Linear token ids: optional BOS, then packed per-action ints (truncated)."""
    out: list[int] = []
    if include_bos:
        out.append(TOK_BOS)
    for pa in hand.actions[:max_actions]:
        out.append(pack_action_token(pa, num_players=hand.num_players))
    return tuple(out)


def decode_action_sequence(
    tokens: Sequence[int],
    *,
    num_players: int,
    include_bos: bool = True,
) -> tuple[tuple[str, str, str, float | None], ...]:
    """Decode packed tokens back to coarse action tuples (for tests / debugging)."""
    it = iter(tokens)
    if include_bos:
        first = next(it, TOK_PAD)
        if first != TOK_BOS:
            msg = "expected BOS"
            raise ValueError(msg)
    decoded: list[tuple[str, str, str, float | None]] = []
    for tok in it:
        if tok == TOK_PAD:
            break
        decoded.append(unpack_action_token(tok, num_players=num_players))
    return tuple(decoded)
