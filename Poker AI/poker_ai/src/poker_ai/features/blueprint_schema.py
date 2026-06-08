"""Blueprint v2 feature column schema — source of truth for extended JSONL / Parquet."""

from __future__ import annotations

from dataclasses import dataclass

BLUEPRINT_VERSION = "v2"

# Base columns (always present in features.jsonl)
BASE_COLUMNS: tuple[str, ...] = (
    "hand_id",
    "info_set_key",
    "tensor",
    "range",
    "range_l1",
)

# Extended columns when ``blueprint_full=True``
EXTENDED_COLUMNS: tuple[str, ...] = (
    "blueprint_version",
    "num_players",
    "big_blind",
    "board_texture",
    "student_extras",
    "hero_net_bb",
    "hero_showdown",
)

ALL_COLUMNS: tuple[str, ...] = BASE_COLUMNS + EXTENDED_COLUMNS


@dataclass(frozen=True, slots=True)
class ColumnSpec:
    name: str
    dtype: str
    shape: str
    description: str


COLUMN_SPECS: tuple[ColumnSpec, ...] = (
    ColumnSpec("hand_id", "int64", "scalar", "Canonical hand id in poker_ai.db"),
    ColumnSpec("info_set_key", "string", "scalar", "Stable CFR info-set key"),
    ColumnSpec("tensor", "float64", "(52,)", "Flat info-set tensor"),
    ColumnSpec("range", "float64", "(1326,)", "Hero range vector"),
    ColumnSpec("range_l1", "float64", "scalar", "L1 norm of range vector"),
    ColumnSpec("blueprint_version", "string", "scalar", "Feature schema version (v2)"),
    ColumnSpec("num_players", "int64", "scalar", "Seats dealt"),
    ColumnSpec("big_blind", "float64", "scalar", "Big blind in currency units"),
    ColumnSpec("board_texture", "int16", "(16,)", "Board texture embedding"),
    ColumnSpec("student_extras", "float64", "(N,)", "SPR / pot odds / table buckets"),
    ColumnSpec("hero_net_bb", "float64", "scalar", "Hero net result in big blinds"),
    ColumnSpec("hero_showdown", "bool", "scalar", "Hero reached showdown"),
)


def validate_row(row: dict[str, object], *, blueprint_full: bool) -> list[str]:
    """Return list of validation errors (empty = OK)."""
    errors: list[str] = []
    required = ALL_COLUMNS if blueprint_full else BASE_COLUMNS
    for col in required:
        if col not in row:
            errors.append(f"missing column {col!r}")
    if "tensor" in row:
        t = row["tensor"]
        if not isinstance(t, (list, tuple)) or len(t) != 52:
            errors.append(f"tensor length {len(t) if isinstance(t, (list, tuple)) else '?'} != 52")
    if blueprint_full and row.get("blueprint_version") != BLUEPRINT_VERSION:
        errors.append(f"blueprint_version must be {BLUEPRINT_VERSION!r}")
    return errors
