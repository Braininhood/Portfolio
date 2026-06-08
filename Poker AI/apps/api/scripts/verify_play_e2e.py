"""Browser E2E — Play vs AI page (Phase W7 / W12).

Requires API + built SPA on :8000 and Playwright:

    cd poker_ai
    uv sync --extra dev
    uv run playwright install chromium
    uv run python ../apps/api/scripts/verify_play_e2e.py

Or from repo root after ``npm run build`` in apps/web and ``python -m poker_ai serve --no-web``.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, ContextManager, cast

_API_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _API_DIR.parents[1]
_SRC = _REPO_ROOT / "poker_ai" / "src"
for p in (_SRC, _API_DIR):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

API = os.environ.get("POKER_AI_API", "http://127.0.0.1:8000")
BASE = API.rstrip("/")


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=30) as resp:
        return json.loads(resp.read().decode())


def _report(checks: list[tuple[str, bool, str]]) -> None:
    ok = sum(1 for _, passed, _ in checks if passed)
    print(f"\nPlay E2E: {ok}/{len(checks)} passed\n")
    for name, passed, detail in checks:
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}] {name}: {detail}")
    print()


def _load_sync_playwright() -> Callable[[], ContextManager[Any]] | None:
    """Playwright is optional (``uv sync --extra dev``); load at runtime only."""
    try:
        mod = importlib.import_module("playwright.sync_api")
    except ImportError:
        return None
    sync_playwright = getattr(mod, "sync_playwright", None)
    if not callable(sync_playwright):
        return None
    return cast(Callable[[], ContextManager[Any]], sync_playwright)


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    sync_playwright = _load_sync_playwright()
    if sync_playwright is None:
        checks.append(
            (
                "playwright installed",
                False,
                "pip install playwright && playwright install chromium",
            )
        )
        _report(checks)
        return 1

    dist = _REPO_ROOT / "apps" / "web" / "dist" / "index.html"
    if not dist.is_file():
        checks.append(("web dist built", False, f"missing {dist}"))
        _report(checks)
        return 1
    checks.append(("web dist built", True, str(dist)))

    try:
        status = _get("/status")
        checks.append(("GET /status", True, status.get("version", "ok")))
    except Exception as exc:
        checks.append(("GET /status", False, str(exc)))
        _report(checks)
        return 1

    page_url = f"{BASE}/play"
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(page_url, wait_until="networkidle", timeout=60_000)
            title = page.title()
            checks.append(("navigate /play", "Poker" in title or page.locator("body").count() > 0, title))

            body = page.locator("body").inner_text(timeout=15_000)
            checks.append(
                (
                    "play page renders",
                    "play" in body.lower() or "seat" in body.lower() or "bot" in body.lower(),
                    f"{len(body)} chars",
                )
            )

            sw_resp = page.request.get(f"{BASE}/sw.js")
            checks.append(
                (
                    "service worker asset",
                    sw_resp.ok and "serviceWorker" not in sw_resp.text()[:80].lower(),
                    f"HTTP {sw_resp.status}",
                )
            )

            # Start session via API then reload play (session in URL optional)
            sess = json.loads(
                urllib.request.urlopen(
                    urllib.request.Request(
                        f"{BASE}/play/sessions",
                        data=json.dumps(
                            {
                                "seats": 2,
                                "user_seat": 0,
                                "bots": ["fish", "tag"],
                                "buy_in_bb": 100,
                                "small_blind_bb": 0.5,
                                "big_blind_bb": 1.0,
                                "ante_bb": 0.0,
                                "timeout_ms": 10000,
                            }
                        ).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    ),
                    timeout=60,
                ).read().decode()
            )
            sid = sess.get("session_id")
            checks.append(("POST /play/sessions", bool(sid), f"session_id={sid}"))

            if sid:
                page.goto(f"{page_url}?session={sid}", wait_until="networkidle", timeout=60_000)
                checks.append(
                    (
                        "play session UI",
                        page.locator("button").count() >= 1,
                        f"buttons={page.locator('button').count()}",
                    )
                )
        except Exception as exc:
            checks.append(("browser flow", False, str(exc)))
        finally:
            browser.close()

    _report(checks)
    return 0 if all(p for _, p, _ in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
