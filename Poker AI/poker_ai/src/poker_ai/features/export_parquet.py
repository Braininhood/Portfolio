"""Export features.jsonl to versioned Parquet snapshots (blueprint v2)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from poker_ai.features.blueprint_schema import ALL_COLUMNS, BLUEPRINT_VERSION


class BlueprintValidationReport(TypedDict):
    hands_checked: int
    schema_ok: bool
    errors: list[str]
    blueprint_full: bool


class ParquetExportResult(TypedDict):
    num_rows: int
    version: str
    parquet_path: str
    manifest_path: str


def export_features_parquet(
    source: Path,
    *,
    since: str | None = None,
    out_dir: Path | None = None,
) -> ParquetExportResult:
    """Write ``data/processed/v<date>/features.parquet`` + manifest."""
    if not source.is_file():
        raise FileNotFoundError(f"Features file not found: {source}")

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        msg = "pyarrow required for Parquet export (pip install pyarrow)"
        raise RuntimeError(msg) from exc

    version = datetime.now(tz=UTC).strftime("%Y%m%d")
    if since:
        version = since.replace("-", "")[:8] or version
    dest_dir = out_dir or Path("data/processed") / f"v{version}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = dest_dir / "features.parquet"

    rows: list[dict[str, object]] = []
    with source.open(encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    if not rows:
        raise ValueError("features.jsonl is empty")

    table = pa.Table.from_pylist(rows)
    pq.write_table(table, parquet_path)

    manifest = {
        "version": version,
        "blueprint_version": BLUEPRINT_VERSION,
        "columns": list(ALL_COLUMNS),
        "num_rows": len(rows),
        "source": str(source.resolve()),
        "parquet_path": str(parquet_path.resolve()),
        "created_at": datetime.now(tz=UTC).isoformat(),
    }
    manifest_path = dest_dir / "FEATURE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "num_rows": len(rows),
        "version": version,
        "parquet_path": str(parquet_path.resolve()),
        "manifest_path": str(manifest_path.resolve()),
    }


def validate_blueprint_file(path: Path, *, blueprint_full: bool = False) -> BlueprintValidationReport:
    """Round-trip validate JSONL rows against blueprint schema."""
    from poker_ai.features.blueprint_schema import validate_row

    if not path.is_file():
        raise FileNotFoundError(path)
    n = 0
    errors: list[str] = []
    with path.open(encoding="utf-8") as fp:
        for i, line in enumerate(fp, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            n += 1
            row_errs = validate_row(row, blueprint_full=blueprint_full)
            for e in row_errs:
                errors.append(f"line {i}: {e}")
            if len(errors) >= 20:
                break
    return {
        "hands_checked": n,
        "schema_ok": len(errors) == 0,
        "errors": errors[:20],
        "blueprint_full": blueprint_full,
    }
