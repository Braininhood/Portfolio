"""Walk paths, detect format, parse, and upsert into the store."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poker_ai.config.settings import get_settings
from poker_ai.ingest.parallel import parse_files_parallel
from poker_ai.ingest.parse_file import parse_file_hands as _parse_file_hands
from poker_ai.ingest.stats import IngestStats
from poker_ai.ingest.store_gate import parsed_hand_passes_store_gate
from poker_ai.runtime.progress import ProgressFn
from poker_ai.runtime.workers import resolve_worker_count
from poker_ai.store.repository import insert_hand, upsert_hand

_HAND_GLOBS = ("**/*.txt", "**/*.json", "**/*.phh", "**/*.phhs")

CancelCheck = Callable[[], bool]


class IngestCancelled(Exception):
    """Raised when ``cancel_check`` returns True during ingest."""


async def ingest_path(
    path: Path,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    uid_secret: str,
    max_hands: int | None = None,
    workers: int | None = None,
    progress: ProgressFn = None,
    cancel_check: CancelCheck | None = None,
) -> IngestStats:
    """Ingest files under ``path`` (file or directory, including subfolders).

    When ``max_hands`` is set, stop after that many **new** hands (duplicates updated
    do not count toward the limit). Re-importing the same hand updates it but does not
    inflate your library count.
    """
    if max_hands is not None and max_hands <= 0:
        max_hands = None
    files_processed = 0
    hands_new = 0
    hands_updated = 0
    hands_skipped = 0
    tree_root = path.resolve() if path.is_dir() else None
    require_complete = get_settings().ingest_require_complete_hands
    files = collect_hand_files(path)
    n_files = len(files)
    # Parallel batch cannot stop cleanly on new-hand cap — use serial when capped.
    n_workers = 1 if max_hands is not None else resolve_worker_count(workers)

    append_only = os.environ.get("POKER_AI_INGEST_APPEND_ONLY", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if not append_only:
        from sqlalchemy import func, select

        from poker_ai.store.models import Game

        async with session_factory() as probe:
            n_existing = int(await probe.scalar(select(func.count()).select_from(Game)) or 0)
            append_only = n_existing == 0

    def _emit(pct: int, msg: str, **detail: Any) -> None:
        if progress:
            progress({"pct": pct, "msg": msg, "detail": detail})

    def _check_cancel() -> None:
        if cancel_check and cancel_check():
            raise IngestCancelled("Import stopped")

    def _at_new_cap() -> bool:
        return max_hands is not None and hands_new >= max_hands

    async def _upsert_one(session: AsyncSession, parsed: Any, *, source_file: Path | None = None) -> None:
        nonlocal hands_new, hands_updated, hands_skipped
        if not parsed_hand_passes_store_gate(parsed, require_complete=require_complete):
            hands_skipped += 1
            return
        from poker_ai.ingest.canonical_id import INGEST_PHH
        from poker_ai.ingest.corpus_policy import phh_hand_passes_policy

        if getattr(parsed, "ingest_source", None) == INGEST_PHH and not phh_hand_passes_policy(
            parsed,
            file_path=source_file,
        ):
            hands_skipped += 1
            return
        if append_only:
            await insert_hand(session, parsed)
            hands_new += 1
            return
        outcome = await upsert_hand(session, parsed)
        if outcome == "new":
            hands_new += 1
        else:
            hands_updated += 1

    if n_workers > 1 and len(files) >= 8:
        files_processed = len(files)
        parsed_list = parse_files_parallel(
            files,
            uid_secret=uid_secret,
            tree_root=tree_root,
            workers=n_workers,
        )
        batch_size = max(50, int(os.environ.get("POKER_AI_INGEST_BATCH_SIZE", "500")))
        for i in range(0, len(parsed_list), batch_size):
            _check_cancel()
            if _at_new_cap():
                break
            chunk = parsed_list[i : i + batch_size]
            async with session_factory() as session:
                async with session.begin():
                    for parsed in chunk:
                        if _at_new_cap():
                            break
                        await _upsert_one(session, parsed)
            if hands_new > 0 and (hands_new == 1 or hands_new % 200 == 0):
                _emit(
                    min(99, int(100 * hands_new / max(max_hands or hands_new, 1))),
                    f"Added {hands_new:,} new hands"
                    + (f" ({hands_updated:,} duplicates updated)" if hands_updated else ""),
                    hands_new=hands_new,
                    hands_updated=hands_updated,
                    hands_cap=max_hands,
                    files_total=n_files,
                )
    else:
        for fp in files:
            _check_cancel()
            if _at_new_cap():
                break
            files_processed += 1
            _emit(
                min(99, int(100 * files_processed / max(n_files, 1))),
                f"Reading {fp.name} ({files_processed}/{n_files} files)",
                file_index=files_processed,
                files_total=n_files,
                hands_new=hands_new,
            )
            async with session_factory() as session:
                async with session.begin():
                    for parsed in _parse_file_hands(fp, uid_secret=uid_secret, tree_root=tree_root):
                        _check_cancel()
                        if _at_new_cap():
                            break
                        await _upsert_one(session, parsed, source_file=fp)
                        if hands_new > 0 and hands_new % 100 == 0:
                            _emit(
                                min(99, int(100 * hands_new / max(max_hands or hands_new * 2, 1))),
                                f"Added {hands_new:,} new hands",
                                hands_new=hands_new,
                                hands_updated=hands_updated,
                                hands_cap=max_hands,
                                current_file=fp.name,
                            )
    return IngestStats(
        files_processed=files_processed,
        hands_new=hands_new,
        hands_updated=hands_updated,
        hands_skipped=hands_skipped,
    )


def collect_hand_files(path: Path) -> list[Path]:
    """All ingestable files under ``path`` (recursive), deduped, sorted."""
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []
    by_key: dict[str, Path] = {}
    for pat in _HAND_GLOBS:
        for p in path.glob(pat):
            by_key[p.resolve().as_posix()] = p
    return sorted(by_key.values(), key=lambda p: p.as_posix().lower())


def _collect_hand_files(path: Path) -> list[Path]:
    """Backward-compatible alias."""
    return collect_hand_files(path)


def count_hand_files(path: Path) -> int:
    """Number of ingestable files under ``path`` (for UI preview)."""
    return len(collect_hand_files(path))


def run_ingest_sync(
    path: Path,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    uid_secret: str,
    max_hands: int | None = None,
    workers: int | None = None,
    progress: ProgressFn = None,
    cancel_check: CancelCheck | None = None,
) -> IngestStats:
    """Blocking wrapper used by Typer and the API job runner."""
    return asyncio.run(
        ingest_path(
            path,
            session_factory=session_factory,
            uid_secret=uid_secret,
            max_hands=max_hands,
            workers=workers,
            progress=progress,
            cancel_check=cancel_check,
        )
    )
