"""Project paths for TexasSolver install and discovery."""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """``poker_ai`` package root (contains ``pyproject.toml``)."""
    # bridge → solver → poker_ai → src → project root
    return Path(__file__).resolve().parents[4]


def default_texas_install_dir() -> Path:
    return project_root() / "artifacts" / "third_party" / "texassolver"


def vendored_texas_source_dir() -> Path:
    return project_root() / "TexasSolver"


def vendored_texas_resources_dir() -> Path:
    return vendored_texas_source_dir() / "resources"


def install_manifest_path(install_dir: Path | None = None) -> Path:
    root = install_dir or default_texas_install_dir()
    return root / "install.json"
