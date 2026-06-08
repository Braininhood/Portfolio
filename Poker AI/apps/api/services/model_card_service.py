"""Resolve MODEL_CARD.md for GET /models/{name}/card (Phase W9)."""

from __future__ import annotations

from pathlib import Path

from poker_ai.learn.model_registry import REGISTRY, get_model_info

# API name aliases → registry name
_ALIASES: dict[str, str] = {
    "hhformer": "hhformer",
    "student": "student_hu",
    "student_hu": "student_hu",
    "student_multiway": "student_multiway",
    "preflop_hu": "preflop_hu",
    "preflop_6max": "preflop_6max",
    "style_encoder": "style_encoder",
    "solver_cache": "solver_cache",
}

_FALLBACK_CARDS: dict[str, Path] = {
    "hhformer": Path("artifacts/hhformer/v1/MODEL_CARD.md"),
    "student_hu": Path("artifacts/student/v1/MODEL_CARD.md"),
    "student_multiway": Path("artifacts/student/multiway_v1/MODEL_CARD.md"),
    "preflop_hu": Path("artifacts/solver/preflop_hu/MODEL_CARD.md"),
    "preflop_6max": Path("artifacts/solver/preflop_6max/MODEL_CARD.md"),
    "style_encoder": Path("artifacts/style_encoder/v1/MODEL_CARD.md"),
    "solver_cache": Path("artifacts/solver_cache/MODEL_CARD.md"),
}


def resolve_model_card(name: str) -> tuple[Path, str | None]:
    """Return (path, version) or raise FileNotFoundError."""
    reg_name = _ALIASES.get(name, name)
    if reg_name not in REGISTRY and reg_name not in _FALLBACK_CARDS:
        msg = f"unknown model {name!r}"
        raise FileNotFoundError(msg)

    info = get_model_info(reg_name)
    version = info.current_version
    candidates: list[Path] = []

    if info.current_path:
        p = Path(info.current_path)
        if p.is_file():
            candidates.append(p.parent / "MODEL_CARD.md")
        elif p.is_dir():
            candidates.append(p / "MODEL_CARD.md")

    fb = _FALLBACK_CARDS.get(reg_name)
    if fb is not None:
        candidates.append(fb)

    root = REGISTRY.get(reg_name)
    if root is not None:
        cur = root / "CURRENT"
        if cur.is_file():
            ver = cur.read_text(encoding="utf-8").strip()
            candidates.append(root / ver / "MODEL_CARD.md")
        candidates.append(root / "v1" / "MODEL_CARD.md")

    for path in candidates:
        if path.is_file():
            return path, version

    msg = f"MODEL_CARD.md not found for {name!r}"
    raise FileNotFoundError(msg)
