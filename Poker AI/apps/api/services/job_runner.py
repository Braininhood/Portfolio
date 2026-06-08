"""Dispatch background jobs to ``poker_ai`` library entrypoints (Phase W1)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poker_ai.config.settings import get_settings
from poker_ai.runtime.workers import resolve_worker_count
from poker_ai.store import jobs_store
from poker_ai.store.db import get_async_session_factory

from services.job_hub import hub

logger = logging.getLogger(__name__)

JOB_TYPES = frozenset(
    {
        "ingest",
        "features_build",
        "features_export_parquet",
        "features_validate_blueprint",
        "train_hhformer",
        "train_hhformer_finetune",
        "solve_preflop",
        "solve_grid",
        "train_student",
        "train_cql",
        "train_style",
        "league_run",
        "league_replay_run",
        "train_multiway_student",
        "play_study_materialize",
        "play_auto_learn",
        "equity_backfill",
        "validate_student",
        "league_train_exploiters",
        "aivat_audit",
        "policy_bench",
        "solve_kuhn",
        "features_hhformer_embed",
        "opponents_eval_exploit",
        "train_value_net",
        "train_decision_quality",
    }
)

_cancelled: set[str] = set()
_cancel_lock = threading.Lock()
_running_tasks: dict[str, asyncio.Task[None]] = {}
_tasks_lock = threading.Lock()


def request_cancel(job_id: str) -> None:
    with _cancel_lock:
        _cancelled.add(job_id)


def is_cancelled(job_id: str) -> bool:
    with _cancel_lock:
        return job_id in _cancelled


def clear_cancel(job_id: str) -> None:
    with _cancel_lock:
        _cancelled.discard(job_id)


def _register_task(job_id: str, task: asyncio.Task[None]) -> None:
    with _tasks_lock:
        _running_tasks[job_id] = task


def _unregister_task(job_id: str) -> None:
    with _tasks_lock:
        _running_tasks.pop(job_id, None)


async def release_orphaned_jobs(
    session_factory: async_sessionmaker[AsyncSession],
) -> int:
    """On API startup, clear queued/running rows left from a previous process."""
    async with session_factory() as session:
        async with session.begin():
            ids = await jobs_store.cancel_all_active(
                session,
                error="Stopped because the API restarted. Start a new task when ready.",
            )
    return len(ids)


async def force_cancel_job(
    job_id: str,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    reason: str = "Stopped by user",
) -> bool:
    """Immediately mark a job cancelled and signal workers (DB gate opens at once)."""
    request_cancel(job_id)
    with _tasks_lock:
        task = _running_tasks.get(job_id)
    if task is not None and not task.done():
        task.cancel()
    factory = session_factory
    updated = await asyncio.to_thread(jobs_store.sync_cancel_job, job_id, reason=reason)
    if not updated:
        async with factory() as session:
            row = await jobs_store.fetch_job(session, job_id)
        if row is None:
            return False
        if str(row["status"]) in ("done", "error", "cancelled"):
            return True
        return False
    hub.emit_from_worker(
        factory,
        job_id,
        {"status": "cancelled", "msg": "Stopped", "error": reason, "pct": 0},
    )
    return True


async def force_cancel_all_active(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    reason: str = "Stopped by user (release all)",
) -> list[str]:
    async with session_factory() as session:
        async with session.begin():
            ids = await jobs_store.list_active_jobs(session, limit=500)
            job_ids = [str(r["id"]) for r in ids]
    for job_id in job_ids:
        request_cancel(job_id)
    for job_id in job_ids:
        await force_cancel_job(job_id, session_factory=session_factory, reason=reason)
    return job_ids


def _make_emit(
    session_factory: async_sessionmaker[AsyncSession],
    job_id: str,
    job_type: str,
) -> Callable[[dict[str, Any]], None]:
    from services.terminal_log import log_job_progress

    def emit(event: dict[str, Any]) -> None:
        log_job_progress(job_id, job_type, event)
        hub.emit_from_worker(session_factory, job_id, event)

    return emit


async def run_job_async(
    job_id: str,
    job_type: str,
    params: dict[str, Any],
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> None:
    """Mark running, execute in thread pool, persist terminal state."""
    factory = session_factory or get_async_session_factory()
    current = asyncio.current_task()
    if current is not None:
        _register_task(job_id, current)  # type: ignore[arg-type]
    try:
        await _run_job_body(job_id, job_type, params, session_factory=factory)
    finally:
        _unregister_task(job_id)
        clear_cancel(job_id)


async def _run_job_body(
    job_id: str,
    job_type: str,
    params: dict[str, Any],
    *,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    factory = session_factory
    clear_cancel(job_id)

    async with factory() as session:
        row = await jobs_store.fetch_job(session, job_id)
    if row is None:
        return
    if str(row["status"]) == "cancelled" or is_cancelled(job_id):
        return

    started = jobs_store.utcnow_naive()
    async with factory() as session:
        async with session.begin():
            await jobs_store.update_job(
                session,
                job_id,
                status="running",
                started_at=started,
            )

    emit = _make_emit(factory, job_id, job_type)
    from services.terminal_log import log_job_line, log_job_params

    log_job_line(job_id, job_type, "queued → running")
    log_job_params(job_id, job_type, params)
    emit({"pct": 0, "msg": f"Starting {job_type}…", "detail": {"type": job_type}})

    try:
        result = await asyncio.to_thread(_execute_job, job_id, job_type, params, emit)
        if is_cancelled(job_id):
            raise JobCancelledError("Job cancelled by user")
        async with factory() as session:
            row_now = await jobs_store.fetch_job(session, job_id)
        if row_now and str(row_now["status"]) == "cancelled":
            return
        finished = jobs_store.utcnow_naive()
        async with factory() as session:
            async with session.begin():
                await jobs_store.update_job(
                    session,
                    job_id,
                    status="done",
                    finished_at=finished,
                    result_json=json.dumps(result, separators=(",", ":")),
                    progress_json=json.dumps(
                        {"pct": 100, "msg": "Complete", "detail": result},
                        separators=(",", ":"),
                    ),
                )
        from services.job_friendly import friendly_job_summary

        db_hands: int | None = None
        try:

            async def _count() -> int:
                async with factory() as session:
                    from poker_ai.store.loader import count_parsed_hands

                    return await count_parsed_hands(session)

            db_hands = await _count()
        except Exception:
            db_hands = None
        friendly = friendly_job_summary(
            job_type, status="done", result=result, db_hands=db_hands
        )
        terminal = {
            "status": "done",
            "result": result,
            "pct": 100,
            "msg": str(friendly["headline"]),
            "friendly": friendly,
        }
        hub.emit_from_worker(factory, job_id, terminal)
        log_job_line(job_id, job_type, f"done — {friendly.get('headline', 'Complete')}")
    except JobCancelledError as exc:
        log_job_line(job_id, job_type, f"cancelled — {exc}")
        await asyncio.to_thread(jobs_store.sync_cancel_job, job_id, reason=str(exc))
        hub.emit_from_worker(
            factory,
            job_id,
            {"status": "cancelled", "error": str(exc), "msg": str(exc)},
        )
    except asyncio.CancelledError:
        log_job_line(job_id, job_type, "cancelled — task stopped")
        reason = "Stopped by user"
        await asyncio.to_thread(jobs_store.sync_cancel_job, job_id, reason=reason)
        hub.emit_from_worker(
            factory,
            job_id,
            {"status": "cancelled", "error": reason, "msg": reason},
        )
        raise
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        log_job_line(job_id, job_type, f"FAILED — {exc}", level=logging.ERROR)
        finished = jobs_store.utcnow_naive()
        err = str(exc)
        async with factory() as session:
            async with session.begin():
                await jobs_store.update_job(
                    session,
                    job_id,
                    status="error",
                    finished_at=finished,
                    error=err,
                )
        from services.job_friendly import friendly_error_message, friendly_job_summary

        friendly = friendly_job_summary(
            job_type,
            status="error",
            error=err,
        )
        hub.emit_from_worker(
            factory,
            job_id,
            {
                "status": "error",
                "error": friendly_error_message(err),
                "msg": str(friendly["headline"]),
                "friendly": friendly,
            },
        )


class JobCancelledError(Exception):
    """Raised when ``request_cancel`` was called for this job."""


def _configure_stdio_utf8() -> None:
    """Avoid Windows charmap crashes when library code prints non-ASCII."""
    import sys

    if sys.platform != "win32":
        return
    import os

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8")
            except Exception:
                pass


def _execute_job(
    job_id: str,
    job_type: str,
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    from poker_ai.runtime.cancel import WorkCancelled
    from services.terminal_log import log_job_line

    _configure_stdio_utf8()
    log_job_line(job_id, job_type, f"worker thread started ({job_type})")
    try:
        if job_type == "ingest":
            return _job_ingest(params, emit, job_id)
        if job_type == "features_build":
            return _job_features_build(params, emit, job_id)
        if job_type == "train_hhformer":
            return _job_train_hhformer(params, emit, job_id)
        if job_type == "train_hhformer_finetune":
            return _job_train_hhformer_finetune(params, emit, job_id)
        if job_type == "solve_preflop":
            return _job_solve_preflop(params, emit, job_id)
        if job_type == "solve_grid":
            return _job_solve_grid(params, emit, job_id)
        if job_type == "train_student":
            return _job_train_student(params, emit, job_id)
        if job_type == "train_cql":
            return _job_train_cql(params, emit, job_id)
        if job_type == "train_style":
            return _job_train_style(params, emit, job_id)
        if job_type == "league_run":
            return _job_league_run(params, emit, job_id)
        if job_type == "train_multiway_student":
            return _job_train_multiway(params, emit, job_id)
        if job_type == "play_study_materialize":
            return _job_play_study_materialize(params, emit)
        if job_type == "play_auto_learn":
            return _job_play_auto_learn(params, emit, job_id)
        if job_type == "equity_backfill":
            return _job_equity_backfill(params, emit, job_id)
        if job_type == "validate_student":
            return _job_validate_student(params, emit, job_id)
        if job_type == "league_train_exploiters":
            return _job_league_train_exploiters(params, emit, job_id)
        if job_type == "features_export_parquet":
            return _job_features_export_parquet(params, emit, job_id)
        if job_type == "features_validate_blueprint":
            return _job_features_validate_blueprint(params, emit, job_id)
        if job_type == "league_replay_run":
            return _job_league_replay_run(params, emit, job_id)
        if job_type == "aivat_audit":
            return _job_aivat_audit(params, emit, job_id)
        if job_type == "policy_bench":
            return _job_policy_bench(params, emit, job_id)
        if job_type == "solve_kuhn":
            return _job_solve_kuhn(params, emit, job_id)
        if job_type == "features_hhformer_embed":
            return _job_features_hhformer_embed(params, emit, job_id)
        if job_type == "opponents_eval_exploit":
            return _job_opponents_eval_exploit(params, emit, job_id)
        if job_type == "train_value_net":
            return _job_train_value_net(params, emit, job_id)
        if job_type == "train_decision_quality":
            return _job_train_decision_quality(params, emit, job_id)
        msg = f"Unknown job type: {job_type}"
        raise ValueError(msg)
    except WorkCancelled as exc:
        log_job_line(job_id, job_type, "cancelled by user")
        raise JobCancelledError("Stopped by user") from exc


def _cancel_check(job_id: str) -> Callable[[], bool]:
    return lambda: is_cancelled(job_id)


def _job_ingest(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from poker_ai.ingest.service import run_ingest_sync

    path_raw = params.get("path")
    if not path_raw:
        raise ValueError("ingest requires params.path")
    path = Path(str(path_raw))
    if not path.exists():
        raise FileNotFoundError(path)
    settings = get_settings()
    factory = get_async_session_factory()
    max_hands = params.get("max_hands")
    if max_hands is not None:
        max_hands = int(max_hands)
    workers = params.get("workers")
    if workers is not None:
        workers = int(workers)

    async def _count_hands() -> int:
        async with factory() as session:
            from poker_ai.store.loader import count_parsed_hands

            return await count_parsed_hands(session)

    hands_before = asyncio.run(_count_hands())
    from poker_ai.ingest.service import IngestCancelled

    try:
        stats = run_ingest_sync(
            path,
            session_factory=factory,
            uid_secret=settings.player_uid_hmac_secret,
            max_hands=max_hands,
            workers=resolve_worker_count(workers) if workers is not None else None,
            progress=emit,
            cancel_check=_cancel_check(job_id),
        )
    except IngestCancelled as exc:
        raise JobCancelledError("Import stopped") from exc
    if is_cancelled(job_id):
        raise JobCancelledError("Import stopped")
    hands_after = asyncio.run(_count_hands())
    return {
        "files_seen": stats.files_processed,
        "hands_new": stats.hands_new,
        "hands_updated": stats.hands_updated,
        "hands_skipped": stats.hands_skipped,
        "hands_written": stats.hands_written,
        "hands_before": hands_before,
        "hands_after": hands_after,
        "library_growth": hands_after - hands_before,
    }


def _job_features_build(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from poker_ai.features.build import write_feature_jsonl

    output = Path(str(params.get("output", "features.jsonl")))
    blueprint_full = str(params.get("blueprint_full", False)).lower() in ("1", "true", "yes")
    since_raw = params.get("since")
    since_dt: datetime | None = None
    if since_raw:
        since_dt = datetime.fromisoformat(str(since_raw)).replace(tzinfo=UTC)
    workers = resolve_worker_count(int(params["workers"]) if params.get("workers") is not None else None)
    factory = get_async_session_factory()

    async def _run() -> int:
        async with factory() as session:
            return await write_feature_jsonl(
                session,
                output,
                since=since_dt,
                workers=workers,
                blueprint_full=blueprint_full,
                progress=emit,
                cancel_check=_cancel_check(job_id),
            )

    try:
        n = asyncio.run(_run())
    except Exception as exc:
        from poker_ai.runtime.cancel import WorkCancelled

        if isinstance(exc, WorkCancelled) or is_cancelled(job_id):
            raise JobCancelledError("Stopped") from exc
        raise
    if is_cancelled(job_id):
        raise JobCancelledError("Stopped")
    out_path = output.resolve()
    result = {"hands_written": n, "output": str(out_path), "blueprint_full": blueprint_full}
    try:
        from poker_ai.learn.dataset_versioning import record_snapshot

        snap = record_snapshot(out_path)
        result["snapshot_version"] = snap.version
        result["snapshot_hash"] = snap.content_hash[:16]
    except OSError:
        pass
    return result


def _job_train_hhformer(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from poker_ai.learn.pretrain_hhformer import PretrainConfig, run_pretrain

    cfg = PretrainConfig(
        epochs=int(params.get("epochs", 50)),
        batch_size=int(params.get("batch_size", 256)),
        seed=int(params.get("seed", 42)),
        device=str(params.get("device", "auto")),
        max_hands=int(params["max_hands"]) if params.get("max_hands") is not None else None,
        num_workers=int(params.get("num_workers", 0)),
        amp=not bool(params.get("no_amp", False)),
    )
    out = Path(str(params.get("output", "artifacts/hhformer/v1")))
    metrics = run_pretrain(
        artifact_dir=out,
        session_factory=get_async_session_factory(),
        cfg=cfg,
        progress=emit,
        cancel_check=_cancel_check(job_id),
    )
    from dataclasses import asdict

    return {"artifact_dir": str(out.resolve()), "metrics": asdict(metrics)}


def _job_train_hhformer_finetune(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    """Solver-supervised HHFormer fine-tune → artifacts/hhformer/v2 (W10 Item 4)."""
    from dataclasses import asdict

    from poker_ai.learn.pretrain_hhformer import PretrainConfig, run_pretrain

    cfg = PretrainConfig(
        epochs=int(params.get("epochs", 8)),
        batch_size=int(params.get("batch_size", 128)),
        seed=int(params.get("seed", 42)),
        device=str(params.get("device", "auto")),
        max_hands=int(params["max_hands"]) if params.get("max_hands") is not None else 5000,
        num_workers=int(params.get("num_workers", 0)),
        amp=not bool(params.get("no_amp", False)),
    )
    out = Path(str(params.get("output", "artifacts/hhformer/v2")))
    emit({"pct": 2, "msg": "HHFormer solver fine-tune (continual pretrain on solver-masked spots)"})
    metrics = run_pretrain(
        artifact_dir=out,
        session_factory=get_async_session_factory(),
        cfg=cfg,
        progress=emit,
        cancel_check=_cancel_check(job_id),
    )
    card = out / "MODEL_CARD.md"
    if card.is_file():
        body = card.read_text(encoding="utf-8")
        if "fine-tuned" not in body.lower():
            card.write_text(
                body.replace("# HHFormer v1", "# HHFormer v2 (solver fine-tuned)"),
                encoding="utf-8",
            )
    return {"artifact_dir": str(out.resolve()), "metrics": asdict(metrics), "version": "v2"}


def _job_train_cql(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from dataclasses import asdict

    from poker_ai.learn.train_cql import CQLTrainConfig, run_train_cql

    cfg = CQLTrainConfig(
        epochs=int(params.get("epochs", 15)),
        batch_size=int(params.get("batch_size", 128)),
        alpha=float(params.get("alpha", 1.0)),
        seed=int(params.get("seed", 42)),
        device=str(params.get("device", "auto")),
        max_rows=int(params["max_rows"]) if params.get("max_rows") is not None else 50_000,
    )
    out = Path(str(params.get("output", "artifacts/cql/v1")))
    metrics = run_train_cql(
        artifact_dir=out,
        cfg=cfg,
        progress=emit,
        cancel_check=_cancel_check(job_id),
    )
    return {"artifact_dir": str(out.resolve()), "metrics": asdict(metrics)}


def _param_bool(val: Any, default: bool = False) -> bool:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    s = str(val).strip().lower()
    if s in ("1", "true", "yes", "on"):
        return True
    if s in ("0", "false", "no", "off", ""):
        return False
    return default


def _resolve_job_workers(params: dict[str, Any]) -> int:
    """UI sends ``workers: 0`` for auto — treat as unset (not ``resolve_worker_count(0)``)."""
    if not _param_bool(params.get("force_parallel_workers"), True):
        return 1
    raw = params.get("workers")
    if raw is None or raw == 0 or raw == "0":
        return resolve_worker_count(None)
    return resolve_worker_count(int(raw))


def _poker_ai_subprocess_env() -> tuple[dict[str, str], Path]:
    """PYTHONPATH + cwd matching ``poker_ai serve`` (so child sees same imports as CLI)."""
    api_dir = Path(__file__).resolve().parents[1]
    repo_root = api_dir.parents[1]
    src = repo_root / "poker_ai" / "src"
    cwd = repo_root / "poker_ai"
    env = os.environ.copy()
    parts = [str(src), str(api_dir), env.get("PYTHONPATH", "")]
    env["PYTHONPATH"] = os.pathsep.join(p for p in parts if p)
    return env, cwd


def _emit_ndjson_progress(path: Path, emit: Callable[[dict[str, Any]], None], seen: int) -> int:
    if not path.is_file():
        return seen
    lines = path.read_text(encoding="utf-8").splitlines()
    for i in range(seen, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
        try:
            emit(json.loads(line))
        except json.JSONDecodeError:
            logger.warning("Skipping malformed progress line: %s", line[:120])
    return len(lines)


def _job_solve_preflop_isolated(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
    *,
    n_workers: int,
) -> dict[str, Any]:
    """Run preflop solve in a fresh process (Windows parallel — same as CLI)."""
    from services.terminal_log import log_job_line

    env, cwd = _poker_ai_subprocess_env()
    log_job_line(
        job_id,
        "solve_preflop",
        f"Windows: isolated subprocess ({n_workers} workers, subprocess shards)",
    )
    emit(
        {
            "pct": 2,
            "msg": f"Starting isolated preflop job ({n_workers} workers, same as CLI)",
            "detail": {"workers": n_workers, "isolated": True, "platform": "win32"},
        }
    )

    with tempfile.TemporaryDirectory(prefix="preflop_job_") as td:
        td_path = Path(td)
        progress_path = td_path / "progress.ndjson"
        result_path = td_path / "result.json"
        cfg_path = td_path / "config.json"
        cfg = dict(params)
        cfg["workers"] = n_workers
        cfg["progress_path"] = str(progress_path)
        cfg["result_path"] = str(result_path)
        cfg_path.write_text(json.dumps(cfg, separators=(",", ":")), encoding="utf-8")

        proc = subprocess.Popen(
            [sys.executable, "-m", "poker_ai.solver.preflop_job_isolated", str(cfg_path)],
            cwd=str(cwd),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        seen = 0
        while proc.poll() is None:
            seen = _emit_ndjson_progress(progress_path, emit, seen)
            time.sleep(1.0)
        seen = _emit_ndjson_progress(progress_path, emit, seen)

        if proc.returncode != 0:
            err_path = cfg_path.with_suffix(".error.txt")
            detail = (
                err_path.read_text(encoding="utf-8")
                if err_path.is_file()
                else f"exit code {proc.returncode}"
            )
            raise RuntimeError(f"Isolated preflop job failed: {detail}")

        return json.loads(result_path.read_text(encoding="utf-8"))


def _job_solve_preflop(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from poker_ai.policy.cfr_policy import CFRPolicy
    from poker_ai.solver.preflop_equity import EquityMode
    from poker_ai.solver.solve_preflop import resolve_solve_config, solve_preflop
    from services.terminal_log import log_job_line

    n_workers = _resolve_job_workers(params)
    if sys.platform == "win32" and n_workers > 1:
        return _job_solve_preflop_isolated(params, emit, job_id, n_workers=n_workers)

    positions = str(params.get("positions", "6max")).lower()
    num_players = 2 if positions in {"hu", "heads-up", "headsup"} else 6
    eq_raw = str(params.get("equity_mode", "random")).lower()
    eq_mode: EquityMode = "real" if eq_raw == "real" else "random"
    requested_iters = int(params.get("iters", 20_000))
    production = _param_bool(params.get("production"), False)
    cfg = resolve_solve_config(
        num_players=num_players,
        iterations=requested_iters,
        chance_samples=int(params.get("chance_samples", 64)),
        equity_mode=eq_mode,
        prune_min_mass=float(params.get("prune_min_mass", 5.0)),
        production=production,
    )
    effective_iters = cfg.iterations
    if production and effective_iters != requested_iters:
        note = (
            f"production=True: CFR iterations {requested_iters:,} → {effective_iters:,} "
            f"(HU minimum 50,000 when production is on)"
        )
        log_job_line(job_id, "solve_preflop", note)
        emit({"pct": 1, "msg": note, "detail": {"requested_iters": requested_iters, "effective_iters": effective_iters}})

    if n_workers > 1:
        log_job_line(job_id, "solve_preflop", f"CFR workers={n_workers}")

    output = Path(str(params.get("output", "artifacts/solver/preflop_cfr.json")))
    if num_players == 2 and output.name == "preflop_cfr.json":
        output = Path(
            str(
                params.get(
                    "output_hu",
                    "artifacts/solver/preflop_hu_real.json"
                    if eq_mode == "real"
                    else "artifacts/solver/preflop_hu.json",
                )
            )
        )
    result = solve_preflop(
        num_players=num_players,
        iterations=effective_iters,
        chance_samples=cfg.chance_samples,
        seed=int(params.get("seed", 42)),
        max_raises=int(params.get("max_raises", 1)),
        workers=n_workers,
        measure_exploitability=bool(params.get("measure_exploitability", False)),
        equity_mode=cfg.equity_mode,
        equity_mc_samples=int(params.get("equity_mc_samples", 2000)),
        production=production,
        prune_min_mass=cfg.prune_min_mass,
        progress=emit,
    )
    policy = CFRPolicy(
        strategy=result.strategy,
        equity_mode=result.equity_mode,
        equity_mc_samples=result.equity_mc_samples,
    )
    exp = result.exploitability_mbb if result.exploitability_mbb is not None else -1.0
    policy.save_json(
        output,
        iterations=result.iterations,
        exploitability_mbb=exp,
        equity_mode=result.equity_mode,
        equity_mc_samples=result.equity_mc_samples,
    )
    return {
        "output": str(output.resolve()),
        "info_sets": result.num_info_sets,
        "iterations": result.iterations,
        "workers": result.workers,
    }


def _job_solve_grid(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from poker_ai.solver.bridge.batch import solve_grid
    from poker_ai.solver.bridge.texas import Backend

    backend_raw = str(params.get("backend", "auto")).lower()
    if backend_raw not in ("auto", "mock", "texas"):
        raise ValueError("backend must be auto, mock, or texas")
    b: Backend = backend_raw  # type: ignore[assignment]
    cache_dir = Path(str(params.get("cache_dir", "artifacts/solver_cache")))
    result = solve_grid(
        n_spots=int(params.get("n_spots", 128)),
        cache_dir=cache_dir,
        backend=b,
        seed=int(params.get("seed", 42)),
        skip_cached=not bool(params.get("refresh", False)),
        continue_on_error=bool(params.get("continue_on_error", False)),
        texas_threads=int(params.get("texas_threads", 2)),
        progress=emit,
    )
    return {
        "requested": result.requested,
        "solved": result.solved,
        "cache_hits": result.cache_hits,
        "failed": result.failed,
        "backends": result.backends,
        "cache_dir": str(cache_dir.resolve()),
    }


def _job_train_student(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from dataclasses import asdict

    from poker_ai.learn.train_student import TrainStudentConfig, run_train_student

    metrics = run_train_student(
        cache_dir=Path(str(params.get("cache_dir", "artifacts/solver_cache"))),
        hhformer_dir=Path(str(params.get("hhformer_dir", "artifacts/hhformer/v1"))),
        artifact_dir=Path(str(params.get("output", "artifacts/student/v1"))),
        cfg=TrainStudentConfig(
            epochs=int(params.get("epochs", 30)),
            batch_size=int(params.get("batch_size", 128)),
            seed=int(params.get("seed", 42)),
            device=str(params.get("device", "auto")),
        ),
        play_study_manifest=(
            Path(str(params["play_study_manifest"]))
            if params.get("play_study_manifest")
            else _default_play_study_manifest()
        ),
        play_study_only=bool(params.get("play_study_only", False)),
        progress=emit,
        cancel_check=_cancel_check(job_id),
    )
    result: dict[str, Any] = {"metrics": asdict(metrics)}
    if bool(params.get("auto_promote")) and bool(params.get("play_study_only")):
        from poker_ai.policy.router_sources import promote_play_study_to_router

        result["router"] = promote_play_study_to_router(hu=True, multiway=False, confirm=True).to_dict()
    return result


def _job_train_style(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from dataclasses import asdict

    from poker_ai.learn.style_contrastive import StyleTrainConfig, run_style_contrastive

    metrics = run_style_contrastive(
        session_factory=get_async_session_factory(),
        artifact_dir=Path(str(params.get("output", "artifacts/style_encoder/v1"))),
        cfg=StyleTrainConfig(
            epochs=int(params.get("epochs", 25)),
            batch_size=int(params.get("batch_size", 256)),
            seed=int(params.get("seed", 42)),
            device=str(params.get("device", "auto")),
            limit_hands=int(params["limit_hands"]) if params.get("limit_hands") is not None else None,
            val_frac=float(params.get("val_frac", 0.15)),
        ),
        progress=emit,
        cancel_check=_cancel_check(job_id),
    )
    return {"metrics": asdict(metrics)}


def _job_play_study_materialize(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    from services.play_study_service import materialize_play_study

    emit({"pct": 10, "msg": "Reading play_hands from database…"})
    result = materialize_play_study(output_dir=str(params.get("output", "artifacts/play_study")))
    emit({"pct": 100, "msg": f"Training manifest ready — {result.get('hands', 0)} hands, {result.get('hero_decisions', 0)} hero decisions"})
    return result


def _default_play_study_manifest() -> Path | None:
    from services.play_auto_learn import default_play_study_manifest

    return default_play_study_manifest()


def _job_play_auto_learn(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from services.play_auto_learn import run_play_study_train_pipeline

    return run_play_study_train_pipeline(params, emit, job_id)


def _job_equity_backfill(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from dataclasses import asdict
    from datetime import datetime

    from poker_ai.equity.backfill import backfill_equities_sync

    since_raw = params.get("since")
    since_dt: datetime | None = None
    if since_raw:
        since_dt = datetime.strptime(str(since_raw), "%Y-%m-%d").replace(tzinfo=UTC)
    limit = int(params["limit"]) if params.get("limit") is not None else None
    stats = backfill_equities_sync(
        get_async_session_factory(),
        since=since_dt,
        limit=limit,
        skip_existing=not _param_bool(params.get("refresh"), False),
        mc_samples=int(params.get("mc_samples", 6000)),
        progress=emit,
        cancel_check=_cancel_check(job_id),
    )
    emit({"pct": 100, "msg": f"Equity backfill done — {stats.hands_updated} hands"})
    return {"stats": asdict(stats)}


def _job_train_multiway(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from dataclasses import asdict

    from poker_ai.learn.train_multiway_student import TrainMultiwayConfig, run_train_multiway_student

    settings = get_settings()
    monker = params.get("monker_dir")
    monker_path = Path(str(monker)) if monker else settings.monker_export_dir
    metrics = run_train_multiway_student(
        session_factory=get_async_session_factory(),
        hhformer_dir=Path(str(params.get("hhformer_dir", "artifacts/hhformer/v1"))),
        artifact_dir=Path(str(params.get("output", "artifacts/student/multiway_v1"))),
        cfg=TrainMultiwayConfig(
            epochs=int(params.get("epochs", 20)),
            batch_size=int(params.get("batch_size", 128)),
            seed=int(params.get("seed", 42)),
            device=str(params.get("device", "auto")),
            row_limit=int(params["row_limit"]) if params.get("row_limit") is not None else 50_000,
            monker_export_dir=monker_path if monker_path.is_dir() else None,
            write_monker_to_cache=settings.solver_cache_dir,
        ),
        play_study_manifest=(
            Path(str(params["play_study_manifest"]))
            if params.get("play_study_manifest")
            else _default_play_study_manifest()
        ),
        play_study_only=bool(params.get("play_study_only", False)),
        progress=emit,
        cancel_check=_cancel_check(job_id),
    )
    result = {"metrics": asdict(metrics)}
    if bool(params.get("auto_promote")) and bool(params.get("play_study_only")):
        from poker_ai.policy.router_sources import promote_play_study_to_router

        result["router"] = promote_play_study_to_router(hu=False, multiway=True, confirm=True).to_dict()
    return result


def _job_league_run(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from poker_ai.league.formats import parse_table_sizes
    from poker_ai.league.orchestrator import LeagueConfig, run_league

    run_until = bool(params.get("run_until_wall", False))
    hours = float(params.get("hours", 0.1))
    until_hours = params.get("until_hours")
    if until_hours is not None and str(until_hours).strip() != "":
        run_until = True
        max_sec = float(until_hours) * 3600.0
    else:
        max_sec = hours * 3600.0
    table_sizes_raw = str(params.get("table_sizes", "2,6,9"))
    if run_until and table_sizes_raw == "2,6,9":
        sizes = parse_table_sizes("6max,9max")
    else:
        sizes = parse_table_sizes(table_sizes_raw)
    hands_per = int(params.get("hands_per_matchup", 200))
    report = Path(str(params.get("report", "reports/league_leaderboard.json")))
    nw = resolve_worker_count(int(params["workers"]) if params.get("workers") is not None else None)
    result = run_league(
        cfg=LeagueConfig(
            hands_per_matchup=hands_per,
            max_wall_sec=max_sec,
            run_until_wall=run_until,
            until_include_hu=_param_bool(params.get("until_hu"), False),
            until_multiway_only=not _param_bool(params.get("until_hu"), False),
            seed=int(params.get("seed", 42)),
            report_path=report,
            table_sizes=sizes,
            workers=nw,
            min_hands_for_promotion=min(1000, hands_per * len(sizes) * 2),
        ),
        progress=emit,
        cancel_check=_cancel_check(job_id),
    )
    return {
        "hands_played": result.hands_played,
        "matchups": result.matchups,
        "wall_sec": result.wall_sec,
        "promoted": result.promoted,
        "report": str(result.report_path.resolve()),
        "main_elo": result.main_elo,
        "run_until_wall": run_until,
    }


def _job_validate_student(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from poker_ai.learn.validate_student import run_student_gates

    if is_cancelled(job_id):
        from poker_ai.runtime.cancel import WorkCancelled

        raise WorkCancelled("Stopped by user")

    cache_dir = Path(str(params.get("cache_dir", "artifacts/solver_cache")))
    hhformer_dir = Path(str(params.get("hhformer_dir", "artifacts/hhformer/v1")))
    student_dir = Path(str(params.get("student_dir", "artifacts/student/v1")))
    backend = str(params.get("backend", "mock"))
    n_spots = int(params.get("n_spots", 1000))
    epochs = int(params.get("epochs", 30))
    seed = int(params.get("seed", 42))

    emit({"pct": 5, "msg": f"Solving {n_spots} teacher spots ({backend})…"})
    gate = run_student_gates(
        n_spots=n_spots,
        cache_dir=cache_dir,
        hhformer_dir=hhformer_dir,
        student_dir=student_dir,
        backend=backend,
        seed=seed,
        train_epochs=epochs,
    )
    emit({"pct": 95, "msg": "Checking MSE and latency gates…"})

    passed = gate.mse_ok and gate.latency_ok
    result = {
        "n_spots": gate.n_spots,
        "mse_val": gate.mse_val,
        "mse_ok": gate.mse_ok,
        "p99_sec": gate.p99_sec,
        "latency_ok": gate.latency_ok,
        "passed": passed,
        "student_dir": str(gate.student_dir.resolve()),
        "cache_dir": str(gate.cache_dir.resolve()),
    }
    if not passed:
        msg = (
            f"Student gates failed: mse={gate.mse_val:.4f} "
            f"({'OK' if gate.mse_ok else 'FAIL ≤0.05'}) "
            f"p99={gate.p99_sec * 1000:.1f}ms "
            f"({'OK' if gate.latency_ok else 'FAIL'})"
        )
        raise RuntimeError(msg)
    return result


def _job_league_train_exploiters(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from dataclasses import asdict

    from poker_ai.league.exploiter_loop import ExploiterLoopConfig, run_exploiter_loop

    if is_cancelled(job_id):
        from poker_ai.runtime.cancel import WorkCancelled

        raise WorkCancelled("Stopped by user")

    hands = int(params.get("hands", 400))
    max_checkpoints = int(params.get("max_checkpoints", 5))
    out_dir = Path(str(params.get("out_dir", "artifacts/league/exploiters/v1")))

    emit({"pct": 10, "msg": "Calibrating exploiters vs league checkpoints…"})
    report = run_exploiter_loop(
        ExploiterLoopConfig(hands_per_matchup=hands, max_checkpoints=max_checkpoints),
        out_dir=out_dir,
    )
    emit({"pct": 100, "msg": "Exploiter calibration complete"})
    checkpoint_ids = sorted({r.checkpoint_id for r in report.checkpoint_results})
    return {
        "best_strength": report.best_strength,
        "beats_all_checkpoints": report.beats_all_checkpoints,
        "checkpoints_targeted": len(checkpoint_ids),
        "artifact_dir": report.artifact_dir,
        "checkpoint_results": [asdict(r) for r in report.checkpoint_results],
    }


def _job_features_export_parquet(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from poker_ai.features.export_parquet import export_features_parquet

    if is_cancelled(job_id):
        from poker_ai.runtime.cancel import WorkCancelled

        raise WorkCancelled("Stopped by user")
    source = Path(str(params.get("source", "features.jsonl")))
    since = params.get("since")
    emit({"pct": 10, "msg": "Exporting features to Parquet…"})
    result = export_features_parquet(source, since=str(since) if since else None)
    emit({"pct": 100, "msg": f"Exported {result['num_rows']} rows"})
    return dict(result)


def _job_features_validate_blueprint(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from poker_ai.features.export_parquet import validate_blueprint_file

    if is_cancelled(job_id):
        from poker_ai.runtime.cancel import WorkCancelled

        raise WorkCancelled("Stopped by user")
    source = Path(str(params.get("source", "features.jsonl")))
    blueprint_full = bool(params.get("blueprint_full", False))
    emit({"pct": 10, "msg": "Validating feature schema…"})
    result = validate_blueprint_file(source, blueprint_full=blueprint_full)
    if not result["schema_ok"]:
        first = result["errors"][0] if result["errors"] else "schema validation failed"
        raise ValueError(first)
    emit({"pct": 100, "msg": f"Schema OK ({result['hands_checked']} hands)"})
    return dict(result)


def _job_league_replay_run(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from dataclasses import asdict

    from poker_ai.league.replay_league import run_replay_league

    limit = int(params.get("limit", 500))
    strata = str(params.get("strata", "hu,mw"))
    agents = str(params.get("agents", "main_agent,distilled_gto"))
    since_raw = params.get("since")
    since_dt = None
    if since_raw:
        since_dt = datetime.fromisoformat(str(since_raw)).replace(tzinfo=UTC)

    report = run_replay_league(
        limit=limit,
        strata=strata,
        agents=agents,
        since=since_dt,
        progress=emit,
        cancel_check=_cancel_check(job_id),
    )
    return {
        "hands_scored": report.hands_scored,
        "hero_decisions": report.hero_decisions,
        "aivat_mode": report.aivat_mode,
        "report": report.report_path,
        "agents": [asdict(a) for a in report.agents],
        "by_format": report.by_format,
    }


def _job_aivat_audit(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from dataclasses import asdict

    from poker_ai.eval.aivat import run_aivat_audit

    if is_cancelled(job_id):
        from poker_ai.runtime.cancel import WorkCancelled

        raise WorkCancelled("Stopped by user")
    os.environ["POKER_AI_AIVAT_FULL"] = "1"
    hands = int(params.get("hands", 1000))
    seed = int(params.get("seed", 42))
    report_path = Path(str(params.get("report", "reports/aivat_audit.json")))
    emit({"pct": 10, "msg": f"Running AIVAT audit on {hands} hands…"})
    report = run_aivat_audit(hands=hands, seed=seed, report_path=report_path)
    emit({"pct": 100, "msg": "AIVAT audit complete"})
    return asdict(report)


def _job_policy_bench(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from poker_ai.policy.bench import bench_policy, write_bench_report
    from poker_ai.policy.distilled_policy import DistilledPolicy, load_best_policy
    from poker_ai.policy.heuristic import HeuristicPolicy
    from poker_ai.policy.postflop_equity import PostflopEquityPolicy
    from poker_ai.policy.stacked import StackedPolicy

    if is_cancelled(job_id):
        from poker_ai.runtime.cancel import WorkCancelled

        raise WorkCancelled("Stopped by user")

    n_samples = int(params.get("samples", 500))
    n_warmup = int(params.get("warmup", 10))
    report_path = Path(str(params.get("report", "reports/policy_bench.json")))
    results = []
    factories = (
        ("heuristic", HeuristicPolicy),
        ("postflop_equity", PostflopEquityPolicy),
        ("stacked", lambda: StackedPolicy.from_artifacts()),
        ("best", load_best_policy),
    )
    emit({"pct": 5, "msg": "Benchmarking policy latency…"})
    for label, factory in factories:
        if is_cancelled(job_id):
            from poker_ai.runtime.cancel import WorkCancelled

            raise WorkCancelled("Stopped by user")
        try:
            pol = factory()
            results.append(bench_policy(pol, n_samples=n_samples, n_warmup=n_warmup))
        except Exception:
            continue
    if Path("artifacts/student/v1/student.safetensors").is_file():
        try:
            dist = DistilledPolicy.from_artifacts()
            results.append(bench_policy(dist, n_samples=n_samples, n_warmup=n_warmup))
        except Exception:
            pass
    if not results:
        raise RuntimeError("No policies available to benchmark")
    write_bench_report(results, report_path)
    best_p99 = min(r.p99_ms for r in results)
    emit({"pct": 100, "msg": f"Best p99={best_p99:.1f}ms"})
    return {
        "report": str(report_path.resolve()),
        "policies": [r.to_dict() for r in results],
        "best_p99_ms": round(best_p99, 2),
        "target_p99_ms": 30.0,
        "passed": best_p99 < 30.0,
    }


def _job_solve_kuhn(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from poker_ai.solver.cfr import CFRSolver, ExternalSamplingMCCFRSolver
    from poker_ai.solver.validate import OpenSpielKuhnBridge, openspiel_exploitability_mbb

    if is_cancelled(job_id):
        from poker_ai.runtime.cancel import WorkCancelled

        raise WorkCancelled("Stopped by user")

    iters = int(params.get("iters", 10_000))
    mode = str(params.get("mode", "cfr_plus"))
    emit({"pct": 10, "msg": f"Running Kuhn CFR ({mode})…"})
    game = OpenSpielKuhnBridge()
    if mode == "external":
        solver = ExternalSamplingMCCFRSolver(game)
    else:
        solver = CFRSolver(game, mode="cfr_plus" if mode == "cfr_plus" else "vanilla")
    solver.run(iters)
    strat = solver.average_strategy()
    exp = openspiel_exploitability_mbb(strat, big_blind=1.0)
    emit({"pct": 100, "msg": f"Kuhn exploitability={exp:.4f} mbb/g"})
    return {
        "iters": iters,
        "mode": mode,
        "info_sets": len(strat),
        "exploitability_mbb": round(exp, 4),
        "passed": exp < 50.0,
    }


def _job_features_hhformer_embed(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from poker_ai.learn.hhformer_inference import EmbedConfig, export_embeddings_jsonl

    if is_cancelled(job_id):
        from poker_ai.runtime.cancel import WorkCancelled

        raise WorkCancelled("Stopped by user")

    output = Path(str(params.get("output", "data/processed/hhformer_embeddings.jsonl")))
    weights = Path(str(params.get("weights", "artifacts/hhformer/v1")))
    device = str(params.get("device", "auto"))
    batch_size = int(params.get("batch_size", 256))
    max_hands = int(params["max_hands"]) if params.get("max_hands") is not None else None
    with_equity = bool(params.get("with_equity", False))
    emit({"pct": 10, "msg": "Exporting HHFormer embeddings…"})
    cfg = EmbedConfig(
        weights_dir=weights,
        device=device,
        batch_size=batch_size,
        max_hands=max_hands,
        with_equity=with_equity,
    )
    n = export_embeddings_jsonl(get_async_session_factory(), output, cfg=cfg)
    emit({"pct": 100, "msg": f"Exported {n} embeddings"})
    return {"hands_written": n, "output": str(output.resolve())}


def _job_opponents_eval_exploit(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from dataclasses import asdict

    from poker_ai.opponents.eval import evaluate_exploit_vs_gto

    if is_cancelled(job_id):
        from poker_ai.runtime.cancel import WorkCancelled

        raise WorkCancelled("Stopped by user")

    hands = int(params.get("hands", 400))
    seed = int(params.get("seed", 42))
    baseline = str(params.get("baseline", "best"))
    strength = float(params.get("strength", 0.28))
    use_best = baseline.strip().lower() != "heuristic"
    emit({"pct": 10, "msg": f"Evaluating exploit vs {baseline} baseline…"})
    results = evaluate_exploit_vs_gto(
        hands_per_opponent=hands,
        seed=seed,
        use_best_baseline=use_best,
        deviation_strength=strength,
        alternate_seats=not bool(params.get("no_seat_alt", False)),
    )
    mean_delta = sum(r.delta_bb100 for r in results) / max(1, len(results))
    emit({"pct": 100, "msg": f"Mean exploit delta={mean_delta:+.2f} bb/100"})
    return {
        "baseline": baseline,
        "strength": strength,
        "mean_delta_bb100": round(mean_delta, 2),
        "results": [asdict(r) for r in results],
        "passed": mean_delta >= 5.0,
    }


def _job_train_value_net(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from dataclasses import asdict

    from poker_ai.learn.train_value_net import TrainValueNetConfig, run_train_value_net

    if is_cancelled(job_id):
        from poker_ai.runtime.cancel import WorkCancelled

        raise WorkCancelled("Stopped by user")

    cfg = TrainValueNetConfig(
        epochs=int(params.get("epochs", 20)),
        batch_size=int(params.get("batch_size", 128)),
        seed=int(params.get("seed", 42)),
        device=str(params.get("device", "auto")),
    )
    cache_dir = Path(str(params.get("cache_dir", "artifacts/solver_cache")))
    hhformer_dir = Path(str(params.get("hhformer_dir", "artifacts/hhformer/v1")))
    out = Path(str(params.get("output", "artifacts/value_net/v1")))
    emit({"pct": 10, "msg": "Training value net on solver cache…"})
    metrics = run_train_value_net(
        cache_dir=cache_dir,
        hhformer_dir=hhformer_dir,
        artifact_dir=out,
        cfg=cfg,
        progress=emit,
        cancel_check=_cancel_check(job_id),
    )
    return {"artifact_dir": str(out.resolve()), "metrics": asdict(metrics)}


def _job_train_decision_quality(
    params: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
    job_id: str,
) -> dict[str, Any]:
    from dataclasses import asdict

    from poker_ai.learn.train_decision_quality import (
        TrainDecisionQualityConfig,
        run_train_decision_quality,
    )

    if is_cancelled(job_id):
        from poker_ai.runtime.cancel import WorkCancelled

        raise WorkCancelled("Stopped by user")

    cfg = TrainDecisionQualityConfig(
        epochs=int(params.get("epochs", 15)),
        batch_size=int(params.get("batch_size", 64)),
        seed=int(params.get("seed", 42)),
        device=str(params.get("device", "auto")),
        row_limit=int(params.get("row_limit", 5000)),
    )
    hhformer_dir = Path(str(params.get("hhformer_dir", "artifacts/hhformer/v1")))
    out = Path(str(params.get("output", "artifacts/decision_quality/v1")))
    emit({"pct": 5, "msg": "Loading hero spots from library…"})
    metrics = run_train_decision_quality(
        hhformer_dir=hhformer_dir,
        artifact_dir=out,
        cfg=cfg,
        progress=emit,
        cancel_check=_cancel_check(job_id),
    )
    return {"artifact_dir": str(out.resolve()), "metrics": asdict(metrics)}
