"""HHFormer self-supervised pretraining (MAP + MCP + SOP)."""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from poker_ai.features.hhformer_tokens import _MAX_WINNER_SEATS
from poker_ai.learn._ml_deps import cuda_available, require_torch, save_state_dict_safetensors
from poker_ai.learn.dataset import (
    BatchTensors,
    collate_sequences,
    load_sequences_sync,
    make_train_dataloader,
    train_val_split,
)
from poker_ai.models.hhformer import HHFormer, HHFormerConfig
from poker_ai.runtime.cancel import WorkCancelled
from poker_ai.runtime.progress import ProgressFn


@dataclass(frozen=True, slots=True)
class PretrainConfig:
    epochs: int = 50
    batch_size: int = 256
    lr: float = 3e-4
    weight_decay: float = 0.01
    map_prob: float = 0.15
    mcp_prob: float = 0.15
    lambda_map: float = 0.6
    lambda_mcp: float = 0.2
    lambda_sop: float = 0.2
    val_frac: float = 0.1
    seed: int = 42
    device: str = "auto"
    max_hands: int | None = None
    num_workers: int = 0
    log_every: int = 50
    eval_every: int = 0
    amp: bool = True


@dataclass
class PretrainMetrics:
    seed: int
    epochs: int
    batch_size: int
    train_hands: int
    val_hands: int
    map_top1_acc: float
    mcp_top1_acc: float
    sop_auc: float
    probe_auc: float
    final_loss: float
    parameters: int
    device: str
    finished_at: str
    wall_time_sec: float = 0.0
    steps_per_epoch: int = 0


def estimate_training_seconds(
    n_train: int,
    epochs: int,
    batch_size: int,
    *,
    device: str,
) -> float:
    """Rough wall-clock estimate (forward+backward only; CPU vs GPU dominates)."""
    steps = epochs * max(1, math.ceil(n_train / max(1, batch_size)))
    if device == "cuda":
        sec_per_step = 0.06
    elif device == "mps":
        sec_per_step = 0.12
    else:
        sec_per_step = 1.2
    return steps * sec_per_step


def _log(msg: str) -> None:
    print(msg, flush=True)


def _mps_available() -> bool:
    torch = require_torch()
    mps = getattr(torch.backends, "mps", None)
    if mps is None:
        return False
    try:
        return bool(mps.is_available())
    except (AssertionError, RuntimeError):
        return False


def _pick_device(name: str) -> str:
    """Resolve device; fall back to CPU if CUDA/MPS was requested but unavailable."""
    requested = name.strip().lower() if name else "auto"

    if requested == "auto":
        if cuda_available():
            return "cuda"
        if _mps_available():
            return "mps"
        return "cpu"

    if requested == "cuda":
        if cuda_available():
            return "cuda"
        _log(
            "WARNING: --device cuda requested but this PyTorch build has no CUDA "
            "(CPU-only wheel). Training on CPU."
        )
        _log("  GPU install: https://pytorch.org/get-started/locally/ (choose CUDA).")
        return "cpu"

    if requested == "mps":
        if _mps_available():
            return "mps"
        _log("WARNING: --device mps requested but MPS is unavailable. Training on CPU.")
        return "cpu"

    if requested == "cpu":
        return "cpu"

    _log(f"WARNING: unknown device {name!r}; using CPU.")
    return "cpu"


def _make_grad_scaler(*, use_amp: bool) -> Any | None:
    if not use_amp:
        return None
    torch = require_torch()
    return torch.amp.GradScaler("cuda")


def _batch_to_torch(batch: BatchTensors, device: Any) -> dict[str, Any]:
    torch = require_torch()
    return {
        "token_ids": torch.tensor(batch.token_ids, dtype=torch.long, device=device),
        "attn_mask": torch.tensor(batch.attn_mask, dtype=torch.bool, device=device),
        "action_targets": torch.tensor(batch.action_targets, dtype=torch.long, device=device),
        "card_targets": torch.tensor(batch.card_targets, dtype=torch.long, device=device),
        "map_mask": torch.tensor(batch.map_mask, dtype=torch.bool, device=device),
        "mcp_mask": torch.tensor(batch.mcp_mask, dtype=torch.bool, device=device),
        "winner_seat": torch.tensor(batch.winner_seat, dtype=torch.long, device=device),
        "has_showdown": torch.tensor(batch.has_showdown, dtype=torch.bool, device=device),
        "hero_strength": torch.tensor(batch.hero_strength, dtype=torch.long, device=device),
    }


