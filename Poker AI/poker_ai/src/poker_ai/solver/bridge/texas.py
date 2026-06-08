"""TexasSolver console driver + JSON strategy parser (Phase 7)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from poker_ai.config.settings import get_settings
from poker_ai.solver.bridge.cache import cache_key, ranges_hash
from poker_ai.solver.bridge.grid import default_bet_sizes
from poker_ai.solver.bridge.install_texas import (
    TexasInstallManifest,
    discover_installed_bundle,
    find_console_executable,
)
from poker_ai.solver.bridge.mock_teacher import solve_mock
from poker_ai.solver.bridge.paths import (
    vendored_texas_resources_dir,
    vendored_texas_source_dir,
)
from poker_ai.solver.bridge.schemas import STUDENT_ACTIONS, SolvedSpot, SpotSpec

Backend = Literal["texas", "mock", "auto"]


def build_input_txt(spec: SpotSpec, *, dump_path: str = "output_result.json") -> str:
    """TexasSolver console command file (``set_*`` lines)."""
    bet_sizes = spec.bet_sizes if spec.bet_sizes else default_bet_sizes()
    lines = [
        f"set_pot {spec.pot_chips}",
        f"set_effective_stack {spec.effective_stack}",
        f"set_board {spec.normalized_board()}",
        f"set_range_oop {spec.range_oop}",
        f"set_range_ip {spec.range_ip}",
    ]
    for pos, street, kind, val in bet_sizes:
        if val.lower() == "allin":
            lines.append(f"set_bet_sizes {pos},{street},{kind},allin")
        else:
            lines.append(f"set_bet_sizes {pos},{street},{kind},{val}")
    lines.extend(
        [
            f"set_allin_threshold {spec.allin_threshold}",
            "build_tree",
            f"set_thread_num {spec.thread_num}",
            f"set_accuracy {spec.accuracy}",
            f"set_max_iteration {spec.max_iteration}",
            "set_print_interval 10",
            "set_use_isomorphism 1",
            "start_solve",
            "set_dump_rounds 1",
            f"dump_result {dump_path}",
        ]
    )
    return "\n".join(lines) + "\n"


def _normalize_texas_action(label: str) -> str:
    low = label.lower().strip()
    if low.startswith("bet"):
        return "bet"
    if low.startswith("raise"):
        return "raise"
    if low in ("allin", "all-in"):
        return "allin"
    if low in ("check", "call", "fold"):
        return low
    return low


def _aggregate_combo_strategy(strat: dict[str, Any]) -> dict[str, float] | None:
    """TexasSolver console v0.2: ``strategy`` holds per-combo probability lists."""
    actions = strat.get("actions")
    combos = strat.get("strategy")
    if not isinstance(actions, list) or not isinstance(combos, dict) or not combos:
        return None
    sums = [0.0] * len(actions)
    n = 0
    for probs in combos.values():
        if not isinstance(probs, list) or len(probs) != len(actions):
            continue
        for i, p in enumerate(probs):
            try:
                sums[i] += float(p)
            except (TypeError, ValueError):
                continue
        n += 1
    if n <= 0:
        return None
    out: dict[str, float] = {}
    for label, total in zip(actions, sums, strict=False):
        key = _normalize_texas_action(str(label))
        out[key] = out.get(key, 0.0) + total / n
    return out


def _flatten_strategy(node: dict[str, Any], out: dict[str, float]) -> None:
    """Walk TexasSolver JSON tree and collect action -> frequency at root-ish nodes."""
    strat = node.get("strategy")
    if isinstance(strat, dict):
        agg = _aggregate_combo_strategy(strat)
        if agg:
            for k, v in agg.items():
                out[k] = out.get(k, 0.0) + v
            return
        for k, v in strat.items():
            try:
                out[str(k).lower()] = float(v)
            except (TypeError, ValueError):
                continue
    children = node.get("childrens") or node.get("children") or []
    if isinstance(children, list) and children and not strat:
        _flatten_strategy(children[0], out)


def _map_to_student_actions(raw: dict[str, float]) -> tuple[tuple[str, ...], tuple[float, ...]]:
    """Collapse TexasSolver action names into the 5-slot student vocabulary."""
    fold = raw.get("fold", 0.0)
    check = raw.get("check", 0.0) + raw.get("call", 0.0)
    bet = sum(v for k, v in raw.items() if "bet" in k and "allin" not in k)
    raise_ = sum(v for k, v in raw.items() if "raise" in k)
    allin = raw.get("allin", 0.0) + raw.get("all-in", 0.0)
    agg = bet + raise_
    if agg <= 0 and sum(raw.values()) > 0:
        agg = max(0.0, 1.0 - fold - check - allin)
    b33 = agg * 0.55
    b66 = agg * 0.45
    mass = [fold, check, b33, b66, allin]
    s = sum(mass)
    if s <= 0:
        mass = [0.2, 0.2, 0.2, 0.2, 0.2]
    else:
        mass = [m / s for m in mass]
    return STUDENT_ACTIONS, tuple(mass)


def parse_result_json(path: Path) -> tuple[tuple[str, ...], tuple[float, ...]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list) and raw:
        raw = raw[0]
    if not isinstance(raw, dict):
        msg = f"Unexpected TexasSolver JSON shape in {path}"
        raise ValueError(msg)
    collected: dict[str, float] = {}
    _flatten_strategy(raw, collected)
    if not collected:
        msg = f"No strategy found in {path}"
        raise ValueError(msg)
    return _map_to_student_actions(collected)


def _resource_dir_for_exe(exe: Path) -> Path:
    root = exe.parent
    resources = vendored_texas_resources_dir()
    if (resources / "compairer" / "card5_dic_sorted.txt").is_file():
        return resources
    for candidate in (root / "resources", root.parent / "resources"):
        if (candidate / "compairer" / "card5_dic_sorted.txt").is_file():
            return candidate.resolve()
    return resources


def _exe_candidates(install_dir: Path | None) -> list[Path]:
    settings = get_settings()
    out: list[Path] = []
    if settings.texas_solver_exe:
        out.append(Path(settings.texas_solver_exe))
    env = os.environ.get("POKER_AI_TEXAS_SOLVER_EXE", "").strip()
    if env:
        out.append(Path(env))
    base = install_dir or settings.texas_solver_install_dir
    manifest = discover_installed_bundle(base)
    if manifest is not None:
        out.append(manifest.executable)
    vendored = vendored_texas_source_dir()
    if vendored.is_dir():
        built = find_console_executable(vendored)
        if built is not None:
            out.append(built)
    for name in ("console_solver.exe", "console_solver", "TexasSolver-console.exe"):
        found = shutil.which(name)
        if found:
            out.append(Path(found))
    return out


def resolve_texas_bundle(
    *,
    executable: Path | None = None,
    install_dir: Path | None = None,
) -> TexasInstallManifest | None:
    """Resolve console binary + ``resources`` (compairer tables) for subprocess runs."""
    settings = get_settings()
    base = install_dir or settings.texas_solver_install_dir

    if executable is not None and executable.is_file():
        root = executable.parent
        return TexasInstallManifest(
            version="custom",
            executable=executable.resolve(),
            resource_dir=_resource_dir_for_exe(executable),
            install_root=root.resolve(),
        )

    for path in _exe_candidates(base):
        if not path.is_file():
            continue
        manifest = discover_installed_bundle(base)
        if manifest is not None and manifest.executable.resolve() == path.resolve():
            return manifest
        return TexasInstallManifest(
            version="custom",
            executable=path.resolve(),
            resource_dir=_resource_dir_for_exe(path),
            install_root=path.parent.resolve(),
        )

    return discover_installed_bundle(base)


@dataclass(slots=True)
class TexasSolverDriver:
    """Subprocess wrapper for ``console_solver`` (AGPL teacher)."""

    executable: Path | None = None
    install_dir: Path | None = None
    timeout_sec: int = 600

    def resolve_bundle(self) -> TexasInstallManifest | None:
        install = self.install_dir
        if install is None:
            install = get_settings().texas_solver_install_dir
        return resolve_texas_bundle(executable=self.executable, install_dir=install)

    def resolve_executable(self) -> Path | None:
        bundle = self.resolve_bundle()
        return bundle.executable if bundle else None

    def available(self) -> bool:
        return self.resolve_executable() is not None

    def run(self, spec: SpotSpec) -> SolvedSpot:
        bundle = self.resolve_bundle()
        if bundle is None:
            msg = (
                "TexasSolver executable not found. Run: "
                "python -m poker_ai solve install-texas "
                "Or set POKER_AI_TEXAS_SOLVER_EXE. Use backend=mock for offline labels."
            )
            raise FileNotFoundError(msg)
        exe = bundle.executable
        resource_dir = bundle.resource_dir
        key = cache_key(spec)
        with tempfile.TemporaryDirectory(prefix="poker_ai_texas_") as tmp:
            work = Path(tmp)
            input_path = work / "input.txt"
            out_json = work / "output_result.json"
            dump_path = str(out_json.resolve())
            input_path.write_text(
                build_input_txt(spec, dump_path=dump_path),
                encoding="utf-8",
            )
            cmd = [
                str(exe),
                "-i",
                str(input_path.resolve()),
                "-r",
                str(resource_dir.resolve()),
                "-m",
                "holdem",
            ]
            proc = subprocess.run(
                cmd,
                cwd=str(bundle.install_root),
                capture_output=True,
                text=True,
                timeout=self.timeout_sec,
                check=False,
            )
            if proc.returncode != 0:
                msg = f"TexasSolver failed ({proc.returncode}): {proc.stderr[-2000:]}"
                raise RuntimeError(msg)
            if not out_json.is_file():
                msg = f"TexasSolver did not write {out_json}"
                raise FileNotFoundError(msg)
            labels, freqs = parse_result_json(out_json)
        return SolvedSpot(
            cache_key=key,
            board=spec.normalized_board(),
            sizing_tree_id=spec.sizing_tree_id,
            ranges_hash=ranges_hash(spec.range_oop, spec.range_ip),
            action_labels=labels,
            frequencies=freqs,
            backend="texas",
            meta={
                "executable": str(exe),
                "resource_dir": str(resource_dir),
            },
        )


def solve_spot(
    spec: SpotSpec,
    *,
    backend: Backend = "auto",
    driver: TexasSolverDriver | None = None,
) -> SolvedSpot:
    """Solve one spot with TexasSolver or the mock teacher."""
    if backend == "mock":
        return solve_mock(spec)
    drv = driver or TexasSolverDriver()
    if backend == "texas" or (backend == "auto" and drv.available()):
        try:
            return drv.run(spec)
        except (FileNotFoundError, RuntimeError, subprocess.TimeoutExpired):
            if backend == "texas":
                raise
    return solve_mock(spec)
