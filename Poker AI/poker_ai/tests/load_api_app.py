"""Load ``apps/api/main.py`` for integration tests (pyright-safe, no ``import main``)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from fastapi import FastAPI

_PKG_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _PKG_ROOT.parent
_API_MAIN = _REPO_ROOT / "apps" / "api" / "main.py"


def _ensure_paths() -> None:
    api_dir = _API_MAIN.parent
    src_dir = _PKG_ROOT / "src"
    for p in (src_dir, api_dir):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)


def load_api_app() -> FastAPI:
    """Import the FastAPI application from ``apps/api/main.py``."""
    _ensure_paths()
    spec = importlib.util.spec_from_file_location("poker_ai_api_main", _API_MAIN)
    if spec is None or spec.loader is None:
        msg = f"cannot load API module from {_API_MAIN}"
        raise ImportError(msg)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    application = getattr(mod, "app", None)
    if application is None:
        msg = "apps/api/main.py has no 'app' attribute"
        raise ImportError(msg)
    return application