def _masked_ce(
    logits: Any,
    targets: Any,
    mask: Any,
) -> tuple[Any, float]:
    torch = require_torch()
    flat_logits = logits[mask]
    flat_targets = targets[mask]
    if flat_targets.numel() == 0:
        z = logits.sum() * 0.0
        return z, 0.0
    loss = torch.nn.functional.cross_entropy(flat_logits, flat_targets)
    pred = flat_logits.argmax(dim=-1)
    acc = (pred == flat_targets).float().mean().item()
    return loss, acc


def _binary_auc(scores: list[float], labels: list[int]) -> float:
    if not scores:
        return 0.0
    pairs = sorted(zip(scores, labels, strict=True), key=lambda x: x[0])
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    rank_sum = 0.0
    for i, (_s, lab) in enumerate(pairs, start=1):
        if lab:
            rank_sum += i
    u = rank_sum - n_pos * (n_pos + 1) / 2
    return float(u / (n_pos * n_neg))


def _linear_probe_auc(
    embeddings: Any,
    labels: Any,
    *,
    device: Any,
    steps: int = 200,
) -> float:
    """Quick logistic probe: hero preflop class vs CLS embedding."""
    torch = require_torch()
    valid = labels >= 0
    if valid.sum() < 8:
        return 0.5
    x = embeddings[valid].detach()
    y = (labels[valid] > 84).long()
    if y.unique().numel() < 2:
        return 0.5
    probe = torch.nn.Linear(x.shape[-1], 1, device=device)
    opt = torch.optim.Adam(probe.parameters(), lr=1e-2)
    for _ in range(steps):
        opt.zero_grad()
        logit = probe(x).squeeze(-1)
        loss = torch.nn.functional.binary_cross_entropy_with_logits(logit, y.float())
        loss.backward()
        opt.step()
    with torch.no_grad():
        scores = torch.sigmoid(probe(x).squeeze(-1)).cpu().tolist()
    return _binary_auc(scores, y.cpu().tolist())


def _compute_loss(
    model: Any,
    tensors: dict[str, Any],
    *,
    cfg: PretrainConfig,
) -> Any:
    torch = require_torch()
    key_padding_mask = ~tensors["attn_mask"]
    out = model(tensors["token_ids"], key_padding_mask=key_padding_mask)

    map_loss, _ = _masked_ce(
        out["action_logits"],
        tensors["action_targets"],
        tensors["map_mask"],
    )
    mcp_loss, _ = _masked_ce(
        out["card_logits"],
        tensors["card_targets"],
        tensors["mcp_mask"],
    )
    sop_loss = out["show_logits"].sum() * 0.0
    if tensors["has_showdown"].any():
        idx = tensors["has_showdown"]
        seats = tensors["winner_seat"].clamp(min=0, max=_MAX_WINNER_SEATS - 1)
        sop_loss = torch.nn.functional.cross_entropy(out["show_logits"][idx], seats[idx])

    return cfg.lambda_map * map_loss + cfg.lambda_mcp * mcp_loss + cfg.lambda_sop * sop_loss


def _run_epoch(
    model: Any,
    loader: Any,
    *,
    cfg: PretrainConfig,
    device: Any,
    optimizer: Any,
    epoch: int,
    use_amp: bool,
    scaler: Any | None,
) -> float:
    torch = require_torch()
    total_loss = 0.0
    n_batches = 0
    t0 = time.perf_counter()

    for batch_idx, collated in enumerate(loader):
        tensors = _batch_to_torch(collated, device)
        model.train()
        optimizer.zero_grad(set_to_none=True)
        if use_amp and scaler is not None:
            with torch.autocast("cuda", enabled=True):
                loss = _compute_loss(model, tensors, cfg=cfg)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            loss = _compute_loss(model, tensors, cfg=cfg)
            loss.backward()
            optimizer.step()
        total_loss += float(loss.item())
        n_batches += 1
        if cfg.log_every > 0 and batch_idx > 0 and batch_idx % cfg.log_every == 0:
            elapsed = time.perf_counter() - t0
            _log(
                f"  epoch {epoch + 1} batch {batch_idx}/{len(loader)} "
                f"loss={loss.item():.4f} elapsed={elapsed:.0f}s"
            )

    return total_loss / max(1, n_batches)


@dataclass
class _ValMetrics:
    map_acc: float
    mcp_acc: float
    sop_auc: float
    probe_auc: float


