"""Phase 12 install verification — timing + smoke after bootstrap.

Usage (after ``install.ps1`` / ``install.sh`` and ``poker_ai serve``)::

    python apps/api/scripts/verify_phase12_install.py

Records wall times for health, smoke, static dashboard, and sim throughput.
Fresh-VM ≤5 min is operator-timed; this script validates post-install readiness.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(os.path.dirname(_API_DIR))
_POKER_AI = os.path.join(_REPO_ROOT, "poker_ai")
_WEB_DIST = os.path.join(_REPO_ROOT, "apps", "web", "dist", "index.html")

API = os.environ.get("POKER_AI_API", "http://127.0.0.1:8000")
MAX_INSTALL_VERIFY_SEC = float(os.environ.get("POKER_AI_PHASE12_MAX_SEC", "300"))


def _get(path: str, timeout: float = 120.0) -> dict:
    with urllib.request.urlopen(f"{API}{path}", timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    t0 = time.perf_counter()
    checks: list[tuple[str, bool, str]] = []

    dist_ok = Path(_WEB_DIST).is_file()
    checks.append(("Dashboard build (apps/web/dist/index.html)", dist_ok, _WEB_DIST))

    try:
        t1 = time.perf_counter()
        health = _get("/health", timeout=10.0)
        dt = time.perf_counter() - t1
        checks.append(("GET /health", health.get("status") == "ok", f"{dt:.2f}s {health}"))
    except Exception as exc:
        checks.append(("GET /health", False, str(exc)))

    try:
        t1 = time.perf_counter()
        smoke = _get("/health/smoke", timeout=180.0)
        dt = time.perf_counter() - t1
        passed = bool(smoke.get("all_passed", smoke.get("ok")))
        checks.append(("GET /health/smoke", passed, f"{dt:.2f}s all_passed={passed}"))
    except Exception as exc:
        checks.append(("GET /health/smoke", False, str(exc)))

    try:
        t1 = time.perf_counter()
        bench = _get("/sim/throughput?wall_sec=15", timeout=60.0)
        dt = time.perf_counter() - t1
        hpm = float(bench.get("hands_per_minute") or 0)
        checks.append(
            (
                "GET /sim/throughput",
                hpm >= 100,
                f"{dt:.2f}s hpm={hpm:.1f}",
            )
        )
    except urllib.error.HTTPError as exc:
        checks.append(("GET /sim/throughput", False, f"HTTP {exc.code}"))
    except Exception as exc:
        checks.append(("GET /sim/throughput", False, str(exc)))

    elapsed = time.perf_counter() - t0
    within_budget = elapsed <= MAX_INSTALL_VERIFY_SEC
    checks.append(
        (
            f"Post-install verify wall ≤ {MAX_INSTALL_VERIFY_SEC:.0f}s",
            within_budget,
            f"elapsed={elapsed:.1f}s (VM install-to-dashboard target is ≤300s manual)",
        )
    )

    print("\n=== Phase 12 install verification ===\n")
    ok = 0
    for name, passed, detail in checks:
        mark = "OK" if passed else "FAIL"
        print(f"  [{mark}] {name}")
        if detail:
            print(f"         {detail}")
        if passed:
            ok += 1
    print(f"\n{ok}/{len(checks)} checks passed.\n")

    report = {
        "api": API,
        "elapsed_sec": round(elapsed, 2),
        "checks": [{"name": n, "passed": p, "detail": d} for n, p, d in checks],
    }
    out = Path(_POKER_AI) / "reports" / "phase12_install_verify.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report: {out}")

    return 0 if all(c[1] for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
