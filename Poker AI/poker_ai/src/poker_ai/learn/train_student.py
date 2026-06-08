"""Behavioral cloning on TexasSolver / mock teacher cache (Phase 7)."""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, TypeVar

from poker_ai.learn._ml_deps import require_torch, save_state_dict_safetensors
from poker_ai.learn.hhformer_inference import load_hhformer
from poker_ai.learn.student_dataset import (
    StudentRow,
    collate_student_batch,
    load_student_rows,
    load_training_jsonl,
    write_training_parquet,
)
from poker_ai.models.student import StudentConfig, StudentHead
from poker_ai.runtime.cancel import WorkCancelled
from poker_ai.runtime.progress import ProgressFn
from poker_ai.solver.bridge.cache import SolverCache


@dataclass(frozen=True, slots=True)
class TrainStudentConfig:
    epochs: int = 30
    batch_size: int = 128
    lr: float = 1e-3
    weight_decay: float = 0.01
    val_frac: float = 0.1
    seed: int = 42
    device: str = "auto"
    freeze_hhformer: bool = True


@dataclass
class TrainStudentMetrics:
    seed: int
    train_rows: int
    val_rows: int
    mse_val: float
    kl_val: float
    parameters_student: int
    device: str
    teacher_backends: dict[str, int]
    finished_at: str
    wall_time_sec: float = 0.0


def _model_card(metrics: TrainStudentMetrics, *, cache_dir: Path, val_frac: float) -> str:
    return f"""# Student policy v1 (Phase 7)

## Summary
Behavioral clone of offline GTO teacher strategies (TexasSolver AGPL or mock equity teacher).

## Training data
- Cache directory: `{cache_dir}`
- Rows: {metrics.train_rows + metrics.val_rows} (val_frac={val_frac})
- Teacher backends: {json.dumps(metrics.teacher_backends)}

## Metrics (held-out)
- MSE on action frequencies: **{metrics.mse_val:.4f}**
- KL (teacher || student): **{metrics.kl_val:.4f}**

## License / compliance
**TexasSolver** ([bupticybee/TexasSolver](https://github.com/bupticybee/TexasSolver))
is **AGPL-3.0**.
Rows labeled `backend=texas` are derived from that solver. Redistribution of those
teacher artifacts requires AGPL compliance. The student weights are MIT-licensed code
trained on those labels — document provenance and do not ship TexasSolver binaries
without meeting AGPL obligations.

## Inference
- Target: p99 < 10 ms on CPU (see `tests/test_solver_phase7.py`)
- Runtime: `DistilledPolicy` + frozen HHFormer [CLS]
"""


def default_student_artifact_dir() -> Path:
    return Path("artifacts/student/v1")


T = TypeVar("T")