def _evaluate(
    model: Any,
    sequences: list[Any],
    *,
    cfg: PretrainConfig,
    device: Any,
    rng: random.Random,
) -> _ValMetrics:
    torch = require_torch()
    model.eval()
    map_correct_t = torch.tensor(0, device=device)
    map_total_t = torch.tensor(0, device=device)
    mcp_correct_t = torch.tensor(0, device=device)
    mcp_total_t = torch.tensor(0, device=device)
    sop_scores: list[float] = []
    sop_labels: list[int] = []
    cls_chunks: list[Any] = []
    hero: list[int] = []

    bs = min(cfg.batch_size, max(1, len(sequences)))
    for start in range(0, len(sequences), bs):
        batch = sequences[start : start + bs]
        collated = collate_sequences(batch, map_prob=cfg.map_prob, mcp_prob=cfg.mcp_prob, rng=rng)
        tensors = _batch_to_torch(collated, device)
        key_padding_mask = ~tensors["attn_mask"]
        with torch.no_grad():
            out = model(tensors["token_ids"], key_padding_mask=key_padding_mask)

        al = out["action_logits"]
        pred_a = al.argmax(dim=-1)
        tgt_a = tensors["action_targets"]
        map_valid = tensors["map_mask"] & (tgt_a >= 0)
        map_correct_t += ((pred_a == tgt_a) & map_valid).sum()
        map_total_t += map_valid.sum()

        cl = out["card_logits"]
        pred_c = cl.argmax(dim=-1)
        tgt_c = tensors["card_targets"]
        mcp_valid = tensors["mcp_mask"] & (tgt_c >= 0)
        mcp_correct_t += ((pred_c == tgt_c) & mcp_valid).sum()
        mcp_total_t += mcp_valid.sum()

        if tensors["has_showdown"].any():
            idx = tensors["has_showdown"]
            seats = tensors["winner_seat"].clamp(min=0, max=_MAX_WINNER_SEATS - 1)
            probs = torch.softmax(out["show_logits"][idx], dim=-1)
            for row, seat in zip(probs, seats[idx], strict=False):
                sop_scores.append(float(row[seat].item()))
                sop_labels.append(1)
                others = row.clone()
                others[seat] = 0
                neg = int(others.argmax().item())
                sop_scores.append(float(row[neg].item()))
                sop_labels.append(0)

        cls_chunks.append(out["cls"])
        hero.extend(collated.hero_strength)

    map_acc = float(map_correct_t.item()) / max(1, int(map_total_t.item()))
    mcp_acc = float(mcp_correct_t.item()) / max(1, int(mcp_total_t.item()))
    sop_auc = _binary_auc(sop_scores, sop_labels)
    if cls_chunks:
        emb = torch.cat(cls_chunks, dim=0)
        probe_auc = _linear_probe_auc(
            emb,
            torch.tensor(hero, device=device),
            device=device,
        )
    else:
        probe_auc = 0.5
    return _ValMetrics(map_acc=map_acc, mcp_acc=mcp_acc, sop_auc=sop_auc, probe_auc=probe_auc)


def default_artifact_dir() -> Path:
    project_root = Path(__file__).resolve().parents[3]
    return project_root / "artifacts" / "hhformer" / "v1"


def _write_model_card(path: Path, metrics: PretrainMetrics) -> None:
    body = f"""# HHFormer v1

Self-supervised hand-history encoder (Phase 5).

## Metrics (held-out)

| Metric | Value |
|--------|-------|
| MAP top-1 | {metrics.map_top1_acc:.3f} |
| MCP top-1 | {metrics.mcp_top1_acc:.3f} |
| SOP AUC | {metrics.sop_auc:.3f} |
| Strength probe AUC | {metrics.probe_auc:.3f} |

## Training

- Seed: `{metrics.seed}`
- Epochs: `{metrics.epochs}`
- Batch size: `{metrics.batch_size}`
- Parameters: `{metrics.parameters:,}`

No external LLM weights. Trained only on local hand histories.
"""
    path.write_text(body, encoding="utf-8")


