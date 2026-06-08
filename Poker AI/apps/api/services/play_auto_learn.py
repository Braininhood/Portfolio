"""Auto-learn from Play vs AI — debounced pipeline after each hand (Phase W7)."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from poker_ai.config.settings import get_settings
from poker_ai.store import jobs_store

logger = logging.getLogger(__name__)

_STATE_PATH = Path("artifacts/play_study/auto_learn_state.json")
_debounce_task: asyncio.Task[None] | None = None
_debounce_lock = asyncio.Lock()


def _state_path() -> Path:
    p = _STATE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _read_state() -> dict[str, Any]:
    p = _state_path()
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _write_state(data: dict[str, Any]) -> None:
    _state_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def run_play_study_train_pipeline(
    params: dict[str, Any],
    emit: Any,
    job_id: str,
) -> dict[str, Any]:
    """Sequential: manifest → HU train → MW train → optional router promote."""
    from poker_ai.learn.train_multiway_student import TrainMultiwayConfig, run_train_multiway_student
    from poker_ai.learn.train_student import TrainStudentConfig, run_train_student
    from poker_ai.policy.router_sources import promote_play_study_to_router
    from poker_ai.store.db import get_async_session_factory

    from services.job_runner import _cancel_check
    from services.play_study_service import materialize_play_study

    cancel = _cancel_check(job_id)
    auto_promote = bool(params.get("auto_promote", True))
    hu_epochs = int(params.get("hu_epochs", 20))
    mw_epochs = int(params.get("mw_epochs", 15))
    batch_size = int(params.get("batch_size", 128))
    device = str(params.get("device", "auto"))
    output_root = Path(str(params.get("output_root", "artifacts/play_study")))

    emit({"pct": 2, "msg": "Refreshing play-study manifest from database…"})
    mat = materialize_play_study(output_dir=str(output_root))
    manifest = Path(str(mat.get("manifest_path", "artifacts/play_study/manifest.json")))
    hu_n = int(mat.get("hero_decisions_hu") or 0)
    mw_n = int(mat.get("hero_decisions_multiway") or 0)
    if hu_n < 1 and mw_n < 1:
        raise ValueError("No trainable play decisions in database yet.")

    trained: list[dict[str, Any]] = []
    hu_out = Path("artifacts/student/play_study_hu_v1")
    mw_out = Path("artifacts/student/play_study_multiway_v1")

    if hu_n >= 1:
        if cancel():
            from poker_ai.runtime.cancel import WorkCancelled

            raise WorkCancelled("Stopped")
        emit({"pct": 15, "msg": f"Training HU student from {hu_n} play decisions…"})
        hu_metrics = run_train_student(
            artifact_dir=hu_out,
            cfg=TrainStudentConfig(epochs=hu_epochs, batch_size=batch_size, device=device),
            play_study_manifest=manifest,
            play_study_only=True,
            progress=emit,
            cancel_check=cancel,
        )
        trained.append({"route": "hu", "decisions": hu_n, "metrics": asdict(hu_metrics)})

    if mw_n >= 1:
        if cancel():
            from poker_ai.runtime.cancel import WorkCancelled

            raise WorkCancelled("Stopped")
        emit({"pct": 55, "msg": f"Training multi-way student from {mw_n} play decisions…"})
        mw_metrics = run_train_multiway_student(
            session_factory=get_async_session_factory(),
            artifact_dir=mw_out,
            cfg=TrainMultiwayConfig(epochs=mw_epochs, batch_size=batch_size, device=device),
            play_study_manifest=manifest,
            play_study_only=True,
            progress=emit,
            cancel_check=cancel,
        )
        trained.append({"route": "multiway", "decisions": mw_n, "metrics": asdict(mw_metrics)})

    router_status: dict[str, Any] | None = None
    if auto_promote:
        emit({"pct": 95, "msg": "Activating play-study weights in live router…"})
        status = promote_play_study_to_router(
            hu=hu_n >= 1,
            multiway=mw_n >= 1,
            confirm=True,
        )
        router_status = status.to_dict()

    _write_state(
        {
            "last_run_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "hero_decisions_hu": hu_n,
            "hero_decisions_multiway": mw_n,
            "manifest_path": str(manifest.resolve()),
        }
    )
    emit({"pct": 100, "msg": "Play auto-learn complete — router updated for your next hand."})
    return {
        "materialize": mat,
        "trained": trained,
        "router": router_status,
        "auto_promote": auto_promote,
    }


def default_play_study_manifest() -> Path | None:
    p = Path("artifacts/play_study/manifest.json")
    return p.resolve() if p.is_file() else None


def enrich_train_params(params: dict[str, Any]) -> dict[str, Any]:
    """Blend play-study rows into standard train jobs when manifest exists."""
    out = dict(params)
    manifest = default_play_study_manifest()
    if manifest is not None and "play_study_manifest" not in out:
        out["play_study_manifest"] = str(manifest)
    return out


async def _has_blocking_job(session_factory: Any) -> bool:
    from poker_ai.store.db import get_async_session_factory

    factory = session_factory or get_async_session_factory()
    async with factory() as session:
        active = await jobs_store.list_active_jobs(session, limit=20)
    block_types = {
        "play_auto_learn",
        "play_study_materialize",
        "train_student",
        "train_multiway_student",
        "ingest",
        "equity_backfill",
    }
    return any(str(j.get("type")) in block_types for j in active)


async def _queue_auto_learn_job() -> None:
    from poker_ai.store.db import get_async_session_factory

    from services.job_runner import run_job_async

    settings = get_settings()
    if not settings.play_auto_learn:
        return

    factory = get_async_session_factory()
    if await _has_blocking_job(factory):
        logger.info("play auto-learn skipped — another job is active")
        return

    from services.play_study_service import get_play_study_status

    stats = get_play_study_status()
    if not stats.get("ready_for_training"):
        return

    hu_n = int(stats.get("hero_decisions_hu") or 0)
    mw_n = int(stats.get("hero_decisions_multiway") or 0)
    if hu_n < 1 and mw_n < 1:
        return

    prev = _read_state()
    prev_hu = int(prev.get("hero_decisions_hu") or 0)
    prev_mw = int(prev.get("hero_decisions_multiway") or 0)
    delta = (hu_n - prev_hu) + (mw_n - prev_mw)
    min_delta = max(1, settings.play_auto_learn_min_decisions)
    if prev.get("last_run_at") and delta < min_delta:
        logger.debug("play auto-learn skipped — only %s new decisions (need %s)", delta, min_delta)
        return

    job_id = uuid.uuid4().hex
    params = {
        "auto_promote": True,
        "hu_epochs": settings.play_auto_learn_hu_epochs,
        "mw_epochs": settings.play_auto_learn_mw_epochs,
        "device": "auto",
    }
    jobs_store.sync_insert_job(
        job_id=job_id,
        job_type="play_auto_learn",
        status="queued",
        params=params,
    )
    logger.info("play auto-learn queued job %s (hu=%s mw=%s delta=%s)", job_id[:8], hu_n, mw_n, delta)
    asyncio.create_task(run_job_async(job_id, "play_auto_learn", params, session_factory=factory))


async def schedule_play_auto_learn() -> None:
    """Debounce auto-learn after hero finishes a hand (Play vs AI)."""
    global _debounce_task

    if not get_settings().play_auto_learn:
        return

    async with _debounce_lock:
        if _debounce_task is not None and not _debounce_task.done():
            _debounce_task.cancel()
            try:
                await _debounce_task
            except asyncio.CancelledError:
                pass

        debounce = max(5.0, float(get_settings().play_auto_learn_debounce_sec))

        async def _wait_and_run() -> None:
            await asyncio.sleep(debounce)
            try:
                await _queue_auto_learn_job()
            except Exception:
                logger.warning("play auto-learn scheduling failed", exc_info=True)

        _debounce_task = asyncio.create_task(_wait_and_run())
