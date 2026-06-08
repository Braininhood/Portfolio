"""v2 Stream D — diagnostics jobs API parity smoke test."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = os.environ.get("POKER_AI_API", "http://127.0.0.1:8000")

JOB_TYPES = (
    "policy_bench",
    "solve_kuhn",
    "features_hhformer_embed",
    "opponents_eval_exploit",
    "aivat_audit",
)


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{API}{path}", timeout=30) as resp:
        return json.loads(resp.read().decode())


def _post_job(job_type: str, params: dict | None = None) -> str:
    body = json.dumps({"type": job_type, "params": params or {}}).encode()
    req = urllib.request.Request(
        f"{API}/jobs",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    return str(data.get("job_id", ""))


def main() -> int:
    errors: list[str] = []
    try:
        _get("/league/checkpoints")
    except urllib.error.HTTPError as exc:
        errors.append(f"GET /league/checkpoints: {exc.code}")

    for jt in JOB_TYPES:
        try:
            params: dict = {}
            if jt == "policy_bench":
                params = {"samples": 50}
            elif jt == "solve_kuhn":
                params = {"iters": 1000}
            elif jt == "features_hhformer_embed":
                params = {"max_hands": 10}
            elif jt == "opponents_eval_exploit":
                params = {"hands": 50}
            elif jt == "aivat_audit":
                params = {"hands": 100}
            job_id = _post_job(jt, params)
            if not job_id:
                errors.append(f"POST /jobs {jt}: no job_id")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode() if exc.fp else ""
            if exc.code == 409:
                print(f"SKIP {jt}: job already running")
                continue
            errors.append(f"POST /jobs {jt}: {exc.code} {body[:120]}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1
    print(f"OK: checkpoints + {len(JOB_TYPES)} job types accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
