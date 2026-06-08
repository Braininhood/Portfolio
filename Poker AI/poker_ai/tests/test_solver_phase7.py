"""Phase 7 — TexasSolver bridge, cache, distilled student."""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pytest

from poker_ai.solver.bridge.batch import solve_grid
from poker_ai.solver.bridge.cache import SolverCache, cache_key
from poker_ai.solver.bridge.grid import generate_spot_grid
from poker_ai.solver.bridge.install_texas import (
    TexasInstallManifest,
    _is_valid_zip,
    find_console_executable,
    release_zip_name,
    write_install_manifest,
)
from poker_ai.solver.bridge.mock_teacher import mock_strategy, solve_mock
from poker_ai.solver.bridge.schemas import SpotSpec
from poker_ai.solver.bridge.texas import build_input_txt, parse_result_json, resolve_texas_bundle


def test_cache_roundtrip(tmp_path: Path) -> None:
    spec = SpotSpec(board="Qs,Jh,2h", pot_chips=10, effective_stack=95)
    spot = solve_mock(spec)
    cache = SolverCache(tmp_path)
    cache.put(spot)
    key = cache_key(spec)
    loaded = cache.get(key)
    assert loaded is not None
    assert loaded.frequencies == spot.frequencies
    assert abs(sum(loaded.frequencies) - 1.0) < 1e-6


def test_mock_teacher_normalized() -> None:
    spec = SpotSpec(board="As,Kd,7c", pot_chips=15, effective_stack=60)
    labels, freqs = mock_strategy(spec)
    assert len(labels) == len(freqs)
    assert sum(freqs) == pytest.approx(1.0, abs=1e-6)


def test_release_zip_name_windows() -> None:
    name = release_zip_name()
    assert "TexasSolver-" in name
    assert name.endswith(".zip")


def test_is_valid_zip_rejects_truncated(tmp_path: Path) -> None:
    bad = tmp_path / "trunc.zip"
    bad.write_bytes(b"PK\x03\x04" + b"x" * 4096)
    assert not _is_valid_zip(bad)


def test_find_console_executable_nested(tmp_path: Path) -> None:
    nested = tmp_path / "bin"
    nested.mkdir()
    exe = nested / "console_solver.exe"
    exe.write_bytes(b"")
    found = find_console_executable(tmp_path)
    assert found == exe.resolve()


def test_resolve_bundle_from_manifest(tmp_path: Path) -> None:
    install = tmp_path / "v0.2.0"
    install.mkdir(parents=True)
    exe = install / "console_solver.exe"
    exe.write_bytes(b"")
    resources = install / "resources" / "compairer"
    resources.mkdir(parents=True)
    (resources / "card5_dic_sorted.txt").write_text("x", encoding="utf-8")
    manifest = TexasInstallManifest(
        version="v0.2.0",
        executable=exe.resolve(),
        resource_dir=(install / "resources").resolve(),
        install_root=install.resolve(),
    )
    write_install_manifest(manifest, tmp_path)
    bundle = resolve_texas_bundle(install_dir=tmp_path)
    assert bundle is not None
    assert bundle.executable == exe.resolve()


def test_build_input_txt_has_board() -> None:
    spec = SpotSpec(
        board="Qs,Jh,2h", pot_chips=10, effective_stack=95, range_oop="AA", range_ip="KK"
    )
    txt = build_input_txt(spec)
    assert "set_board Qs,Jh,2h" in txt
    assert "dump_result" in txt


def test_parse_texas_json_sample(tmp_path: Path) -> None:
    sample = {
        "strategy": {"check": 0.4, "bet": 0.35, "fold": 0.05, "raise": 0.1, "allin": 0.1},
        "childrens": [],
    }
    path = tmp_path / "out.json"
    path.write_text(json.dumps(sample), encoding="utf-8")
    labels, freqs = parse_result_json(path)
    assert len(labels) == 5
    assert sum(freqs) == pytest.approx(1.0, abs=1e-5)


def test_parse_texas_combo_strategy_json(tmp_path: Path) -> None:
    """Console v0.2 dumps per-combo lists under strategy.strategy."""
    sample = {
        "node_type": "action",
        "strategy": {
            "actions": ["CHECK", "BET 8.000000", "BET 25.000000"],
            "strategy": {
                "AhKh": [0.6, 0.35, 0.05],
                "2c2d": [0.8, 0.15, 0.05],
            },
        },
        "childrens": [],
    }
    path = tmp_path / "combo.json"
    path.write_text(json.dumps(sample), encoding="utf-8")
    labels, freqs = parse_result_json(path)
    assert len(labels) == 5
    assert sum(freqs) == pytest.approx(1.0, abs=1e-5)


