"""Health check endpoints.

GET /health/check  — structured first-load system check (OS · Python · DB · GPU · TexasSolver · Disk)
POST /texas/install — stream the output of `poker_ai solve install-texas` to the browser

Every warn/fail item includes exact fix commands for Windows, Linux, and macOS so
the web UI can show the right command for the user's OS without any guesswork.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_db, get_schema_revision
from schemas import HealthCheckItem, HealthCheckResponse
from services.hardware import detect_hardware
from poker_ai import __version__
from poker_ai.store.loader import count_parsed_hands

router = APIRouter(tags=["health"])

# Minimum free disk space in GB before showing a warning/error
_DISK_WARN_GB = 5.0
_DISK_FAIL_GB = 1.5


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def _check_os() -> HealthCheckItem:
    hw = detect_hardware()
    return HealthCheckItem(
        id="os",
        name="Operating system",
        status="pass",
        value=f"{hw.os_name} · {hw.cpu.arch}",
        can_skip=True,
    )


def _check_python() -> HealthCheckItem:
    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    minor = sys.version_info.minor
    major = sys.version_info.major
    if major < 3 or (major == 3 and minor < 11):
        return HealthCheckItem(
            id="python",
            name="Python environment",
            status="fail",
            value=f"Python {ver} — need 3.11+",
            advice="Python 3.11 or newer is required. Install it and recreate the virtual environment.",
            fix_windows="winget install Python.Python.3.11\nuv sync --all-extras",
            fix_linux="sudo apt install python3.11\nuv sync --all-extras",
            fix_macos="brew install python@3.11\nuv sync --all-extras",
            can_skip=False,
            docs_section="Phase W0 §1",
        )
    return HealthCheckItem(
        id="python",
        name="Python & poker_ai",
        status="pass",
        value=f"Python {ver} · poker_ai v{__version__}",
        can_skip=False,
    )


async def _check_database(session: AsyncSession) -> HealthCheckItem:
    current_rev = get_schema_revision()
    n_hands: int | None = None
    try:
        n_hands = await count_parsed_hands(session)
    except Exception:
        return HealthCheckItem(
            id="database",
            name="Database",
            status="fail",
            value="Cannot connect to database",
            advice="Run the database migration to create or upgrade the database.",
            fix_windows="python -m poker_ai db migrate",
            fix_linux="python -m poker_ai db migrate",
            fix_macos="python -m poker_ai db migrate",
            can_skip=False,
            docs_section="Phase W0 §1",
        )

    hands_str = f"{n_hands:,}" if n_hands is not None else "?"
    return HealthCheckItem(
        id="database",
        name="Database",
        status="pass",
        value=f"{hands_str} hands",
        can_skip=False,
    )


def _check_gpu() -> HealthCheckItem:
    hw = detect_hardware()

    if hw.gpu and hw.gpu.cuda_available:
        cuda_label = hw.gpu.cuda_version or "available"
        return HealthCheckItem(
            id="gpu",
            name="GPU / CUDA",
            status="pass",
            value=f"{hw.gpu.name} · {hw.gpu.vram_gb} GB · CUDA {cuda_label}",
            can_skip=True,
        )

    if hw.gpu:
        # GPU detected but CUDA not available (e.g. Metal without torch, or driver issue)
        return HealthCheckItem(
            id="gpu",
            name="GPU / CUDA",
            status="warn",
            value=f"{hw.gpu.name} · CUDA not available",
            advice=(
                "GPU detected but CUDA is not available to PyTorch. "
                "Training will fall back to CPU (~4× slower). "
                "Install CUDA-enabled PyTorch to use your GPU."
            ),
            fix_windows=(
                "# Install CUDA PyTorch (RTX 50-series / CUDA 12.8):\n"
                "powershell -File poker_ai/scripts/install_torch_cuda.ps1"
            ),
            fix_linux=(
                "# NVIDIA CUDA 12.8:\n"
                "pip install torch --index-url https://download.pytorch.org/whl/cu128\n\n"
                "# AMD ROCm:\n"
                "pip install torch --index-url https://download.pytorch.org/whl/rocm6.2"
            ),
            fix_macos=(
                "# Apple Silicon (M1/M2/M3/M4) — MPS backend:\n"
                "pip install torch torchvision torchaudio\n"
                "# Then train with: --device mps"
            ),
            can_skip=True,
            docs_section="Phase W0 §3",
        )

    # No GPU at all — CPU only
    return HealthCheckItem(
        id="gpu",
        name="GPU / CUDA",
        status="warn",
        value="CPU only — no GPU detected",
        advice=(
            "No GPU found. Training will run on CPU which is ~4× slower "
            "(HHFormer: ~30 min instead of ~7 min). "
            "The app works fully on CPU; GPU is optional but recommended."
        ),
        fix_windows=(
            "# 1. Ensure NVIDIA drivers are installed: https://www.nvidia.com/drivers\n"
            "# 2. Install CUDA PyTorch:\n"
            "powershell -File poker_ai/scripts/install_torch_cuda.ps1"
        ),
        fix_linux=(
            "# 1. Install NVIDIA drivers:\n"
            "sudo apt install nvidia-driver-535\n\n"
            "# 2. Install CUDA PyTorch:\n"
            "pip install torch --index-url https://download.pytorch.org/whl/cu128"
        ),
        fix_macos=(
            "# Apple Silicon: install PyTorch with MPS support:\n"
            "pip install torch torchvision torchaudio\n"
            "# Training automatically uses MPS on Apple Silicon."
        ),
        can_skip=True,
        docs_section="Phase W0 §3",
    )


def _check_texas() -> HealthCheckItem:
    # Use the library's own detection — reads install.json manifest so it always
    # finds the binary regardless of where it was installed or registered.
    try:
        from poker_ai.solver.bridge.install_texas import texas_solver_status
        ts = texas_solver_status()
        installed: bool = bool(ts.get("installed"))
        exe: str = ts.get("executable") or ""
        version: str = ts.get("version") or ""
    except Exception:
        installed = False
        exe = ""
        version = ""

    if installed and exe and Path(exe).is_file():
        label = f"Installed · {Path(exe).name}"
        if version:
            label = f"Installed · {version} · {Path(exe).name}"
        return HealthCheckItem(
            id="texas_solver",
            name="TexasSolver",
            status="pass",
            value=label,
            can_skip=True,
        )

    # Not installed — offer auto-install on all platforms (pre-built binaries exist
    # for Windows/Linux/macOS on the TexasSolver GitHub releases page).
    fix_common = (
        "# Option B — register an existing binary:\n"
        "python -m poker_ai solve register-texas --exe /path/to/console_solver\n\n"
        "# Option C — build from source (requires CMake):\n"
        "cd poker_ai/TexasSolver\n"
        "cmake -B build -DCMAKE_BUILD_TYPE=Release\n"
        "cmake --build build --config Release\n"
        "python -m poker_ai solve register-texas --exe build/console_solver\n\n"
        "# Option D — skip (student uses Phase 4 equity labels, lower quality)"
    )
    fix_with_auto = (
        "# Option A — install automatically (click the Install button above, or run):\n"
        "python -m poker_ai solve install-texas\n\n"
    ) + fix_common

    return HealthCheckItem(
        id="texas_solver",
        name="TexasSolver",
        status="warn",
        value="Not installed",
        advice=(
            "TexasSolver is used to build the postflop solver cache that trains the "
            "distilled student policy. Without it the student uses Phase 4 equity labels "
            "(lower quality). The app works without TexasSolver — this is optional."
        ),
        fix_windows=fix_with_auto,
        fix_linux=fix_with_auto,
        fix_macos=fix_with_auto,
        can_skip=True,
        can_auto_install=True,
        docs_section="Phase W0 §4",
    )


def _check_disk() -> HealthCheckItem:
    hw = detect_hardware()
    free = hw.disk.free_gb
    total = hw.disk.total_gb
    path = hw.disk.path

    used_pct = round((total - free) / total * 100) if total > 0 else 0
    value = f"{free:.1f} GB free of {total:.0f} GB ({used_pct}% used) on {path}"

    if free < _DISK_FAIL_GB:
        return HealthCheckItem(
            id="disk",
            name="Disk space",
            status="fail",
            value=value,
            advice=(
                f"Only {free:.1f} GB free. The app needs at least {_DISK_FAIL_GB} GB. "
                "Models alone take ~500 MB; solver cache can reach ~2 GB. "
                "Free up disk space before continuing."
            ),
            fix_windows="# Free up space: open Settings → Storage → Temporary files",
            fix_linux="# Find large files: du -sh /* 2>/dev/null | sort -rh | head -20",
            fix_macos="# Free up space: open About This Mac → Storage → Manage",
            can_skip=False,
            docs_section="Phase W0",
        )

    if free < _DISK_WARN_GB:
        return HealthCheckItem(
            id="disk",
            name="Disk space",
            status="warn",
            value=value,
            advice=(
                f"Only {free:.1f} GB free. Recommended: at least {_DISK_WARN_GB} GB. "
                "The solver cache and trained models can use 1–3 GB."
            ),
            fix_windows="# Free up space: open Settings → Storage → Temporary files",
            fix_linux="du -sh /* 2>/dev/null | sort -rh | head -20",
            fix_macos="# Free up space: open About This Mac → Storage → Manage",
            can_skip=True,
            docs_section="Phase W0",
        )

    return HealthCheckItem(
        id="disk",
        name="Disk space",
        status="pass",
        value=value,
        can_skip=True,
    )


# ---------------------------------------------------------------------------
# TexasSolver auto-install (streaming)
# ---------------------------------------------------------------------------


async def _stream_install() -> AsyncIterator[str]:
    """Run `poker_ai solve install-texas` and yield Server-Sent Event lines."""
    cmd = [sys.executable, "-m", "poker_ai", "solve", "install-texas"]
    yield "data: Starting TexasSolver installation…\n\n"

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert proc.stdout is not None
        async for raw in proc.stdout:
            line = raw.decode(errors="replace").rstrip()
            # SSE format: each message is "data: <text>\n\n"
            yield f"data: {line}\n\n"

        await proc.wait()
        if proc.returncode == 0:
            yield "data: \n\n"
            yield "data: ✓ Installation complete.\n\n"
            yield "event: done\ndata: ok\n\n"
        else:
            yield f"data: \n\ndata: ✗ Process exited with code {proc.returncode}.\n\n"
            yield "event: error\ndata: non-zero exit\n\n"
    except Exception as exc:  # noqa: BLE001
        yield f"data: ✗ Error: {exc}\n\n"
        yield "event: error\ndata: exception\n\n"


@router.post("/texas/install")
async def texas_install() -> StreamingResponse:
    """Stream the output of `poker_ai solve install-texas` as Server-Sent Events.

    The client should connect with ``EventSource`` (or ``fetch`` + ``ReadableStream``)
    and listen for ``done`` / ``error`` named events to know when the install finishes.
    After receiving ``done`` the UI should re-run the health check to update the
    TexasSolver row from *warn* to *pass*.
    """
    return StreamingResponse(
        _stream_install(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.get("/health/check", response_model=HealthCheckResponse)
async def health_check(session: AsyncSession = Depends(get_db)) -> HealthCheckResponse:
    """Run all system health checks and return structured pass/warn/fail results.

    Designed for the first-load health check page in the web UI.
    Results are cached by the browser (localStorage) for 30 minutes.
    """
    hw = detect_hardware()

    checks: list[HealthCheckItem] = [
        _check_os(),
        _check_python(),
        await _check_database(session),
        _check_gpu(),
        _check_texas(),
        _check_disk(),
    ]

    statuses = {c.status for c in checks}
    return HealthCheckResponse(
        os_name=hw.os_name,
        os_platform=hw.os_platform,
        all_passed="fail" not in statuses and "warn" not in statuses,
        has_warnings="warn" in statuses or "fail" in statuses,
        checks=checks,
    )
