"""FastAPI application — Phase 10 realtime API."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure ``poker_ai`` (editable install) and ``apps/api`` imports resolve.
_API_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _API_DIR.parents[1]
_SRC = _REPO_ROOT / "poker_ai" / "src"
for p in (_SRC, _API_DIR):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import (
    blueprint,
    compliance,
    decide,
    drill,
    equity,
    hands,
    health,
    health_check,
    ingest,
    jobs,
    league,
    licenses,
    play,
    players,
    drift,
    models_registry,
    replay,
    sim,
    smoke,
    solver,
    setup,
    status,
    system_paths,
)
from services.job_hub import hub
from services.job_runner import release_orphaned_jobs
from services.terminal_log import configure_serve_logging

configure_serve_logging()

from poker_ai.store.db import get_async_session_factory
from poker_ai.store.migrate import upgrade_head


@asynccontextmanager
async def _lifespan(app: FastAPI):
    import asyncio

    upgrade_head()
    hub.set_loop(asyncio.get_running_loop())
    factory = get_async_session_factory()
    n = await release_orphaned_jobs(factory)
    if n:
        import logging

        logging.getLogger(__name__).info("Released %s orphaned background task(s) on startup", n)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Poker AI API",
        version="0.1.0",
        description="Local-first decision, replay, and league dashboard API (no outbound calls).",
        lifespan=_lifespan,
    )
    origins = os.environ.get(
        "POKER_AI_API_CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    allow = [o.strip() for o in origins if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _cors_headers(request: Request) -> dict[str, str]:
        origin = request.headers.get("origin")
        if origin and origin in allow:
            return {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
            }
        return {}

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        """JSON errors for unexpected failures (browser hides 500 bodies without CORS)."""
        cors = _cors_headers(request)
        if isinstance(exc, HTTPException):
            hdrs = {**(getattr(exc, "headers", None) or {}), **cors}
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=hdrs or None,
            )
        return JSONResponse(status_code=500, content={"detail": str(exc)}, headers=cors)

    app.include_router(health.router)
    app.include_router(smoke.router)
    app.include_router(health_check.router)
    app.include_router(licenses.router)
    app.include_router(compliance.router)
    app.include_router(status.router)
    app.include_router(system_paths.router)
    app.include_router(ingest.router)
    app.include_router(setup.router)
    app.include_router(jobs.router)
    app.include_router(decide.router)
    app.include_router(drill.router)
    app.include_router(equity.router)
    app.include_router(hands.router)
    app.include_router(replay.router)
    app.include_router(league.router)
    app.include_router(blueprint.router)
    app.include_router(sim.router)
    app.include_router(play.router)
    app.include_router(players.router)
    app.include_router(drift.router)
    app.include_router(models_registry.router)
    app.include_router(solver.router)

    _mount_favicon(app)
    _mount_spa_if_built(app)
    return app


def _mount_favicon(app: FastAPI) -> None:
    """Avoid 404 noise when the browser requests /favicon.ico (API-only or SPA mode)."""
    from fastapi.responses import FileResponse

    candidates = [
        _API_DIR.parent / "web" / "public" / "favicon.svg",
        _API_DIR.parent / "web" / "dist" / "favicon.svg",
        _API_DIR.parent / "web" / "dist" / "favicon.ico",
    ]

    @app.get("/favicon.ico", include_in_schema=False)
    async def _favicon() -> FileResponse:
        for path in candidates:
            if path.is_file():
                media = "image/svg+xml" if path.suffix == ".svg" else "image/x-icon"
                return FileResponse(path, media_type=media)
        raise HTTPException(status_code=404, detail="favicon not found")


def _mount_spa_if_built(app: FastAPI) -> None:
    """Serve ``apps/web/dist`` when present (production / ``--no-web`` install)."""
    dist_dir = _API_DIR.parent / "web" / "dist"
    if not dist_dir.is_dir():
        return
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="spa")


app = create_app()
