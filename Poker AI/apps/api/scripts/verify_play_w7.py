"""W7 verification — Play vs AI API + coaching + decide game_state path.

Usage (from repo root, with API running on :8000)::

    cd poker_ai
    python ../apps/api/scripts/verify_play_w7.py
    python scripts/verify_play_w7.py   # shim in poker_ai/scripts/
"""

from __future__ import annotations

import json
import os
import sys
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


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{API}{path}", timeout=30) as resp:
        return json.loads(resp.read().decode())


def _post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    try:
        status = _get("/status")
        checks.append(("GET /status", True, f"ok — {status.get('version', 'api')}"))
    except Exception as exc:
        checks.append(("GET /status", False, str(exc)))
        _report(checks)
        return 1

    try:
        bots = _get("/play/bots")
        n_bots = len(bots.get("bots") or [])
        checks.append(("GET /play/bots", n_bots >= 5, f"{n_bots} bots"))
    except Exception as exc:
        checks.append(("GET /play/bots", False, str(exc)))

    sid: str | None = None
    try:
        sess = _post(
            "/play/sessions",
            {
                "seats": 6,
                "user_seat": 0,
                "bots": ["fish", "tag", "random", "lag", "distilled_gto"],
                "buy_in_bb": 100,
                "small_blind_bb": 0.5,
                "big_blind_bb": 1.0,
                "ante_bb": 0.0,
                "timeout_ms": 10000,
            },
        )
        sid = sess.get("session_id")
        checks.append(("POST /play/sessions", bool(sid), f"session_id={sid}"))
    except Exception as exc:
        checks.append(("POST /play/sessions", False, str(exc)))
        _report(checks)
        return 1

    try:
        detail = _get(f"/play/sessions/{sid}")
        checks.append(("GET /play/sessions/{{id}}", detail.get("session") is not None, "detail ok"))
    except Exception as exc:
        checks.append(("GET /play/sessions/{id}", False, str(exc)))

    try:
        study = _get("/play/study/status")
        checks.append(
            (
                "GET /play/study/status",
                "hero_decisions" in study,
                f"hands={study.get('hands', 0)} decisions={study.get('hero_decisions', 0)}",
            )
        )
    except Exception as exc:
        checks.append(("GET /play/study/status", False, str(exc)))

    manifest = Path(_REPO_ROOT) / "artifacts" / "play_study" / "manifest.json"
    if manifest.is_file():
        checks.append(("play_study manifest", True, str(manifest.resolve())))
    else:
        checks.append(("play_study manifest", True, "not materialized — run POST /play/study/prepare"))

    try:
        from poker_ai.learn.play_study_loader import collect_play_study_stats, load_play_study_student_rows

        stats = collect_play_study_stats()
        rows = load_play_study_student_rows(manifest_path=manifest) if manifest.is_file() else []
        checks.append(
            (
                "play_study_loader -> StudentRow",
                True,
                f"decisions={stats.get('hero_decisions', 0)} rows={len(rows)}",
            )
        )
    except Exception as exc:
        checks.append(("play_study_loader", False, str(exc)))

    try:
        from services.play_coaching import session_summary_payload

        class _FakeSession:
            config = type(
                "C",
                (),
                {
                    "seats": 6,
                    "buy_in_bb": 100,
                    "ante_bb": 0,
                    "small_blind_bb": 0.5,
                    "big_blind_bb": 1.0,
                },
            )()

            def session_stats(self):
                return {"hands": 2, "net_bb": 3.0, "vpip_pct": 50.0, "pfr_pct": 25.0}

            completed_hands = [
                {"opponent_bb": {"fish": 5.0, "tag": -2.0}},
                {"opponent_bb": {"fish": 3.0, "tag": 1.0}},
            ]

        summary = session_summary_payload(_FakeSession(), showdown_wins=1, showdown_hands=1)
        opp = summary.get("opponent_results") or []
        has_breakdown = len(opp) >= 2 and any(o["bot_id"] == "fish" for o in opp)
        checks.append(("Session opponent BB breakdown", has_breakdown, f"{len(opp)} opponents"))
    except Exception as exc:
        checks.append(("Session opponent BB breakdown", False, str(exc)))

    try:
        from services.decide_service import run_decide_for_state
        from services.play_session_snapshot import game_state_from_dict, game_state_to_dict
        from poker_ai.policy.bench import _postflop_state

        state = _postflop_state()
        encoded = game_state_to_dict(state)
        restored = game_state_from_dict(encoded)
        result = run_decide_for_state(restored, policy_name="heuristic")
        has_actions = bool(result.get("actions"))
        checks.append(
            ("POST /decide game_state path", has_actions, f"{len(result.get('actions') or [])} actions")
        )
    except Exception as exc:
        checks.append(("POST /decide game_state path", False, str(exc)))

    try:
        end = _post(f"/play/sessions/{sid}/end", {})
        summary = end.get("summary") or {}
        checks.append(
            (
                "POST /play/sessions/{id}/end",
                end.get("status") == "finished",
                f"net_bb={summary.get('net_bb')} opponents={len(summary.get('opponent_results') or [])}",
            )
        )
    except Exception as exc:
        checks.append(("POST /play/sessions/{id}/end", False, str(exc)))

    return _report(checks)


def _report(checks: list[tuple[str, bool, str]]) -> int:
    failed = 0
    for name, ok, detail in checks:
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {name}: {detail}")
        if not ok:
            failed += 1
    if failed:
        print(f"\n{failed} check(s) failed.")
        return 1
    print(f"\nAll {len(checks)} W7 API checks passed.")
    print("\n--- Manual browser checklist (Day 30 item #8) ---")
    print("1. Open http://127.0.0.1:5173/play — 6-max, Fish+TAG+Random+LAG+GTO")
    print("2. Play 5 hands — confirm timer ring counts down and auto fold/check fires")
    print("3. Reach showdown — villain hole cards flip on the felt + detail panel")
    print("4. Enable AI hints — bar appears ~200ms after your turn (POST /decide)")
    print("5. End session — summary shows VPIP/PFR, opponent BB chips, View hand history")
    print("6. Study panel — Train student from play hands (needs 5+ hero decisions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
