"""Resolve ring/HU preflop CFR JSON paths by table size (Phase 6)."""

from __future__ import annotations

from pathlib import Path

_SOLVER_ROOT = Path("artifacts/solver")

_PINNED: dict[int, str] = {
    2: "preflop_hu_real.json",
    6: "preflop_cfr.json",
    8: "preflop_8max.json",
    9: "preflop_9max.json",
    10: "preflop_10max.json",
}


def preflop_cfr_filename(num_seats: int) -> str:
    """Default artifact basename for a solve or registry entry."""
    if num_seats in _PINNED:
        return _PINNED[num_seats]
    if num_seats <= 6:
        return _PINNED[6]
    return f"preflop_{num_seats}max.json"


def preflop_cfr_path(num_seats: int, *, root: Path | None = None) -> Path:
    base = root or _SOLVER_ROOT
    return base / preflop_cfr_filename(num_seats)


def resolve_preflop_cfr_path(num_seats: int, *, root: Path | None = None) -> Path | None:
    """Pick the best available CFR chart for ``num_seats`` (exact, then ring fallbacks)."""
    base = root or _SOLVER_ROOT
    candidates: list[int] = [num_seats]
    if num_seats > 6:
        for n in (10, 9, 8, 6):
            if n not in candidates:
                candidates.append(n)
    elif num_seats < 6 and num_seats != 2:
        candidates.append(6)
    for n in candidates:
        p = base / preflop_cfr_filename(n)
        if p.is_file():
            return p
    hu = base / "preflop_hu.json"
    if num_seats == 2 and hu.is_file():
        return hu
    return None
