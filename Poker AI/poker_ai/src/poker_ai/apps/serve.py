"""``poker_ai serve`` — local API + Vite dashboard (Phase 10)."""

from __future__ import annotations

import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Annotated, Any

_DEFAULT_API_PORTS = (8000, 8765, 8001, 8080)

import typer


def _repo_root() -> Path:
    # serve.py → apps → poker_ai → src → project root
    return Path(__file__).resolve().parents[4]


def _api_dir() -> Path:
    return _repo_root() / "apps" / "api"


def _web_dir() -> Path:
    return _repo_root() / "apps" / "web"


def _can_bind(host: str, port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
    except OSError:
        return False


def _resolve_api_port(host: str, preferred: int) -> int:
    """Pick a port we can bind to (preferred first, then fallbacks)."""
    candidates = (preferred, *(p for p in _DEFAULT_API_PORTS if p != preferred))
    for port in candidates:
        if _can_bind(host, port):
            if port != preferred:
                typer.echo(
                    f"Port {preferred} is busy or blocked — using {port} instead "
                    f"(or stop the other process: netstat -ano | findstr :{preferred})",
                )
            return port
    typer.echo(
        f"No free API port among {list(candidates)}. "
        "Stop other Poker AI / Python servers or pass --api-port <number>.",
        err=True,
    )
    raise typer.Exit(code=1)


def _api_ready(host: str, port: int, timeout_sec: float = 90.0) -> bool:
    """Poll ``/health`` until the API accepts connections."""
    url = f"http://{host}:{port}/health"
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.5)
    return False


def _popen_kwargs() -> dict[str, Any]:
    """Windows: new process group so we can taskkill the full tree on exit."""
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {}


def _kill_process_tree(proc: subprocess.Popen[Any] | None) -> None:
    """Stop uvicorn --reload (parent + worker) and npm dev."""
    if proc is None:
        return
    pid = proc.pid
    if proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
    else:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def serve_cmd(
    host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
    api_port: Annotated[int, typer.Option("--api-port", min=1)] = 8000,
    web_port: Annotated[int, typer.Option("--web-port", min=1)] = 5173,
    no_web: Annotated[bool, typer.Option("--no-web", help="API only (skip Vite).")] = False,
    reload: Annotated[
        bool,
        typer.Option(
            "--reload/--no-reload",
            help="Reload API on code changes (extra process; harder to stop on Windows).",
        ),
    ] = False,
) -> None:
    """Run FastAPI (uvicorn) and optionally the Vite dev server."""
    api_dir = _api_dir()
    main_py = api_dir / "main.py"
    if not main_py.is_file():
        typer.echo(f"API not found: {main_py}", err=True)
        raise typer.Exit(code=1)

    try:
        import uvicorn  # noqa: F401
    except ImportError:
        typer.echo("Install API deps: pip install -e '.[api]' from poker_ai/", err=True)
        raise typer.Exit(code=1) from None

    src = _repo_root() / "poker_ai" / "src"
    env = os.environ.copy()
    py_path = os.pathsep.join([str(src), str(api_dir), env.get("PYTHONPATH", "")]).strip(os.pathsep)
    env["PYTHONPATH"] = py_path
    env.setdefault("POKER_AI_API_CORS_ORIGINS", f"http://{host}:{web_port},http://127.0.0.1:{web_port}")

    api_port = _resolve_api_port(host, api_port)

    api_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--app-dir",
        str(api_dir),
        "--host",
        host,
        "--port",
        str(api_port),
        "--log-level",
        "info",
    ]
    if reload:
        api_cmd.extend(
            [
                "--reload",
                "--reload-dir",
                str(api_dir),
                "--reload-dir",
                str(src),
            ]
        )
    typer.echo(f"Starting API: http://{host}:{api_port} (docs /docs)")
    if reload:
        typer.echo("API reload ON — use --no-reload for easier Ctrl+C on Windows.")
    typer.echo("Job progress logs stream below on stderr ([job type id] …).")
    popen_kw = _popen_kwargs()
    api_proc: subprocess.Popen[Any] = subprocess.Popen(
        api_cmd,
        cwd=str(_repo_root() / "poker_ai"),
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr,
        **popen_kw,
    )
    typer.echo("Waiting for API (migrations can take a minute on first start)…")
    if api_proc.poll() is not None or not _api_ready(host, api_port):
        typer.echo(f"API failed to start on port {api_port}. Check errors above.", err=True)
        _kill_process_tree(api_proc)
        raise typer.Exit(code=1)
    typer.echo(f"API ready: http://{host}:{api_port}")

    dist_dir = _web_dir() / "dist"
    static_built = dist_dir.is_dir() and (dist_dir / "index.html").is_file()
    if no_web and static_built:
        typer.echo(f"Serving dashboard from build: http://{host}:{api_port}/status")
    elif no_web:
        typer.echo(
            "No apps/web/dist — run: cd apps/web && npm install && npm run build "
            "(or start without --no-web for Vite dev).",
        )

    web_proc: subprocess.Popen[Any] | None = None
    if not no_web:
        web = _web_dir()
        npm = shutil.which("npm")
        if npm is None:
            typer.echo("npm not found — run with --no-web or install Node.js", err=True)
            _kill_process_tree(api_proc)
            raise typer.Exit(code=1)
        if not (web / "node_modules").is_dir():
            typer.echo("Installing web deps (npm install)…")
            subprocess.run([npm, "install"], cwd=str(web), check=True)
        web_env = env.copy()
        web_env["VITE_API_BASE_URL"] = f"http://{host}:{api_port}"
        web_env["VITE_WS_BASE_URL"] = f"ws://{host}:{api_port}"
        web_env["VITE_API_PORT"] = str(api_port)
        web_cmd = [npm, "run", "dev", "--", "--host", host, "--port", str(web_port)]
        typer.echo(f"Starting dashboard: http://{host}:{web_port}")
        web_proc = subprocess.Popen(web_cmd, cwd=str(web), env=web_env, **popen_kw)
    elif static_built:
        import webbrowser

        dashboard_url = f"http://{host}:{api_port}/status"
        typer.echo(f"Opening {dashboard_url}")
        webbrowser.open(dashboard_url)

    typer.echo("Press Ctrl+C once to stop (may take a few seconds on Windows).")

    stop_requested = False

    def _shutdown_all() -> None:
        nonlocal stop_requested
        if stop_requested:
            return
        stop_requested = True
        typer.echo("\nStopping API and web servers…")
        _kill_process_tree(web_proc)
        _kill_process_tree(api_proc)

    try:
        while not stop_requested and api_proc.poll() is None:
            if web_proc is not None and web_proc.poll() is not None:
                typer.echo("Web server exited.", err=True)
                break
            time.sleep(0.25)
        if api_proc.poll() is not None and web_proc is not None and web_proc.poll() is None:
            typer.echo(
                f"API stopped on port {api_port} (Vite will show ECONNREFUSED on /api).",
                err=True,
            )
    except KeyboardInterrupt:
        _shutdown_all()
    finally:
        _shutdown_all()
    typer.echo("Stopped.")

