"""Hardware detection — CPU, GPU, RAM, disk, and worker recommendations.

Runs locally; never makes outbound network calls.
All subprocess calls are read-only queries to the OS.
Cross-platform: Windows, Linux, macOS.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CpuInfo:
    name: str
    physical_cores: int
    logical_cores: int
    arch: str  # "x86_64" | "ARM64" | ...


@dataclass
class GpuInfo:
    name: str
    vram_gb: float
    driver_version: str
    cuda_version: str | None = None  # from torch, e.g. "12.8"
    cuda_available: bool = False


@dataclass
class RamInfo:
    total_gb: float
    available_gb: float


@dataclass
class WorkerRecommendation:
    """Safe worker count + plain-English explanation for a given task type."""

    recommended: int
    max_safe: int
    current_env: int  # value from POKER_AI_NUM_WORKERS env var (0 = not set)
    warning: str | None  # non-None if current_env looks wrong
    explanation: str
    by_task: dict[str, int]  # {"ingest": 16, "train_hhformer": 4, ...}


@dataclass
class DiskInfo:
    free_gb: float
    total_gb: float
    path: str  # which filesystem was checked


@dataclass
class HardwareInfo:
    cpu: CpuInfo
    gpu: GpuInfo | None
    ram: RamInfo
    disk: DiskInfo
    workers: WorkerRecommendation
    os_name: str   # "Windows 11 Home", "Ubuntu 22.04", "macOS 14.2"
    os_platform: str  # "win32" | "linux" | "darwin"


# ---------------------------------------------------------------------------
# CPU detection
# ---------------------------------------------------------------------------


def _detect_cpu() -> CpuInfo:
    logical = os.cpu_count() or 1
    arch = platform.machine()

    # Physical core count — platform-specific
    physical = _physical_core_count(logical)

    # Human-readable name
    name = _cpu_name()

    return CpuInfo(
        name=name,
        physical_cores=physical,
        logical_cores=logical,
        arch=arch,
    )


def _physical_core_count(logical_fallback: int) -> int:
    """Return physical (non-hyperthreaded) core count."""
    # Windows — PowerShell WMI (works on Win 10/11 without wmic)
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NonInteractive",
                    "-Command",
                    "(Get-WmiObject Win32_Processor).NumberOfCores",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except Exception:
            pass

    # Linux — /proc/cpuinfo
    if sys.platform == "linux":
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text()
            core_ids: set[str] = set()
            for line in cpuinfo.splitlines():
                if line.startswith("core id"):
                    core_ids.add(line.split(":")[1].strip())
            if core_ids:
                return len(core_ids)
        except Exception:
            pass

    # macOS — sysctl
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.physicalcpu"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except Exception:
            pass

    # Fallback: assume half of logical (typical for HT)
    return max(1, logical_fallback // 2)


def _cpu_name() -> str:
    """Return a human-readable CPU name."""
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NonInteractive",
                    "-Command",
                    "(Get-WmiObject Win32_Processor).Name",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                name = result.stdout.strip()
                if name:
                    return name
        except Exception:
            pass

    if sys.platform == "linux":
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text()
            for line in cpuinfo.splitlines():
                if line.startswith("model name"):
                    return line.split(":")[1].strip()
        except Exception:
            pass

    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                name = result.stdout.strip()
                if name:
                    return name
        except Exception:
            pass

    # Last resort: platform.processor() (gives family/model string on Windows)
    return platform.processor() or "Unknown CPU"


# ---------------------------------------------------------------------------
# GPU detection
# ---------------------------------------------------------------------------


def _detect_gpu() -> GpuInfo | None:
    """Detect GPU — NVIDIA (CUDA), AMD (ROCm), Apple Silicon (Metal/MPS), or None."""

    # --- NVIDIA via nvidia-smi (Windows + Linux + macOS with eGPU) ---
    nvidia_info = _nvidia_smi_info()
    if nvidia_info:
        name, vram_gb, driver = nvidia_info
        cuda_ver, cuda_avail = _torch_cuda_info()
        return GpuInfo(
            name=name,
            vram_gb=vram_gb,
            driver_version=driver,
            cuda_version=cuda_ver,
            cuda_available=cuda_avail,
        )

    # --- NVIDIA via PyTorch CUDA only (nvidia-smi not on PATH) ---
    cuda_ver, cuda_avail = _torch_cuda_info()
    if cuda_avail:
        try:
            import torch

            props = torch.cuda.get_device_properties(0)
            return GpuInfo(
                name=torch.cuda.get_device_name(0),
                vram_gb=round(props.total_memory / 1024**3, 1),
                driver_version="unknown",
                cuda_version=cuda_ver,
                cuda_available=True,
            )
        except Exception:
            pass

    # --- Apple Silicon — Metal / MPS (macOS only) ---
    if sys.platform == "darwin":
        mps = _apple_mps_info()
        if mps:
            return mps

    # --- AMD ROCm (Linux) ---
    if sys.platform == "linux":
        rocm = _rocm_info()
        if rocm:
            return rocm

    return None


def _apple_mps_info() -> GpuInfo | None:
    """Detect Apple Silicon GPU via PyTorch MPS or system_profiler."""
    # PyTorch MPS check (fastest)
    try:
        import torch

        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            chip_name = _macos_chip_name() or "Apple Silicon"
            return GpuInfo(
                name=f"{chip_name} (Metal/MPS)",
                vram_gb=0.0,  # unified memory — not separately reported
                driver_version="Metal",
                cuda_version="MPS",
                cuda_available=True,  # MPS is the macOS equivalent of CUDA
            )
    except ImportError:
        pass

    # system_profiler fallback (works without PyTorch)
    try:
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                key = line.strip()
                if key.startswith("Chipset Model:") or key.startswith("GPU:"):
                    name = key.split(":", 1)[1].strip()
                    if name:
                        return GpuInfo(
                            name=name,
                            vram_gb=0.0,
                            driver_version="Metal",
                            cuda_version=None,
                            cuda_available=False,
                        )
    except Exception:
        pass

    return None


def _macos_chip_name() -> str | None:
    """Return Apple chip name (e.g. 'Apple M3 Pro') on macOS."""
    try:
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except Exception:
        pass
    # Newer Apple Silicon uses hw.targettype
    try:
        result = subprocess.run(
            ["sysctl", "-n", "hw.targettype"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except Exception:
        pass
    return None


def _rocm_info() -> GpuInfo | None:
    """Detect AMD GPU via rocm-smi (Linux + ROCm stack)."""
    try:
        result = subprocess.run(
            ["rocm-smi", "--showproductname", "--csv"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode == 0:
            lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
            for line in lines[1:]:  # skip CSV header
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2 and parts[1]:
                    # Try to get VRAM
                    vram_gb = 0.0
                    try:
                        mem_result = subprocess.run(
                            ["rocm-smi", "--showmeminfo", "vram", "--csv"],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        if mem_result.returncode == 0:
                            for mline in mem_result.stdout.splitlines()[1:]:
                                mparts = mline.split(",")
                                if len(mparts) >= 3:
                                    vram_gb = round(int(mparts[2]) / 1024**3, 1)
                                    break
                    except Exception:
                        pass
                    return GpuInfo(
                        name=parts[1],
                        vram_gb=vram_gb,
                        driver_version="ROCm",
                        cuda_version="ROCm",
                        cuda_available=True,
                    )
    except Exception:
        pass
    return None


def _nvidia_smi_info() -> tuple[str, float, str] | None:
    """Return (name, vram_gb, driver_version) from nvidia-smi, or None."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader",
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        # First GPU only (single-GPU workstation assumption)
        line = result.stdout.strip().splitlines()[0]
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            return None
        name = parts[0]
        # memory is like "12227 MiB"
        mem_str = parts[1].replace("MiB", "").replace("GiB", "").strip()
        mem_gb = round(float(mem_str) / 1024, 1) if "MiB" in parts[1] else float(mem_str)
        driver = parts[2]
        return name, mem_gb, driver
    except Exception:
        return None


