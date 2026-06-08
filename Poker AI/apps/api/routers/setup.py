"""Setup wizard — pipeline readiness and one-click job launch (Phase W4)."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_db
from schemas import JobCreatedResponse
from services.job_gate import JobConflictError, assert_no_active_job
from services.job_runner import JOB_TYPES, run_job_async
from services.setup_steps import (
    STEP_RUN_DEFAULTS,
    build_setup_steps,
    requirements_met,
)

from poker_ai.store import jobs_store
from poker_ai.store.db import get_async_session_factory

router = APIRouter(prefix="/setup", tags=["setup"])


class SetupStepSchema(BaseModel):
    id: str
    title: str
    description: str
    ready: bool
    detail: str
    requires: list[str]
    optional: bool = False
    optional_note: str | None = None
    job_type: str | None = None
    texas_solver_found: bool | None = None
    can_run: bool = False


class SetupStepsResponse(BaseModel):
    steps: list[SetupStepSchema]
    ready_count: int
    pending_count: int


class SetupRunRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)


class TexasRegisterRequest(BaseModel):
    exe_path: str = Field(..., description="Absolute path to TexasSolver console_solver")


class TexasRegisterResponse(BaseModel):
    status: str
    version: str | None = None
    exe_path: str | None = None


class DatasetSnapshotSchema(BaseModel):
    version: str
    num_hands: int
    num_features: int
    content_hash: str
    features_path: str
    created_at: str
    is_active: bool = False


class DatasetSnapshotsResponse(BaseModel):
    snapshots: list[DatasetSnapshotSchema]
    active_version: str | None = None


class SetActiveSnapshotRequest(BaseModel):
    version: str = Field(..., description="Snapshot version id, e.g. 2026-05-31")


async def _steps_with_flags(session: AsyncSession) -> list[SetupStepSchema]:
    raw = await build_setup_steps(session)
    by_id = {s["id"]: s for s in raw}
    out: list[SetupStepSchema] = []
    for s in raw:
        can_run = bool(s.get("job_type")) and requirements_met(s, by_id)
        out.append(SetupStepSchema(**s, can_run=can_run))
    return out


@router.get("/steps", response_model=SetupStepsResponse)
async def list_setup_steps(session: AsyncSession = Depends(get_db)) -> SetupStepsResponse:
    steps = await _steps_with_flags(session)
    ready_count = sum(1 for s in steps if s.ready)
    pending_count = sum(1 for s in steps if not s.ready and not s.optional)
    return SetupStepsResponse(
        steps=steps,
        ready_count=ready_count,
        pending_count=pending_count,
    )


@router.post("/run/{step_id}", response_model=JobCreatedResponse, status_code=202)
async def run_setup_step(
    step_id: str,
    body: SetupRunRequest | None = None,
    session: AsyncSession = Depends(get_db),
) -> JobCreatedResponse:
    if step_id == "ingest":
        raise HTTPException(
            status_code=400,
            detail="Use Import page to add hand histories (POST /ingest/local or upload).",
        )
    if step_id not in STEP_RUN_DEFAULTS:
        raise HTTPException(status_code=404, detail=f"Unknown setup step '{step_id}'")

    factory = get_async_session_factory()
    async with factory() as check_session:
        raw = await build_setup_steps(check_session)
    by_id = {s["id"]: s for s in raw}
    step = by_id.get(step_id)
    if step is None:
        raise HTTPException(status_code=404, detail=f"Unknown setup step '{step_id}'")
    if not requirements_met(step, by_id):
        missing = [r for r in step["requires"] if not by_id.get(r, {}).get("ready")]
        raise HTTPException(
            status_code=409,
            detail=f"Complete these steps first: {', '.join(missing)}",
        )

    job_type, defaults = STEP_RUN_DEFAULTS[step_id]
    if job_type not in JOB_TYPES:
        raise HTTPException(status_code=500, detail=f"Job type '{job_type}' is not configured")

    overrides = (body.params if body else {}) or {}
    if step_id == "solve_grid" and not step.get("texas_solver_found") and "backend" not in overrides:
        overrides = {**defaults, **overrides, "backend": "mock", "n_spots": min(int(overrides.get("n_spots", 4)), 4)}

    params = {**defaults, **overrides}
    if job_type in ("train_student", "train_multiway_student"):
        from services.play_auto_learn import enrich_train_params

        params = enrich_train_params(params)
    job_id = str(uuid.uuid4())
    try:
        await assert_no_active_job(session)
        jobs_store.sync_insert_job(
            job_id=job_id,
            job_type=job_type,
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

    run_factory = get_async_session_factory()
    asyncio.create_task(run_job_async(job_id, job_type, params, session_factory=run_factory))
    return JobCreatedResponse(job_id=job_id)


@router.post("/texas/register", response_model=TexasRegisterResponse)
async def register_texas_solver(req: TexasRegisterRequest) -> TexasRegisterResponse:
    """Register an existing TexasSolver binary (CLI: solve register-texas --exe)."""
    exe = Path(req.exe_path).expanduser()
    try:
        from poker_ai.solver.bridge.install_texas import register_texas_executable, texas_solver_status

        manifest = register_texas_executable(exe)
        ts = texas_solver_status()
        version = ts.get("version") or manifest.version
        return TexasRegisterResponse(
            status="ok",
            version=str(version) if version else None,
            exe_path=str(manifest.executable),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/snapshots", response_model=DatasetSnapshotsResponse)
async def list_dataset_snapshots() -> DatasetSnapshotsResponse:
    from poker_ai.learn.dataset_versioning import ensure_snapshots_from_disk, get_active_version

    snaps = ensure_snapshots_from_disk()
    active = get_active_version()
    return DatasetSnapshotsResponse(
        active_version=active,
        snapshots=[
            DatasetSnapshotSchema(
                version=s.version,
                num_hands=s.num_hands,
                num_features=s.num_features,
                content_hash=s.content_hash[:16] if s.content_hash else "",
                features_path=s.features_path,
                created_at=s.created_at,
                is_active=s.is_active,
            )
            for s in snaps
        ],
    )


@router.post("/snapshots/active", response_model=DatasetSnapshotSchema)
async def set_active_dataset_snapshot(req: SetActiveSnapshotRequest) -> DatasetSnapshotSchema:
    from poker_ai.learn.dataset_versioning import set_active_version

    try:
        snap = set_active_version(req.version.replace(" (live)", "").split()[0])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DatasetSnapshotSchema(
        version=snap.version,
        num_hands=snap.num_hands,
        num_features=snap.num_features,
        content_hash=snap.content_hash[:16] if snap.content_hash else "",
        features_path=snap.features_path,
        created_at=snap.created_at,
        is_active=True,
    )
