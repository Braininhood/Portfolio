"""Browse cached solver (teacher) spots."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from deps import cached_settings
from schemas import (
    SolverActionRow,
    SolverSpotDetail,
    SolverSpotSummary,
    SolverSpotsResponse,
    SolverStatsResponse,
)

from poker_ai.solver.bridge.cache import SolverCache
from poker_ai.solver.bridge.schemas import STUDENT_ACTIONS

router = APIRouter(prefix="/solver", tags=["solver"])

_FRIENDLY_ACTION = {
    "fold": "Fold",
    "check_call": "Check / call",
    "bet_33": "Bet ⅓ pot",
    "bet_66": "Bet ⅔ pot",
    "allin": "All-in",
}


def _cache() -> SolverCache:
    return SolverCache(cached_settings().solver_cache_dir)


def _spot_summary(path: Path) -> SolverSpotSummary | None:
    import json

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    labels = [str(x) for x in raw.get("action_labels", STUDENT_ACTIONS)]
    freqs = [float(x) for x in raw.get("frequencies", [])]
    if not freqs:
        return None
    top_i = max(range(len(freqs)), key=lambda i: freqs[i])
    top_label = labels[top_i] if top_i < len(labels) else labels[0]
    return SolverSpotSummary(
        cache_key=str(raw.get("cache_key", path.stem)),
        board=str(raw.get("board", "—")),
        backend=str(raw.get("backend", "unknown")),
        top_action=_FRIENDLY_ACTION.get(top_label, top_label),
        top_frequency_pct=round(freqs[top_i] * 100, 1),
    )


@router.get("/stats", response_model=SolverStatsResponse)
def solver_stats() -> SolverStatsResponse:
    st = _cache().stats()
    backends = st.get("backends") or {}
    return SolverStatsResponse(
        total_spots=int(st.get("count", 0)),
        backends={str(k): int(v) for k, v in backends.items()},
        cache_dir=str(_cache().root_dir),
    )


@router.get("/spots", response_model=SolverSpotsResponse)
def list_solver_spots(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SolverSpotsResponse:
    spots_dir = _cache().root_dir / "spots"
    if not spots_dir.is_dir():
        return SolverSpotsResponse(total=0, page=page, page_size=page_size, spots=[])
    paths = sorted(spots_dir.glob("*.json"), key=lambda p: p.name)
    total = len(paths)
    start = (page - 1) * page_size
    chunk = paths[start : start + page_size]
    spots: list[SolverSpotSummary] = []
    for path in chunk:
        row = _spot_summary(path)
        if row is not None:
            spots.append(row)
    return SolverSpotsResponse(
        total=total,
        page=page,
        page_size=page_size,
        spots=spots,
    )


@router.get("/spots/{cache_key}", response_model=SolverSpotDetail)
def get_solver_spot(cache_key: str) -> SolverSpotDetail:
    spot = _cache().get(cache_key)
    if spot is None:
        raise HTTPException(status_code=404, detail="Spot not in cache")
    actions = [
        SolverActionRow(
            action=_FRIENDLY_ACTION.get(label, label),
            frequency_pct=round(freq * 100, 1),
        )
        for label, freq in zip(spot.action_labels, spot.frequencies, strict=True)
    ]
    top_i = max(range(len(spot.frequencies)), key=lambda i: spot.frequencies[i])
    return SolverSpotDetail(
        cache_key=spot.cache_key,
        board=spot.board,
        backend=spot.backend,
        summary=(
            f"Community cards on the table: {spot.board}. "
            f"(Solver spots do not include private hole cards — only the shared board.) "
            f"Best play here is usually "
            f"{_FRIENDLY_ACTION.get(spot.action_labels[top_i], spot.action_labels[top_i])} "
            f"({spot.frequencies[top_i] * 100:.0f}% of the time)."
        ),
        board_note=(
            "Shows only the flop/turn/river cards every player shares. "
            "Your two private cards are not part of this cache entry."
        ),
        actions=actions,
        meta=spot.meta,
    )
