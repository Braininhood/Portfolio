"""Training rows from solver cache + HHFormer tokenization (Phase 7)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.core.cards import parse_card
from poker_ai.features.board_texture import texture_int16
from poker_ai.features.hhformer_tokens import TOK_PAD, encode_hand_sequence
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer
from poker_ai.models.student import encode_state_extras
from poker_ai.solver.bridge.cache import SolverCache
from poker_ai.solver.bridge.schemas import SolvedSpot


@dataclass(frozen=True, slots=True)
class StudentRow:
    token_ids: tuple[int, ...]
    state_extras: tuple[float, ...]
    target_freqs: tuple[float, ...]
    cache_key: str


def _action(
    *,
    player_id: int,
    position: str,
    street: str,
    action_type: str,
    amount: float = 0.0,
    bpr: float | None = None,
) -> ParsedAction:
    return ParsedAction(
        player_id=player_id,
        position=position,
        street=street,
        action_type=action_type,
        amount=amount,
        is_all_in=False,
        effective_stack=100.0,
        pot_before=10.0,
        pot_after=10.0,
        bet_to_pot_ratio=bpr,
    )


def _spot_to_parsed_hand(spot: SolvedSpot, *, hero_cards: str = "As Kh") -> ParsedHand:
    """Synthetic hand for HHFormer encoding (board + minimal action line)."""
    board = spot.board.replace(",", " ")
    parts = [p.strip() for p in board.split() if p.strip()]
    actions: list[ParsedAction] = [
        _action(
            player_id=1, position="BTN", street="Preflop", action_type="Raise", amount=20.0, bpr=2.0
        ),
        _action(player_id=2, position="BB", street="Preflop", action_type="Call", amount=20.0),
    ]
    if len(parts) >= 3:
        actions.append(
            _action(player_id=2, position="BB", street="Flop", action_type="Check", amount=0.0)
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
        num_players=2,
        small_blind=5.0,
        big_blind=10.0,
        hero_position="BTN",
        hero_cards=hero_cards,
        board_cards=" ".join(parts) if parts else None,
        pot_preflop=20.0,
        pot_flop=40.0 if len(parts) >= 3 else 0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=players,
        actions=tuple(actions),
    )


def row_from_spot(spot: SolvedSpot, *, hero_cards: str = "As Kh") -> StudentRow:
    hand = _spot_to_parsed_hand(spot, hero_cards=hero_cards)
    tokens = encode_hand_sequence(hand).token_ids
    board_ints = tuple(parse_card(p) for p in hand.board_cards.split())
    tex = texture_int16(board_ints)
    meta = spot.meta or {}
    pot = int(meta.get("pot_chips", 10))
    eff = int(meta.get("effective_stack", 95))
    extras = encode_state_extras(
        hero_is_ip=True,
        effective_stack=eff,
        pot_chips=pot,
        board_texture=tex,
        sizing_tree_id=spot.sizing_tree_id,
    )
    return StudentRow(
        token_ids=tuple(tokens),
        state_extras=extras,
        target_freqs=spot.frequencies,
        cache_key=spot.cache_key,
    )


def load_student_rows(
    cache: SolverCache,
    *,
    enrich_meta: bool = True,
) -> list[StudentRow]:
    rows: list[StudentRow] = []
    for spot in cache.load_all():
        if enrich_meta and "pot_chips" not in (spot.meta or {}):
            spot = SolvedSpot(
                cache_key=spot.cache_key,
                board=spot.board,
                sizing_tree_id=spot.sizing_tree_id,
                ranges_hash=spot.ranges_hash,
                action_labels=spot.action_labels,
                frequencies=spot.frequencies,
                backend=spot.backend,
                meta={**(spot.meta or {}), "pot_chips": 10, "effective_stack": 95},
            )
        rows.append(row_from_spot(spot))
    return rows


def write_training_parquet(rows: list[StudentRow], path: Path) -> None:
    """JSONL fallback when pyarrow is unavailable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(
                json.dumps(
                    {
                        "cache_key": r.cache_key,
                        "token_ids": list(r.token_ids),
                        "state_extras": list(r.state_extras),
                        "target_freqs": list(r.target_freqs),
                    }
                )
                + "\n"
            )


def load_training_jsonl(path: Path) -> list[StudentRow]:
    rows: list[StudentRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        rows.append(
            StudentRow(
                token_ids=tuple(int(x) for x in raw["token_ids"]),
                state_extras=tuple(float(x) for x in raw["state_extras"]),
                target_freqs=tuple(float(x) for x in raw["target_freqs"]),
                cache_key=str(raw["cache_key"]),
            )
        )
    return rows


def collate_student_batch(rows: list[StudentRow], *, pad_id: int = TOK_PAD) -> dict[str, Any]:
    from poker_ai.learn._ml_deps import require_torch

    torch = require_torch()
    max_len = max(len(r.token_ids) for r in rows)
    b = len(rows)
    ids = torch.full((b, max_len), pad_id, dtype=torch.long)
    mask = torch.ones((b, max_len), dtype=torch.bool)
    for i, r in enumerate(rows):
        seq = r.token_ids
        ids[i, : len(seq)] = torch.tensor(seq, dtype=torch.long)
        mask[i, : len(seq)] = False
    extras = torch.tensor([list(r.state_extras) for r in rows], dtype=torch.float32)
    targets = torch.tensor([list(r.target_freqs) for r in rows], dtype=torch.float32)
    return {"token_ids": ids, "key_padding_mask": mask, "state_extras": extras, "targets": targets}
