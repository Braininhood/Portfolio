"""Datasets for HHFormer pretraining."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from poker_ai.features.hhformer_tokens import (
    _ACTION_VOCAB_BASE,
    _CARD_VOCAB_BASE,
    KIND_ACTION,
    KIND_CARD,
    TOK_MASK,
    TOK_PAD,
    HandSequence,
    encode_hand_sequence,
)
from poker_ai.ingest.records import ParsedHand


@dataclass(frozen=True, slots=True)
class BatchTensors:
    """One collated training batch (numpy-friendly dict before torch)."""

    token_ids: list[list[int]]
    attn_mask: list[list[bool]]
    action_targets: list[list[int]]
    card_targets: list[list[int]]
    map_mask: list[list[bool]]
    mcp_mask: list[list[bool]]
    winner_seat: list[int]
    has_showdown: list[bool]
    hero_strength: list[int]


def sequence_targets(seq: HandSequence) -> tuple[list[int], list[int]]:
    """Per-position action / card targets (``-1`` = ignore)."""
    act: list[int] = []
    card: list[int] = []
    for tid, kind in zip(seq.token_ids, seq.token_kinds, strict=True):
        if kind == KIND_ACTION and tid >= _ACTION_VOCAB_BASE:
            act.append(tid - _ACTION_VOCAB_BASE)
        else:
            act.append(-1)
        if kind == KIND_CARD and tid >= _CARD_VOCAB_BASE:
            card.append(tid - _CARD_VOCAB_BASE)
        else:
            card.append(-1)
    return act, card


def apply_random_masks(
    token_ids: Sequence[int],
    token_kinds: Sequence[int],
    *,
    map_prob: float,
    mcp_prob: float,
    rng: Any,
) -> tuple[list[int], list[bool], list[bool]]:
    """Return masked input ids plus MAP / MCP mask flags."""
    out = list(token_ids)
    map_m = [False] * len(out)
    mcp_m = [False] * len(out)
    for i, kind in enumerate(token_kinds):
        if out[i] == TOK_PAD:
            continue
        if kind == KIND_ACTION and rng.random() < map_prob:
            out[i] = TOK_MASK
            map_m[i] = True
        elif kind == KIND_CARD and rng.random() < mcp_prob:
            out[i] = TOK_MASK
            mcp_m[i] = True
    return out, map_m, mcp_m


async def load_hand_sequences(
    session_factory: Any,
    *,
    since: Any = None,
    limit: int | None = None,
) -> list[HandSequence]:
    """Load encoded sequences from the canonical store."""
    from poker_ai.store.loader import iter_parsed_hands_since

    out: list[HandSequence] = []
    async with session_factory() as session:
        async for hand in iter_parsed_hands_since(session, since=since):
            out.append(encode_hand_sequence(hand))
            if limit is not None and len(out) >= limit:
                break
    return out


def hands_to_sequences(hands: Sequence[ParsedHand]) -> list[HandSequence]:
    return [encode_hand_sequence(h) for h in hands]


def collate_sequences(
    batch: Sequence[HandSequence],
    *,
    map_prob: float,
    mcp_prob: float,
    rng: Any,
) -> BatchTensors:
    token_ids: list[list[int]] = []
    attn_mask: list[list[bool]] = []
    action_targets: list[list[int]] = []
    card_targets: list[list[int]] = []
    map_mask: list[list[bool]] = []
    mcp_mask: list[list[bool]] = []
    winner_seat: list[int] = []
    has_showdown: list[bool] = []
    hero_strength: list[int] = []

    for seq in batch:
        masked, mm, cm = apply_random_masks(
            seq.token_ids,
            seq.token_kinds,
            map_prob=map_prob,
            mcp_prob=mcp_prob,
            rng=rng,
        )
        act_t, card_t = sequence_targets(seq)
        token_ids.append(masked)
        attn_mask.append([t != TOK_PAD for t in seq.token_ids])
        action_targets.append(act_t)
        card_targets.append(card_t)
        map_mask.append(mm)
        mcp_mask.append(cm)
        winner_seat.append(-1 if seq.winner_seat is None else seq.winner_seat)
        has_showdown.append(seq.winner_seat is not None)
        hero_strength.append(seq.hero_strength_class)

    return BatchTensors(
        token_ids=token_ids,
        attn_mask=attn_mask,
        action_targets=action_targets,
        card_targets=card_targets,
        map_mask=map_mask,
        mcp_mask=mcp_mask,
        winner_seat=winner_seat,
        has_showdown=has_showdown,
        hero_strength=hero_strength,
    )


def train_val_split(
    seqs: Sequence[HandSequence],
    *,
    val_frac: float = 0.1,
    seed: int = 42,
) -> tuple[list[HandSequence], list[HandSequence]]:
    import random

    idx = list(range(len(seqs)))
    rng = random.Random(seed)
    rng.shuffle(idx)
    n_val = max(1, int(len(seqs) * val_frac)) if len(seqs) > 1 else 0
    val_idx = set(idx[:n_val])
    train = [seqs[i] for i in range(len(seqs)) if i not in val_idx]
    val = [seqs[i] for i in val_idx]
    return train, val


def load_sequences_sync(session_factory: Any, *, limit: int | None = None) -> list[HandSequence]:
    return asyncio.run(load_hand_sequences(session_factory, limit=limit))


class HandSequenceDataset:
    """Top-level, picklable dataset (``__len__`` / ``__getitem__`` for :class:`DataLoader`)."""

    def __init__(self, seqs: Sequence[HandSequence]) -> None:
        self._seqs: list[HandSequence] = list(seqs)

    def __len__(self) -> int:
        return len(self._seqs)

    def __getitem__(self, index: int) -> HandSequence:
        return self._seqs[index]


def _dataloader_worker_init(seed: int, worker_id: int) -> None:
    import random

    import numpy as np

    wseed = seed + worker_id
    random.seed(wseed)
    np.random.seed(wseed % (2**32))


class _CollateFn:
    """Picklable collate for :class:`torch.utils.data.DataLoader` workers."""

    __slots__ = ("_map_prob", "_mcp_prob", "_seed")

    def __init__(self, *, map_prob: float, mcp_prob: float, seed: int) -> None:
        self._map_prob = map_prob
        self._mcp_prob = mcp_prob
        self._seed = seed

    def __call__(self, batch: list[HandSequence]) -> BatchTensors:
        rng_seed = self._seed
        try:
            from poker_ai.learn._ml_deps import require_torch

            rng_seed = int(require_torch().initial_seed() % (2**32))
        except ImportError:
            pass
        return collate_sequences(
            batch,
            map_prob=self._map_prob,
            mcp_prob=self._mcp_prob,
            rng=random.Random(rng_seed),
        )


def make_train_dataloader(
    sequences: Sequence[HandSequence],
    *,
    batch_size: int,
    seed: int,
    map_prob: float,
    mcp_prob: float,
    num_workers: int = 0,
) -> Any:
    """``DataLoader`` over hand sequences with per-batch masking in collate."""
    from functools import partial

    from poker_ai.learn._ml_deps import cuda_available, require_torch

    require_torch()
    from torch.utils.data import DataLoader

    nw = max(0, num_workers)
    use_cuda = cuda_available()
    worker_init = partial(_dataloader_worker_init, seed) if nw > 0 else None
    return DataLoader(
        HandSequenceDataset(sequences),  # type: ignore[arg-type]
        batch_size=min(batch_size, max(1, len(sequences))),
        shuffle=True,
        num_workers=nw,
        collate_fn=_CollateFn(map_prob=map_prob, mcp_prob=mcp_prob, seed=seed),
        pin_memory=use_cuda and nw > 0,
        persistent_workers=nw > 0,
        worker_init_fn=worker_init,
        drop_last=False,
    )
