"""Feature drift reports — poker-relevant shifts only (Phase 11 / W8)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# IDs and row metadata — never count toward yellow/red.
DRIFT_SKIP_FOR_FLAGGING: frozenset[str] = frozenset(
    {
        "hand_id",
    }
)

FEATURE_CATALOG: dict[str, dict[str, str]] = {
    "range_l1": {
        "label": "Hero range concentration",
        "meaning": (
            "How “peaked” the encoded hero hand range is per row (near 1.0 = one hand type; "
            "lower = more mixed / uniform encoding). Shifts can mean different hole-card "
            "patterns or sites in newer imports."
        ),
        "advice_when_flagged": (
            "Compare old vs new imports on Import. Re-run **Prepare hands for AI**, check "
            "**Dataset snapshots** on Setup, and wait for a green drift report before "
            "**Promote** on the Models page."
        ),
    },
}

INFORMATIONAL_FEATURES: dict[str, dict[str, str]] = {
    "hand_id": {
        "label": "Hand ID (technical)",
        "meaning": (
            "Internal row number — grows every time you import hands. A large “shift” here "
            "usually means the library got bigger, not that the player pool changed."
        ),
        "note": "Shown for transparency; does not affect green / yellow / red.",
    },
}


@dataclass(frozen=True, slots=True)
class DriftReportMeta:
    date: str
    filename: str
    features_flagged: int
    status: str
    created_at: str


def _status_from_flagged(n: int) -> str:
    if n == 0:
        return "green"
    if n <= 2:
        return "yellow"
    return "red"


def _summary_advice(status: str, flagged: int, rows: list[dict[str, Any]]) -> str:
    if status == "green":
        return (
            "Your prepared training data looks stable between the older and newer halves "
            "of features.jsonl. Safe to continue training and consider model promotion "
            "after league checks."
        )
    flagged_names = [
        str(r.get("label") or r.get("feature") or "")
        for r in rows
        if r.get("flagged")
    ]
    names = ", ".join(flagged_names) if flagged_names else "key poker features"
    if status == "yellow":
        return (
            f"Moderate drift on {names}. Review what changed in your hand library (new site, "
            f"stakes, or batch import), refresh features, and re-run this check before promoting models."
        )
    return (
        f"Strong drift on {names}. Pause automatic nightly retrain promotion, import or "
        "filter hands intentionally, re-run **Prepare hands for AI**, then confirm green here."
    )


def list_drift_reports(output_dir: Path = Path("data/drift")) -> list[DriftReportMeta]:
    if not output_dir.is_dir():
        return []
    out: list[DriftReportMeta] = []
    for p in sorted(output_dir.glob("drift_*.html"), reverse=True):
        stem = p.stem.replace("drift_", "")
        meta_path = output_dir / f"drift_{stem}.json"
        flagged = 0
        created = datetime.fromtimestamp(p.stat().st_mtime, tz=UTC).isoformat()
        status = "green"
        if meta_path.is_file():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                flagged = int(meta.get("poker_features_flagged", meta.get("features_flagged", 0)))
                created = str(meta.get("created_at", created))
                status = str(meta.get("status", _status_from_flagged(flagged)))
            except (json.JSONDecodeError, OSError):
                pass
        out.append(
            DriftReportMeta(
                date=stem[:10] if len(stem) >= 10 else stem,
                filename=p.name,
                features_flagged=flagged,
                status=status,
                created_at=created,
            )
        )
    return out


def load_report_detail(date: str, output_dir: Path = Path("data/drift")) -> dict[str, Any] | None:
    """Structured report for the web UI (from sidecar JSON)."""
    for stem in (date, date[:10]):
        meta_path = output_dir / f"drift_{stem}.json"
        if meta_path.is_file():
            try:
                return json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return None
    return None


def _catalog_for(col: str) -> dict[str, str]:
    if col in FEATURE_CATALOG:
        return FEATURE_CATALOG[col]
    if col in INFORMATIONAL_FEATURES:
        return INFORMATIONAL_FEATURES[col]
    return {
        "label": col.replace("_", " ").title(),
        "meaning": "Numeric field from features.jsonl — compare older vs newer hands in your library.",
        "advice_when_flagged": "Re-run Prepare hands for AI and check whether a large new import changed this statistic.",
    }


def _drift_from_features_jsonl(
    path: Path,
    *,
    flagged: int,
    rows: list[dict[str, Any]],
    max_features: int = 20,
    min_rows: int = 50,
    shift_threshold: float = 0.15,
) -> tuple[list[dict[str, Any]], int]:
    """Compare first vs second half means; only poker-relevant columns affect status."""
    records: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, dict):
                records.append(obj)
    except (OSError, json.JSONDecodeError):
        rows.append(
            {
                "feature": path.name,
                "label": "Features file",
                "note": "Could not parse features JSONL.",
                "flagged": False,
                "counts_toward_status": False,
            }
        )
        return rows, flagged

    if len(records) < min_rows:
        rows.append(
            {
                "feature": path.name,
                "label": "Not enough data",
                "note": f"Need at least {min_rows} prepared hands. Run Prepare hands for AI on Setup.",
                "flagged": False,
                "counts_toward_status": False,
            }
        )
        return rows, flagged

    numeric_keys: list[str] = []
    for key in records[0]:
        if key == "tensor" or key == "range":
            continue
        if all(
            isinstance(r.get(key), (int, float)) and not isinstance(r.get(key), bool)
            for r in records[: min(100, len(records))]
        ):
            numeric_keys.append(key)

    mid = len(records) // 2
    ref_slice = records[:mid]
    cur_slice = records[mid:]

    for col in numeric_keys[:max_features]:
        ref_vals = [float(r[col]) for r in ref_slice if isinstance(r.get(col), (int, float))]
        cur_vals = [float(r[col]) for r in cur_slice if isinstance(r.get(col), (int, float))]
        if not ref_vals or not cur_vals:
            continue
        ref_mean = sum(ref_vals) / len(ref_vals)
        cur_mean = sum(cur_vals) / len(cur_vals)
        shift = abs(cur_mean - ref_mean) / (abs(ref_mean) + 1e-6)
        catalog = _catalog_for(col)
        counts = col not in DRIFT_SKIP_FOR_FLAGGING
        is_flagged = counts and shift > shift_threshold
        if is_flagged:
            flagged += 1
        row: dict[str, Any] = {
            "feature": col,
            "label": catalog.get("label", col),
            "meaning": catalog.get("meaning", catalog.get("note", "")),
            "shift": round(shift, 4),
            "ref_mean": round(ref_mean, 4),
            "cur_mean": round(cur_mean, 4),
            "flagged": is_flagged,
            "counts_toward_status": counts,
        }
        if is_flagged and "advice_when_flagged" in catalog:
            row["advice"] = catalog["advice_when_flagged"]
        if not counts and col in INFORMATIONAL_FEATURES:
            row["note"] = INFORMATIONAL_FEATURES[col].get("note", "")
        rows.append(row)

    return rows, flagged


def run_drift_check(
    *,
    output_dir: Path = Path("data/drift"),
    features_path: Path | None = None,
) -> DriftReportMeta:
    """Build drift HTML + JSON from features.jsonl (poker-relevant flags only)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    date = datetime.now(tz=UTC).strftime("%Y-%m-%d")
    flagged = 0
    rows: list[dict[str, Any]] = []

    feat = features_path or Path("features.jsonl")
    hands_compared = 0
    if feat.is_file():
        rows, flagged = _drift_from_features_jsonl(feat, flagged=flagged, rows=rows)
        try:
            hands_compared = sum(1 for ln in feat.read_text(encoding="utf-8").splitlines() if ln.strip())
        except OSError:
            hands_compared = 0

    status = _status_from_flagged(flagged)
    summary_advice = _summary_advice(status, flagged, rows)

    html = [
        "<html><head><meta charset='utf-8'><title>Drift report</title>",
        "<style>body{font-family:sans-serif;margin:1rem} table{border-collapse:collapse}",
        "td,th{border:1px solid #ccc;padding:6px} .flag{background:#fff3cd}",
        ".info{color:#666;font-size:0.9em}</style></head><body>",
        f"<h1>Drift report {date}</h1>",
        f"<p>Status: <strong>{status.upper()}</strong> — {flagged} poker-relevant feature(s) flagged.</p>",
        f"<p class='info'>{summary_advice}</p>",
        "<p class='info'><em>Compared older half vs newer half of your prepared features file "
        f"({hands_compared:,} hands). Hand ID shifts are ignored for status.</em></p>",
        "<table><tr><th>Feature</th><th>Older avg</th><th>Newer avg</th><th>Shift</th><th>Counts?</th></tr>",
    ]
    for r in rows[:30]:
        cls = "flag" if r.get("flagged") else ""
        counts = "Yes" if r.get("counts_toward_status") else "No (info only)"
        html.append(
            f"<tr class='{cls}'><td><strong>{r.get('label', r.get('feature'))}</strong>"
            f"<br><span class='info'>{r.get('meaning', '')}</span></td>"
            f"<td>{r.get('ref_mean', '—')}</td><td>{r.get('cur_mean', '—')}</td>"
            f"<td>{r.get('shift', r.get('note', ''))}</td><td>{counts}</td></tr>"
        )
    html.append("</table></body></html>")

    filename = f"drift_{date}.html"
    out_html = output_dir / filename
    out_html.write_text("\n".join(html), encoding="utf-8")
    created_at = datetime.now(tz=UTC).isoformat()
    meta: dict[str, Any] = {
        "date": date,
        "poker_features_flagged": flagged,
        "features_flagged": flagged,
        "status": status,
        "created_at": created_at,
        "hands_compared": hands_compared,
        "summary_advice": summary_advice,
        "method": (
            "Splits features.jsonl into older vs newer halves. Only poker-relevant numeric "
            "columns (not hand_id) affect green/yellow/red."
        ),
        "features": rows,
    }
    (output_dir / f"drift_{date}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return DriftReportMeta(
        date=date,
        filename=filename,
        features_flagged=flagged,
        status=status,
        created_at=created_at,
    )
