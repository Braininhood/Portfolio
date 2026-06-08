"""Decision quality rows from DB hero spots vs teacher policy (blueprint v2)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from typing import Any

from poker_ai.core.profiles import PlayerProfile
from poker_ai.core.replay import state_after_actions
from poker_ai.features.board_texture import texture_int16
from poker_ai.features.hhformer_tokens import TOK_PAD, encode_hand_sequence
from poker_ai.core.cards import parse_card
from poker_ai.ingest.records import ParsedHand
from poker_ai.learn.multiway_dataset import _hero_player_id
from poker_ai.models.student import encode_state_extras
from poker_ai.policy.base import ActionDist


@dataclass(frozen=True, slots=True)
class DecisionQualityRow:
    token_ids: tuple[int, ...]
    state_extras: tuple[float, ...]
    target_quality: float
    hand_id: int


def _action_bucket(action_type: str, bpr: float | None) -> str:
    t = action_type.lower()
    if t == "fold":
        return "fold"
    if t in ("check", "call"):
        return "check_call"
    if t in ("bet", "raise"):
        if bpr is not None and bpr >= 0.55:
            return "bet_66"
        if bpr is not None and bpr >= 0.25:
            return "bet_33"
        return "bet_33"
    return "check_call"


def _teacher_quality(dist: ActionDist, hero_action: str) -> float:
    d = dist.normalized()
    if not d.actions:
        return 0.5
    bucket = hero_action
    mass = 0.0
    for (kind, _amt, _seat), prob in zip(d.actions, d.probs, strict=False):
        b = _action_bucket(kind, None)
        if b == bucket:
            mass += float(prob)
    return max(0.0, min(1.0, mass))


def _hand_through_action(hand: ParsedHand, action_index: int) -> ParsedHand:
    return replace(hand, actions=hand.actions[: action_index + 1])


def _row_from_hand_action(
    hand: ParsedHand,
    action_index: int,
    *,
    teacher: Any,
    profile: PlayerProfile,
) -> DecisionQualityRow | None:
    hero_pid = _hero_player_id(hand)
    if hero_pid is None:
        return None
    pa = hand.actions[action_index]
    if pa.player_id != hero_pid:
        return None
    try:
        state = state_after_actions(hand, action_index, lenient=True)
    except (ValueError, KeyError, IndexError):
        return None
    if state.hand_over:
        return None
    dist = teacher.propose(state, profile)
    bucket = _action_bucket(pa.action_type, pa.bet_to_pot_ratio)
    quality = _teacher_quality(dist, bucket)

    sub = _hand_through_action(hand, action_index)
    tokens = encode_hand_sequence(sub).token_ids
    board_ints = ()
    if sub.board_cards:
        try:
            board_ints = tuple(parse_card(p) for p in sub.board_cards.split())
        except ValueError:
            board_ints = ()
    tex = texture_int16(board_ints)
    extras = encode_state_extras(
        hero_is_ip=True,
        effective_stack=int(pa.effective_stack),
        pot_chips=int(max(pa.pot_before, 1)),
        board_texture=tex,
        sizing_tree_id="quality_v1",
    )
    return DecisionQualityRow(
        token_ids=tuple(tokens),
        state_extras=extras,
        target_quality=quality,
        hand_id=hand.hand_id,
    )


async def load_decision_quality_rows(
    session,
    *,
    limit: int = 5000,
    max_hands: int = 20_000,
) -> list[DecisionQualityRow]:
    from poker_ai.policy.distilled_policy import load_best_policy
    from poker_ai.store.loader import iter_parsed_hands_since

    try:
        teacher = load_best_policy()
    except Exception:
        from poker_ai.policy.heuristic import HeuristicPolicy

        teacher = HeuristicPolicy()
    profile = PlayerProfile(profile_id="hero")
    rows: list[DecisionQualityRow] = []
    hands_seen = 0
    async for hand in iter_parsed_hands_since(session):
        hands_seen += 1
        if hands_seen > max_hands:
            break
        for idx in range(len(hand.actions)):
            row = _row_from_hand_action(hand, idx, teacher=teacher, profile=profile)
            if row is not None:
                rows.append(row)
            if len(rows) >= limit:
                return rows
    return rows


def load_decision_quality_rows_sync(
    *,
    limit: int = 5000,
    max_hands: int = 20_000,
) -> list[DecisionQualityRow]:
    from poker_ai.store.db import get_async_session_factory

    async def _run() -> list[DecisionQualityRow]:
        factory = get_async_session_factory()
        async with factory() as session:
            return await load_decision_quality_rows(
                session, limit=limit, max_hands=max_hands
            )

    return asyncio.run(_run())


def collate_quality_batch(rows: list[DecisionQualityRow], *, pad_id: int = TOK_PAD) -> dict[str, Any]:
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
    targets = torch.tensor([r.target_quality for r in rows], dtype=torch.float32)
    return {
        "token_ids": ids,
        "key_padding_mask": mask,
        "state_extras": extras,
        "targets": targets,
    }
