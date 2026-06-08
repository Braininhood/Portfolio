"""Training rows from Monker / multi-way JSON exports (Phase 7c)."""

from __future__ import annotations

import json
from pathlib import Path

from poker_ai.core.cards import parse_card
from poker_ai.features.board_texture import texture_int16
from poker_ai.features.hhformer_tokens import encode_hand_sequence
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer
from poker_ai.learn.multiway_dataset import MultiwayRow
from poker_ai.models.multiway_student import encode_multiway_extras
from poker_ai.solver.bridge.monker import (
    frequencies_to_student_targets,
    parse_monker_export_file,
)
from poker_ai.solver.bridge.schemas import SolvedSpot


def _synthetic_hand_from_spot(
    spot: SolvedSpot,
    *,
    n_active: int,
    num_seats: int,
    hero_cards: str = "As Kh",
) -> ParsedHand:
    board = spot.board.replace(",", " ")
    parts = [p.strip() for p in board.split() if p.strip()]
    meta = spot.meta or {}
    pot = float(meta.get("pot_chips", 10))
    actions: list[ParsedAction] = [
        ParsedAction(
            player_id=1,
            position="BTN",
            street="Preflop",
            action_type="Raise",
            amount=20.0,
            is_all_in=False,
            effective_stack=100.0,
            pot_before=pot,
            pot_after=pot,
            bet_to_pot_ratio=2.0,
        ),
    ]
    if len(parts) >= 3:
        actions.append(
            ParsedAction(
                player_id=2,
                position="BB",
                street="Flop",
                action_type="Check",
                amount=0.0,
                is_all_in=False,
                effective_stack=100.0,
                pot_before=pot,
                pot_after=pot,
                bet_to_pot_ratio=None,
            )
        )
    players = (
        ParsedPlayer(1, "BTN", 100.0, 100.0, True, "hero", None),
        ParsedPlayer(2, "BB", 100.0, 100.0, False, "villain", None),
    )
    hid = abs(hash(spot.cache_key)) % (2**31 - 1)
    return ParsedHand(
        hand_id=hid,
        stakes="0.05/0.10",
        game_type="NLH",
        num_players=num_seats,
        small_blind=5.0,
        big_blind=10.0,
        hero_position="BTN",
        hero_cards=hero_cards,
        board_cards=" ".join(parts) if parts else None,
        pot_preflop=pot,
        pot_flop=pot if len(parts) >= 3 else 0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=players,
        actions=tuple(actions),
    )


def row_from_monker_spot(
    spot: SolvedSpot,
    *,
    n_active: int = 3,
    num_seats: int = 6,
    hero_cards: str = "As Kh",
) -> MultiwayRow:
    """Build a :class:`MultiwayRow` from a cached Monker / mock multi-way teacher spot."""
    n_active = int(spot.meta.get("n_active", n_active))
    num_seats = int(spot.meta.get("num_seats", num_seats))
    hand = _synthetic_hand_from_spot(
        spot, n_active=n_active, num_seats=num_seats, hero_cards=hero_cards
    )
    seq = encode_hand_sequence(hand)
    board_ints = tuple(parse_card(p) for p in hand.board_cards.split()) if hand.board_cards else ()
    tex = texture_int16(board_ints)
    meta = spot.meta or {}
    pot = int(meta.get("pot_chips", 10))
    eff = int(meta.get("effective_stack", 95))
    targets = frequencies_to_student_targets(spot.action_labels, spot.frequencies)
    extras = encode_multiway_extras(
        hero_is_ip=True,
        effective_stack=eff,
        pot_chips=pot,
        board_texture=tex,
        n_active=n_active,
        num_seats=num_seats,
        sizing_tree_id=spot.sizing_tree_id,
    )
    return MultiwayRow(
        token_ids=tuple(seq.token_ids),
        state_extras=extras,
        target_freqs=targets,
        hand_id=hand.hand_id,
        n_active=n_active,
    )


def load_monker_training_rows(
    export_dir: Path,
    *,
    also_write_cache: Path | None = None,
) -> list[MultiwayRow]:
    """Load all ``*.json`` exports under ``export_dir`` as training rows."""
    if not export_dir.is_dir():
        return []

    rows: list[MultiwayRow] = []
    cache_rows: list[SolvedSpot] = []

    for path in sorted(export_dir.glob("*.json")):
        try:
            spot = parse_monker_export_file(path)
        except (json.JSONDecodeError, ValueError, OSError):
            continue
        cache_rows.append(spot)
        rows.append(row_from_monker_spot(spot))

    if also_write_cache is not None and cache_rows:
        from poker_ai.solver.bridge.cache import SolverCache

        cache = SolverCache(also_write_cache)
        for spot in cache_rows:
            cache.put(spot)

    return rows
