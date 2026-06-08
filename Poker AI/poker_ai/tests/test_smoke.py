"""Smoke tests for Phase 0 scaffold."""

from __future__ import annotations

import runpy
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

import poker_ai.apps.cli.main as cli_main_mod
from poker_ai import __version__
from poker_ai.apps.cli.main import app, main

runner = CliRunner()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_version_constant() -> None:
    assert __version__
    parts = __version__.split(".")
    assert len(parts) >= 2


def test_cli_help_shows_banner_text() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Poker AI" in result.stdout
    assert "local-first" in result.stdout
    assert "ROADMAP.md" in result.stdout


def test_cli_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_console_main_invokes_cli(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["poker_ai", "version"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code in (0, None)
    assert __version__ in capsys.readouterr().out


def test_runpy_main_module_invokes_version(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """In-process coverage for ``poker_ai.__main__`` (``python -m poker_ai``)."""
    monkeypatch.setattr(sys, "argv", ["poker_ai", "version"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("poker_ai.__main__", run_name="__main__")
    assert exc.value.code in (0, None)
    assert __version__ in capsys.readouterr().out


def test_cli_main_py_run_as_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cover ``if __name__ == '__main__'`` in ``apps/cli/main.py``."""
    monkeypatch.setattr(sys, "argv", ["main.py", "version"])
    path = Path(cli_main_mod.__file__)
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(path), run_name="__main__")
    assert exc.value.code in (0, None)


def test_python_m_poker_ai_version() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "poker_ai", "version"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert __version__ in proc.stdout


def test_cli_main_py_script_entry() -> None:
    main_py = Path(cli_main_mod.__file__)
    proc = subprocess.run(
        [sys.executable, str(main_py), "version"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert __version__ in proc.stdout
