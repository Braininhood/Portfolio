"""Model version registry — CURRENT pointer + promote/rollback (Phase 11 / W8)."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Registry name -> artifacts root directory (under poker_ai cwd)
REGISTRY: dict[str, Path] = {
    "hhformer": Path("artifacts/hhformer"),
    "student_hu": Path("artifacts/student"),
    "student_multiway": Path("artifacts/student/multiway_v1").parent,  # versions as subdirs
    "preflop_hu": Path("artifacts/solver"),
    "preflop_6max": Path("artifacts/solver"),
    "preflop_8max": Path("artifacts/solver"),
    "preflop_9max": Path("artifacts/solver"),
    "preflop_10max": Path("artifacts/solver"),
    "style_encoder": Path("artifacts/style_encoder"),
    "solver_cache": Path("artifacts/solver_cache"),
    "student_play_study_hu": Path("artifacts/student/play_study_hu_v1").parent,
    "student_play_study_multiway": Path("artifacts/student/play_study_multiway_v1").parent,
}

# Fixed artifact filenames for non-versioned solver JSON
SOLVER_PINNED: dict[str, str] = {
    "preflop_hu": "preflop_hu_real.json",
    "preflop_6max": "preflop_cfr.json",
    "preflop_8max": "preflop_8max.json",
    "preflop_9max": "preflop_9max.json",
    "preflop_10max": "preflop_10max.json",
}


@dataclass
class ModelVersionInfo:
    name: str
    current_version: str | None
    candidate_version: str | None
    current_metrics: dict[str, float]
    candidate_metrics: dict[str, float] | None
    can_promote: bool
    can_rollback: bool
    current_path: str | None = None
    note: str | None = None


def _read_metrics(version_dir: Path) -> dict[str, float]:
    mf = version_dir / "metrics.json"
    if not mf.is_file():
        return {}
    try:
        data = json.loads(mf.read_text(encoding="utf-8"))
        out: dict[str, float] = {}
        for k, v in data.items():
            if isinstance(v, (int, float)):
                out[k] = float(v)
        return out
    except (json.JSONDecodeError, OSError):
        return {}


def _list_version_dirs(root: Path) -> list[str]:
    if not root.is_dir():
        return []
    names = []
    for p in root.iterdir():
        if p.is_dir() and p.name.startswith("v") and p.name != "vCURRENT":
            names.append(p.name)
    return sorted(names, reverse=True)


def _current_file(root: Path) -> Path:
    return root / "CURRENT"


def _read_current(root: Path) -> str | None:
    cf = _current_file(root)
    if cf.is_file():
        return cf.read_text(encoding="utf-8").strip() or None
    # Legacy: single v1 folder without CURRENT
    if (root / "v1").is_dir():
        return "v1"
    return None


def get_model_info(name: str) -> ModelVersionInfo:
    if name in SOLVER_PINNED:
        root = REGISTRY[name]
        pinned = root / SOLVER_PINNED[name]
        ready = pinned.is_file()
        return ModelVersionInfo(
            name=name,
            current_version="production" if ready else None,
            candidate_version=None,
            current_metrics={},
            candidate_metrics=None,
            can_promote=False,
            can_rollback=False,
            current_path=str(pinned) if ready else None,
            note="Tabular CFR JSON — re-run solve preflop to update.",
        )

    if name == "student_multiway":
        root = Path("artifacts/student")
        current = _read_current(root) or ("multiway_v1" if (root / "multiway_v1").is_dir() else None)
        versions = [v for v in _list_version_dirs(root) if v.startswith("multiway") or v == "multiway_v1"]
        if (root / "multiway_v1").is_dir() and "multiway_v1" not in versions:
            versions.append("multiway_v1")
        cur_dir = root / current if current else None
        metrics = _read_metrics(cur_dir) if cur_dir and cur_dir.is_dir() else {}
        return ModelVersionInfo(
            name=name,
            current_version=current,
            candidate_version=None,
            current_metrics=metrics,
            candidate_metrics=None,
            can_promote=False,
            can_rollback=bool((root / "PREVIOUS").is_file()),
            current_path=str(cur_dir) if cur_dir else None,
        )

    if name == "student_hu":
        root = Path("artifacts/student")
        current = _read_current(root) or ("v1" if (root / "v1").is_dir() else None)
        cur_dir = root / current if current else None
        metrics = _read_metrics(cur_dir) if cur_dir and cur_dir.is_dir() else {}
        versions = _list_version_dirs(root)
        candidate = next((v for v in versions if v != current), None)
        cand_metrics = _read_metrics(root / candidate) if candidate else None
        return ModelVersionInfo(
            name=name,
            current_version=current,
            candidate_version=candidate,
            current_metrics=metrics,
            candidate_metrics=cand_metrics,
            can_promote=candidate is not None and bool(cand_metrics),
            can_rollback=bool((root / "PREVIOUS").is_file()),
            current_path=str(cur_dir) if cur_dir else None,
        )

    root = REGISTRY.get(name, Path(f"artifacts/{name}"))
    current = _read_current(root)
    versions = _list_version_dirs(root)
    candidate = next((v for v in versions if v != current), None)
    cur_dir = root / current if current else None
    return ModelVersionInfo(
        name=name,
        current_version=current,
        candidate_version=candidate,
        current_metrics=_read_metrics(cur_dir) if cur_dir and cur_dir.is_dir() else {},
        candidate_metrics=_read_metrics(root / candidate) if candidate else None,
        can_promote=candidate is not None,
        can_rollback=bool((root / "PREVIOUS").is_file()),
        current_path=str(cur_dir) if cur_dir else None,
    )


def list_models() -> list[ModelVersionInfo]:
    names = [
        "hhformer",
        "student_hu",
        "student_multiway",
        "student_play_study_hu",
        "student_play_study_multiway",
        "preflop_hu",
        "preflop_6max",
        "preflop_8max",
        "preflop_9max",
        "preflop_10max",
        "style_encoder",
        "solver_cache",
    ]
    return [get_model_info(n) for n in names]


def promote(
    name: str,
    *,
    confirm: bool = False,
    skip_gates: bool = False,
) -> ModelVersionInfo:
    if not confirm:
        msg = "Promotion requires confirm=True (and drift/league gates in production)."
        raise ValueError(msg)
    if not skip_gates:
        from poker_ai.learn.promotion_gates import evaluate_promotion_gates

        report = evaluate_promotion_gates(name)
        if not report.can_promote:
            blocking = ", ".join(report.blocking) or "gates failed"
            raise ValueError(f"Promotion gates blocked for {name}: {blocking}")
    info = get_model_info(name)
    if not info.candidate_version:
        raise ValueError(f"No candidate version for {name}")
    root = REGISTRY.get(name, Path(f"artifacts/{name}"))
    if name == "student_hu":
        root = Path("artifacts/student")
    prev = _read_current(root)
    if prev:
        (root / "PREVIOUS").write_text(prev, encoding="utf-8")
    _current_file(root).write_text(info.candidate_version, encoding="utf-8")
    return get_model_info(name)


def rollback(name: str) -> ModelVersionInfo:
    root = REGISTRY.get(name, Path(f"artifacts/{name}"))
    if name == "student_hu":
        root = Path("artifacts/student")
    prev_file = root / "PREVIOUS"
    if not prev_file.is_file():
        raise ValueError(f"No previous version recorded for {name}")
    prev = prev_file.read_text(encoding="utf-8").strip()
    current = _read_current(root)
    _current_file(root).write_text(prev, encoding="utf-8")
    if current:
        prev_file.write_text(current, encoding="utf-8")
    return get_model_info(name)
