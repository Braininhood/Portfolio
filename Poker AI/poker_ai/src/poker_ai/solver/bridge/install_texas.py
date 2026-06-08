"""Download and install TexasSolver console binaries (AGPL) by host OS."""

from __future__ import annotations

import json
import platform
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.solver.bridge.paths import (
    default_texas_install_dir,
    install_manifest_path,
    project_root,
    vendored_texas_resources_dir,
)

DEFAULT_RELEASE_TAG = "v0.2.0"
GITHUB_RELEASE_BASE = "https://github.com/bupticybee/TexasSolver/releases/download"
GITHUB_API_RELEASE = "https://api.github.com/repos/bupticybee/TexasSolver/releases/tags"

# Rough minimum sizes (bytes) — catches HTML error pages / truncated downloads.
_EXPECTED_MIN_ZIP_BYTES: dict[str, int] = {
    "win32": 30_000_000,
    "darwin": 25_000_000,
    "linux": 10_000_000,
}

_CONSOLE_NAMES = (
    "console_solver.exe",
    "console_solver",
    "TexasSolver-console.exe",
    "TexasSolver-console",
)


@dataclass(frozen=True, slots=True)
class TexasInstallManifest:
    version: str
    executable: Path
    resource_dir: Path
    install_root: Path

    def to_json(self) -> dict[str, str]:
        return {
            "version": self.version,
            "executable": str(self.executable),
            "resource_dir": str(self.resource_dir),
            "install_root": str(self.install_root),
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> TexasInstallManifest:
        return cls(
            version=str(data["version"]),
            executable=Path(str(data["executable"])),
            resource_dir=Path(str(data["resource_dir"])),
            install_root=Path(str(data["install_root"])),
        )


def release_zip_name(*, tag: str = DEFAULT_RELEASE_TAG) -> str:
    """Asset filename on GitHub releases for this machine."""
    system = sys.platform
    if system == "win32":
        suffix = "Windows"
    elif system == "darwin":
        suffix = "MacOs"
    elif system.startswith("linux"):
        suffix = "Linux"
    else:
        msg = f"Unsupported platform for TexasSolver auto-install: {system} ({platform.machine()})"
        raise OSError(msg)
    return f"TexasSolver-{tag}-{suffix}.zip"


def release_download_url(*, tag: str = DEFAULT_RELEASE_TAG) -> str:
    return f"{GITHUB_RELEASE_BASE}/{tag}/{release_zip_name(tag=tag)}"


def _fetch_release_asset_url(*, tag: str, zip_name: str) -> str | None:
    """Resolve browser_download_url from GitHub API (more reliable than guessing)."""
    api_url = f"{GITHUB_API_RELEASE}/{tag}"
    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": "poker-ai-texassolver-install/1.0",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return None
    for asset in data.get("assets", []):
        if asset.get("name") == zip_name:
            url = asset.get("browser_download_url")
            return str(url) if url else None
    return None


def _is_valid_zip(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 1024:
        return False
    header = path.read_bytes()[:4]
    if header[:2] != b"PK":
        return False
    min_bytes = _EXPECTED_MIN_ZIP_BYTES.get(sys.platform, 5_000_000)
    return path.stat().st_size >= min_bytes


def _has_compairer_table(resources: Path) -> bool:
    return (resources / "compairer" / "card5_dic_sorted.txt").is_file()


def _pick_resource_dir(install_root: Path) -> Path | None:
    candidates = [
        install_root / "resources",
        install_root / "TexasSolver" / "resources",
    ]
    for path in candidates:
        if _has_compairer_table(path):
            return path.resolve()
    for path in install_root.rglob("resources"):
        if path.is_dir() and _has_compairer_table(path):
            return path.resolve()
    vendored = vendored_texas_resources_dir()
    if _has_compairer_table(vendored):
        return vendored.resolve()
    return None


def find_console_executable(
    root: Path,
    *,
    max_depth: int = 6,
) -> Path | None:
    """Locate ``console_solver`` under *root* (release zip or local build)."""
    root = root.resolve()
    if not root.exists():
        return None
    for name in _CONSOLE_NAMES:
        direct = root / name
        if direct.is_file():
            return direct
    depth = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        depth = len(rel_parts)
        if depth > max_depth:
            continue
        if path.name in _CONSOLE_NAMES:
            return path.resolve()
    return None


def load_install_manifest(install_dir: Path | None = None) -> TexasInstallManifest | None:
    path = install_manifest_path(install_dir)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        manifest = TexasInstallManifest.from_json(data)
    except KeyError:
        return None
    if manifest.executable.is_file() and _has_compairer_table(manifest.resource_dir):
        return manifest
    return None


def write_install_manifest(manifest: TexasInstallManifest, install_dir: Path | None = None) -> Path:
    dest_dir = install_dir or default_texas_install_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = install_manifest_path(dest_dir)
    path.write_text(json.dumps(manifest.to_json(), indent=2) + "\n", encoding="utf-8")
    return path


def discover_installed_bundle(
    install_dir: Path | None = None,
) -> TexasInstallManifest | None:
    """Return a valid install manifest if the console binary and resources exist."""
    base = install_dir or default_texas_install_dir()
    manifest = load_install_manifest(base)
    if manifest is not None:
        return manifest
    for sub in sorted(base.iterdir(), reverse=True) if base.is_dir() else []:
        if not sub.is_dir():
            continue
        exe = find_console_executable(sub)
        if exe is None:
            continue
        resources = _pick_resource_dir(sub)
        if resources is None:
            continue
        return TexasInstallManifest(
            version=sub.name,
            executable=exe,
            resource_dir=resources,
            install_root=sub.resolve(),
        )
    exe = find_console_executable(base)
    if exe is None:
        return None
    resources = _pick_resource_dir(base)
    if resources is None:
        return None
    return TexasInstallManifest(
        version="unknown",
        executable=exe,
        resource_dir=resources,
        install_root=base.resolve(),
    )


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "poker-ai-texassolver-install/1.0",
            "Accept": "application/octet-stream",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp, dest.open("wb") as out:
            shutil.copyfileobj(resp, out)
    except urllib.error.URLError as exc:
        msg = f"Download failed: {url} ({exc})"
        raise OSError(msg) from exc
    if not _is_valid_zip(dest):
        dest.unlink(missing_ok=True)
        msg = (
            f"Downloaded file is not a valid TexasSolver zip (wrong size or corrupt): {dest.name}. "
            "Download manually from https://github.com/bupticybee/TexasSolver/releases "
            f"and run: python -m poker_ai solve register-texas --zip PATH"
        )
        raise OSError(msg)


def install_texas_solver(
    *,
    install_dir: Path | None = None,
    tag: str = DEFAULT_RELEASE_TAG,
    force: bool = False,
) -> TexasInstallManifest:
    """
    Download the official release zip for this OS and unpack under *install_dir*.

    Does not redistribute the binary in git — only writes under ``artifacts/third_party/``.
    """
    base = (install_dir or default_texas_install_dir()).resolve()
    extract_root = base / tag

    if not force:
        existing = discover_installed_bundle(base)
        if existing is not None and existing.install_root.name == tag:
            write_install_manifest(existing, base)
            return existing

    if extract_root.exists() and force:
        shutil.rmtree(extract_root)

    zip_name = release_zip_name(tag=tag)
    url = _fetch_release_asset_url(tag=tag, zip_name=zip_name) or release_download_url(tag=tag)
    zip_path = base / zip_name

    if force and zip_path.is_file():
        zip_path.unlink()
    if not _is_valid_zip(zip_path):
        if zip_path.is_file():
            zip_path.unlink()
        _download(url, zip_path)

    extract_root.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_root)
    except zipfile.BadZipFile as exc:
        zip_path.unlink(missing_ok=True)
        msg = (
            f"Invalid zip at {zip_path}. Re-run with --force or register a manual download:\n"
            f"  python -m poker_ai solve register-texas --zip PATH"
        )
        raise OSError(msg) from exc

    return _manifest_from_extract(extract_root, tag=tag, install_dir=base)


def register_texas_from_zip(
    zip_path: Path,
    *,
    install_dir: Path | None = None,
    tag: str = DEFAULT_RELEASE_TAG,
    force: bool = False,
) -> TexasInstallManifest:
    """Unpack a locally downloaded release zip (skips network download)."""
    zip_path = zip_path.resolve()
    if not zip_path.is_file():
        raise FileNotFoundError(f"Zip not found: {zip_path}")
    if not _is_valid_zip(zip_path):
        raise OSError(
            f"Not a valid TexasSolver release zip: {zip_path} "
            f"(size={zip_path.stat().st_size} bytes; expected ≥ "
            f"{_EXPECTED_MIN_ZIP_BYTES.get(sys.platform, 5_000_000):,} on {sys.platform})"
        )
    base = (install_dir or default_texas_install_dir()).resolve()
    extract_root = base / tag
    if extract_root.exists() and force:
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_root)
    return _manifest_from_extract(extract_root, tag=tag, install_dir=base)