def split_train_val_rows(
    rows: list[T], val_frac: float, seed: int
) -> tuple[list[T], list[T]]:
    """Shuffle and split rows into train / validation lists."""
    rng = random.Random(seed)
    idx = list(range(len(rows)))
    rng.shuffle(idx)
    n_val = max(1, int(len(rows) * val_frac)) if len(rows) > 5 else max(0, len(rows) // 5)
    val_idx = set(idx[:n_val])
    train = [rows[i] for i in range(len(rows)) if i not in val_idx]
    val = [rows[i] for i in val_idx]
    return train, val


def _split_rows(
    rows: list[StudentRow], val_frac: float, seed: int
) -> tuple[list[StudentRow], list[StudentRow]]:
    return split_train_val_rows(rows, val_frac, seed)


def _mse(pred: Any, target: Any) -> float:
    return float(((pred - target) ** 2).mean().item())


def _kl(pred: Any, target: Any) -> float:
    eps = 1e-8
    p = pred.clamp(min=eps)
    t = target.clamp(min=eps)
    return float((t * (t.log() - p.log())).sum(dim=-1).mean().item())


def run_train_student(
    *,
    cache_dir: Path = Path("artifacts/solver_cache"),
    hhformer_dir: Path = Path("artifacts/hhformer/v1"),
    artifact_dir: Path | None = None,
    cfg: TrainStudentConfig | None = None,
    training_jsonl: Path | None = None,
    play_study_manifest: Path | None = None,
    play_study_only: bool = False,
    progress: ProgressFn = None,
    cancel_check: Callable[[], bool] | None = None,
) -> TrainStudentMetrics:
    torch = require_torch()
    nn = torch.nn
    cfg = cfg or TrainStudentConfig()
    out = artifact_dir or default_student_artifact_dir()
    out.mkdir(parents=True, exist_ok=True)

    rows: list[StudentRow] = []
    play_study_count = 0
    if training_jsonl is not None and training_jsonl.is_file():
        rows = load_training_jsonl(training_jsonl)
    elif not play_study_only:
        cache = SolverCache(cache_dir)
        rows = load_student_rows(cache)

    if play_study_manifest is not None and play_study_manifest.is_file():
        from poker_ai.learn.play_study_loader import load_play_study_student_rows

        play_rows = load_play_study_student_rows(manifest_path=play_study_manifest)
        play_study_count = len(play_rows)
        if play_study_only:
            rows = play_rows
        elif play_rows:
            rows = rows + play_rows

    if not rows:
        if play_study_only and play_study_manifest:
            msg = (
                f"No HU play-study rows (need exactly 2 players in pot) in {play_study_manifest}. "
                "Play heads-up or wait until the table is down to two players."
            )
        elif play_study_manifest:
            msg = f"No training rows — check play study manifest {play_study_manifest} or solver cache {cache_dir}."
        else:
            msg = f"No training rows in {cache_dir} — run `solve grid` first."
        raise ValueError(msg)
    if play_study_only and len(rows) < 1:
        raise ValueError("Need at least one HU play-study decision to train.")

    train_rows, val_rows = _split_rows(rows, cfg.val_frac, cfg.seed)
    write_training_parquet(rows, out / "training_rows.jsonl")

    hhformer, _, device_name = load_hhformer(hhformer_dir, device=cfg.device)
    if cfg.freeze_hhformer:
        for p in hhformer.parameters():
            p.requires_grad = False

    student = StudentHead(StudentConfig()).module.to(torch.device(device_name))
    opt = torch.optim.AdamW(student.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    loss_fn = nn.MSELoss()

    t0 = time.perf_counter()
    for epoch in range(cfg.epochs):
        if cancel_check and cancel_check():
            raise WorkCancelled("Stopped by user")
        if progress:
            progress(
                {
                    "pct": int((epoch + 1) / max(cfg.epochs, 1) * 100),
                    "msg": f"Student epoch {epoch + 1}/{cfg.epochs}",
                    "detail": {"epoch": epoch + 1, "epochs": cfg.epochs},
                }
            )
        random.Random(cfg.seed + epoch).shuffle(train_rows)
        for start in range(0, len(train_rows), cfg.batch_size):
            batch = train_rows[start : start + cfg.batch_size]
            if not batch:
                continue
            data = collate_student_batch(batch)
            dev = torch.device(device_name)
            ids = data["token_ids"].to(dev)
            mask = data["key_padding_mask"].to(dev)
            extras = data["state_extras"].to(dev)
            targets = data["targets"].to(dev)
            with torch.no_grad():
                cls = hhformer(ids, key_padding_mask=mask)["cls"]
            pred = student(cls, extras)
            loss = loss_fn(pred, targets)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()

    student.eval()
    val_mse = 0.0
    val_kl = 0.0
    n_batches = 0
    with torch.no_grad():
        for start in range(0, len(val_rows), cfg.batch_size):
            batch = val_rows[start : start + cfg.batch_size]
            if not batch:
                continue
            data = collate_student_batch(batch)
            dev = torch.device(device_name)
            ids = data["token_ids"].to(dev)
            mask = data["key_padding_mask"].to(dev)
            extras = data["state_extras"].to(dev)
            targets = data["targets"].to(dev)
            cls = hhformer(ids, key_padding_mask=mask)["cls"]
            pred = student(cls, extras)
            val_mse += _mse(pred, targets)
            val_kl += _kl(pred, targets)
            n_batches += 1
    if n_batches:
        val_mse /= n_batches
        val_kl /= n_batches

    backends: dict[str, int] = {}
    if play_study_count:
        backends["play_study"] = play_study_count
    if training_jsonl is None and not play_study_only:
        for s in SolverCache(cache_dir).load_all():
            backends[s.backend] = backends.get(s.backend, 0) + 1

    metrics = TrainStudentMetrics(
        seed=cfg.seed,
        train_rows=len(train_rows),
        val_rows=len(val_rows),
        mse_val=val_mse,
        kl_val=val_kl,
        parameters_student=student.count_parameters(),
        device=device_name,
        teacher_backends=backends,
        finished_at=datetime.now(tz=UTC).isoformat(),
        wall_time_sec=time.perf_counter() - t0,
    )
    save_state_dict_safetensors(student.state_dict(), str(out / "student.safetensors"))
    (out / "metrics.json").write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    (out / "MODEL_CARD.md").write_text(
        _model_card(metrics, cache_dir=cache_dir, val_frac=cfg.val_frac),
        encoding="utf-8",
    )
    config_blob = {
        "hhformer_dir": str(hhformer_dir),
        "cache_dir": str(cache_dir),
        "student_config": asdict(StudentConfig()),
        "train_config": asdict(cfg),
    }
    (out / "training_data.json").write_text(json.dumps(config_blob, indent=2), encoding="utf-8")
    return metrics
