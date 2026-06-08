"""Persist promoted main-agent checkpoints for league_exploiter training (Phase 9)."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LeagueCheckpoint:
    checkpoint_id: str
    created_at: str
    main_elo: float
    hands: int
    promoted: bool
    student_hu_dir: str | None
    student_multiway_dir: str | None
    note: str = ""


def _root() -> Path:
    return Path("artifacts/league/checkpoints")


def _index_path() -> Path:
    return _root() / "index.json"


def list_checkpoints() -> list[LeagueCheckpoint]:
    p = _index_path()
    if not p.is_file():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    out: list[LeagueCheckpoint] = []
    for row in raw.get("checkpoints") or []:
        if not isinstance(row, dict):
            continue
        out.append(
            LeagueCheckpoint(
                checkpoint_id=str(row.get("checkpoint_id", "")),
                created_at=str(row.get("created_at", "")),
                main_elo=float(row.get("main_elo") or 0.0),
                hands=int(row.get("hands") or 0),
                promoted=bool(row.get("promoted")),
                student_hu_dir=row.get("student_hu_dir"),
                student_multiway_dir=row.get("student_multiway_dir"),
                note=str(row.get("note") or ""),
            )
        )
    return out


def _read_index() -> dict[str, object]:
    p = _index_path()
    if not p.is_file():
        return {"checkpoints": [], "current": None}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {"checkpoints": [], "current": None}


def _write_index(data: dict[str, object]) -> None:
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    _index_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def register_checkpoint(
    *,
    main_elo: float,
    hands: int,
    promoted: bool,
    student_hu: Path | None = None,
    student_multiway: Path | None = None,
    note: str = "",
) -> LeagueCheckpoint:
    """Snapshot current student dirs and append to checkpoint index."""
    ts = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    cid = f"main_{ts}"
    dest = _root() / cid
    dest.mkdir(parents=True, exist_ok=True)

    hu_dest: Path | None = None
    mw_dest: Path | None = None
    if student_hu is not None and student_hu.is_dir():
        hu_dest = dest / "student_hu"
        if hu_dest.exists():
            shutil.rmtree(hu_dest)
        shutil.copytree(student_hu, hu_dest)
    if student_multiway is not None and student_multiway.is_dir():
        mw_dest = dest / "student_multiway"
        if mw_dest.exists():
            shutil.rmtree(mw_dest)
        shutil.copytree(student_multiway, mw_dest)

    meta = {
        "checkpoint_id": cid,
        "created_at": datetime.now(tz=UTC).isoformat(),
        "main_elo": main_elo,
        "hands": hands,
        "promoted": promoted,
        "student_hu_dir": str(hu_dest) if hu_dest else None,
        "student_multiway_dir": str(mw_dest) if mw_dest else None,
        "note": note,
    }
    (dest / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    idx = _read_index()
    raw_rows = idx.get("checkpoints")
    rows: list[object] = list(raw_rows) if isinstance(raw_rows, list) else []
    rows.insert(0, meta)
    idx["checkpoints"] = rows[:50]
    if promoted:
        idx["current"] = cid
    _write_index(idx)

    return LeagueCheckpoint(
        checkpoint_id=cid,
        created_at=str(meta["created_at"]),
        main_elo=main_elo,
        hands=hands,
        promoted=promoted,
        student_hu_dir=meta["student_hu_dir"],
        student_multiway_dir=meta["student_multiway_dir"],
        note=note,
    )


def current_checkpoint_id() -> str | None:
    idx = _read_index()
    cur = idx.get("current")
    return str(cur) if cur else None
