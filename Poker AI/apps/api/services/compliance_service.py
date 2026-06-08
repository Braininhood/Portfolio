"""Compliance summary for GET /compliance (Phase W9)."""

from __future__ import annotations

import json
from pathlib import Path

from schemas import ComplianceResponse

from services.smoke_service import get_last_smoke_result

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LICENSES = _REPO_ROOT / "LICENSES" / "inventory.json"


def _load_license_entries() -> list[dict]:
    if not _LICENSES.is_file():
        return []
    try:
        data = json.loads(_LICENSES.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return data.get("entries", [])
    except (json.JSONDecodeError, OSError):
        return []


def build_compliance_response() -> ComplianceResponse:
    entries = _load_license_entries()
    agpl = [
        str(e.get("package", ""))
        for e in entries
        if "AGPL" in str(e.get("license_type", "")).upper()
    ]
    smoke = get_last_smoke_result()
    offline_ok = bool(smoke and smoke.all_passed)
    datasheet = "/datasheet" if (_REPO_ROOT / "doc" / "DATASHEET.md").is_file() else None
    return ComplianceResponse(
        owned_data_only=True,
        no_external_ai_services=True,
        offline_mode_verified=offline_ok,
        tos_note=(
            "Offline analysis tool only — import your own hand histories, run sims and study "
            "tools locally. No real-time assistance on third-party poker clients. "
            "See doc/SECURITY_AND_COMPLIANCE.md."
        ),
        datasheet_url=datasheet,
        licenses_count=len(entries),
        agpl_packages=agpl,
    )