def register_texas_executable(
    executable: Path,
    *,
    install_dir: Path | None = None,
    tag: str = DEFAULT_RELEASE_TAG,
    resource_dir: Path | None = None,
) -> TexasInstallManifest:
    """Register a built ``console_solver`` (e.g. from vendored ``TexasSolver/``)."""
    executable = executable.resolve()
    if not executable.is_file():
        raise FileNotFoundError(f"Executable not found: {executable}")
    resources = resource_dir.resolve() if resource_dir else _pick_resource_dir(executable.parent)
    if resources is None:
        resources = vendored_texas_resources_dir().resolve()
    if not _has_compairer_table(resources):
        msg = f"compairer tables missing under {resources}"
        raise FileNotFoundError(msg)
    base = (install_dir or default_texas_install_dir()).resolve()
    manifest = TexasInstallManifest(
        version=tag,
        executable=executable,
        resource_dir=resources,
        install_root=executable.parent.resolve(),
    )
    write_install_manifest(manifest, base)
    return manifest


def _manifest_from_extract(
    extract_root: Path,
    *,
    tag: str,
    install_dir: Path,
) -> TexasInstallManifest:
    exe = find_console_executable(extract_root)
    if exe is None:
        msg = f"No console_solver binary found under {extract_root}"
        raise FileNotFoundError(msg)
    resources = _pick_resource_dir(extract_root)
    if resources is None:
        msg = f"TexasSolver compairer tables not found under {extract_root}"
        raise FileNotFoundError(msg)
    manifest = TexasInstallManifest(
        version=tag,
        executable=exe.resolve(),
        resource_dir=resources,
        install_root=extract_root.resolve(),
    )
    write_install_manifest(manifest, install_dir)
    return manifest