def run_pretrain(
    *,
    artifact_dir: Path | None = None,
    session_factory: Any = None,
    cfg: PretrainConfig | None = None,
    progress: ProgressFn = None,
    cancel_check: Callable[[], bool] | None = None,
) -> PretrainMetrics:
    """Load hands, train HHFormer, write artifacts."""
    cfg = cfg or PretrainConfig()
    torch = require_torch()
    rng = random.Random(cfg.seed)
    torch.manual_seed(cfg.seed)

    if session_factory is None:
        from poker_ai.store.db import get_async_session_factory

        session_factory = get_async_session_factory()

    sequences = load_sequences_sync(session_factory, limit=cfg.max_hands)
    if not sequences:
        msg = "No hands in store — run ingest before training HHFormer."
        raise RuntimeError(msg)

    train_seqs, val_seqs = train_val_split(sequences, val_frac=cfg.val_frac, seed=cfg.seed)
    device_name = _pick_device(cfg.device)
    device = torch.device(device_name)
    use_amp = cfg.amp and device_name == "cuda" and cuda_available()
    scaler = _make_grad_scaler(use_amp=use_amp)

    n_train = len(train_seqs)
    steps_per_epoch = max(1, math.ceil(n_train / max(1, cfg.batch_size)))
    est_sec = estimate_training_seconds(n_train, cfg.epochs, cfg.batch_size, device=device_name)
    _log(
        f"HHFormer train: hands={len(sequences)} train={n_train} val={len(val_seqs)} "
        f"epochs={cfg.epochs} batch={cfg.batch_size} steps/epoch~{steps_per_epoch} "
        f"device={device_name} workers={cfg.num_workers} amp={use_amp}"
    )
    _log(f"Rough estimate (compute only): {est_sec / 3600:.1f} h ({est_sec:.0f} s)")
    if device_name == "cpu":
        _log("Tip: use --device cuda if you have a GPU; CPU on 30k×50 epochs is often 2–6+ h.")

    loader = make_train_dataloader(
        train_seqs,
        batch_size=cfg.batch_size,
        seed=cfg.seed,
        map_prob=cfg.map_prob,
        mcp_prob=cfg.mcp_prob,
        num_workers=cfg.num_workers,
    )

    wrapper = HHFormer(HHFormerConfig())
    model = wrapper.module.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    wall0 = time.perf_counter()
    final_loss = 0.0
    for epoch in range(cfg.epochs):
        if cancel_check and cancel_check():
            raise WorkCancelled("Stopped by user")
        ep_t0 = time.perf_counter()
        final_loss = _run_epoch(
            model,
            loader,
            cfg=cfg,
            device=device,
            optimizer=optimizer,
            epoch=epoch,
            use_amp=use_amp,
            scaler=scaler,
        )
        _log(
            f"epoch {epoch + 1}/{cfg.epochs} avg_loss={final_loss:.4f} "
            f"elapsed={time.perf_counter() - ep_t0:.0f}s"
        )
        if progress:
            progress(
                {
                    "pct": int((epoch + 1) / max(cfg.epochs, 1) * 100),
                    "msg": f"Epoch {epoch + 1}/{cfg.epochs} - loss {final_loss:.4f}",
                    "detail": {
                        "epoch": epoch + 1,
                        "epochs": cfg.epochs,
                        "loss": final_loss,
                    },
                }
            )
        if cfg.eval_every > 0 and (epoch + 1) % cfg.eval_every == 0:
            mid = _evaluate(model, val_seqs, cfg=cfg, device=device, rng=rng)
            _log(f"  val MAP={mid.map_acc:.3f} SOP_AUC={mid.sop_auc:.3f} probe={mid.probe_auc:.3f}")

    val = _evaluate(model, val_seqs, cfg=cfg, device=device, rng=rng)
    wall_time = time.perf_counter() - wall0

    metrics = PretrainMetrics(
        seed=cfg.seed,
        epochs=cfg.epochs,
        batch_size=cfg.batch_size,
        train_hands=len(train_seqs),
        val_hands=len(val_seqs),
        map_top1_acc=val.map_acc,
        mcp_top1_acc=val.mcp_acc,
        sop_auc=val.sop_auc,
        probe_auc=val.probe_auc,
        final_loss=final_loss,
        parameters=wrapper.count_parameters(),
        device=device_name,
        finished_at=datetime.now(UTC).isoformat(),
        wall_time_sec=wall_time,
        steps_per_epoch=steps_per_epoch,
    )

    out_dir = artifact_dir or default_artifact_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics.json").write_text(
        json.dumps(asdict(metrics), indent=2),
        encoding="utf-8",
    )
    _write_model_card(out_dir / "MODEL_CARD.md", metrics)

    save_state_dict_safetensors(model.state_dict(), str(out_dir / "weights.safetensors"))
    return metrics
