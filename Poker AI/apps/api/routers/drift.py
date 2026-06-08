"""Drift monitoring API (Phase W8)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

router = APIRouter(prefix="/drift", tags=["drift"])


class DriftReportSchema(BaseModel):
    date: str
    filename: str
    features_flagged: int
    status: str
    created_at: str


class DriftListResponse(BaseModel):
    reports: list[DriftReportSchema]
    latest_status: str | None = None


class DriftFeatureRowSchema(BaseModel):
    feature: str
    label: str
    meaning: str = ""
    shift: float | None = None
    ref_mean: float | None = None
    cur_mean: float | None = None
    flagged: bool = False
    counts_toward_status: bool = True
    advice: str | None = None
    note: str | None = None


class DriftReportDetailSchema(BaseModel):
    date: str
    status: str
    poker_features_flagged: int
    hands_compared: int = 0
    summary_advice: str = ""
    method: str = ""
    features: list[DriftFeatureRowSchema] = []


class ChangepointSchema(BaseModel):
    player_uid: str
    display_name: str
    detected_at: str
    description: str
    confidence: float


class ChangepointsResponse(BaseModel):
    alerts: list[ChangepointSchema]


@router.get("/reports", response_model=DriftListResponse)
async def list_reports() -> DriftListResponse:
    from poker_ai.observability.drift import list_drift_reports

    reports = list_drift_reports(Path("data/drift"))
    items = [
        DriftReportSchema(
            date=r.date,
            filename=r.filename,
            features_flagged=r.features_flagged,
            status=r.status,
            created_at=r.created_at,
        )
        for r in reports
    ]
    latest = items[0].status if items else None
    return DriftListResponse(reports=items, latest_status=latest)


@router.get("/reports/{date}", response_class=HTMLResponse)
async def get_report_html(date: str) -> HTMLResponse:
    path = Path("data/drift") / f"drift_{date}.html"
    if not path.is_file():
        alt = Path("data/drift") / f"drift_{date[:10]}.html"
        path = alt if alt.is_file() else path
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Drift report not found")
    return HTMLResponse(path.read_text(encoding="utf-8"))


@router.get("/reports/{date}/detail", response_model=DriftReportDetailSchema)
async def get_report_detail(date: str) -> DriftReportDetailSchema:
    from poker_ai.observability.drift import load_report_detail

    raw = load_report_detail(date, Path("data/drift"))
    if raw is None:
        raise HTTPException(status_code=404, detail="Drift report detail not found")
    return DriftReportDetailSchema(
        date=str(raw.get("date", date)),
        status=str(raw.get("status", "green")),
        poker_features_flagged=int(raw.get("poker_features_flagged", raw.get("features_flagged", 0))),
        hands_compared=int(raw.get("hands_compared", 0)),
        summary_advice=str(raw.get("summary_advice", "")),
        method=str(raw.get("method", "")),
        features=[DriftFeatureRowSchema(**f) for f in raw.get("features", [])],
    )


@router.post("/run", response_model=DriftReportSchema)
async def run_drift_now() -> DriftReportSchema:
    from poker_ai.observability.drift import run_drift_check

    meta = run_drift_check(output_dir=Path("data/drift"))
    return DriftReportSchema(
        date=meta.date,
        filename=meta.filename,
        features_flagged=meta.features_flagged,
        status=meta.status,
        created_at=meta.created_at,
    )


@router.get("/changepoints", response_model=ChangepointsResponse)
async def get_changepoints(
    refresh: bool = False,
    player_uid: str | None = None,
) -> ChangepointsResponse:
    from poker_ai.learn.changepoint import detect_changepoints, scan_play_sessions_for_changepoints

    if refresh:
        alerts = scan_play_sessions_for_changepoints()
        if not alerts:
            alerts = detect_changepoints()
    else:
        alerts = detect_changepoints(player_uid=player_uid)
    if player_uid:
        alerts = [a for a in alerts if a.player_uid == player_uid]
    return ChangepointsResponse(
        alerts=[
            ChangepointSchema(
                player_uid=a.player_uid,
                display_name=a.display_name,
                detected_at=a.detected_at,
                description=a.description,
                confidence=a.confidence,
            )
            for a in alerts
        ]
    )
