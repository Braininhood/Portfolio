"""Phase 3 feature layer (info sets, board texture, ranges, sequence tokens)."""

from __future__ import annotations

from poker_ai.features.board_texture import compute_board_flags, texture_embedding_16
from poker_ai.features.info_set import (
    MAX_ACTION_SLOTS,
    UNKNOWN_PREFLOP,
    InfoSetParts,
    encode_hand_tensor,
    info_set_key,
    parts_flat_ints,
    parts_from_flat_ints,
    parts_from_hand,
    parts_from_tensor,
    parts_to_tensor,
)
from poker_ai.features.range import (
    NUM_HOLE_COMBOS,
    combo_at_index,
    combo_from_index,
    combo_index,
    combo_index_from_string,
    l1_sum,
    normalize_l1,
    one_hot_range,
    one_hot_range_from_hole_string,
    uniform_range,
)
from poker_ai.features.sequence import (
    TOK_BOS,
    TOK_PAD,
    decode_action_sequence,
    encode_action_sequence,
    pack_action_token,
    position_index,
    unpack_action_token,
)

__all__ = [
    "MAX_ACTION_SLOTS",
    "NUM_HOLE_COMBOS",
    "TOK_BOS",
    "TOK_PAD",
    "UNKNOWN_PREFLOP",
    "InfoSetParts",
    "combo_at_index",
    "combo_from_index",
    "combo_index",
    "combo_index_from_string",
    "compute_board_flags",
    "decode_action_sequence",
    "encode_action_sequence",
    "encode_hand_tensor",
    "info_set_key",
    "l1_sum",
    "normalize_l1",
    "one_hot_range",
    "one_hot_range_from_hole_string",
    "pack_action_token",
    "parts_flat_ints",
    "parts_from_flat_ints",
    "parts_from_hand",
    "parts_from_tensor",
    "parts_to_tensor",
    "position_index",
    "texture_embedding_16",
    "uniform_range",
    "unpack_action_token",
]