def _torch_cuda_info() -> tuple[str | None, bool]:
    """Return (cuda_version_str | None, is_available)."""
    try:
        import torch

        avail = torch.cuda.is_available()
        ver = torch.version.cuda if avail else None
        return ver, avail
    except ImportError:
        return None, False


# ---------------------------------------------------------------------------
# RAM detection
# ---------------------------------------------------------------------------


def _detect_ram() -> RamInfo:
    total = _ram_bytes_win() or _ram_bytes_linux() or _ram_bytes_macos()
    # Available memory: rough estimate (75% of total as floor)
    # Full detection requires psutil; keep it optional
    available = total * 0.75 if total else 0
    return RamInfo(
        total_gb=round((total or 0) / 1024**3, 1),
        available_gb=round(available / 1024**3, 1),
    )


def _ram_bytes_win() -> int | None:
    if sys.platform != "win32":
        return None
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NonInteractive",
                "-Command",
                "(Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except Exception:
        pass
    return None


def _ram_bytes_linux() -> int | None:
    if sys.platform != "linux":
        return None
    try:
        meminfo = Path("/proc/meminfo").read_text()
        for line in meminfo.splitlines():
            if line.startswith("MemTotal"):
                kb = int(line.split(":")[1].strip().split()[0])
                return kb * 1024
    except Exception:
        pass
    return None


