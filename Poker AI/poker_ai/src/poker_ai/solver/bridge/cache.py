"""Disk cache of solved spots keyed by board × tree × ranges (Phase 7)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import xxhash

from poker_ai.solver.bridge.schemas import SolvedSpot, SpotSpec


def _hash_text(text: str) -> str:
    return xxhash.xxh64(text.encode("utf-8")).hexdigest()


def board_hash(board: str) -> str:
    norm = board.replace(",", " ").strip().lower()
    parts = sorted(p.strip() for p in norm.split() if p.strip())
    return _hash_text(",".join(parts))


def sizing_tree_hash(spec: SpotSpec) -> str:
    lines = [spec.sizing_tree_id]
    for row in spec.bet_sizes:
        lines.append("|".join(row))
    lines.append(f"allin={spec.allin_threshold}")
    return _hash_text("\n".join(lines))


def ranges_hash(range_oop: str, range_ip: str) -> str:
    return _hash_text(f"oop:{range_oop.strip()}\nip:{range_ip.strip()}")


def cache_key(spec: SpotSpec) -> str:
    """Stable key: ``(board_hash, sizing_tree_hash, ranges_hash)``."""
    return _hash_text(
        f"{board_hash(spec.normalized_board())}|"
        f"{sizing_tree_hash(spec)}|"
        f"{ranges_hash(spec.range_oop, spec.range_ip)}"
    )


@dataclass
class SolverCache:
    """JSONL index + per-spot JSON payloads under ``root_dir``."""

    root_dir: Path
    _index_path: Path = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.root_dir = Path(self.root_dir).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.root_dir / "index.jsonl"

    def path_for(self, key: str) -> Path:
        return self.root_dir / "spots" / f"{key}.json"

    def contains(self, key: str) -> bool:
        return self.path_for(key).is_file()

    def get(self, key: str) -> SolvedSpot | None:
        path = self.path_for(key)
        if not path.is_file():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        return SolvedSpot.from_dict(raw)

    def put(self, spot: SolvedSpot) -> Path:
        path = self.path_for(spot.cache_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(spot.to_dict(), indent=2), encoding="utf-8")
        row = {"cache_key": spot.cache_key, "board": spot.board, "backend": spot.backend}
        with self._index_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
        return path

    def load_all(self) -> list[SolvedSpot]:
        spots_dir = self.root_dir / "spots"
        if not spots_dir.is_dir():
            return []
        out: list[SolvedSpot] = []
        for path in sorted(spots_dir.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            out.append(SolvedSpot.from_dict(raw))
        return out

    def stats(self) -> dict[str, Any]:
        rows = self.load_all()
        backends: dict[str, int] = {}
        for s in rows:
            backends[s.backend] = backends.get(s.backend, 0) + 1
        return {"count": len(rows), "backends": backends}
