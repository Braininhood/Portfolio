"""SimCLR-style contrastive pretraining for style embeddings (Phase 8)."""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np

from poker_ai.learn._ml_deps import require_torch, save_state_dict_safetensors
from poker_ai.learn.pretrain_hhformer import _pick_device
from poker_ai.learn.style_dataset import (
    StyleWindow,
    augment_window,
    collate_style_batch,
    load_style_windows,
    split_windows_for_knn,
)
from poker_ai.models.style_encoder import StyleEncoder, StyleEncoderConfig
from poker_ai.runtime.cancel import WorkCancelled
from poker_ai.runtime.progress import ProgressFn


@dataclass(frozen=True, slots=True)
class StyleTrainConfig:
    epochs: int = 25
    batch_size: int = 256
    lr: float = 3e-4
    weight_decay: float = 0.01
    temperature: float = 0.07
    val_frac: float = 0.15
    seed: int = 42
    device: str = "auto"
    limit_hands: int | None = None


@dataclass
class StyleTrainMetrics:
    seed: int
    train_windows: int
    val_windows: int
    val_players: int
    knn_top5_acc: float
    knn_top1_acc: float
    loss_final: float
    parameters: int
    device: str
    finished_at: str
    wall_time_sec: float = 0.0


def default_style_artifact_dir() -> Path:
    return Path("artifacts/style_encoder/v1")


def simclr_loss(z_a: Any, z_b: Any, *, temperature: float) -> Any:
    """NT-Xent on two augmented views (batch must be shuffled i.i.d.)."""
    torch = require_torch()
    F = torch.nn.functional
    z = F.normalize(torch.cat([z_a, z_b], dim=0), dim=1)
    n = z_a.size(0)
    logits = (z @ z.T) / temperature
    mask = torch.eye(2 * n, device=z.device, dtype=torch.bool)
    logits = logits.masked_fill(mask, -1e9)
    targets = torch.cat(
        [
            torch.arange(n, 2 * n, device=z.device),
            torch.arange(0, n, device=z.device),
        ],
    )
    return F.cross_entropy(logits, targets)


def encode_windows(
    module: Any,
    windows: list[StyleWindow],
    *,
    device: Any,
    batch_size: int = 512,
) -> tuple[np.ndarray, list[str]]:
    """Batch-encode windows to unit vectors + parallel uid list."""
    torch = require_torch()
    module.eval()
    vecs: list[np.ndarray] = []
    uids: list[str] = []
    with torch.no_grad():
        for start in range(0, len(windows), batch_size):
            chunk = windows[start : start + batch_size]
            slots, tokens, pad_mask = collate_style_batch(chunk, device=device)
            z = module(slots, tokens, key_padding_mask=pad_mask)
            vecs.append(z.cpu().numpy())
            uids.extend(w.player_uid for w in chunk)
    if not vecs:
        return np.zeros((0, module.cfg.style_dim), dtype=np.float32), []
    return np.vstack(vecs).astype(np.float32), uids


def knn_player_retrieval_accuracy(
    embeddings: np.ndarray,
    player_uids: list[str],
    *,
    k: int = 5,
    query_indices: list[int] | None = None,
    query_embeddings: np.ndarray | None = None,
    query_uids: list[str] | None = None,
) -> tuple[float, float]:
    """Top-1 / top-5: query vectors retrieve same ``player_uid`` from the index bank."""
    if len(embeddings) < k:
        return 0.0, 0.0
    if query_embeddings is not None and query_uids is not None:
        queries = list(range(len(query_embeddings)))
        q_embs = query_embeddings
        q_uids = query_uids
    else:
        queries = query_indices if query_indices is not None else list(range(len(embeddings)))
        q_embs = embeddings
        q_uids = player_uids
    top1 = 0
    top5 = 0
    for qi in queries:
        q_uid = q_uids[qi]
        sims = embeddings @ q_embs[qi]
        order = np.argsort(-sims)
        neighbours = list(order[:k])
        hits = [player_uids[i] for i in neighbours]
        if hits and hits[0] == q_uid:
            top1 += 1
        if q_uid in hits:
            top5 += 1
    n = max(1, len(queries))
    return top1 / n, top5 / n


