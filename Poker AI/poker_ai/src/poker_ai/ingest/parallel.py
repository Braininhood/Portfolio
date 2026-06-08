"""Parallel file parsing for directory ingest."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from poker_ai.ingest.parse_file import parse_file_hands
from poker_ai.ingest.records import ParsedHand


def _parse_one(args: tuple[str, str, str | None]) -> list[ParsedHand]:
    path_s, uid_secret, tree_root_s = args
    tree_root = Path(tree_root_s) if tree_root_s else None
    return parse_file_hands(Path(path_s), uid_secret=uid_secret, tree_root=tree_root)


def parse_files_parallel(
    files: list[Path],
    *,
    uid_secret: str,
    tree_root: Path | None,
    workers: int,
) -> list[ParsedHand]:
    """Parse hand files in a process pool; order follows ``files``."""
    if workers <= 1 or len(files) < 8:
        out: list[ParsedHand] = []
        for fp in files:
            out.extend(parse_file_hands(fp, uid_secret=uid_secret, tree_root=tree_root))
        return out

    root_s = str(tree_root.resolve()) if tree_root is not None else None
    tasks = [(str(fp.resolve()), uid_secret, root_s) for fp in files]
    chunks: list[list[ParsedHand]] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        chunks = list(pool.map(_parse_one, tasks, chunksize=max(1, len(tasks) // (workers * 4))))
    merged: list[ParsedHand] = []
    for chunk in chunks:
        merged.extend(chunk)
    return merged
