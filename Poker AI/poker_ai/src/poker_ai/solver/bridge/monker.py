"""MonkerSolver / multi-way tree export bridge (Phase 7c — licensed teacher JSON)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from poker_ai.solver.bridge.cache import _hash_text, cache_key
from poker_ai.solver.bridge.mock_teacher import mock_strategy
from poker_ai.solver.bridge.schemas import STUDENT_ACTIONS, SolvedSpot, SpotSpec


@dataclass(frozen=True, slots=True)
class MultiwaySpotSpec(SpotSpec):
    """3+ player postflop spot (extends HU :class:`SpotSpec`)."""

    n_active: int = 3
    num_seats: int = 6


def _map_action_label(label: str) -> str:
    """Map export label → :data:`STUDENT_ACTIONS` bucket."""
    low = label.strip().lower().replace(" ", "_")
    if low in ("fold", "f"):
        return "fold"
    if low in ("check", "call", "check_call", "c", "x"):
        return "check_call"
    if low in ("bet_33", "bet33", "bet_small", "small", "33"):
        return "bet_33"
    if low in ("bet_66", "bet66", "bet_medium", "medium", "66", "raise"):
        return "bet_66"
    if low in ("allin", "all_in", "shove", "jam"):
        return "allin"
    if low in ("bet", "b"):
        return "bet_33"
    return "check_call"


def frequencies_to_student_targets(
    labels: tuple[str, ...],
    freqs: tuple[float, ...],
) -> tuple[float, ...]:
    """Collapse arbitrary export labels into the student vocabulary."""
    mass = {k: 0.0 for k in STUDENT_ACTIONS}
    for lab, f in zip(labels, freqs, strict=False):
        mass[_map_action_label(lab)] += float(f)
    s = sum(mass.values()) or 1.0
    return tuple(mass[k] / s for k in STUDENT_ACTIONS)


def parse_monker_export(path: Path) -> tuple[tuple[str, ...], tuple[float, ...]]:
    """Parse strategy frequencies from a Monker-style JSON export."""
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("strategy") or data.get("frequencies") or data
    if isinstance(raw, dict):
        labels = tuple(str(k) for k in raw.keys())
        freqs = tuple(float(v) for v in raw.values())
        s = sum(freqs) or 1.0
        return labels, tuple(f / s for f in freqs)
    msg = f"unsupported Monker export shape in {path}"
    raise ValueError(msg)


def parse_monker_export_file(path: Path) -> SolvedSpot:
    """Load one export file into a :class:`SolvedSpot` with multi-way metadata."""
    data = json.loads(path.read_text(encoding="utf-8"))
    board_raw = data.get("board") or path.stem.replace("_", ",")
    spec = MultiwaySpotSpec(
        board=str(board_raw),
        pot_chips=int(data.get("pot_chips", data.get("pot", 10))),
        effective_stack=int(data.get("effective_stack", data.get("stack", 95))),
        n_active=int(data.get("n_active", data.get("players", 3))),
        num_seats=int(data.get("num_seats", data.get("table_size", 6))),
        sizing_tree_id=str(data.get("sizing_tree_id", "monker_export")),
    )
    labels, freqs = parse_monker_export(path)
    key = _hash_text(f"{cache_key(spec)}|mw{spec.n_active}|s{spec.num_seats}|{path.stem}")
    return SolvedSpot(
        cache_key=key,
        board=spec.normalized_board(),
        sizing_tree_id=spec.sizing_tree_id,
        ranges_hash="monker_export",
        action_labels=labels,
        frequencies=frequencies_to_student_targets(labels, freqs),
        backend="monker",
        meta={
            "n_active": spec.n_active,
            "num_seats": spec.num_seats,
            "pot_chips": spec.pot_chips,
            "effective_stack": spec.effective_stack,
            "source": str(path),
        },
    )


def solve_multiway_spot(spec: MultiwaySpotSpec, *, backend: str = "auto") -> SolvedSpot:
    """Offline teacher for a multi-way spot (mock unless Monker export present)."""
    from poker_ai.solver.bridge.cache import ranges_hash

    key = _hash_text(f"{cache_key(spec)}|mw{spec.n_active}|s{spec.num_seats}")
    if backend in ("mock", "auto"):
        labels, freqs = mock_strategy(spec)
        if spec.n_active >= 4:
            freqs = _tighten_mock(freqs)
        return SolvedSpot(
            cache_key=key,
            board=spec.normalized_board(),
            sizing_tree_id=spec.sizing_tree_id,
            ranges_hash=ranges_hash(spec.range_oop, spec.range_ip),
            frequencies=freqs,
            action_labels=labels,
            backend="monker_mock",
            meta={
                "n_active": spec.n_active,
                "num_seats": spec.num_seats,
                "pot_chips": spec.pot_chips,
                "effective_stack": spec.effective_stack,
            },
        )
    msg = "Monker live integration requires licensed export files; use backend=mock"
    raise NotImplementedError(msg)


def _tighten_mock(freqs: tuple[float, ...]) -> tuple[float, ...]:
    arr = list(freqs)
    if len(arr) >= 5:
        arr[0] = min(1.0, arr[0] + 0.08)
        for i in (2, 3, 4):
            arr[i] = max(0.0, arr[i] * 0.85)
    s = sum(arr) or 1.0
    return tuple(x / s for x in arr)


def load_monker_export_dir(export_dir: Path) -> list[SolvedSpot]:
    """Load all ``*.json`` teacher rows from a Monker export directory."""
    if not export_dir.is_dir():
        return []
    out: list[SolvedSpot] = []
    for path in sorted(export_dir.glob("*.json")):
        try:
            out.append(parse_monker_export_file(path))
        except (json.JSONDecodeError, ValueError, OSError):
            continue
    return out


def monker_lookup_key(spec: MultiwaySpotSpec) -> str:
    return _hash_text(f"{cache_key(spec)}|mw{spec.n_active}|s{spec.num_seats}")


class MonkerTeacherCache:
    """In-memory index of Monker exports for runtime blend (Phase 7c)."""

    def __init__(self, export_dir: Path) -> None:
        self._by_key: dict[str, tuple[float, ...]] = {}
        for spot in load_monker_export_dir(export_dir):
            self._by_key[spot.cache_key] = spot.frequencies
            spec = MultiwaySpotSpec(
                board=spot.board.replace(",", " "),
                pot_chips=int(spot.meta.get("pot_chips", 10)),
                effective_stack=int(spot.meta.get("effective_stack", 95)),
                n_active=int(spot.meta.get("n_active", 3)),
                num_seats=int(spot.meta.get("num_seats", 6)),
            )
            self._by_key[monker_lookup_key(spec)] = spot.frequencies

    def get(self, key: str) -> tuple[float, ...] | None:
        return self._by_key.get(key)

    def __len__(self) -> int:
        return len(self._by_key)
