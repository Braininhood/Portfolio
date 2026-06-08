"""Train DeepStack-lite value head on solver cache (blueprint v2)."""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from poker_ai.learn._ml_deps import require_torch, save_state_dict_safetensors
from poker_ai.learn.hhformer_inference import load_hhformer
from poker_ai.learn.train_student import split_train_val_rows
from poker_ai.learn.value_net_dataset import ValueRow, collate_value_batch, load_value_rows
from poker_ai.models.value_net import ValueNetHead
from poker_ai.runtime.cancel import WorkCancelled
from poker_ai.runtime.progress import ProgressFn
from poker_ai.solver.bridge.cache import SolverCache


@dataclass(frozen=True, slots=True)
class TrainValueNetConfig:
    epochs: int = 20
    batch_size: int = 128
    lr: float = 1e-3
    weight_decay: float = 0.01
    val_frac: float = 0.1
    seed: int = 42
    device: str = "auto"


@dataclass
class TrainValueNetMetrics:
    seed: int
    train_rows: int
    val_rows: int
    mse_val: float
    parameters: int
    device: str
    finished_at: str
    wall_time_sec: float = 0.0


def run_train_value_net(
    *,
    cache_dir: Path = Path("artifacts/solver_cache"),
    hhformer_dir: Path = Path("artifacts/hhformer/v1"),
    artifact_dir: Path | None = None,
    cfg: TrainValueNetConfig | None = None,
    progress: ProgressFn = None,
    cancel_check: Callable[[], bool] | None = None,
) -> TrainValueNetMetrics:
    torch = require_torch()
    nn = torch.nn
    cfg = cfg or TrainValueNetConfig()
    out = artifact_dir or Path("artifacts/value_net/v1")
    out.mkdir(parents=True, exist_ok=True)

    rows = load_value_rows(SolverCache(cache_dir))
    if not rows:
        msg = f"No solver cache rows in {cache_dir} — run solve grid first."
        raise ValueError(msg)

    train_rows, val_rows = split_train_val_rows(rows, cfg.val_frac, cfg.seed)
    hhformer, _, device_name = load_hhformer(hhformer_dir, device=cfg.device)
    for p in hhformer.parameters():
        p.requires_grad = False

    head = ValueNetHead().module.to(torch.device(device_name))
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
                    "msg": f"Value net epoch {epoch + 1}/{cfg.epochs}",
                }
            )
        random.Random(cfg.seed + epoch).shuffle(train_rows)
        for start in range(0, len(train_rows), cfg.batch_size):
            batch: list[ValueRow] = train_rows[start : start + cfg.batch_size]
            if not batch:
                continue
            data = collate_value_batch(batch)
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
            data = collate_value_batch(batch)
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

    metrics = TrainValueNetMetrics(
        seed=cfg.seed,
        train_rows=len(train_rows),
        val_rows=len(val_rows),
        mse_val=val_mse,
        parameters=sum(p.numel() for p in head.parameters() if p.requires_grad),
        device=device_name,
        finished_at=datetime.now(tz=UTC).isoformat(),
        wall_time_sec=time.perf_counter() - t0,
    )
    save_state_dict_safetensors(head.state_dict(), str(out / "value_net.safetensors"))
    (out / "metrics.json").write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    return metrics
