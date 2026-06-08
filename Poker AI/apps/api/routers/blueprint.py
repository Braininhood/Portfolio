"""Blueprint architecture document from doc/blueprint.yaml."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from schemas import BlueprintResponse, BlueprintSection

router = APIRouter(tags=["blueprint"])

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BLUEPRINT_PATH = _REPO_ROOT / "doc" / "blueprint.yaml"


def _parse_blueprint_yaml(text: str) -> BlueprintResponse:
    try:
        import yaml
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="PyYAML required for blueprint") from exc

    doc = yaml.safe_load(text)
    if not isinstance(doc, dict):
        raise HTTPException(status_code=500, detail="invalid blueprint.yaml")
    sections_raw = doc.get("sections") or []
    sections: list[BlueprintSection] = []
    for row in sections_raw:
        if isinstance(row, dict):
            sections.append(
                BlueprintSection(
                    id=str(row.get("id", "")),
                    title=str(row.get("title", "")),
                    body=str(row.get("body", "")).strip(),
                )
            )
    return BlueprintResponse(
        title=str(doc.get("title", "Poker AI Blueprint")),
        version=str(doc.get("version", "1")),
        sections=sections,
        raw_yaml=text,
    )


@router.get("/blueprint", response_model=BlueprintResponse)
def get_blueprint() -> BlueprintResponse:
    if not _BLUEPRINT_PATH.is_file():
        raise HTTPException(status_code=404, detail="doc/blueprint.yaml missing")
    text = _BLUEPRINT_PATH.read_text(encoding="utf-8")
    return _parse_blueprint_yaml(text)