def test_solve_grid_mock(tmp_path: Path) -> None:
    result = solve_grid(n_spots=12, cache_dir=tmp_path, backend="mock", seed=1)
    assert result.requested == 12
    assert result.solved + result.cache_hits == 12
    cache = SolverCache(tmp_path)
    assert cache.stats()["count"] == result.solved


def test_generate_spot_grid_count() -> None:
    specs = generate_spot_grid(n_spots=50, seed=0)
    assert len(specs) == 50


def test_student_head_forward() -> None:
    pytest.importorskip("torch")
    from poker_ai.learn._ml_deps import require_torch
    from poker_ai.models.student import StudentConfig, StudentHead

    torch = require_torch()
    head = StudentHead(StudentConfig()).module
    cls = torch.randn(4, 256)
    extras = torch.randn(4, 28)
    out = head(cls, extras)
    assert out.shape == (4, 5)
    assert torch.allclose(out.sum(dim=-1), torch.ones(4), atol=1e-5)


@pytest.mark.ml
def test_train_student_mock_cache(tmp_path: Path) -> None:
    pytest.importorskip("torch")
    from poker_ai.learn._ml_deps import save_state_dict_safetensors
    from poker_ai.learn.train_student import TrainStudentConfig, run_train_student
    from poker_ai.models.hhformer import HHFormer

    solve_grid(n_spots=40, cache_dir=tmp_path / "cache", backend="mock", seed=7)
    hh_dir = tmp_path / "hhformer"
    hh_dir.mkdir()
    wrapper = HHFormer()
    save_state_dict_safetensors(wrapper.module.state_dict(), str(hh_dir / "weights.safetensors"))

    metrics = run_train_student(
        cache_dir=tmp_path / "cache",
        hhformer_dir=hh_dir,
        artifact_dir=tmp_path / "student",
        cfg=TrainStudentConfig(epochs=8, batch_size=16, val_frac=0.15, seed=1),
    )
    assert metrics.mse_val <= 0.05
    assert (tmp_path / "student" / "MODEL_CARD.md").is_file()
    text = (tmp_path / "student" / "MODEL_CARD.md").read_text(encoding="utf-8")
    assert "AGPL" in text


@pytest.mark.ml
def test_distilled_inference_latency_p99(tmp_path: Path) -> None:
    pytest.importorskip("torch")
    from hand_fixture import make_six_max_hand
    from poker_ai.core.cards import cards_from_space_separated
    from poker_ai.core.engine import initial_state_from_parsed_hand
    from poker_ai.core.game import Street
    from poker_ai.core.profiles import PlayerProfile
    from poker_ai.learn._ml_deps import save_state_dict_safetensors
    from poker_ai.learn.train_student import TrainStudentConfig, run_train_student
    from poker_ai.models.hhformer import HHFormer
    from poker_ai.policy.distilled_policy import DistilledPolicy

    solve_grid(n_spots=24, cache_dir=tmp_path / "cache", backend="mock", seed=3)
    hh_dir = tmp_path / "hhformer"
    hh_dir.mkdir()
    wrapper = HHFormer()
    save_state_dict_safetensors(wrapper.module.state_dict(), str(hh_dir / "weights.safetensors"))
    run_train_student(
        cache_dir=tmp_path / "cache",
        hhformer_dir=hh_dir,
        artifact_dir=tmp_path / "student",
        cfg=TrainStudentConfig(epochs=5, batch_size=8),
    )
    policy = DistilledPolicy.from_artifacts(
        student_dir=tmp_path / "student",
        hhformer_dir=hh_dir,
        cache_dir=tmp_path / "cache",
    )
    hand = make_six_max_hand(
        hand_id=99,
        hero_seat=0,
        hero_cards="AhKd",
        hero_position="BTN",
    )
    state = initial_state_from_parsed_hand(hand)
    state.street = Street.FLOP
    state.board = list(cards_from_space_separated("Qs Jh 2h"))
    state.acting_seat = 0
    profile = PlayerProfile(profile_id="hero")
    _ = policy.propose(state, profile)
    times: list[float] = []
    for _ in range(50):
        t0 = time.perf_counter()
        dist = policy.propose(state, profile)
        times.append(time.perf_counter() - t0)
        assert dist.actions
    p99 = float(np.percentile(times, 99))
    from poker_ai.learn.validate_student import _p99_max_sec

    limit = _p99_max_sec()
    assert p99 < limit, f"p99 latency {p99 * 1000:.1f} ms exceeds {limit * 1000:.1f} ms bound"
