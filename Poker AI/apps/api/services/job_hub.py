"""In-process job progress fan-out: WebSocket subscribers + SQLite persistence (Phase W1)."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poker_ai.store import jobs_store

logger = logging.getLogger(__name__)


def _json_dumps(data: dict[str, Any]) -> str:
    return json.dumps(data, separators=(",", ":"))


class JobProgressHub:
    """Thread-safe bridge: worker threads → main asyncio loop → DB + WebSockets."""

    _PERSIST_INTERVAL_SEC = 1.0

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._thread_lock = threading.Lock()
        self._ws_by_job: dict[str, set[WebSocket]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._last_persist: dict[str, float] = {}
        self._latest: dict[str, dict[str, Any]] = {}

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def latest_progress(self, job_id: str) -> dict[str, Any] | None:
        with self._thread_lock:
            return self._latest.get(job_id)

    async def register(self, job_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._ws_by_job.setdefault(job_id, set()).add(ws)

    async def unregister(self, job_id: str, ws: WebSocket) -> None:
        async with self._lock:
            subs = self._ws_by_job.get(job_id)
            if not subs:
                return
            subs.discard(ws)
            if not subs:
                del self._ws_by_job[job_id]

    async def _broadcast_ws(self, job_id: str, event: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        async with self._lock:
            targets = list(self._ws_by_job.get(job_id, ()))
        for ws in targets:
            try:
                await ws.send_json(event)
            except WebSocketDisconnect:
                dead.append(ws)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.unregister(job_id, ws)

    async def emit(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        job_id: str,
        event: dict[str, Any],
        persist_progress: bool = True,
    ) -> None:
        """Persist last progress snapshot and push to subscribers."""
        with self._thread_lock:
            self._latest[job_id] = event
        if persist_progress and "status" not in event:
            now = time.monotonic()
            last = self._last_persist.get(job_id, 0.0)
            if now - last >= self._PERSIST_INTERVAL_SEC:
                self._last_persist[job_id] = now
                try:
                    jobs_store.sync_update_progress(job_id, _json_dumps(event))
                except Exception:
                    logger.warning("progress persist failed for job %s", job_id, exc_info=True)
        await self._broadcast_ws(job_id, event)

    def emit_from_worker(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        job_id: str,
        event: dict[str, Any],
    ) -> None:
        """Called from executor threads; sync persist + marshal WS to the API event loop."""
        with self._thread_lock:
            self._latest[job_id] = event
        if "status" not in event:
            now = time.monotonic()
            last = self._last_persist.get(job_id, 0.0)
            if now - last >= self._PERSIST_INTERVAL_SEC:
                self._last_persist[job_id] = now
                try:
                    jobs_store.sync_update_progress(job_id, _json_dumps(event))
                except Exception:
                    logger.warning("sync progress persist failed for job %s", job_id, exc_info=True)
        loop = self._loop
        if loop is None or not loop.is_running():
            return
        fut = asyncio.run_coroutine_threadsafe(
            self._broadcast_ws(job_id, event),
            loop,
        )
        fut.add_done_callback(
            lambda f: f.exception() and logger.warning("WS broadcast failed", exc_info=f.exception())
        )


hub = JobProgressHub()
