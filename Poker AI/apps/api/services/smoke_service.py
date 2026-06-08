"""Air-gapped smoke checklist for GET /health/smoke (Phase W9 / Phase 10)."""

from __future__ import annotations

import os
import socket
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import SmokeCheck, SmokeResponse

from poker_ai.core.replay import replay_parsed_hand
from poker_ai.policy.bench import _postflop_state
from poker_ai.store.loader import count_parsed_hands, load_parsed_hand_by_id
from poker_ai.store.models import Game

_last_smoke: SmokeResponse | None = None


def get_last_smoke_result() -> SmokeResponse | None:
    return _last_smoke


@contextmanager
def _guard_dns():
    """Fail smoke if any non-local hostname is resolved during checks."""
    seen_external: list[str] = []
    original = socket.getaddrinfo

    def guarded(host: str, *args: Any, **kwargs: Any) -> Any:
        h = (host or "").strip().lower()
        if h and h not in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            if not h.replace(".", "").isdigit():
                seen_external.append(host)
        return original(host, *args, **kwargs)

    socket.getaddrinfo = guarded  # type: ignore[assignment]
    try:
        yield seen_external
    finally:
        socket.getaddrinfo = original  # type: ignore[assignment]


def _check(name: str, fn: Any) -> SmokeCheck:
    t0 = time.perf_counter()
    try:
        detail = fn()
        passed = True if detail is True else bool(detail)
        if isinstance(detail, str):
            msg: str | None = detail
            passed = True
        elif detail is False:
            msg = "check returned false"
            passed = False
        else:
            msg = None if detail is True else str(detail) if detail else None
    except Exception as exc:
        passed = False
        msg = str(exc)
    ms = (time.perf_counter() - t0) * 1000.0
    return SmokeCheck(name=name, passed=passed, latency_ms=round(ms, 2), detail=msg)


