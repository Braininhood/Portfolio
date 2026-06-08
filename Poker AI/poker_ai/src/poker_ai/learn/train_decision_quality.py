"""Train decision quality audit head on DB hero spots (blueprint v2)."""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from poker_ai.learn._ml_deps import require_torch, save_state_dict_safetensors
from poker_ai.learn.decision_quality_dataset import (
    DecisionQualityRow,
    collate_quality_batch,
    load_decision_quality_rows_sync,
)
from poker_ai.learn.hhformer_inference import load_hhformer
from poker_ai.learn.train_student import split_train_val_rows
from poker_ai.models.decision_quality_head import DecisionQualityHead
from poker_ai.runtime.cancel import WorkCancelled
from poker_ai.runtime.progress import ProgressFn


@dataclass(frozen=True, slots=True)
class TrainDecisionQualityConfig:
    epochs: int = 15
    batch_size: int = 64
    lr: float = 1e-3
    weight_decay: float = 0.01
    val_frac: float = 0.1
    seed: int = 42
    device: str = "auto"
    row_limit: int = 5000
    max_hands: int = 20_000


@dataclass
class TrainDecisionQualityMetrics:
    seed: int
    train_rows: int
    val_rows: int
    mse_val: float
    mean_quality: float
    parameters: int
    device: str
    finished_at: str
    wall_time_sec: float = 0.0


def run_train_decision_quality(
    *,
    hhformer_dir: Path = Path("artifacts/hhformer/v1"),
    artifact_dir: Path | None = None,
    cfg: TrainDecisionQualityConfig | None = None,
    progress: ProgressFn = None,
    cancel_check: Callable[[], bool] | None = None,
) -> TrainDecisionQualityMetrics:
    torch = require_torch()
    nn = torch.nn
    cfg = cfg or TrainDecisionQualityConfig()
    out = artifact_dir or Path("artifacts/decision_quality/v1")
    out.mkdir(parents=True, exist_ok=True)

    if progress:
        progress({"pct": 5, "msg": "Loading hero decision rows from library…"})
    rows = load_decision_quality_rows_sync(limit=cfg.row_limit, max_hands=cfg.max_hands)
    if len(rows) < 50:
        msg = "Need >=50 hero decision rows — import hands and run equity backfill first."
        raise ValueError(msg)

    train_rows, val_rows = split_train_val_rows(rows, cfg.val_frac, cfg.seed)
    hhformer, _, device_name = load_hhformer(hhformer_dir, device=cfg.device)
    for p in hhformer.parameters():
        p.requires_grad = False

    head = DecisionQualityHead().module.to(torch.device(device_name))
    opt = torch.optim.AdamW(head.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    loss_fn = nn.MSELoss()
    t0 = time.perf_counter()

    for epoch in range(cfg.epochs):
        if cancel_check and cancel_check():
            raise WorkCancelled("Stopped by user")
        if progress:
            progress(
                {
                    "pct": int((epoch + 1) / max(cfg.epochs, 1) * 100),
                    "msg": f"Decision quality epoch {epoch + 1}/{cfg.epochs}",
                }
            )
        random.Random(cfg.seed + epoch).shuffle(train_rows)
        for start in range(0, len(train_rows), cfg.batch_size):
            batch: list[DecisionQualityRow] = train_rows[start : start + cfg.batch_size]
            if not batch:
                continue
            data = collate_quality_batch(batch)
            dev = torch.device(device_name)
            ids = data["token_ids"].to(dev)
            mask = data["key_padding_mask"].to(dev)
            extras = data["state_extras"].to(dev)
            targets = data["targets"].to(dev)
            with torch.no_grad():
                cls = hhformer(ids, key_padding_mask=mask)["cls"]
            pred = head(cls, extras)
            loss = loss_fn(pred, targets)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()

    val_mse = 0.0
    n_batches = 0
    head.eval()
    with torch.no_grad():
        for start in range(0, len(val_rows), cfg.batch_size):
            batch = val_rows[start : start + cfg.batch_size]
            if not batch:
                continue
            data = collate_quality_batch(batch)
            dev = torch.device(device_name)
            ids = data["token_ids"].to(dev)
            mask = data["key_padding_mask"].to(dev)
            extras = data["state_extras"].to(dev)
            targets = data["targets"].to(dev)
            cls = hhformer(ids, key_padding_mask=mask)["cls"]
            pred = head(cls, extras)
            val_mse += float(((pred - targets) ** 2).mean().item())
            n_batches += 1
    if n_batches:
        val_mse /= n_batches

    mean_q = sum(r.target_quality for r in rows) / len(rows)
    metrics = TrainDecisionQualityMetrics(
        seed=cfg.seed,
        train_rows=len(train_rows),
        val_rows=len(val_rows),
        mse_val=val_mse,
        mean_quality=mean_q,
        parameters=sum(p.numel() for p in head.parameters() if p.requires_grad),
        device=device_name,
        finished_at=datetime.now(tz=UTC).isoformat(),
        wall_time_sec=time.perf_counter() - t0,
    )
    save_state_dict_safetensors(head.state_dict(), str(out / "decision_quality.safetensors"))
    (out / "metrics.json").write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    return metrics
