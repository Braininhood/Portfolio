"""Train multi-way student from DB imitation (Phase 7b V2)."""

from __future__ import annotations

import asyncio
import json
import random
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from poker_ai.features.hhformer_tokens import TOK_PAD
from poker_ai.learn._ml_deps import require_torch, save_state_dict_safetensors
from poker_ai.learn.hhformer_inference import load_hhformer
from poker_ai.learn.multiway_dataset import MultiwayRow, collate_multiway_batch, load_multiway_rows
from poker_ai.models.multiway_student import MultiwayStudentConfig, MultiwayStudentHead
from poker_ai.runtime.cancel import WorkCancelled
from poker_ai.runtime.progress import ProgressFn


@dataclass(frozen=True, slots=True)
class TrainMultiwayConfig:
    epochs: int = 20
    batch_size: int = 128
    lr: float = 1e-3
    weight_decay: float = 0.01
    val_frac: float = 0.1
    seed: int = 42
    device: str = "auto"
    freeze_hhformer: bool = True
    row_limit: int | None = 50_000
    monker_export_dir: Path | None = None
    write_monker_to_cache: Path | None = None


@dataclass
class TrainMultiwayMetrics:
    seed: int
    train_rows: int
    val_rows: int
    monker_rows: int
    db_rows: int
    mse_val: float
    device: str
    finished_at: str
    wall_time_sec: float = 0.0


def default_multiway_artifact_dir() -> Path:
    return Path("artifacts/student/multiway_v1")


