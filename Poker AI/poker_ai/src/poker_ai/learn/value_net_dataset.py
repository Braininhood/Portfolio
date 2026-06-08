"""Value-net training rows from solver cache (blueprint v2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from poker_ai.features.hhformer_tokens import TOK_PAD
from poker_ai.learn.student_dataset import load_student_rows, row_from_spot
from poker_ai.models.value_net import teacher_value_target
from poker_ai.solver.bridge.cache import SolverCache


@dataclass(frozen=True, slots=True)
class ValueRow:
    token_ids: tuple[int, ...]
    state_extras: tuple[float, ...]
    target_value: float
    cache_key: str


def load_value_rows(cache: SolverCache) -> list[ValueRow]:
    rows: list[ValueRow] = []
    for spot in cache.load_all():
        student_row = row_from_spot(spot)
        target = teacher_value_target(spot.action_labels, spot.frequencies)
        rows.append(
            ValueRow(
                token_ids=student_row.token_ids,
                state_extras=student_row.state_extras,
                target_value=target,
                cache_key=spot.cache_key,
            )
        )
    if not rows:
        student_rows = load_student_rows(cache)
        return [
            ValueRow(
                token_ids=r.token_ids,
                state_extras=r.state_extras,
                target_value=teacher_value_target(
                    ("fold", "check_call", "bet_33", "bet_66", "allin"),
                    r.target_freqs,
                ),
                cache_key=r.cache_key,
            )
            for r in student_rows
        ]
    return rows


def collate_value_batch(rows: list[ValueRow], *, pad_id: int = TOK_PAD) -> dict[str, Any]:
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
    targets = torch.tensor([r.target_value for r in rows], dtype=torch.float32)
    return {
        "token_ids": ids,
        "key_padding_mask": mask,
        "state_extras": extras,
        "targets": targets,
    }
