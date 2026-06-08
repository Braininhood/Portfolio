"""GET /licenses — third-party license inventory (Phase W9)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from schemas import LicenseEntry, LicensesResponse

router = APIRouter(tags=["compliance"])

_REPO_ROOT = Path(__file__).resolve().parents[3]
_INVENTORY = _REPO_ROOT / "LICENSES" / "inventory.json"


@router.get("/licenses", response_model=LicensesResponse)
async def list_licenses() -> LicensesResponse:
    if not _INVENTORY.is_file():
        raise HTTPException(
            status_code=404,
            detail="LICENSES/inventory.json not found — run license inventory generation.",
        )
    try:
        raw = json.loads(_INVENTORY.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    rows = raw if isinstance(raw, list) else raw.get("entries", [])
    entries = [
        LicenseEntry(
            package=str(r.get("package", "")),
            version=str(r.get("version", "")),
            license_type=str(r.get("license_type", r.get("license", "UNKNOWN"))),
            url=r.get("url"),
            note=r.get("note"),
        )
        for r in rows
    ]
    note = raw.get("generated_note") if isinstance(raw, dict) else None
    return LicensesResponse(entries=entries, generated_note=note)
