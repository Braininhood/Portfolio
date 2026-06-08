"""REST + WebSocket for the background job queue (Phase W1)."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_db
from schemas import (
    JobCreatedResponse,
    JobDetailResponse,
    JobFriendlySummary,
    JobListResponse,
    JobNextStep,
    JobProgressEvent,
    JobRequest,
    JobSummary,
    NightlyScheduleRequest,
    ScheduleEntrySchema,
    ScheduleListResponse,
    ScheduleRequest,
    ScheduleUpdateResponse,
)
from services.job_friendly import friendly_error_message, friendly_job_summary
from services.job_hub import hub
from services.job_gate import JobConflictError, assert_no_active_job
from services.job_runner import (
    JOB_TYPES,
    force_cancel_all_active,
    force_cancel_job,
    is_cancelled,
    request_cancel,
    run_job_async,
)

from poker_ai.store import jobs_store
from poker_ai.store.db import get_async_session_factory
from poker_ai.store.loader import count_parsed_hands

router = APIRouter(tags=["jobs"])

_SCHEDULE_LABELS: dict[str, str] = {
    "features_build": "Prepare hands for AI",
    "train_hhformer": "Train HHFormer",
    "train_multiway_student": "Multi-way AI",
    "train_student": "Train decision AI",
    "league_run": "Bot league",
}


async def _schedule_entry_schema(
    session: AsyncSession,
    entry: Any,
) -> ScheduleEntrySchema:
    from services import job_schedule

    last = await jobs_store.last_finished_job(session, entry.job_type)
    last_at: str | None = None
    last_status: str | None = None
    if last:
        last_at = _dt_iso(last.get("finished_at"))
        last_status = str(last.get("status", ""))
    task_name = entry.os_task_name or job_schedule.task_name(entry.job_type)
    return ScheduleEntrySchema(
        job_type=entry.job_type,
        label=_SCHEDULE_LABELS.get(entry.job_type) or entry.job_type,
        enabled=entry.enabled,
        time_local=entry.time_local,
        frequency=entry.frequency,
        day_of_week=entry.day_of_week,
        os_installed=job_schedule.os_task_installed(task_name) if entry.enabled else False,
        last_run_at=last_at,
        last_run_status=last_status,
    )


def _dt_iso(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


def _parse_json_col(raw: Any) -> dict[str, Any] | None:
    if raw is None or raw == "":
        return None
    try:
        parsed = json.loads(str(raw))
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except json.JSONDecodeError:
        return None


def _progress_from_row(row: dict[str, Any]) -> JobProgressEvent | None:
    raw = row.get("progress_json")
    if not raw:
        return None
    data = _parse_json_col(raw)
    if not data:
        return None
    return JobProgressEvent(
        pct=int(data.get("pct", 0)),
        msg=str(data.get("msg", "")),
        detail=data.get("detail") if isinstance(data.get("detail"), dict) else None,
    )


def _best_progress_event(row: dict[str, Any]) -> dict[str, Any] | None:
    """Merge DB snapshot with in-memory latest (worker thread may be ahead of async loop)."""
    db = _progress_from_row(row)
    live = hub.latest_progress(str(row["id"]))
    if db is None and live is None:
        return None
    if db is None:
        return live
    if live is None:
        return db.model_dump(exclude_none=True)
    db_pct = int(db.pct)
    live_pct = int(live.get("pct", 0))
    if live_pct > db_pct:
        return live
    if live_pct == db_pct and len(str(live.get("msg", ""))) > len(db.msg):
        return live
    return db.model_dump(exclude_none=True)


def _row_to_summary(row: dict[str, Any]) -> JobSummary:
    return JobSummary(
        job_id=str(row["id"]),
        type=str(row["type"]),
        status=str(row["status"]),
        created_at=_dt_iso(row.get("created_at")),
        started_at=_dt_iso(row.get("started_at")),
        finished_at=_dt_iso(row.get("finished_at")),
        progress=_progress_from_row(row),
        error=str(row["error"]) if row.get("error") else None,
    )


def _friendly_schema(
    job_type: str,
    *,
    status: str,
    result: dict[str, Any] | None,
    error: str | None,
    db_hands: int | None,
) -> JobFriendlySummary:
    raw = friendly_job_summary(
        job_type,
        status=status,
        result=result,
        error=error,
        db_hands=db_hands,
    )
    steps = [
        JobNextStep(
            label=s["label"],
            path=s["path"],
            hint=s.get("hint"),
            action=s.get("action"),
            job_type=s.get("job_type"),
            job_params=s.get("job_params") if isinstance(s.get("job_params"), dict) else {},
        )
        for s in raw.get("next_steps", [])
    ]
    return JobFriendlySummary(
        headline=str(raw["headline"]),
        explanation=str(raw["explanation"]),
        advice=list(raw.get("advice", [])),
        next_steps=steps,
        severity=str(raw.get("severity", "info")),
    )


async def _row_to_detail(row: dict[str, Any], session: AsyncSession) -> JobDetailResponse:
    base = _row_to_summary(row)
    result = _parse_json_col(row.get("result_json"))
    err_raw = str(row["error"]) if row.get("error") else None
    db_hands: int | None = None
    try:
        db_hands = await count_parsed_hands(session)
    except Exception:
        db_hands = None
    friendly = _friendly_schema(
        str(row["type"]),
        status=str(row["status"]),
        result=result,
        error=friendly_error_message(err_raw) if err_raw and str(row["status"]) == "error" else err_raw,
        db_hands=db_hands,
    )
    return JobDetailResponse(
        **base.model_dump(),
        params=_parse_json_col(row.get("params_json")),
        result=result,
        friendly=friendly,
    )


@router.post("/jobs", response_model=JobCreatedResponse, status_code=202)
async def create_job(req: JobRequest, session: AsyncSession = Depends(get_db)) -> JobCreatedResponse:
    if req.type not in JOB_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown job type '{req.type}'. Allowed: {', '.join(sorted(JOB_TYPES))}",
        )
    params = dict(req.params)
    if req.type in ("train_student", "train_multiway_student"):
        from services.play_auto_learn import enrich_train_params

        params = enrich_train_params(params)
    job_id = str(uuid.uuid4())
    try:
        await assert_no_active_job(session)
        jobs_store.sync_insert_job(
            job_id=job_id,
            job_type=req.type,
            status="queued",
            params=params,
        )
    except JobConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "message": str(exc),
                "active_job_id": exc.job_id,
                "active_job_type": exc.job_type,
            },
        ) from exc
    factory = get_async_session_factory()
    from services.terminal_log import log_job_line

    log_job_line(job_id, req.type, "accepted via POST /jobs (queued)")
    asyncio.create_task(run_job_async(job_id, req.type, params, session_factory=factory))
    return JobCreatedResponse(job_id=job_id)


@router.get("/jobs/schedule", response_model=ScheduleListResponse)
async def get_job_schedule(session: AsyncSession = Depends(get_db)) -> ScheduleListResponse:
    from services import job_schedule

    entries, nightly_enabled, msg = job_schedule.list_schedule_entries()
    data = job_schedule.load_config()
    schemas = [await _schedule_entry_schema(session, e) for e in entries]
    last_nightly = await jobs_store.last_nightly_run_at(session)
    return ScheduleListResponse(
        platform=job_schedule.platform_name(),
        scheduler_available=job_schedule.scheduler_available(),
        nightly_enabled=nightly_enabled,
        nightly_start_time=str(data.get("nightly_start_time", "00:00")),
        entries=schemas,
        last_nightly_run_at=last_nightly,
        message=msg,
    )


@router.post("/jobs/schedule", response_model=ScheduleUpdateResponse)
async def update_job_schedule(
    req: ScheduleRequest,
    session: AsyncSession = Depends(get_db),
) -> ScheduleUpdateResponse:
    from services import job_schedule

    try:
        job_schedule.upsert_schedule_entry(
            job_type=req.job_type,
            enabled=req.enabled,
            time_local=req.time_local,
            frequency=req.frequency,
            day_of_week=req.day_of_week,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    entries, nightly, msg = job_schedule.list_schedule_entries()
    schemas = [await _schedule_entry_schema(session, e) for e in entries]
    return ScheduleUpdateResponse(entries=schemas, message=msg)


@router.post("/jobs/schedule/nightly", response_model=ScheduleUpdateResponse)
async def update_nightly_schedule(
    req: NightlyScheduleRequest,
    session: AsyncSession = Depends(get_db),
) -> ScheduleUpdateResponse:
    from services import job_schedule

    try:
        job_schedule.set_nightly_bundle(enabled=req.enabled, start_time=req.start_time)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    entries, _, msg = job_schedule.list_schedule_entries()
    schemas = [await _schedule_entry_schema(session, e) for e in entries]
    hint = None
    if req.enabled and not job_schedule.scheduler_available():
        hint = msg
    elif req.enabled:
        hint = (
            "Nightly retrain scheduled. Tasks run via CLI (python -m poker_ai …) — "
            "the dashboard does not need to stay open."
        )
    return ScheduleUpdateResponse(entries=schemas, message=hint or msg)


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(session: AsyncSession = Depends(get_db)) -> JobListResponse:
    rows = await jobs_store.list_jobs_recent(session, limit=50)
    jobs = [_row_to_summary(r) for r in rows]
    return JobListResponse(jobs=jobs, total=len(jobs))


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: str, session: AsyncSession = Depends(get_db)) -> JobDetailResponse:
    row = await jobs_store.fetch_job(session, job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return await _row_to_detail(row, session)


@router.get("/jobs/active/summary")
async def active_jobs_summary(session: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    rows = await jobs_store.list_active_jobs(session, limit=20)
    return {
        "active": [_row_to_summary(r) for r in rows],
        "count": len(rows),
    }


@router.post("/jobs/cancel-all", status_code=202)
async def cancel_all_jobs() -> dict[str, Any]:
    """Release every queued/running job so new work can start (fixes stuck tasks)."""
    factory = get_async_session_factory()
    ids = await force_cancel_all_active(
        factory,
        reason="Stopped by user (release all tasks)",
    )
    return {"cancelled": ids, "count": len(ids)}


@router.post("/jobs/{job_id}/cancel", status_code=202)
async def cancel_job(job_id: str) -> dict[str, str]:
    factory = get_async_session_factory()
    try:
        async with factory() as session:
            row = await jobs_store.fetch_job(session, job_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Job not found")
        status = str(row["status"])
        if status in ("done", "error", "cancelled"):
            return {"job_id": job_id, "status": status}
        request_cancel(job_id)
        ok = await force_cancel_job(
            job_id,
            session_factory=factory,
            reason="Stopped by user",
        )
        if not ok:
            async with factory() as session:
                row = await jobs_store.fetch_job(session, job_id)
            if row is None:
                raise HTTPException(status_code=404, detail="Job not found")
            return {"job_id": job_id, "status": str(row["status"])}
        return {"job_id": job_id, "status": "cancelled"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not cancel job: {exc}") from exc


@router.websocket("/ws/jobs/{job_id}")
async def job_progress_stream(ws: WebSocket, job_id: str) -> None:
    await ws.accept()
    factory = get_async_session_factory()

    async def _safe_send(payload: dict[str, Any]) -> bool:
        try:
            await ws.send_json(payload)
            return True
        except WebSocketDisconnect:
            return False
        except RuntimeError:
            return False

    async with factory() as session:
        row = await jobs_store.fetch_job(session, job_id)
    if row is None:
        await _safe_send({"status": "error", "error": "Job not found", "msg": "Job not found"})
        await ws.close()
        return

    status = str(row["status"])
    progress_payload = _best_progress_event(row)
    if progress_payload is not None:
        if not await _safe_send(progress_payload):
            return
    elif status == "queued":
        if not await _safe_send({"pct": 0, "msg": "Queued…"}):
            return

    if status in ("done", "error", "cancelled"):
        terminal: dict[str, Any] = {"status": status, "msg": status}
        if status == "done":
            terminal["result"] = _parse_json_col(row.get("result_json"))
            terminal["pct"] = 100
        if row.get("error"):
            terminal["error"] = str(row["error"])
        await _safe_send(terminal)
        await ws.close()
        return

    await hub.register(job_id, ws)
    try:
        while True:
            if is_cancelled(job_id):
                await asyncio.sleep(0.5)
                continue
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
                if msg.strip().lower() == "ping":
                    if not await _safe_send({"msg": "pong"}):
                        break
            except asyncio.TimeoutError:
                async with factory() as session:
                    fresh = await jobs_store.fetch_job(session, job_id)
                if fresh and str(fresh["status"]) in ("done", "error", "cancelled"):
                    st = str(fresh["status"])
                    payload: dict[str, Any] = {"status": st, "msg": st}
                    if st == "done":
                        payload["result"] = _parse_json_col(fresh.get("result_json"))
                        payload["pct"] = 100
                    if fresh.get("error"):
                        payload["error"] = str(fresh["error"])
                    await _safe_send(payload)
                    break
                if fresh and str(fresh["status"]) == "running":
                    heartbeat = _best_progress_event(fresh)
                    if heartbeat is not None and not await _safe_send(heartbeat):
                        break
    except WebSocketDisconnect:
        pass
    finally:
        await hub.unregister(job_id, ws)
