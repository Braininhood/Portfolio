"""Open project files/folders in the OS file manager (local API only)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["system"])

# API cwd when started via ``poker_ai serve`` is poker_ai/
_PROJECT_ROOT = Path(__file__).resolve().parents[3] / "poker_ai"


class OpenPathRequest(BaseModel):
    path: str = Field(description="Relative to poker_ai/ or absolute under project")


class OpenPathResponse(BaseModel):
    ok: bool
    resolved: str
    message: str


def _resolve_allowed(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = (_PROJECT_ROOT / p).resolve()
    else:
        p = p.resolve()
    root = _PROJECT_ROOT.resolve()
    try:
        p.relative_to(root)
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail="Path must be inside your poker_ai project folder.",
        ) from exc
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {p}")
    return p


def _open_in_os(path: Path) -> None:
    if sys.platform == "win32":
        if path.is_file():
            subprocess.Popen(["explorer", "/select,", os.path.normpath(str(path))])
        else:
            subprocess.Popen(["explorer", os.path.normpath(str(path))])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        target = path.parent if path.is_file() else path
        subprocess.Popen(["xdg-open", str(target)])


@router.post("/system/open-path", response_model=OpenPathResponse)
async def open_path(req: OpenPathRequest) -> OpenPathResponse:
    """Reveal a file or folder in Explorer / Finder (same machine as the API)."""
    resolved = _resolve_allowed(req.path)
    try:
        _open_in_os(resolved)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    label = "folder" if resolved.is_dir() else "file"
    return OpenPathResponse(
        ok=True,
        resolved=str(resolved),
        message=f"Opened {label} in your file manager.",
    )


@router.get("/system/project-root")
async def project_root() -> dict[str, str]:
    return {"root": str(_PROJECT_ROOT.resolve())}
