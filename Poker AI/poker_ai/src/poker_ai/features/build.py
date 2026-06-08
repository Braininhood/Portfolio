"""Batch feature materialisation from the canonical store."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from poker_ai.features.info_set import encode_hand_tensor, info_set_key
from poker_ai.features.parallel import encode_records_parallel
from poker_ai.features.range import l1_sum, one_hot_range_from_hole_string, uniform_range
from poker_ai.ingest.records import ParsedHand
from poker_ai.runtime.cancel import WorkCancelled
from poker_ai.runtime.progress import ProgressFn

CancelCheck = Callable[[], bool]
from poker_ai.store.loader import count_parsed_hands_since, iter_parsed_hands_since


async def iter_feature_records(
    session: AsyncSession,
    *,
    since: datetime | None = None,
) -> AsyncIterator[dict[str, object]]:
    """Yield JSON-serialisable dicts per stored hand."""
    async for hand in iter_parsed_hands_since(session, since=since):
        tensor = encode_hand_tensor(hand)
        key = info_set_key(hand)
        rng = (
            one_hot_range_from_hole_string(hand.hero_cards)
            if hand.hero_cards and hand.hero_cards.strip()
            else uniform_range()
        )
        yield {
            "hand_id": hand.hand_id,
            "info_set_key": key,
            "tensor": list(tensor),
            "range": list(rng),
            "range_l1": l1_sum(rng),
        }


async def write_feature_jsonl(
    session: AsyncSession,
    out: Path,
    *,
    since: datetime | None = None,
    workers: int = 1,
    batch_size: int = 512,
    blueprint_full: bool = False,
    progress: ProgressFn = None,
    cancel_check: CancelCheck | None = None,
) -> int:
    """Write one JSON object per line; returns number of hands written."""

    def _abort() -> None:
        if cancel_check and cancel_check():
            raise WorkCancelled("Feature build stopped")

    total = await count_parsed_hands_since(session, since=since)
    n = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    batch: list[ParsedHand] = []
    with out.open("w", encoding="utf-8") as fp:
        async for hand in iter_parsed_hands_since(session, since=since):
            _abort()
            batch.append(hand)
            if len(batch) < batch_size:
                continue
            _abort()
            for row in encode_records_parallel(batch, workers=workers, blueprint_full=blueprint_full):
                fp.write(json.dumps(row, separators=(",", ":")))
                fp.write("\n")
                n += 1
            if progress and total > 0:
                mode = "extended" if blueprint_full else "standard"
                progress(
                    {
                        "pct": min(99, int(100 * n / total)),
                        "msg": f"Feature encode ({mode}): {n}/{total} hands",
                        "detail": {"hands_done": n, "hands_total": total, "blueprint_full": blueprint_full},
                    }
                )
            batch.clear()
        if batch:
            _abort()
            for row in encode_records_parallel(batch, workers=workers, blueprint_full=blueprint_full):
                fp.write(json.dumps(row, separators=(",", ":")))
                fp.write("\n")
                n += 1
            if progress and total > 0:
                progress(
                    {
                        "pct": min(99, int(100 * n / total)),
                        "msg": f"Feature encode: {n}/{total} hands",
                        "detail": {"hands_done": n, "hands_total": total},
                    }
                )
    return n