def run_style_contrastive(
    *,
    session_factory: Any,
    artifact_dir: Path | None = None,
    cfg: StyleTrainConfig | None = None,
    windows: list[StyleWindow] | None = None,
    progress: ProgressFn = None,
    cancel_check: Callable[[], bool] | None = None,
) -> StyleTrainMetrics:
    torch = require_torch()
    cfg = cfg or StyleTrainConfig()
    out = artifact_dir or default_style_artifact_dir()
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    if windows is None:
        import asyncio

        windows = asyncio.run(load_style_windows(session_factory, limit_hands=cfg.limit_hands))
    if len(windows) < 20:
        msg = f"Need >= 20 style windows, got {len(windows)} (ingest hands first)."
        raise ValueError(msg)

    train_w, val_w = split_windows_for_knn(windows, val_frac=cfg.val_frac, seed=cfg.seed)
    device = _pick_device(cfg.device)
    enc_cfg = StyleEncoderConfig()
    encoder = StyleEncoder(enc_cfg).module.to(device)
    opt = torch.optim.AdamW(encoder.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    rng = random.Random(cfg.seed)

    def _epoch(batch_windows: list[StyleWindow]) -> float:
        idx = list(range(len(batch_windows)))
        rng.shuffle(idx)
        losses: list[float] = []
        encoder.train()
        for start in range(0, len(idx), cfg.batch_size):
            batch_idx = idx[start : start + cfg.batch_size]
            if len(batch_idx) < 2:
                continue
            batch = [batch_windows[i] for i in batch_idx]
            view_a = [augment_window(w, rng) for w in batch]
            view_b = [augment_window(w, rng) for w in batch]
            slots_a, tok_a, pad_a = collate_style_batch(view_a, device=device)
            slots_b, tok_b, pad_b = collate_style_batch(view_b, device=device)
            z_a = encoder(slots_a, tok_a, key_padding_mask=pad_a)
            z_b = encoder(slots_b, tok_b, key_padding_mask=pad_b)
            loss = simclr_loss(z_a, z_b, temperature=cfg.temperature)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            losses.append(float(loss.item()))
        return float(np.mean(losses)) if losses else 0.0

    loss_final = 0.0
    for ep in range(cfg.epochs):
        if cancel_check and cancel_check():
            raise WorkCancelled("Stopped by user")
        loss_final = _epoch(train_w)
        if progress:
            progress(
                {
                    "pct": int((ep + 1) / max(cfg.epochs, 1) * 100),
                    "msg": f"Style encoder epoch {ep + 1}/{cfg.epochs}",
                    "detail": {"epoch": ep + 1, "epochs": cfg.epochs, "loss": loss_final},
                }
            )

    save_state_dict_safetensors(encoder.state_dict(), str(out / "style_encoder.safetensors"))
    emb_train, uids_train = encode_windows(encoder, train_w, device=device)
    emb_val, uids_val = encode_windows(encoder, val_w, device=device)
    top1, top5 = knn_player_retrieval_accuracy(
        emb_train,
        uids_train,
        k=5,
        query_indices=None,
        query_embeddings=emb_val,
        query_uids=uids_val,
    )

    metrics = StyleTrainMetrics(
        seed=cfg.seed,
        train_windows=len(train_w),
        val_windows=len(val_w),
        val_players=len({w.player_uid for w in val_w}),
        knn_top5_acc=top5,
        knn_top1_acc=top1,
        loss_final=loss_final,
        parameters=encoder.count_parameters(),
        device=str(device),
        finished_at=datetime.now(UTC).isoformat(),
        wall_time_sec=time.perf_counter() - t0,
    )
    (out / "metrics.json").write_text(
        json.dumps(asdict(metrics), indent=2),
        encoding="utf-8",
    )
    (out / "config.json").write_text(
        json.dumps(asdict(enc_cfg), indent=2, default=str),
        encoding="utf-8",
    )
    return metrics


def load_style_encoder(
    artifact_dir: Path | None = None,
    *,
    device: str = "cpu",
) -> tuple[Any, StyleEncoderConfig]:
    """Load trained weights; raises if missing."""
    from safetensors.torch import load_file

    out = artifact_dir or default_style_artifact_dir()
    weights = out / "style_encoder.safetensors"
    if not weights.is_file():
        msg = f"Style encoder weights not found: {weights}"
        raise FileNotFoundError(msg)
    cfg_path = out / "config.json"
    enc_cfg = StyleEncoderConfig()
    if cfg_path.is_file():
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
        enc_cfg = StyleEncoderConfig(
            **{k: v for k, v in raw.items() if k in enc_cfg.__dataclass_fields__}
        )
    torch = require_torch()
    module = StyleEncoder(enc_cfg).module
    module.load_state_dict(load_file(str(weights)))
    module.eval()
    module.to(torch.device(device))
    return module, enc_cfg