def env_setup_hint(manifest: TexasInstallManifest) -> str:
    exe = manifest.executable
    return (
        f"TexasSolver ready.\n"
        f"  executable: {exe}\n"
        f"  resources:  {manifest.resource_dir}\n\n"
        f"PowerShell:\n"
        f'  $env:POKER_AI_TEXAS_SOLVER_EXE = "{exe}"\n\n'
        f"Bash:\n"
        f'  export POKER_AI_TEXAS_SOLVER_EXE="{exe}"\n\n'
        f"Or add to poker_ai/.env:\n"
        f"  POKER_AI_TEXAS_SOLVER_EXE={exe}\n"
    )


def texas_solver_status(install_dir: Path | None = None) -> dict[str, Any]:
    """Diagnostic dict for CLI / tests."""
    base = install_dir or default_texas_install_dir()
    manifest = discover_installed_bundle(base)
    return {
        "platform": sys.platform,
        "machine": platform.machine(),
        "release_zip": release_zip_name(),
        "install_dir": str(base.resolve()),
        "vendored_source": str((project_root() / "TexasSolver").resolve()),
        "installed": manifest is not None,
        "executable": str(manifest.executable) if manifest else None,
        "resource_dir": str(manifest.resource_dir) if manifest else None,
        "version": manifest.version if manifest else None,
    }