def _ram_bytes_macos() -> int | None:
    if sys.platform != "darwin":
        return None
    try:
        result = subprocess.run(
            ["sysctl", "-n", "hw.memsize"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Worker recommendations
# ---------------------------------------------------------------------------

# Explanation text shown in the UI
_WORKER_EXPLANATION_TEMPLATE = """\
Your CPU has {physical} physical cores and {logical} logical cores (including \
hyperthreading/efficiency cores).

For compute-heavy tasks (CFR solving, league simulation) Python uses separate \
processes — one per physical core is most efficient. Using all {logical} logical \
cores does NOT double the speed and will make your computer unresponsive.

Recommended: {recommended} workers
  = {physical} physical cores
  − 2  (reserved for the API server, web browser, and OS)

You can set this higher (up to {max_safe}) for short jobs, or lower if you want \
to use your computer at the same time. The web UI will warn you if your setting \
looks wrong.\
"""

_TASK_WORKER_NOTES = {
    "ingest": "I/O-bound — can use more logical cores (disk reading, not computing)",
    "features_build": "CPU-bound — uses physical cores",
    "train_hhformer": "GPU-bound — DataLoader workers stay small (4–8); GPU does the work",
    "solve_preflop": "CPU-bound — each worker runs a CFR shard",
    "solve_grid": "CPU-bound — each worker runs one TexasSolver spot",
    "train_student": "GPU-bound — DataLoader workers only",
    "train_style": "GPU-bound — DataLoader workers only",
    "league_run": "CPU-bound — each worker plays a matchup",
}


def _worker_recommendation(cpu: CpuInfo, gpu: GpuInfo | None) -> WorkerRecommendation:
    p = cpu.physical_cores
    l = cpu.logical_cores  # noqa: E741

    # Safe default: physical - 2, floor 1
    recommended = max(1, p - 2)
    max_safe = max(1, p - 1)

    # Per-task recommendations
    dl_workers = min(4, max(1, l // 5))  # DataLoader workers for GPU training
    by_task: dict[str, int] = {
        "ingest": min(l, 16),          # I/O-bound — more is fine
        "features_build": recommended,  # CPU-bound
        "train_hhformer": dl_workers,   # GPU-bound: DataLoader only
        "solve_preflop": recommended,   # CPU-bound
        "solve_grid": recommended,      # CPU-bound
        "train_student": dl_workers,    # GPU-bound
        "train_style": dl_workers,      # GPU-bound
        "league_run": recommended,      # CPU-bound
    }

    # Check current env setting
    try:
        current_env = int(os.environ.get("POKER_AI_NUM_WORKERS", "0"))
    except (ValueError, TypeError):
        current_env = 0

    warning: str | None = None
    if current_env > 0:
        if current_env > max_safe:
            warning = (
                f"POKER_AI_NUM_WORKERS={current_env} exceeds the safe maximum "
                f"of {max_safe} for your CPU ({p} physical cores). "
                f"This may slow down your machine or cause crashes. "
                f"Recommended: {recommended}."
            )
        elif current_env == l and l > p:
            warning = (
                f"POKER_AI_NUM_WORKERS={current_env} uses all logical cores "
                f"but your CPU only has {p} physical cores. Hyperthreading does "
                f"not help for compute-heavy Python processes. "
                f"Recommended: {recommended}."
            )

    explanation = _WORKER_EXPLANATION_TEMPLATE.format(
        physical=p,
        logical=l,
        recommended=recommended,
        max_safe=max_safe,
    )

    return WorkerRecommendation(
        recommended=recommended,
        max_safe=max_safe,
        current_env=current_env,
        warning=warning,
        explanation=explanation,
        by_task=by_task,
    )


# ---------------------------------------------------------------------------
# Disk space
# ---------------------------------------------------------------------------


def _detect_disk(reference_path: str = ".") -> DiskInfo:
    """Free and total disk space on the filesystem that contains reference_path."""
    try:
        usage = shutil.disk_usage(reference_path)
        return DiskInfo(
            free_gb=round(usage.free / 1024**3, 1),
            total_gb=round(usage.total / 1024**3, 1),
            path=str(Path(reference_path).resolve()),
        )
    except Exception:
        return DiskInfo(free_gb=0.0, total_gb=0.0, path=reference_path)


# ---------------------------------------------------------------------------
# OS name
# ---------------------------------------------------------------------------


def _os_name() -> str:
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NonInteractive",
                    "-Command",
                    "(Get-WmiObject Win32_OperatingSystem).Caption",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                name = result.stdout.strip()
                if name:
                    return name
        except Exception:
            pass
        return f"Windows {platform.release()}"

    if sys.platform == "linux":
        try:
            data = Path("/etc/os-release").read_text()
            for line in data.splitlines():
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
        except Exception:
            pass
        return "Linux"

    if sys.platform == "darwin":
        ver = platform.mac_ver()[0]
        return f"macOS {ver}" if ver else "macOS"

    return platform.system()


# ---------------------------------------------------------------------------
# Main entry point — cached so it only runs once per process start
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def detect_hardware(reference_path: str = ".") -> HardwareInfo:
    """Detect all hardware info.  Results are cached for the lifetime of the process.

    Cache is intentionally not invalidated — hardware does not change at runtime.
    Call `detect_hardware.cache_clear()` in tests if needed.
    """
    cpu = _detect_cpu()
    gpu = _detect_gpu()
    ram = _detect_ram()
    disk = _detect_disk(reference_path)
    workers = _worker_recommendation(cpu, gpu)
    os_name = _os_name()
    return HardwareInfo(
        cpu=cpu,
        gpu=gpu,
        ram=ram,
        disk=disk,
        workers=workers,
        os_name=os_name,
        os_platform=sys.platform,
    )
