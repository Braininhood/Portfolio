"""Terminal logging for background jobs and API startup (stderr, always visible)."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

_CONFIGURED = False


def configure_serve_logging(*, level: int = logging.INFO) -> None:
    """Attach a stderr handler so job + library logs appear in the serve terminal."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            reconfigure = getattr(stream, "reconfigure", None)
            if callable(reconfigure):
                try:
                    reconfigure(encoding="utf-8")
                except Exception:
                    pass

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(fmt)
    handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers on reload
    if not any(
        isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stderr
        for h in root.handlers
    ):
        root.addHandler(handler)

    for name in (
        "poker_ai",
        "poker_ai.solver",
        "services",
        "services.job_runner",
        "services.terminal_log",
        "uvicorn.error",
        "alembic",
        "alembic.runtime.migration",
    ):
        logging.getLogger(name).setLevel(level if not name.startswith("alembic") else logging.WARNING)


def log_job_line(job_id: str, job_type: str, message: str, *, level: int = logging.INFO) -> None:
    """One line on stderr: ``[job solve_preflop ab12cd34] message``."""
    short = job_id[:8] if len(job_id) > 8 else job_id
    line = f"[job {job_type} {short}] {message}"
    print(line, file=sys.stderr, flush=True)
    logging.getLogger("services.job_runner").log(level, "%s — %s", job_type, message)


def log_job_progress(job_id: str, job_type: str, event: dict[str, Any]) -> None:
    """Mirror WebSocket progress to the terminal."""
    pct = event.get("pct")
    msg = str(event.get("msg") or "").strip()
    detail = event.get("detail")
    if pct is not None:
        head = f"{int(pct):>3}%"
    else:
        head = "   "
    parts = [head, msg] if msg else [head]
    if detail and isinstance(detail, dict) and detail:
        try:
            extra = json.dumps(detail, default=str, separators=(",", ":"))
            if len(extra) > 120:
                extra = extra[:117] + "..."
            parts.append(extra)
        except TypeError:
            parts.append(str(detail)[:120])
    log_job_line(job_id, job_type, " ".join(parts).strip())


def log_job_params(job_id: str, job_type: str, params: dict[str, Any]) -> None:
    """Log job parameters (truncated) at start."""
    try:
        blob = json.dumps(params, default=str, separators=(",", ":"))
    except TypeError:
        blob = str(params)
    if len(blob) > 400:
        blob = blob[:397] + "..."
    log_job_line(job_id, job_type, f"params {blob}")