def _split(
    rows: list[MultiwayRow], val_frac: float, seed: int
) -> tuple[list[MultiwayRow], list[MultiwayRow]]:
    rng = random.Random(seed)
    idx = list(range(len(rows)))
    rng.shuffle(idx)
    n_val = max(1, int(len(rows) * val_frac)) if len(rows) > 10 else max(0, len(rows) // 5)
    val_idx = set(idx[:n_val])
    train = [rows[i] for i in range(len(rows)) if i not in val_idx]
    val = [rows[i] for i in val_idx]
    return train, val


def _to_tensors(batch: dict[str, Any], *, device: Any, max_len: int) -> dict[str, Any]:
    torch = require_torch()
    ids = torch.tensor(batch["token_ids"], dtype=torch.long, device=device)
    mask = torch.zeros_like(ids, dtype=torch.bool)
    for i, row in enumerate(batch["token_ids"]):
        for j, t in enumerate(row):
            if j >= max_len or t == TOK_PAD:
                mask[i, j] = True
    extras = torch.tensor(batch["state_extras"], dtype=torch.float32, device=device)
    targets = torch.tensor(batch["targets"], dtype=torch.float32, device=device)
    return {"token_ids": ids, "key_padding_mask": mask, "state_extras": extras, "targets": targets}


def run_train_multiway_student(
    *,
    session_factory: Any,
    hhformer_dir: Path = Path("artifacts/hhformer/v1"),
    artifact_dir: Path | None = None,
    cfg: TrainMultiwayConfig | None = None,
    play_study_manifest: Path | None = None,
    play_study_only: bool = False,
    progress: ProgressFn = None,
    cancel_check: Callable[[], bool] | None = None,
) -> TrainMultiwayMetrics:
    torch = require_torch()
    nn = torch.nn
    cfg = cfg or TrainMultiwayConfig()
    out = artifact_dir or default_multiway_artifact_dir()
    out.mkdir(parents=True, exist_ok=True)

    play_study_count = 0
    db_rows: list = []
    if not play_study_only:
        db_rows = asyncio.run(load_multiway_rows(session_factory, limit=cfg.row_limit, min_rows=0))
    monker_rows: list = []
    if not play_study_only and cfg.monker_export_dir is not None and cfg.monker_export_dir.is_dir():
        from poker_ai.learn.monker_rows import load_monker_training_rows

        monker_rows = load_monker_training_rows(
            cfg.monker_export_dir,
            also_write_cache=cfg.write_monker_to_cache,
        )
    rows = list(db_rows) + list(monker_rows)
    if play_study_manifest is not None and play_study_manifest.is_file():
        from poker_ai.learn.play_study_loader import load_play_study_multiway_rows

        play_rows = load_play_study_multiway_rows(manifest_path=play_study_manifest)
        play_study_count = len(play_rows)
        if play_study_only:
            rows = play_rows
        elif play_rows:
            rows = rows + play_rows
    min_rows = 1 if play_study_only else 50
    if len(rows) < min_rows:
        if play_study_only and play_study_manifest:
            msg = (
                f"No multi-way play-study rows (need 3+ players postflop) in {play_study_manifest}. "
                "Play more 6/9-max hands to showdown on the flop."
            )
        else:
            msg = (
                f"Need >= {min_rows} multi-way training rows; got {len(rows)} "
                f"(db={len(db_rows)} monker={len(monker_rows)} play={play_study_count}). "
                "Ingest hands, play 6-max vs AI, or add Monker JSON."
            )
        raise ValueError(msg)

    train_rows, val_rows = _split(rows, cfg.val_frac, cfg.seed)
    (out / "training_rows.jsonl").write_text(
        "\n".join(json.dumps({"hand_id": r.hand_id, "n_active": r.n_active}) for r in rows[:5000]),
        encoding="utf-8",
    )

    hhformer, _, device_name = load_hhformer(hhformer_dir, device=cfg.device)
    if cfg.freeze_hhformer:
        for p in hhformer.parameters():
            p.requires_grad = False

    student = MultiwayStudentHead(MultiwayStudentConfig()).module.to(torch.device(device_name))
    opt = torch.optim.AdamW(student.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    loss_fn = nn.MSELoss()
    dev = torch.device(device_name)
    max_len = 128

    t0 = time.perf_counter()
    for epoch in range(cfg.epochs):
        if cancel_check and cancel_check():
            raise WorkCancelled("Stopped by user")
        if progress:
            progress(
                {
                    "pct": int((epoch + 1) / max(cfg.epochs, 1) * 100),
                    "msg": f"Multi-way student epoch {epoch + 1}/{cfg.epochs}",
                    "detail": {"epoch": epoch + 1, "epochs": cfg.epochs},
                }
            )
        random.Random(cfg.seed + epoch).shuffle(train_rows)
        for start in range(0, len(train_rows), cfg.batch_size):
            batch = train_rows[start : start + cfg.batch_size]
            if not batch:
                continue
            data = _to_tensors(collate_multiway_batch(batch), device=dev, max_len=max_len)
            with torch.no_grad():
                cls = hhformer(data["token_ids"], key_padding_mask=data["key_padding_mask"])["cls"]
            pred = student(cls, data["state_extras"])
            loss = loss_fn(pred, data["targets"])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()

    student.eval()
    val_mse = 0.0
    n_batches = 0
    with torch.no_grad():
        for start in range(0, len(val_rows), cfg.batch_size):
            batch = val_rows[start : start + cfg.batch_size]
            if not batch:
                continue
            data = _to_tensors(collate_multiway_batch(batch), device=dev, max_len=max_len)
            cls = hhformer(data["token_ids"], key_padding_mask=data["key_padding_mask"])["cls"]
            pred = student(cls, data["state_extras"])
            val_mse += float(((pred - data["targets"]) ** 2).mean().item())
            n_batches += 1
    if n_batches:
        val_mse /= n_batches

    metrics = TrainMultiwayMetrics(
        seed=cfg.seed,
        train_rows=len(train_rows),
        val_rows=len(val_rows),
        monker_rows=len(monker_rows),
        db_rows=len(db_rows),
        mse_val=val_mse,
        device=device_name,
        finished_at=datetime.now(tz=UTC).isoformat(),
        wall_time_sec=time.perf_counter() - t0,
    )
    save_state_dict_safetensors(student.state_dict(), str(out / "student.safetensors"))
    (out / "metrics.json").write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    monker_note = (
        f"Monker export labels: **{metrics.monker_rows}** rows from `{cfg.monker_export_dir}`.\n"
        if metrics.monker_rows
        else ""
    )
    (out / "MODEL_CARD.md").write_text(
        f"# Multi-way student v1\n\n"
        f"DB imitation: **{metrics.db_rows}** hero postflop spots (`n_active>=3`).\n"
        f"{monker_note}\n"
        f"Train+val: {metrics.train_rows}+{metrics.val_rows}, val MSE: {metrics.mse_val:.4f}\n",
        encoding="utf-8",
    )
    return metrics
