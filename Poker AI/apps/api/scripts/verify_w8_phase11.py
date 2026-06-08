"""W8 Phase 11 verification — drift, models, schedule, snapshots (Day 38).

Usage (API running on :8000)::

    cd poker_ai
    python ../apps/api/scripts/verify_w8_phase11.py
    python scripts/verify_w8_phase11.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(os.path.dirname(_API_DIR))
_SRC = os.path.join(_REPO_ROOT, "poker_ai", "src")
for p in (_SRC, _API_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

API = os.environ.get("POKER_AI_API", "http://127.0.0.1:8000")


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{API}{path}", timeout=30) as resp:
        return json.loads(resp.read().decode())


def _post(path: str, body: dict | None = None) -> dict:
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _report(checks: list[tuple[str, bool, str]]) -> None:
    print("\n=== W8 Phase 11 verification ===\n")
    ok = 0
    for name, passed, detail in checks:
        mark = "OK" if passed else "FAIL"
        print(f"  [{mark}] {name}")
        if detail:
            print(f"         {detail}")
        if passed:
            ok += 1
    print(f"\n{ok}/{len(checks)} checks passed.\n")


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    try:
        health = _get("/health")
        checks.append(("GET /health", health.get("status") == "ok", str(health)))
    except Exception as exc:
        checks.append(("GET /health", False, str(exc)))
        _report(checks)
        return 1

    try:
        drift = _get("/drift/reports")
        n = len(drift.get("reports") or [])
        checks.append(("GET /drift/reports", True, f"{n} report(s), latest={drift.get('latest_status')}"))
    except Exception as exc:
        checks.append(("GET /drift/reports", False, str(exc)))

    try:
        cp = _get("/drift/changepoints")
        checks.append(("GET /drift/changepoints", True, f"{len(cp.get('alerts') or [])} alert(s)"))
    except Exception as exc:
        checks.append(("GET /drift/changepoints", False, str(exc)))

    try:
        models = _get("/models")
        names = [m.get("name") for m in models.get("models") or []]
        checks.append(
            (
                "GET /models",
                "student_hu" in names and "student_multiway" in names,
                f"{len(names)} models",
            )
        )
    except Exception as exc:
        checks.append(("GET /models", False, str(exc)))

    try:
        sched = _get("/jobs/schedule")
        checks.append(
            (
                "GET /jobs/schedule",
                True,
                f"nightly={sched.get('nightly_enabled')} entries={len(sched.get('entries') or [])}",
            )
        )
    except Exception as exc:
        checks.append(("GET /jobs/schedule", False, str(exc)))

    try:
        snaps = _get("/setup/snapshots")
        checks.append(
            (
                "GET /setup/snapshots",
                True,
                f"{len(snaps.get('snapshots') or [])} snapshot(s), active={snaps.get('active_version')}",
            )
        )
    except Exception as exc:
        checks.append(("GET /setup/snapshots", False, str(exc)))

    # Library smoke (no API)
    try:
        from poker_ai.observability.drift import run_drift_check

        tmp = Path("data/drift/_verify_smoke")
        tmp.mkdir(parents=True, exist_ok=True)
        meta = run_drift_check(output_dir=tmp)
        checks.append(("drift.run_drift_check", (tmp / meta.filename).is_file(), meta.status))
    except Exception as exc:
        checks.append(("drift.run_drift_check", False, str(exc)))

    try:
        from poker_ai.learn.model_registry import list_models

        checks.append(("model_registry.list_models", len(list_models()) >= 7, ""))
    except Exception as exc:
        checks.append(("model_registry.list_models", False, str(exc)))

    try:
        from poker_ai.learn.dataset_versioning import list_snapshots

        checks.append(("dataset_versioning.list_snapshots", True, f"{len(list_snapshots())} listed"))
    except Exception as exc:
        checks.append(("dataset_versioning.list_snapshots", False, str(exc)))

    try:
        prof = _get("/players?limit=1")
        players = prof.get("players") or []
        if players:
            uid = players[0]["player_uid"]
            detail = _get(f"/players/{urllib.parse.quote(uid, safe='')}/profile")
            has_cp_field = "changepoint" in detail
            checks.append(("GET /players/{uid}/profile changepoint field", has_cp_field, uid[:12]))
        else:
            checks.append(("GET /players/{uid}/profile changepoint field", True, "no players — skipped"))
    except Exception as exc:
        checks.append(("GET /players/{uid}/profile changepoint field", False, str(exc)))

    _report(checks)
    return 0 if all(c[1] for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
