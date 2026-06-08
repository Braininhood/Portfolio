"""Resolve HU / multi-way student dirs for ``RouterPolicy`` (Phase W7 + W10)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from poker_ai.config.settings import get_settings

RouterRoute = Literal["hu", "multiway"]
_STUDENT_ROOT = Path("artifacts/student")
_POINTER_FILES: dict[RouterRoute, str] = {
    "hu": "ROUTER_HU",
    "multiway": "ROUTER_MULTIWAY",
}
_PLAY_STUDY_DIRS: dict[RouterRoute, str] = {
    "hu": "play_study_hu_v1",
    "multiway": "play_study_multiway_v1",
}
_DEFAULT_DIRS: dict[RouterRoute, Path] = {
    "hu": Path("artifacts/student/v1"),
    "multiway": Path("artifacts/student/multiway_v1"),
}


@dataclass(frozen=True, slots=True)
class RouterBinding:
    route: RouterRoute
    student_dir: Path
    source: str
    play_study: bool


@dataclass(frozen=True, slots=True)
class RouterStatus:
    hu: RouterBinding
    multiway: RouterBinding

    def to_dict(self) -> dict[str, object]:
        return {
            "hu": {
                "student_dir": str(self.hu.student_dir),
                "source": self.hu.source,
                "play_study": self.hu.play_study,
            },
            "multiway": {
                "student_dir": str(self.multiway.student_dir),
                "source": self.multiway.source,
                "play_study": self.multiway.play_study,
            },
        }


def _student_weights_ready(student_dir: Path) -> bool:
    return (student_dir / "student.safetensors").is_file() or (student_dir / "model.pt").is_file()


def _read_pointer(route: RouterRoute) -> str | None:
    ptr = _STUDENT_ROOT / _POINTER_FILES[route]
    if not ptr.is_file():
        return None
    raw = ptr.read_text(encoding="utf-8").strip()
    return raw or None


def _resolve_dir_from_pointer(route: RouterRoute) -> Path | None:
    rel = _read_pointer(route)
    if not rel:
        return None
    candidate = (_STUDENT_ROOT / rel).resolve()
    if _student_weights_ready(candidate):
        return candidate
    return None


def resolve_router_student_dir(route: RouterRoute) -> Path:
    """Return the student artifact directory for ``route`` (pointer → settings → default)."""
    from_pointer = _resolve_dir_from_pointer(route)
    if from_pointer is not None:
        return from_pointer

    s = get_settings()
    if route == "hu":
        configured = s.student_artifact_dir
    else:
        configured = s.multiway_student_dir

    if _student_weights_ready(configured):
        return configured

    default = _DEFAULT_DIRS[route]
    if _student_weights_ready(default):
        return default
    return configured if configured.is_dir() else default


def get_router_binding(route: RouterRoute) -> RouterBinding:
    rel = _read_pointer(route)
    student_dir = resolve_router_student_dir(route)
    play_study_name = _PLAY_STUDY_DIRS[route]
    play_study = student_dir.name == play_study_name or rel == play_study_name
    if rel:
        source = f"pointer:{rel}"
    elif play_study:
        source = "play_study"
    elif student_dir == _DEFAULT_DIRS[route]:
        source = "default"
    else:
        source = "settings"
    return RouterBinding(route=route, student_dir=student_dir, source=source, play_study=play_study)


def get_router_status() -> RouterStatus:
    return RouterStatus(hu=get_router_binding("hu"), multiway=get_router_binding("multiway"))


def play_study_artifact_dir(route: RouterRoute) -> Path:
    return _STUDENT_ROOT / _PLAY_STUDY_DIRS[route]


def promote_play_study_to_router(
    *,
    hu: bool = True,
    multiway: bool = True,
    confirm: bool = False,
) -> RouterStatus:
    """Point router brains at play-study student weights when artifacts exist."""
    if not confirm:
        msg = "Promotion requires confirm=True after reviewing play-study metrics."
        raise ValueError(msg)

    promoted: list[str] = []
    for route, enabled in (("hu", hu), ("multiway", multiway)):
        if not enabled:
            continue
        src = play_study_artifact_dir(route)  # type: ignore[arg-type]
        if not _student_weights_ready(src):
            raise ValueError(
                f"Play-study {route} weights missing at {src} — run play/study train first."
            )
        rel = _PLAY_STUDY_DIRS[route]  # type: ignore[index]
        ptr = _STUDENT_ROOT / _POINTER_FILES[route]  # type: ignore[index]
        _STUDENT_ROOT.mkdir(parents=True, exist_ok=True)
        prev = _read_pointer(route)  # type: ignore[arg-type]
        if prev and prev != rel:
            backup = _STUDENT_ROOT / f"ROUTER_{route.upper()}_PREVIOUS"
            backup.write_text(prev, encoding="utf-8")
        ptr.write_text(rel, encoding="utf-8")
        promoted.append(route)

    if not promoted:
        raise ValueError("Nothing to promote — enable hu and/or multiway.")

    meta = _STUDENT_ROOT / "router_bindings.json"
    meta.write_text(
        json.dumps(
            {
                "promoted_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "routes": promoted,
                "play_study_dirs": {r: _PLAY_STUDY_DIRS[r] for r in promoted},  # type: ignore[index]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return get_router_status()


def rollback_router_play_study(route: RouterRoute) -> RouterStatus:
    """Restore router pointer from ROUTER_*_PREVIOUS if present."""
    backup = _STUDENT_ROOT / f"ROUTER_{route.upper()}_PREVIOUS"
    ptr = _STUDENT_ROOT / _POINTER_FILES[route]
    if not backup.is_file():
        raise ValueError(f"No previous router binding for {route}")
    prev = backup.read_text(encoding="utf-8").strip()
    current = _read_pointer(route)
    ptr.write_text(prev, encoding="utf-8")
    if current:
        backup.write_text(current, encoding="utf-8")
    return get_router_status()