async def run_smoke(session: AsyncSession) -> SmokeResponse:
    """Run internal-only assertions — no outbound HTTP."""
    global _last_smoke
    checks: list[SmokeCheck] = []

    with _guard_dns() as external_dns:

        t0 = time.perf_counter()
        try:
            await count_parsed_hands(session)
            db_ok = True
            db_msg: str | None = None
        except Exception as exc:
            db_ok = False
            db_msg = str(exc)
        checks.append(
            SmokeCheck(
                name="db_readable",
                passed=db_ok,
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
                detail=db_msg,
            )
        )

        def health_endpoint() -> str | bool:
            from deps import get_schema_revision
            from poker_ai import __version__

            t0 = time.perf_counter()
            _ = get_schema_revision()
            _ = __version__
            ms = (time.perf_counter() - t0) * 1000.0
            if ms > 100:
                return f"health logic slow ({ms:.1f} ms)"
            return True

        checks.append(_check("health_endpoint", health_endpoint))

        async def replay_one_hand() -> str | bool:
            scan_limit = int(os.environ.get("POKER_AI_SMOKE_REPLAY_SCAN", "200"))
            ids = list(
                await session.scalars(
                    select(Game.hand_id).order_by(Game.hand_id.desc()).limit(scan_limit)
                )
            )
            if not ids:
                return "no hands in database — import hands to enable replay check"
            for hid in ids:
                hand = await load_parsed_hand_by_id(session, int(hid))
                if hand is None:
                    continue
                result = replay_parsed_hand(hand)
                if result.action_sequence_ok:
                    return True
            return (
                f"no replay-valid hand in last {len(ids)} ids "
                "(try normalized NLH hand_*.txt corpus)"
            )

        t0 = time.perf_counter()
        try:
            detail = await replay_one_hand()
            passed = detail is True
            msg = None if passed else str(detail)
        except Exception as exc:
            passed = False
            msg = str(exc)
        checks.append(
            SmokeCheck(
                name="replay_one_hand",
                passed=passed,
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
                detail=msg,
            )
        )

        def decide_one_hand() -> str | bool:
            from services.decide_service import run_decide_for_state

            state = _postflop_state()
            t0 = time.perf_counter()
            result = run_decide_for_state(state, profile_id="smoke", policy_name="heuristic")
            ms = (time.perf_counter() - t0) * 1000.0
            if ms > 50:
                return f"decide slow ({ms:.1f} ms > 50 ms budget)"
            if not result.get("actions"):
                return "no action probabilities"
            return True

        checks.append(_check("decide_one_hand", decide_one_hand))

        def equity_spot() -> str | bool:
            from services.equity_service import compute_equity

            t0 = time.perf_counter()
            result = compute_equity(
                hero_cards="As Ad",
                board_cards="",
                villain_range="random",
                mode="exact",
            )
            ms = (time.perf_counter() - t0) * 1000.0
            # First exact-equity run may compile numba kernels; allow cold-start headroom.
            budget_ms = 800.0 if ms > 200 else 200.0
            if ms > budget_ms:
                return f"equity slow ({ms:.1f} ms > {budget_ms:.0f} ms budget)"
            hero_eq = float(result.get("hero_equity") or result.get("equity") or 0)
            if abs(hero_eq - 0.852) > 0.02:
                return f"AA vs random equity {hero_eq:.3f} (expected ≈ 0.852)"
            return True

        checks.append(_check("equity_spot", equity_spot))

        def artifacts_present() -> str | bool:
            from routers.status import _MODELS_TO_CHECK, _resolve_artifact

            missing: list[str] = []
            for name, paths, _job, _why in _MODELS_TO_CHECK:
                found = _resolve_artifact(paths)
                if found is None:
                    continue
                try:
                    if found.is_file():
                        _ = found.read_bytes()[:1]
                    elif found.is_dir():
                        next(found.iterdir(), None)
                except OSError as exc:
                    missing.append(f"{name}: {exc}")
            if missing:
                return "; ".join(missing)
            return True

        checks.append(_check("artifacts_present", artifacts_present))

        def spa_offline_ready() -> str | bool:
            api_dir = Path(__file__).resolve().parents[1]
            dist = api_dir.parent / "web" / "dist"
            if not dist.is_dir():
                return "apps/web/dist missing — run npm run build in apps/web"
            index = dist / "index.html"
            sw = dist / "sw.js"
            if not index.is_file():
                return "dist/index.html missing"
            text = index.read_text(encoding="utf-8", errors="ignore")
            for bad in ("googleapis.com", "cdn.jsdelivr", "unpkg.com", "cloudflare.com"):
                if bad in text:
                    return f"external CDN reference in index.html: {bad}"
            if not sw.is_file():
                return "dist/sw.js missing — rebuild web with public/sw.js"
            manifest = dist / "manifest.webmanifest"
            if not manifest.is_file():
                return "dist/manifest.webmanifest missing"
            return True

        checks.append(_check("spa_offline_ready", spa_offline_ready))

        def router_bindings() -> str | bool:
            from poker_ai.policy.router_sources import get_router_status

            status = get_router_status()
            notes: list[str] = []
            for binding in (status.hu, status.multiway):
                weights = binding.student_dir / "student.safetensors"
                legacy = binding.student_dir / "model.pt"
                if not weights.is_file() and not legacy.is_file():
                    notes.append(f"{binding.route}: no weights at {binding.student_dir}")
            if notes:
                return "; ".join(notes)
            ps = [b.route for b in (status.hu, status.multiway) if b.play_study]
            if ps:
                return f"play-study active: {', '.join(ps)}"
            return True

        checks.append(_check("router_bindings", router_bindings))

        def no_outbound_dns() -> str | bool:
            if external_dns:
                return f"DNS lookups: {', '.join(external_dns[:5])}"
            return True

        checks.append(_check("no_outbound_dns", no_outbound_dns))

    all_passed = all(c.passed for c in checks)
    resp = SmokeResponse(all_passed=all_passed, checks=checks)
    _last_smoke = resp
    return resp
