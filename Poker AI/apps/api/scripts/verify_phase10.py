"""Phase 10 exit criteria — decide latency, replayer sample, air-gap (no egress).

Usage (API on :8000)::

    python apps/api/scripts/verify_phase10.py
    cd poker_ai && python ../apps/api/scripts/verify_phase10.py

Dev with internet (skip air-gap probe)::

    set POKER_AI_SKIP_AIRGAP=1
"""

from __future__ import annotations

import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(os.path.dirname(_API_DIR))
_SRC = os.path.join(_REPO_ROOT, "poker_ai", "src")
for p in (_SRC, _API_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

API = os.environ.get("POKER_AI_API", "http://127.0.0.1:8000")
P99_LIMIT_MS = float(os.environ.get("POKER_AI_DECIDE_P99_MS", "30"))
_REPLAY_SCAN = int(os.environ.get("POKER_AI_VERIFY_REPLAY_SCAN", "50"))


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{API}{path}", timeout=60) as resp:
        return json.loads(resp.read().decode())


def _post(path: str, body: dict | None = None) -> dict:
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def _decide_fixture_body() -> dict:
    """Full ``game_state`` round-trip (same as W7 verify) or omit for server bench fixture."""
    use_fixture = os.environ.get("POKER_AI_VERIFY_DECIDE_FIXTURE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if not use_fixture:
        return {"profile_id": "hero", "policy": "distilled"}
    from poker_ai.policy.bench import _postflop_state

    from services.play_session_snapshot import game_state_to_dict

    return {
        "profile_id": "hero",
        "policy": "distilled",
        "game_state": game_state_to_dict(_postflop_state()),
    }


def _report(checks: list[tuple[str, bool, str]]) -> None:
    print("\n=== Phase 10 verification ===\n")
    ok = 0
    for name, passed, detail in checks:
        mark = "OK" if passed else "FAIL"
        print(f"  [{mark}] {name}")
        if detail:
            print(f"         {detail}")
        if passed:
            ok += 1
    print(f"\n{ok}/{len(checks)} checks passed.\n")


def _decide_p99_ms() -> tuple[float, str]:
    body = _decide_fixture_body()
    times: list[float] = []
    for _ in range(40):
        t0 = time.perf_counter()
        _post("/decide", body)
        times.append((time.perf_counter() - t0) * 1000.0)
    times.sort()
    p99 = times[int(len(times) * 0.99) - 1] if len(times) >= 2 else times[-1]
    return p99, f"p99={p99:.1f}ms limit={P99_LIMIT_MS}ms n={len(times)}"


def _find_replayable_hand() -> tuple[int | None, str]:
    """Pick a hand whose engine replay validates (newest ids first)."""
    hands = _get(f"/hands?limit={_REPLAY_SCAN}")
    items = hands.get("hands") or []
    if not items:
        return None, "no hands in index"
    for row in items:
        hid = row.get("hand_id")
        if hid is None:
            continue
        try:
            spot = _get(f"/replay/{hid}")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                continue
            raise
        if spot.get("action_sequence_ok") and (spot.get("actions") or spot.get("num_actions", 0)):
            n = len(spot.get("actions") or []) or int(spot.get("num_actions") or 0)
            return int(hid), f"hand_id={hid} actions={n} action_sequence_ok=true"
    return None, f"no replay-valid hand in first {len(items)} from GET /hands"


def _airgap_probe() -> tuple[bool, str]:
    """Fail if we can reach a public host (deny-egress sanity)."""
    if os.environ.get("POKER_AI_SKIP_AIRGAP", "").lower() in ("1", "true", "yes"):
        return True, "skipped (POKER_AI_SKIP_AIRGAP)"
    try:
        socket.create_connection(("1.1.1.1", 443), timeout=2.0)
        return False, "Outbound TCP to 1.1.1.1:443 succeeded — not air-gapped."
    except OSError:
        return True, "No outbound TCP to 1.1.1.1:443 (expected in air-gap)."


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
        p99, detail = _decide_p99_ms()
        checks.append((f"POST /decide p99 < {P99_LIMIT_MS}ms", p99 < P99_LIMIT_MS, detail))
    except Exception as exc:
        checks.append(("POST /decide latency", False, str(exc)))

    try:
        hid, detail = _find_replayable_hand()
        checks.append(("Replayer sample hand", hid is not None, detail))
    except Exception as exc:
        checks.append(("Replayer sample hand", False, str(exc)))

    try:
        ag, detail = _airgap_probe()
        checks.append(("Air-gap egress probe", ag, detail))
    except Exception as exc:
        checks.append(("Air-gap egress probe", False, str(exc)))

    try:
        smoke = _get("/health/smoke")
        passed = bool(smoke.get("all_passed", smoke.get("ok")))
        failed = [c["name"] for c in smoke.get("checks") or [] if not c.get("passed")]
        detail = f"all_passed={passed}"
        if failed:
            detail += f"; failed={','.join(failed)}"
        checks.append(("GET /health/smoke", passed, detail))
    except Exception as exc:
        checks.append(("GET /health/smoke", False, str(exc)))

    try:
        bench = _get("/sim/throughput?wall_sec=30&min_hands_per_minute=100")
        hpm = float(bench.get("hands_per_minute") or 0)
        passed = bool(bench.get("passed", hpm >= 100))
        checks.append(
            (
                "Sim throughput ≥ 100 hands/min",
                passed,
                f"hpm={hpm:.1f} hands={bench.get('hands')} elapsed={bench.get('elapsed_sec')}s",
            )
        )
    except Exception as exc:
        checks.append(("Sim throughput ≥ 100 hands/min", False, str(exc)))

    _report(checks)
    return 0 if all(c[1] for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
