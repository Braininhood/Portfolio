"""Versioned Parquet/JSONL dataset snapshots for reproducible training (Phase 11 / W8)."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DatasetSnapshot:
    version: str
    num_hands: int
    num_features: int
    content_hash: str
    features_path: str
    created_at: str
    is_active: bool = False


def _processed_root() -> Path:
    return Path("data/processed")


def _active_path() -> Path:
    return _processed_root() / "ACTIVE.json"


def _manifest_path(version_dir: Path) -> Path:
    return version_dir / "manifest.json"


def _hash_file(path: Path, *, max_bytes: int = 512 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        while True:
            chunk = fp.read(65536)
            if not chunk:
                break
            h.update(chunk)
            if fp.tell() >= max_bytes and fp.read(1):
                h.update(str(path.stat().st_size).encode())
                break
    return h.hexdigest()


def _count_jsonl_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    n = 0
    with path.open(encoding="utf-8") as fp:
        for line in fp:
            if line.strip():
                n += 1
    return n


def get_active_version() -> str | None:
    p = _active_path()
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        v = data.get("version")
        return str(v) if v else None
    except (json.JSONDecodeError, OSError):
        return None


def set_active_version(version: str) -> DatasetSnapshot:
    snaps = {s.version: s for s in list_snapshots()}
    if version not in snaps:
        raise ValueError(f"Unknown snapshot version '{version}'")
    _processed_root().mkdir(parents=True, exist_ok=True)
    _active_path().write_text(
        json.dumps({"version": version, "updated_at": datetime.now(tz=UTC).isoformat()}, indent=2),
        encoding="utf-8",
    )
    return snaps[version]


def features_path_for_version(version: str | None = None) -> Path | None:
    """Resolve features.jsonl for training — active snapshot or latest."""
    v = version or get_active_version()
    if v:
        candidate = _processed_root() / f"v{v}" / "features.jsonl"
        if candidate.is_file():
            return candidate
    legacy = Path("features.jsonl")
    return legacy if legacy.is_file() else None


def record_snapshot(source: Path, *, version: str | None = None) -> DatasetSnapshot:
    """Copy features file into ``data/processed/v<date>/`` and write manifest."""
    if not source.is_file():
        raise FileNotFoundError(f"Features file not found: {source}")

    day = version or datetime.now(tz=UTC).strftime("%Y-%m-%d")
    dest_dir = _processed_root() / f"v{day}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / "features.jsonl"

    if source.resolve() != dest_file.resolve():
        shutil.copy2(source, dest_file)

    num_features = _count_jsonl_lines(dest_file)
    content_hash = _hash_file(dest_file)
    created_at = datetime.now(tz=UTC).isoformat()
    manifest = {
        "version": day,
        "num_hands": num_features,
        "num_features": num_features,
        "content_hash": content_hash,
        "features_path": str(dest_file),
        "created_at": created_at,
        "source": str(source.resolve()),
    }
    _manifest_path(dest_dir).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    active = get_active_version()
    if active is None:
        set_active_version(day)

    return DatasetSnapshot(
        version=day,
        num_hands=num_features,
        num_features=num_features,
        content_hash=content_hash,
        features_path=str(dest_file),
        created_at=created_at,
        is_active=get_active_version() == day,
    )


def _snapshot_from_manifest(manifest_path: Path, *, active: str | None) -> DatasetSnapshot | None:
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        version = str(data["version"])
        features_path = str(data.get("features_path") or manifest_path.parent / "features.jsonl")
        return DatasetSnapshot(
            version=version,
            num_hands=int(data.get("num_hands") or data.get("num_features") or 0),
            num_features=int(data.get("num_features") or data.get("num_hands") or 0),
            content_hash=str(data.get("content_hash", "")),
            features_path=features_path,
            created_at=str(data.get("created_at", "")),
            is_active=active == version,
        )
    except (json.JSONDecodeError, KeyError, OSError, TypeError):
        return None


def list_snapshots() -> list[DatasetSnapshot]:
    """All recorded snapshots, newest first."""
    root = _processed_root()
    active = get_active_version()
    out: list[DatasetSnapshot] = []

    if root.is_dir():
        for child in sorted(root.iterdir(), reverse=True):
            if not child.is_dir() or not child.name.startswith("v"):
                continue
            manifest = _manifest_path(child)
            if manifest.is_file():
                snap = _snapshot_from_manifest(manifest, active=active)
                if snap:
                    out.append(snap)

    legacy = Path("features.jsonl")
    if legacy.is_file() and not any(s.features_path.endswith("features.jsonl") and Path(s.features_path).resolve() == legacy.resolve() for s in out):
        day = datetime.fromtimestamp(legacy.stat().st_mtime, tz=UTC).strftime("%Y-%m-%d")
        out.insert(
            0,
            DatasetSnapshot(
                version=f"{day} (live)",
                num_hands=_count_jsonl_lines(legacy),
                num_features=_count_jsonl_lines(legacy),
                content_hash=_hash_file(legacy)[:16],
                features_path=str(legacy.resolve()),
                created_at=datetime.fromtimestamp(legacy.stat().st_mtime, tz=UTC).isoformat(),
                is_active=active is None,
            ),
        )

    return out


def ensure_snapshots_from_disk() -> list[DatasetSnapshot]:
    """Register any v* dirs missing manifests (migration helper)."""
    root = _processed_root()
    if not root.is_dir():
        return list_snapshots()
    for child in root.iterdir():
        if not child.is_dir() or not child.name.startswith("v"):
            continue
        feat = child / "features.jsonl"
        manifest = _manifest_path(child)
        if feat.is_file() and not manifest.is_file():
            version = child.name[1:]  # strip v
            record_snapshot(feat, version=version)
    return list_snapshots()
