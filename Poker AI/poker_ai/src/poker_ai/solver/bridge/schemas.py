"""Pydantic-style dataclasses for solver bridge I/O (Phase 7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Abstract action vocabulary aligned with Phase 6 bet tree + fold.
STUDENT_ACTIONS: tuple[str, ...] = ("fold", "check_call", "bet_33", "bet_66", "allin")


@dataclass(frozen=True, slots=True)
class SpotSpec:
    """One postflop spot for TexasSolver or the mock teacher."""

    board: str  # e.g. "Qs Jh 2h" or "Qs,Jh,2h"
    pot_chips: int = 10
    effective_stack: int = 95
    range_oop: str = ""
    range_ip: str = ""
    # TexasSolver bet sizes: (position, street, kind, pct_or_allin)
    bet_sizes: tuple[tuple[str, str, str, str], ...] = field(default_factory=tuple)
    thread_num: int = 4
    max_iteration: int = 200
    accuracy: float = 0.5
    allin_threshold: float = 1.0
    sizing_tree_id: str = "default_v1"

    def normalized_board(self) -> str:
        raw = self.board.replace(",", " ").strip()
        parts = [p.strip() for p in raw.split() if p.strip()]
        return ",".join(parts)


@dataclass(frozen=True, slots=True)
class SolvedSpot:
    """Teacher strategy for one spot (cache row)."""

    cache_key: str
    board: str
    sizing_tree_id: str
    ranges_hash: str
    action_labels: tuple[str, ...]
    frequencies: tuple[float, ...]
    backend: str  # "texas" | "mock"
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cache_key": self.cache_key,
            "board": self.board,
            "sizing_tree_id": self.sizing_tree_id,
            "ranges_hash": self.ranges_hash,
            "action_labels": list(self.action_labels),
            "frequencies": list(self.frequencies),
            "backend": self.backend,
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> SolvedSpot:
        labels = tuple(str(x) for x in raw.get("action_labels", STUDENT_ACTIONS))
        freqs = tuple(float(x) for x in raw.get("frequencies", []))
        if len(freqs) != len(labels):
            msg = "action_labels and frequencies length mismatch"
            raise ValueError(msg)
        return cls(
            cache_key=str(raw["cache_key"]),
            board=str(raw.get("board", "")),
            sizing_tree_id=str(raw.get("sizing_tree_id", "")),
            ranges_hash=str(raw.get("ranges_hash", "")),
            action_labels=labels,
            frequencies=freqs,
            backend=str(raw.get("backend", "unknown")),
            meta=dict(raw.get("meta") or {}),
        )
