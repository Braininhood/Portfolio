"""Model version management API (Phase W8)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from schemas import ModelCardResponse
from services.model_card_service import resolve_model_card

router = APIRouter(prefix="/models", tags=["models"])


class ModelVersionSchema(BaseModel):
    name: str
    current_version: str | None = None
    candidate_version: str | None = None
    current_metrics: dict[str, float] = Field(default_factory=dict)
    candidate_metrics: dict[str, float] | None = None
    can_promote: bool = False
    can_rollback: bool = False
    current_path: str | None = None
    note: str | None = None


class ModelsResponse(BaseModel):
    models: list[ModelVersionSchema]


class GateCheckSchema(BaseModel):
    gate_id: str
    label: str
    passed: bool
    detail: str
    required: bool = True


class PromotionGatesResponse(BaseModel):
    model_name: str
    can_promote: bool
    blocking: list[str]
    checks: list[GateCheckSchema]


@router.get("/{name}/card", response_model=ModelCardResponse)
async def model_card(name: str) -> ModelCardResponse:
    try:
        path, version = resolve_model_card(name)
        markdown = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ModelCardResponse(
        name=name,
        version=version,
        markdown=markdown,
        path=str(path),
    )


@router.get("", response_model=ModelsResponse)
async def list_model_versions() -> ModelsResponse:
    from poker_ai.learn.model_registry import list_models

    return ModelsResponse(
        models=[
            ModelVersionSchema(
                name=m.name,
                current_version=m.current_version,
                candidate_version=m.candidate_version,
                current_metrics=m.current_metrics,
                candidate_metrics=m.candidate_metrics,
                can_promote=m.can_promote,
                can_rollback=m.can_rollback,
                current_path=m.current_path,
                note=m.note,
            )
            for m in list_models()
        ]
    )


@router.get("/{name}/promotion-gates", response_model=PromotionGatesResponse)
async def promotion_gates(name: str) -> PromotionGatesResponse:
    from poker_ai.learn.promotion_gates import evaluate_promotion_gates

    report = evaluate_promotion_gates(name)
    return PromotionGatesResponse(
        model_name=report.model_name,
        can_promote=report.can_promote,
        blocking=list(report.blocking),
        checks=[
            GateCheckSchema(
                gate_id=c.gate_id,
                label=c.label,
                passed=c.passed,
                detail=c.detail,
                required=c.required,
            )
            for c in report.checks
        ],
    )


@router.post("/{name}/promote", response_model=ModelVersionSchema)
async def promote_model(
    name: str,
    confirm: bool = Query(False, description="Must be true after reviewing gates"),
    skip_gates: bool = Query(False, description="Emergency override — not for production"),
) -> ModelVersionSchema:
    from poker_ai.learn.model_registry import get_model_info, promote

    try:
        info = promote(name, confirm=confirm, skip_gates=skip_gates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ModelVersionSchema(
        name=info.name,
        current_version=info.current_version,
        candidate_version=info.candidate_version,
        current_metrics=info.current_metrics,
        candidate_metrics=info.candidate_metrics,
        can_promote=info.can_promote,
        can_rollback=info.can_rollback,
        current_path=info.current_path,
        note=info.note,
    )


@router.post("/{name}/rollback", response_model=ModelVersionSchema)
async def rollback_model(name: str) -> ModelVersionSchema:
    from poker_ai.learn.model_registry import rollback

    try:
        info = rollback(name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ModelVersionSchema(
        name=info.name,
        current_version=info.current_version,
        candidate_version=info.candidate_version,
        current_metrics=info.current_metrics,
        candidate_metrics=info.candidate_metrics,
        can_promote=info.can_promote,
        can_rollback=info.can_rollback,
        current_path=info.current_path,
        note=info.note,
    )


class RouterBindingSchema(BaseModel):
    student_dir: str
    source: str
    play_study: bool


class RouterStatusSchema(BaseModel):
    hu: RouterBindingSchema
    multiway: RouterBindingSchema


class PromotePlayStudyRequest(BaseModel):
    hu: bool = True
    multiway: bool = True


@router.get("/router/status", response_model=RouterStatusSchema)
async def router_status() -> RouterStatusSchema:
    from poker_ai.policy.router_sources import get_router_status

    status = get_router_status()
    return _router_status_schema(status)


def _router_binding_schema(binding: object) -> RouterBindingSchema:
    from poker_ai.policy.router_sources import RouterBinding

    b = binding
    if isinstance(b, RouterBinding):
        return RouterBindingSchema(
            student_dir=str(b.student_dir),
            source=b.source,
            play_study=b.play_study,
        )
    raise TypeError("expected RouterBinding")


def _router_status_schema(status: object) -> RouterStatusSchema:
    from poker_ai.policy.router_sources import RouterStatus

    if not isinstance(status, RouterStatus):
        raise TypeError("expected RouterStatus")
    return RouterStatusSchema(
        hu=_router_binding_schema(status.hu),
        multiway=_router_binding_schema(status.multiway),
    )


@router.post("/router/promote-play-study", response_model=RouterStatusSchema)
async def promote_play_study_router(
    body: PromotePlayStudyRequest,
    confirm: bool = Query(False, description="Must be true after reviewing play-study training"),
) -> RouterStatusSchema:
    from poker_ai.policy.router_sources import get_router_status, promote_play_study_to_router

    try:
        status = promote_play_study_to_router(hu=body.hu, multiway=body.multiway, confirm=confirm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _router_status_schema(status)


@router.post("/router/rollback-play-study/{route}", response_model=RouterStatusSchema)
async def rollback_play_study_router(route: str) -> RouterStatusSchema:
    from poker_ai.policy.router_sources import get_router_status, rollback_router_play_study

    if route not in ("hu", "multiway"):
        raise HTTPException(status_code=400, detail="route must be hu or multiway")
    try:
        status = rollback_router_play_study(route)  # type: ignore[arg-type]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _router_status_schema(status)
