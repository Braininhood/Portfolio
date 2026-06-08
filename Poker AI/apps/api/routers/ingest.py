"""Import hand histories via browser upload or local folder (Phase W3)."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_db
from schemas import JobCreatedResponse
from services.folder_picker import pick_folder_sync
from services.job_gate import JobConflictError, assert_no_active_job
from services.job_runner import run_job_async

from poker_ai.ingest.service import collect_hand_files, count_hand_files
from poker_ai.runtime.workers import resolve_worker_count
from poker_ai.store.db import get_async_session_factory
from poker_ai.store import jobs_store
from poker_ai.store.loader import count_parsed_hands

router = APIRouter(prefix="/ingest", tags=["import"])

_REPO_ROOT = Path(__file__).resolve().parents[3]
_UPLOADS_ROOT = _REPO_ROOT / "poker_ai" / "data" / "uploads"

_HAND_SUFFIXES = {".txt", ".json", ".phh", ".phhs"}


class LocalIngestRequest(BaseModel):
    path: str = Field(..., description="Folder or file on this computer (absolute path)")
    max_hands: int = Field(
        0,
        ge=0,
        description="Stop after this many NEW hands (0 = no limit). Duplicates do not count.",
    )
    workers: int = Field(0, ge=0, le=32, description="0 = auto")


class IngestStatusResponse(BaseModel):
    total_hands: int
    last_ingest_at: str | None = None
    last_job_id: str | None = None
    last_job_status: str | None = None
    message: str


class SuggestedPath(BaseModel):
    label: str
    path: str
    exists: bool


class IngestPreviewResponse(BaseModel):
    path: str
    files_found: int
    includes_subfolders: bool
    total_hands_in_library: int
    message: str


class BrowseFolderResponse(BaseModel):
    path: str
    cancelled: bool = False


def _safe_upload_dir(job_id: str) -> Path:
    dest = (_UPLOADS_ROOT / job_id).resolve()
    if not str(dest).startswith(str(_UPLOADS_ROOT.resolve())):
        raise HTTPException(status_code=400, detail="Invalid upload path")
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def _validate_local_path(raw: str) -> Path:
    p = Path(raw).expanduser().resolve()
    if not p.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Folder not found: {p}. Check the path (example: D:\\Downloads\\PokerHands).",
        )
    return p


def _suggested_paths() -> list[SuggestedPath]:
    home = Path.home()
    candidates = [
        ("Hand histories (project)", _REPO_ROOT / "hand" / "poker-hand-histories"),
        ("Downloads", home / "Downloads"),
        ("Documents", home / "Documents"),
        ("Desktop", home / "Desktop"),
        ("Poker AI data", _REPO_ROOT / "poker_ai" / "data"),
    ]
    out: list[SuggestedPath] = []
    for label, p in candidates:
        try:
            resolved = p.resolve()
            out.append(SuggestedPath(label=label, path=str(resolved), exists=resolved.is_dir()))
        except OSError:
            out.append(SuggestedPath(label=label, path=str(p), exists=False))
    return out


async def _start_ingest_job(
    *,
    path: Path,
    max_hands: int,
    workers: int,
    session: AsyncSession,
    job_id: str | None = None,
) -> JobCreatedResponse:
    max_hands_param = None if max_hands <= 0 else max_hands
    nw = resolve_worker_count(workers if workers > 0 else None)
    job_id = job_id or str(uuid.uuid4())
    params = {
        "path": str(path),
        "max_hands": max_hands_param,
        "workers": nw,
    }
    try:
        await assert_no_active_job(session)
        jobs_store.sync_insert_job(
            job_id=job_id,
            job_type="ingest",
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
    asyncio.create_task(run_job_async(job_id, "ingest", params, session_factory=factory))
    return JobCreatedResponse(job_id=job_id)


@router.get("/suggested-paths", response_model=list[SuggestedPath])
async def list_suggested_paths() -> list[SuggestedPath]:
    """Common folders on this PC (Downloads, Documents, …) for one-click import."""
    return _suggested_paths()


@router.post("/browse-folder", response_model=BrowseFolderResponse)
async def browse_folder_dialog() -> BrowseFolderResponse:
    """Open a system folder picker and return the absolute path (local app only)."""
    try:
        chosen = await asyncio.to_thread(
            pick_folder_sync,
            title="Select folder with hand histories (includes subfolders)",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    if not chosen:
        return BrowseFolderResponse(path="", cancelled=True)
    resolved = Path(chosen).expanduser().resolve()
    if not resolved.is_dir():
        raise HTTPException(status_code=400, detail="Selected path is not a folder.")
    return BrowseFolderResponse(path=str(resolved), cancelled=False)


@router.get("/status", response_model=IngestStatusResponse)
async def ingest_status(session: AsyncSession = Depends(get_db)) -> IngestStatusResponse:
    total = await count_parsed_hands(session)
    row = (
        await session.execute(
            text(
                "SELECT id, status, finished_at FROM jobs WHERE type = 'ingest' "
                "ORDER BY datetime(created_at) DESC LIMIT 1"
            )
        )
    ).mappings().first()
    last_at = None
    last_id = None
    last_status = None
    if row:
        last_id = str(row["id"])
        last_status = str(row["status"])
        last_at = str(row["finished_at"]) if row.get("finished_at") else None

    if total == 0:
        msg = "No hands in your library yet. Choose a folder or upload files below."
    else:
        msg = f"Your library has {total:,} hands. Duplicates are detected automatically on re-import."

    return IngestStatusResponse(
        total_hands=total,
        last_ingest_at=last_at,
        last_job_id=last_id,
        last_job_status=last_status,
        message=msg,
    )


@router.post("/preview", response_model=IngestPreviewResponse)
async def preview_local_path(
    req: LocalIngestRequest,
    session: AsyncSession = Depends(get_db),
) -> IngestPreviewResponse:
    """Count files under a folder before starting import (includes subfolders)."""
    path = _validate_local_path(req.path)
    n_files = await asyncio.to_thread(count_hand_files, path)
    total = await count_parsed_hands(session)
    cap_note = ""
    if req.max_hands > 0:
        cap_note = f" Import will stop after {req.max_hands:,} new hands (duplicates do not count)."
    return IngestPreviewResponse(
        path=str(path),
        files_found=n_files,
        includes_subfolders=path.is_dir(),
        total_hands_in_library=total,
        message=(
            f"Found {n_files:,} hand history file(s) under this folder (all subfolders included). "
            f"Your library currently has {total:,} hands.{cap_note}"
        ),
    )


@router.post("/upload", response_model=JobCreatedResponse, status_code=202)
async def upload_and_ingest(
    files: list[UploadFile] = File(...),
    max_hands: int = Query(
        0,
        ge=0,
        description="Stop after N new hands (0 = unlimited). Duplicates do not count.",
    ),
    workers: int = Query(0, ge=0, le=32),
    session: AsyncSession = Depends(get_db),
) -> JobCreatedResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Choose at least one hand history file.")
    job_id = str(uuid.uuid4())
    dest = _safe_upload_dir(job_id)
    saved = 0
    for uf in files:
        raw_name = (uf.filename or "upload.txt").replace("\\", "/").lstrip("/")
        if Path(Path(raw_name).name).suffix.lower() not in _HAND_SUFFIXES:
            continue
        target = (dest / raw_name).resolve()
        if not str(target).startswith(str(dest.resolve())):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        content = await uf.read()
        if not content:
            continue
        target.write_bytes(content)
        saved += 1
    if saved == 0:
        raise HTTPException(
            status_code=400,
            detail="No supported files (.txt, .phh, .phhs, .json). Check your selection.",
        )
    return await _start_ingest_job(
        path=dest,
        max_hands=max_hands,
        workers=workers,
        session=session,
        job_id=job_id,
    )


@router.post("/local", response_model=JobCreatedResponse, status_code=202)
async def ingest_local_path(
    req: LocalIngestRequest,
    session: AsyncSession = Depends(get_db),
) -> JobCreatedResponse:
    path = _validate_local_path(req.path)
    if path.is_dir():
        n_files = await asyncio.to_thread(count_hand_files, path)
        if n_files == 0:
            raise HTTPException(
                status_code=400,
                detail="No hand history files found in this folder (searches all subfolders).",
            )
    return await _start_ingest_job(
        path=path,
        max_hands=req.max_hands,
        workers=req.workers,
        session=session,
    )
