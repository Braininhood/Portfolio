"""Parallel feature encoding from parsed hands."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from functools import partial

from poker_ai.features.blueprint_schema import BLUEPRINT_VERSION
from poker_ai.features.info_set import encode_hand_tensor, info_set_key
from poker_ai.features.range import l1_sum, one_hot_range_from_hole_string, uniform_range
from poker_ai.features.student_extras import _hero_result, encode_student_extras
from poker_ai.ingest.records import ParsedHand


def _encode_record(hand: ParsedHand, *, blueprint_full: bool = False) -> dict[str, object]:
    tensor = encode_hand_tensor(hand)
    key = info_set_key(hand)
    rng = (
        one_hot_range_from_hole_string(hand.hero_cards)
        if hand.hero_cards and hand.hero_cards.strip()
        else uniform_range()
    )
    row: dict[str, object] = {
        "hand_id": hand.hand_id,
        "info_set_key": key,
        "tensor": list(tensor),
        "range": list(rng),
        "range_l1": l1_sum(rng),
    }
    if blueprint_full:
        from poker_ai.features.board_texture import texture_int16
        from poker_ai.core.cards import cards_from_space_separated

        board = cards_from_space_separated(hand.board_cards)
        hero_bb, hero_sd = _hero_result(hand)
        row.update(
            {
                "blueprint_version": BLUEPRINT_VERSION,
                "num_players": hand.num_players,
                "big_blind": float(hand.big_blind),
                "board_texture": list(texture_int16(board)),
                "student_extras": list(encode_student_extras(hand)),
                "hero_net_bb": round(hero_bb, 4),
                "hero_showdown": hero_sd,
            }
        )
    return row


def encode_records_parallel(
    hands: list[ParsedHand],
    *,
    workers: int,
    blueprint_full: bool = False,
) -> list[dict[str, object]]:
    if workers <= 1 or len(hands) < 64:
        return [_encode_record(h, blueprint_full=blueprint_full) for h in hands]
    chunk = max(1, len(hands) // (workers * 4))
    fn = partial(_encode_record, blueprint_full=blueprint_full)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(fn, hands, chunksize=chunk))
