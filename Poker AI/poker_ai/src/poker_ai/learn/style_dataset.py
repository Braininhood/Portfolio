"""Action-window dataset for contrastive style pretraining (Phase 8)."""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from poker_ai.features.sequence import TOK_PAD, pack_action_token
from poker_ai.ingest.records import ParsedAction, ParsedHand
from poker_ai.models.style_encoder import (
    DEFAULT_MAX_ACTIONS,
    actions_to_tokens,
    player_uid_slot,
)


@dataclass(frozen=True, slots=True)
class StyleWindow:
    """One training example: recent actions for a single player."""

    player_uid: str
    action_tokens: tuple[int, ...]
    uid_slot: int
    hand_id: int


def _player_actions_chronological(hand: ParsedHand) -> dict[str, list[ParsedAction]]:
    by_pid = {p.player_id: p.player_uid for p in hand.players}
    out: dict[str, list[ParsedAction]] = defaultdict(list)
    for act in hand.actions:
        uid = by_pid.get(act.player_id)
        if uid:
            out[uid].append(act)
    return out


def windows_from_hand(
    hand: ParsedHand,
    *,
    window_size: int = DEFAULT_MAX_ACTIONS,
    stride: int | None = None,
) -> list[StyleWindow]:
    """Slide a fixed window over each player's actions in one hand."""
    step = stride if stride is not None else max(1, window_size // 2)
    rows: list[StyleWindow] = []
    for uid, acts in _player_actions_chronological(hand).items():
        if len(acts) < 2:
            continue
        packed = [pack_action_token(a, num_players=hand.num_players) for a in acts]
        for start in range(0, max(1, len(packed) - 1), step):
            chunk = packed[start : start + window_size]
            if len(chunk) < 2:
                continue
            tokens = actions_to_tokens(
                tuple(acts[start : start + window_size]),
                num_players=hand.num_players,
                max_actions=window_size,
            )
            rows.append(
                StyleWindow(
                    player_uid=uid,
                    action_tokens=tokens,
                    uid_slot=player_uid_slot(uid),
                    hand_id=hand.hand_id,
                )
            )
    return rows


def build_windows_from_hands(
    hands: list[ParsedHand],
    *,
    window_size: int = DEFAULT_MAX_ACTIONS,
    stride: int | None = None,
) -> list[StyleWindow]:
    rows: list[StyleWindow] = []
    for hand in hands:
        rows.extend(windows_from_hand(hand, window_size=window_size, stride=stride))
    return rows


def augment_window(
    window: StyleWindow,
    rng: random.Random,
    *,
    crop_min_frac: float = 0.5,
    token_dropout: float = 0.1,
) -> StyleWindow:
    """SimCLR view: random crop + token dropout (PAD mask)."""
    tokens = list(window.action_tokens)
    non_pad = [i for i, t in enumerate(tokens) if t != TOK_PAD]
    if len(non_pad) >= 2:
        keep = max(2, int(len(non_pad) * rng.uniform(crop_min_frac, 1.0)))
        start = rng.choice(non_pad)
        end = min(len(tokens), start + keep)
        cropped = [TOK_PAD] * len(tokens)
        seg = tokens[start:end]
        off = len(tokens) - len(seg)
        cropped[off:] = seg
        tokens = cropped
    for i, t in enumerate(tokens):
        if t != TOK_PAD and rng.random() < token_dropout:
            tokens[i] = TOK_PAD
    return StyleWindow(
        player_uid=window.player_uid,
        action_tokens=tuple(tokens),
        uid_slot=window.uid_slot,
        hand_id=window.hand_id,
    )


def split_by_player(
    windows: list[StyleWindow],
    *,
    val_frac: float = 0.15,
    seed: int = 42,
) -> tuple[list[StyleWindow], list[StyleWindow]]:
    """Hold out entire players for validation (legacy)."""
    rng = random.Random(seed)
    players = sorted({w.player_uid for w in windows})
    rng.shuffle(players)
    n_val = max(1, int(len(players) * val_frac)) if len(players) > 3 else 1
    val_set = set(players[:n_val])
    train = [w for w in windows if w.player_uid not in val_set]
    val = [w for w in windows if w.player_uid in val_set]
    return train, val


def split_windows_for_knn(
    windows: list[StyleWindow],
    *,
    val_frac: float = 0.2,
    seed: int = 42,
) -> tuple[list[StyleWindow], list[StyleWindow]]:
    """Hold out random windows per player (keeps ≥1 train window when possible)."""
    rng = random.Random(seed)
    by_player: dict[str, list[int]] = defaultdict(list)
    for i, w in enumerate(windows):
        by_player[w.player_uid].append(i)
    val_idx: set[int] = set()
    for idxs in by_player.values():
        if len(idxs) < 2:
            continue
        order = list(idxs)
        rng.shuffle(order)
        n_val = max(1, int(len(order) * val_frac))
        val_idx.update(order[:n_val])
    train = [w for i, w in enumerate(windows) if i not in val_idx]
    val = [w for i, w in enumerate(windows) if i in val_idx]
    return train, val


async def load_style_windows(
    session_factory: Any,
    *,
    limit_hands: int | None = None,
    window_size: int = DEFAULT_MAX_ACTIONS,
) -> list[StyleWindow]:
    from poker_ai.store.loader import iter_parsed_hands_since

    hands: list[ParsedHand] = []
    async with session_factory() as session:
        async for hand in iter_parsed_hands_since(session, since=None):
            hands.append(hand)
            if limit_hands is not None and len(hands) >= limit_hands:
                break
    return build_windows_from_hands(hands, window_size=window_size)


def collate_style_batch(
    batch: list[StyleWindow],
    *,
    device: Any,
) -> tuple[Any, Any, Any]:
    from poker_ai.learn._ml_deps import require_torch

    torch = require_torch()
    slots = torch.tensor([w.uid_slot for w in batch], dtype=torch.long, device=device)
    tokens = torch.tensor([list(w.action_tokens) for w in batch], dtype=torch.long, device=device)
    pad_mask = tokens == TOK_PAD
    return slots, tokens, pad_mask
