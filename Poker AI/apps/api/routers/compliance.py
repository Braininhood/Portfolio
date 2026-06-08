"""GET /compliance — compliance summary + datasheet (Phase W9)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from schemas import ComplianceResponse
from services.compliance_service import build_compliance_response

router = APIRouter(tags=["compliance"])

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DATASHEET = _REPO_ROOT / "doc" / "DATASHEET.md"


@router.get("/compliance", response_model=ComplianceResponse)
async def compliance_summary() -> ComplianceResponse:
    return build_compliance_response()


class DatasheetContentResponse(BaseModel):
    title: str
    markdown: str


def _read_datasheet() -> str:
    if not _DATASHEET.is_file():
        raise HTTPException(status_code=404, detail="doc/DATASHEET.md not found")
    return _DATASHEET.read_text(encoding="utf-8")


@router.get("/compliance/datasheet/content", response_model=DatasheetContentResponse)
async def compliance_datasheet_content() -> DatasheetContentResponse:
    """Markdown datasheet for the dashboard (same styling as other pages)."""
    return DatasheetContentResponse(title="Poker AI — Model datasheet", markdown=_read_datasheet())


@router.get("/compliance/datasheet", response_class=PlainTextResponse)
async def compliance_datasheet() -> str:
    """Raw markdown download (CLI / scripts)."""
    return _read_datasheet()
