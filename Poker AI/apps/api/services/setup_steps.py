"""Setup wizard step readiness (Phase W4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from poker_ai.store.loader import count_parsed_hands

# ``poker_ai serve`` runs uvicorn with cwd = poker_ai/ (same as CLI artifacts).
_PROJECT_ROOT = Path(__file__).resolve().parents[3] / "poker_ai"

_ARTIFACT_REL: dict[str, list[str]] = {
    "train_hhformer": ["artifacts/hhformer/v1/weights.safetensors"],
    "train_student": [
        "artifacts/student/v1/student.safetensors",
        "artifacts/student/v1/model.pt",
    ],
    "train_cql": ["artifacts/cql/v1/cql_policy.safetensors"],
    "train_hhformer_finetune": ["artifacts/hhformer/v2/weights.safetensors"],
    "solve_preflop": [
        "artifacts/solver/preflop_hu_real.json",
        "artifacts/solver/preflop_hu.json",
        "artifacts/solver/preflop_cfr.json",
    ],
    "solve_preflop_8max": ["artifacts/solver/preflop_8max.json"],
    "solve_preflop_9max": ["artifacts/solver/preflop_9max.json"],
    "solve_preflop_10max": ["artifacts/solver/preflop_10max.json"],
    "solve_grid": ["artifacts/solver_cache"],
    "train_style": [
        "artifacts/style_encoder/v1/style_encoder.safetensors",
        "artifacts/style_encoder/v1/model.pt",
    ],
    "train_multiway": [
        "artifacts/student/multiway_v1/student.safetensors",
        "artifacts/student/multiway_v1/model.pt",
    ],
    "train_value_net": ["artifacts/value_net/v1/value_net.safetensors"],
    "train_decision_quality": ["artifacts/decision_quality/v1/decision_quality.safetensors"],
}


def _artifact_paths(step_id: str) -> list[Path]:
    rels = _ARTIFACT_REL.get(step_id, [])
    return [(_PROJECT_ROOT / r).resolve() for r in rels]


def _features_candidates() -> list[Path]:
    return [
        (_PROJECT_ROOT / "features.jsonl").resolve(),
        Path("features.jsonl").resolve(),
    ]

STEP_RUN_DEFAULTS: dict[str, tuple[str, dict[str, Any]]] = {
    "features": ("features_build", {}),
    "train_hhformer": ("train_hhformer", {"device": "auto", "epochs": 30, "batch_size": 256}),
    "solve_preflop": (
        "solve_preflop",
        {
            "positions": "hu",
            "iters": 20_000,
            "equity_mode": "real",
            "production": False,
            "force_parallel_workers": True,
        },
    ),
    "solve_grid": (
        "solve_grid",
        {"n_spots": 128, "backend": "auto", "continue_on_error": True},
    ),
    "train_student": ("train_student", {"device": "auto", "epochs": 30, "batch_size": 128}),
    "train_cql": ("train_cql", {"epochs": 15, "alpha": 1.0, "batch_size": 128, "max_rows": 50_000, "device": "auto", "seed": 42}),
    "train_hhformer_finetune": (
        "train_hhformer_finetune",
        {"epochs": 8, "max_hands": 5000, "batch_size": 128, "device": "auto", "num_workers": 0, "no_amp": False},
    ),
    "train_style": ("train_style", {"epochs": 25, "device": "auto"}),
    "league": ("league_run", {"hours": 0.1, "hands_per_matchup": 200}),
    "equity_backfill": ("equity_backfill", {"mc_samples": 6000}),
    "train_multiway": ("train_multiway_student", {"epochs": 20, "row_limit": 50_000, "device": "auto"}),
    "features_validate": ("features_validate_blueprint", {"source": "features.jsonl", "blueprint_full": False}),
    "train_value_net": ("train_value_net", {"epochs": 20, "batch_size": 128, "device": "auto"}),
    "train_decision_quality": ("train_decision_quality", {"row_limit": 5000, "epochs": 15, "device": "auto"}),
    "league_replay": ("league_replay_run", {"limit": 500, "strata": "hu,mw"}),
    "solve_preflop_8max": (
        "solve_preflop",
        {"positions": "8max", "iters": 25_000, "equity_mode": "real", "production": True, "force_parallel_workers": True},
    ),
    "solve_preflop_9max": (
        "solve_preflop",
        {"positions": "9max", "iters": 25_000, "equity_mode": "real", "production": True, "force_parallel_workers": True},
    ),
    "solve_preflop_10max": (
        "solve_preflop",
        {"positions": "10max", "iters": 25_000, "equity_mode": "real", "production": True, "force_parallel_workers": True},
    ),
}


def _resolve_artifact(paths: list[Path]) -> Path | None:
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


def _artifact_ready(step_id: str) -> bool:
    paths = _artifact_paths(step_id)
    if not paths:
        return False
    return _resolve_artifact(paths) is not None


def _features_ready() -> bool:
    for path in _features_candidates():
        try:
            if path.is_file() and path.stat().st_size > 0:
                return True
        except OSError:
            continue
    return False


def _features_detail() -> str:
    for path in _features_candidates():
        try:
            if path.is_file() and path.stat().st_size > 0:
                mb = path.stat().st_size / (1024 * 1024)
                return f"features.jsonl ready ({mb:.1f} MB)"
        except OSError:
            continue
    return "Feature JSONL not found"


def _hhformer_detail() -> str:
    path = _resolve_artifact(_artifact_paths("train_hhformer"))
    if not path:
        return "Not trained"
    mf = path.parent / "metrics.json"
    if mf.is_file():
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
            parts: list[str] = []
            if data.get("finished_at") or data.get("trained_at"):
                parts.append(str(data.get("finished_at") or data.get("trained_at")))
            for key, label in (
                ("map_accuracy", "MAP"),
                ("val_map", "MAP"),
                ("sop_auc", "SOP AUC"),
            ):
                if key in data and data[key] is not None:
                    v = data[key]
                    if isinstance(v, float) and "auc" in key.lower():
                        parts.append(f"{label} {v:.2f}")
                    elif isinstance(v, float):
                        parts.append(f"{label} {v * 100:.1f}%")
            if parts:
                return " · ".join(parts)
        except Exception:
            pass
    return "Trained — see artifacts/hhformer/v1/"


def _preflop_detail() -> str:
    hu = _resolve_artifact(
        [
            (_PROJECT_ROOT / "artifacts/solver/preflop_hu_real.json").resolve(),
            (_PROJECT_ROOT / "artifacts/solver/preflop_hu.json").resolve(),
        ]
    )
    six = _resolve_artifact([(_PROJECT_ROOT / "artifacts/solver/preflop_cfr.json").resolve()])
    ring = [
        n
        for n, fname in (
            ("8", "preflop_8max.json"),
            ("9", "preflop_9max.json"),
            ("10", "preflop_10max.json"),
        )
        if _resolve_artifact([(_PROJECT_ROOT / "artifacts/solver" / fname).resolve()])
    ]
    parts: list[str] = []
    if hu:
        parts.append("HU")
    if six:
        parts.append("6-max")
    if ring:
        parts.append(f"ring {','.join(ring)}-max")
    if parts:
        return " · ".join(parts) + " ready"
    return "Not solved — run preflop CFR (HU + 6-max minimum; 8/9/10-max optional)"


def _solver_cache_detail() -> str:
    cache = _resolve_artifact(_artifact_paths("solve_grid"))
    if not cache:
        return _texas_grid_detail_not_ready()
    try:
        n = sum(1 for _ in cache.rglob("*") if _.is_file())
    except OSError:
        n = 0
    return f"{n} cached spot file(s)" if n else "Cache folder exists (empty)"


def _texas_grid_detail_not_ready() -> str:
    try:
        from poker_ai.solver.bridge.install_texas import texas_solver_status

        ts = texas_solver_status()
        if ts.get("installed"):
            return "TexasSolver ready — run grid to fill cache"
    except Exception:
        pass
    return "TexasSolver not found — install on System health or use mock backend"


def _texas_found() -> bool:
    try:
        from poker_ai.solver.bridge.install_texas import texas_solver_status

        return bool(texas_solver_status().get("installed"))
    except Exception:
        return False


async def _league_has_run(session: AsyncSession) -> bool:
    row = (
        await session.execute(
            text(
                "SELECT 1 FROM jobs WHERE type = 'league_run' AND status = 'done' LIMIT 1"
            )
        )
    ).first()
    return row is not None


async def build_setup_steps(session: AsyncSession) -> list[dict[str, Any]]:
    """Ordered wizard steps with readiness (matches WEB_IMPLEMENTATION_GUIDE W4)."""
    n_hands = await count_parsed_hands(session)
    ingest_ready = n_hands > 0
    features_ready = _features_ready()
    hh_ready = _artifact_ready("train_hhformer")
    preflop_ready = _artifact_ready("solve_preflop")
    grid_ready = _artifact_ready("solve_grid")
    student_ready = _artifact_ready("train_student")
    style_ready = _artifact_ready("train_style")
    league_ready = await _league_has_run(session)

    steps: list[dict[str, Any]] = [
        {
            "id": "ingest",
            "title": "Import Hand Histories",
            "description": "Load your poker hands into the database",
            "ready": ingest_ready,
            "detail": f"{n_hands:,} hands in store" if ingest_ready else "No hands yet",
            "requires": [],
            "optional": False,
            "job_type": None,
        },
        {
            "id": "features",
            "title": "Build Features",
            "description": "Convert hands to AI-readable tensors and sequences",
            "ready": features_ready,
            "detail": _features_detail(),
            "requires": ["ingest"],
            "optional": False,
            "job_type": "features_build",
        },
        {
            "id": "features_validate",
            "title": "Validate Feature Schema",
            "description": "Round-trip check that features.jsonl matches the blueprint contract",
            "ready": features_ready,
            "detail": "Run after Prepare hands — use Extended preset for v2 full columns",
            "requires": ["features"],
            "optional": True,
            "job_type": "features_validate_blueprint",
        },
        {
            "id": "equity_backfill",
            "title": "Backfill Hand Equities",
            "description": "Write MC pot equity into results.*_equity for Replayer / Drill / HUD",
            "ready": ingest_ready,
            "detail": "Optional — run after import to populate equity columns",
            "requires": ["ingest"],
            "optional": True,
            "job_type": "equity_backfill",
        },
        {
            "id": "train_hhformer",
            "title": "Train HHFormer Model",
            "description": "Pretrain the poker foundation model on your hand history",
            "ready": hh_ready,
            "detail": _hhformer_detail() if hh_ready else "Not trained",
            "requires": ["features"],
            "optional": False,
            "job_type": "train_hhformer",
        },
        {
            "id": "solve_preflop",
            "title": "Solve Preflop Strategy (HU + 6-max)",
            "description": "CFR+ preflop charts for heads-up and six-max (required for league)",
            "ready": preflop_ready,
            "detail": _preflop_detail(),
            "requires": ["ingest"],
            "optional": False,
            "job_type": "solve_preflop",
        },
        {
            "id": "solve_preflop_8max",
            "title": "Preflop 8-max (optional)",
            "description": "Production CFR for eight-handed tables — long CPU run",
            "ready": _artifact_ready("solve_preflop_8max"),
            "detail": "preflop_8max.json ready" if _artifact_ready("solve_preflop_8max") else "Not built",
            "requires": ["ingest"],
            "optional": True,
            "job_type": "solve_preflop",
        },
        {
            "id": "solve_preflop_9max",
            "title": "Preflop 9-max (optional)",
            "description": "Production CFR for nine-handed tables",
            "ready": _artifact_ready("solve_preflop_9max"),
            "detail": "preflop_9max.json ready" if _artifact_ready("solve_preflop_9max") else "Not built",
            "requires": ["ingest"],
            "optional": True,
            "job_type": "solve_preflop",
        },
        {
            "id": "solve_preflop_10max",
            "title": "Preflop 10-max (optional)",
            "description": "Production CFR for full-ring ten-handed tables",
            "ready": _artifact_ready("solve_preflop_10max"),
            "detail": "preflop_10max.json ready" if _artifact_ready("solve_preflop_10max") else "Not built",
            "requires": ["ingest"],
            "optional": True,
            "job_type": "solve_preflop",
        },
        {
            "id": "solve_grid",
            "title": "Build Solver Cache (TexasSolver)",
            "description": "Run TexasSolver on postflop spots to train the student",
            "ready": grid_ready,
            "detail": _solver_cache_detail() if grid_ready else _texas_grid_detail_not_ready(),
            "requires": ["train_hhformer"],
            "optional": False,
            "job_type": "solve_grid",
            "texas_solver_found": _texas_found(),
        },
        {
            "id": "train_value_net",
            "title": "Train Value Net",
            "description": "Scalar EV head on solver cache rows (blueprint v2)",
            "ready": _artifact_ready("train_value_net"),
            "detail": (
                "Value net ready"
                if _artifact_ready("train_value_net")
                else "Run after solver cache — feeds league and drift"
            ),
            "requires": ["solve_grid"],
            "optional": True,
            "job_type": "train_value_net",
        },
        {
            "id": "train_student",
            "title": "Train Distilled Student (HU)",
            "description": "Compress solver knowledge into a fast neural network for heads-up postflop",
            "ready": student_ready,
            "detail": "Student HU weights ready" if student_ready else "Not trained",
            "requires": ["train_hhformer", "solve_grid"],
            "optional": False,
            "job_type": "train_student",
        },
        {
            "id": "train_multiway",
            "title": "Train Multi-way Student",
            "description": "Postflop student for 3+ players (uses HHFormer + Monker when available)",
            "ready": _artifact_ready("train_multiway"),
            "detail": "Multi-way student ready" if _artifact_ready("train_multiway") else "Not trained",
            "requires": ["train_hhformer"],
            "optional": True,
            "job_type": "train_multiway_student",
        },
        {
            "id": "train_cql",
            "title": "Train CQL Policy",
            "description": "Conservative offline RL on solver rows — adds cql_agent to league",
            "ready": _artifact_ready("train_cql"),
            "detail": "CQL artifact ready" if _artifact_ready("train_cql") else "Run after solver cache + student",
            "requires": ["train_student", "solve_grid"],
            "optional": False,
            "job_type": "train_cql",
        },
        {
            "id": "train_hhformer_finetune",
            "title": "Fine-tune HHFormer on Solver Outputs",
            "description": "Continual pretrain with TexasSolver-masked actions (v2 candidate)",
            "ready": _artifact_ready("train_hhformer_finetune"),
            "detail": (
                "HHFormer v2 fine-tuned — promote on Models page"
                if _artifact_ready("train_hhformer_finetune")
                else "Run after solver cache exists"
            ),
            "requires": ["train_hhformer", "solve_grid"],
            "optional": False,
            "job_type": "train_hhformer_finetune",
        },
        {
            "id": "train_decision_quality",
            "title": "Train Decision Quality",
            "description": "Audit head: hero decisions vs GTO teacher in your library",
            "ready": _artifact_ready("train_decision_quality"),
            "detail": (
                "Decision quality model ready"
                if _artifact_ready("train_decision_quality")
                else "Run after HHFormer + features (equity backfill improves accuracy)"
            ),
            "requires": ["train_hhformer", "features"],
            "optional": True,
            "job_type": "train_decision_quality",
        },
        {
            "id": "train_style",
            "title": "Train Style Encoder",
            "description": "Learn opponent profiles from play patterns",
            "ready": style_ready,
            "detail": "Style encoder ready" if style_ready else "Not trained",
            "requires": ["features"],
            "optional": False,
            "job_type": "train_style",
        },
        {
            "id": "league",
            "title": "Run Self-Play League",
            "description": "Let the AI improve through self-play",
            "ready": league_ready,
            "detail": "League completed" if league_ready else "Never run",
            "requires": [
                "solve_preflop",
                "train_student",
                "solve_grid",
                "train_cql",
                "train_hhformer_finetune",
                "train_style",
            ],
            "optional": False,
            "job_type": "league_run",
        },
        {
            "id": "league_replay",
            "title": "League on Your Library",
            "description": "Score AI policies on imported hands (hero replay, not synthetic sim)",
            "ready": league_ready,
            "detail": "Run after import — validates routing and EV on real action sequences",
            "requires": ["ingest", "train_student"],
            "optional": True,
            "job_type": "league_replay_run",
        },
    ]
    return steps


def requirements_met(step: dict[str, Any], steps_by_id: dict[str, dict[str, Any]]) -> bool:
    for req in step.get("requires") or []:
        other = steps_by_id.get(req)
        if other is None or not other.get("ready"):
            return False
    return True
