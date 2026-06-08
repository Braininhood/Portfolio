"""GET /status — full system status: hardware, models, DB, workers."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_db, get_schema_revision
from schemas import (
    CpuInfoSchema,
    DiskInfoSchema,
    GpuInfoSchema,
    ModelStatusSchema,
    RamInfoSchema,
    SystemStatusResponse,
    TexasSolverStatusSchema,
    WorkerRecommendationSchema,
)
from services.hardware import detect_hardware
from poker_ai import __version__
from poker_ai.store import jobs_store
from poker_ai.store.loader import count_parsed_hands

router = APIRouter(tags=["status"])

# ---------------------------------------------------------------------------
# Artifact paths (relative to poker_ai/ working directory)
# ---------------------------------------------------------------------------

_MODELS_TO_CHECK: list[tuple[str, list[Path], str, str]] = [
    # (display_name, artifact_paths — any match counts, job_type, why)
    (
        "HHFormer v1",
        [Path("artifacts/hhformer/v1/weights.safetensors")],
        "train_hhformer",
        "Learns poker “language” from your hand library — feeds the decision AI and style tools.",
    ),
    (
        "Student HU v1",
        [
            Path("artifacts/student/v1/student.safetensors"),
            Path("artifacts/student/v1/model.pt"),  # legacy
        ],
        "train_student",
        "Heads-up postflop decision AI — copies the solver teacher; used for advice and bots.",
    ),
    (
        "Student Multi-way v1",
        [
            Path("artifacts/student/multiway_v1/student.safetensors"),
            Path("artifacts/student/multiway_v1/model.pt"),
        ],
        "train_multiway_student",
        "Postflop AI for 3+ players — needs HHFormer and (ideally) Monker/solver exports.",
    ),
    (
        "Preflop CFR (HU)",
        [
            Path("artifacts/solver/preflop_hu_real.json"),
            Path("artifacts/solver/preflop_hu.json"),
        ],
        "solve_preflop",
        "Heads-up open / 3-bet chart — the bot uses this before the flop in HU pots.",
    ),
    (
        "Preflop CFR (6-max)",
        [Path("artifacts/solver/preflop_cfr.json")],
        "solve_preflop",
        "Six-max preflop chart — needed for full-ring and 6-max simulations.",
    ),
    (
        "Preflop CFR (8-max)",
        [Path("artifacts/solver/preflop_8max.json")],
        "solve_preflop",
        "Eight-max ring chart — used when table has 8 seats and artifact exists.",
    ),
    (
        "Preflop CFR (9-max)",
        [Path("artifacts/solver/preflop_9max.json")],
        "solve_preflop",
        "Nine-max ring chart — used for 9-handed tables.",
    ),
    (
        "Preflop CFR (10-max)",
        [Path("artifacts/solver/preflop_10max.json")],
        "solve_preflop",
        "Ten-max ring chart — full-ring preflop strategy.",
    ),
    (
        "Style Encoder v1",
        [
            Path("artifacts/style_encoder/v1/style_encoder.safetensors"),
            Path("artifacts/style_encoder/v1/model.pt"),
        ],
        "train_style",
        "Clusters player tendencies from your database — powers opponent profiling.",
    ),
    (
        "Solver Cache",
        [Path("artifacts/solver_cache")],
        "solve_grid",
        "Postflop “teacher” spots — the student learns good flop/turn/river play from these.",
    ),
    (
        "CQL Policy v1",
        [Path("artifacts/cql/v1/cql_policy.safetensors")],
        "train_cql",
        "Conservative offline RL policy — league cql_agent and deep-search blend.",
    ),
    (
        "HHFormer v2 (solver fine-tuned)",
        [Path("artifacts/hhformer/v2/weights.safetensors")],
        "train_hhformer_finetune",
        "Solver-supervised continual pretrain — promote on Models page after drift gates.",
    ),
    (
        "Value net",
        [Path("artifacts/value_net/v1/value_net.safetensors")],
        "train_value_net",
        "Scalar spot-value head trained on solver cache — blueprint v2 league/drift input.",
    ),
    (
        "Decision quality",
        [Path("artifacts/decision_quality/v1/decision_quality.safetensors")],
        "train_decision_quality",
        "Hero decision audit vs GTO teacher — flags leaks in imported hands.",
    ),
]


def _resolve_artifact(paths: list[Path]) -> Path | None:
    """First existing path wins (file or non-empty cache directory)."""
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            return path
        try:
            if path.is_dir() and any(path.iterdir()):
                return path
        except OSError:
            continue
    return None


def _model_status(name: str, paths: list[Path], job_type: str, why: str) -> ModelStatusSchema:
    found = _resolve_artifact(paths)
    ready = found is not None
    path = found or paths[0]
    trained_at: str | None = None
    if ready:
        # Try metrics.json next to the artifact
        metrics_candidates = [
            path.parent / "metrics.json",
            path / "metrics.json",  # for directories like solver_cache
        ]
        for mf in metrics_candidates:
            if mf.is_file():
                try:
                    data = json.loads(mf.read_text(encoding="utf-8"))
                    trained_at = data.get("finished_at") or data.get("trained_at")
                    if not trained_at:
                        # Fall back to file modification time
                        ts = mf.stat().st_mtime
                        trained_at = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
                break
        if not trained_at:
            # Use artifact mtime as fallback
            try:
                ts = path.stat().st_mtime
                trained_at = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            except Exception:
                pass
    return ModelStatusSchema(
        name=name,
        ready=ready,
        path=str(path),
        trained_at=trained_at,
        note=None if ready else why,
        job_type=job_type,
        why=why,
    )


def _texas_solver_status() -> TexasSolverStatusSchema:
    """Same source as ``poker_ai solve texas-status`` and ``GET /health/check``."""
    try:
        from poker_ai.solver.bridge.install_texas import texas_solver_status

        ts = texas_solver_status()
        installed = bool(ts.get("installed"))
        exe = ts.get("executable") or ""
        version = ts.get("version") or ""
    except Exception:
        installed = False
        exe = ""
        version = ""

    if installed and exe and Path(exe).is_file():
        note = "Registered and ready"
        if version:
            note = f"{version} · ready"
        return TexasSolverStatusSchema(
            found=True,
            exe_path=str(exe),
            version=version or None,
            note=note,
        )

    return TexasSolverStatusSchema(
        found=False,
        exe_path=None,
        version=None,
        note=(
            "Not found. Open System health → Install TexasSolver, register a binary, "
            "or skip — the student can use mock equity labels instead."
        ),
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.get("/status", response_model=SystemStatusResponse)
async def system_status(session: AsyncSession = Depends(get_db)) -> SystemStatusResponse:
    """Full system status: hardware detection, model readiness, DB state, worker advice."""

    hw = detect_hardware()

    # DB
    n_hands: int | None = None
    try:
        n_hands = await count_parsed_hands(session)
    except Exception:
        n_hands = None

    # Models
    models = [
        _model_status(name, paths, job_type, why) for name, paths, job_type, why in _MODELS_TO_CHECK
    ]

    # TexasSolver
    texas = _texas_solver_status()

    # Convert dataclasses → Pydantic schemas
    cpu_schema = CpuInfoSchema(
        name=hw.cpu.name,
        physical_cores=hw.cpu.physical_cores,
        logical_cores=hw.cpu.logical_cores,
        arch=hw.cpu.arch,
    )

    gpu_schema: GpuInfoSchema | None = None
    if hw.gpu:
        gpu_schema = GpuInfoSchema(
            name=hw.gpu.name,
            vram_gb=hw.gpu.vram_gb,
            driver_version=hw.gpu.driver_version,
            cuda_version=hw.gpu.cuda_version,
            cuda_available=hw.gpu.cuda_available,
        )

    ram_schema = RamInfoSchema(
        total_gb=hw.ram.total_gb,
        available_gb=hw.ram.available_gb,
    )

    workers_schema = WorkerRecommendationSchema(
        recommended=hw.workers.recommended,
        max_safe=hw.workers.max_safe,
        current_env=hw.workers.current_env,
        warning=hw.workers.warning,
        explanation=hw.workers.explanation,
        by_task=hw.workers.by_task,
    )

    disk_schema = DiskInfoSchema(
        free_gb=hw.disk.free_gb,
        total_gb=hw.disk.total_gb,
        path=hw.disk.path,
    )

    job_counts = await jobs_store.count_jobs_by_status(session)
    jobs_running = job_counts.get("running", 0)
    jobs_queued = job_counts.get("queued", 0)

    return SystemStatusResponse(
        version=__version__,
        os_name=hw.os_name,
        os_platform=hw.os_platform,
        cpu=cpu_schema,
        gpu=gpu_schema,
        ram=ram_schema,
        disk=disk_schema,
        workers=workers_schema,
        db_hands=n_hands,
        db_revision=get_schema_revision(),
        models=models,
        texas_solver=texas,
        jobs_running=jobs_running,
        jobs_queued=jobs_queued,
    )
