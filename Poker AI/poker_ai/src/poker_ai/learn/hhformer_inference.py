"""Load HHFormer weights and export per-hand CLS embeddings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.core.cards import cards_from_space_separated
from poker_ai.features.hhformer_tokens import TOK_PAD, encode_hand_sequence
from poker_ai.features.range import one_hot_range_from_hole_string, uniform_range
from poker_ai.ingest.records import ParsedHand
from poker_ai.learn._ml_deps import require_torch
from poker_ai.learn.pretrain_hhformer import _pick_device, default_artifact_dir
from poker_ai.models.hhformer import HHFormer, HHFormerConfig


@dataclass(frozen=True, slots=True)
class EmbedConfig:
    weights_dir: Path
    device: str = "auto"
    batch_size: int = 256
    max_hands: int | None = None
    with_equity: bool = False
    mc_samples: int = 500


def hero_equity_vs_random(hand: ParsedHand, *, mc_samples: int = 500) -> float | None:
    """Phase 4 link: hero combo vs uniform range (exact postflop, MC preflop/partial)."""
    if not hand.hero_cards or not hand.hero_cards.strip():
        return None
    try:
        hero_range = one_hot_range_from_hole_string(hand.hero_cards)
    except ValueError:
        return None
    opp = uniform_range()
    board = cards_from_space_separated(hand.board_cards)
    if len(board) >= 5:
        from poker_ai.equity import equity_range_vs_range

        return float(equity_range_vs_range(hero_range, opp, board))
    from poker_ai.equity.mc import mc_equity_range_vs_range

    return float(
        mc_equity_range_vs_range(
            hero_range,
            opp,
            board,
            n_samples=mc_samples,
            seed=hand.hand_id,
        )
    )


def load_hhformer(
    weights_dir: Path | None = None,
    *,
    device: str = "auto",
) -> tuple[Any, HHFormerConfig, str]:
    """Load weights into an eval model; returns ``(module, config, device_name)``."""
    torch = require_torch()
    from safetensors.torch import load_file

    root = weights_dir or default_artifact_dir()
    weights_path = root / "weights.safetensors"
    if not weights_path.is_file():
        msg = f"Missing weights: {weights_path}"
        raise FileNotFoundError(msg)

    cfg = HHFormerConfig()
    wrapper = HHFormer(cfg)
    state = load_file(str(weights_path))
    wrapper.module.load_state_dict(state)
    device_name = _pick_device(device)
    dev = torch.device(device_name)
    model = wrapper.module.to(dev)
    model.eval()
    return model, cfg, device_name


def _encode_batch(
    model: Any,
    sequences: list[Any],
    *,
    device: Any,
    max_len: int,
) -> list[list[float]]:
    torch = require_torch()
    token_rows: list[list[int]] = []
    masks: list[list[bool]] = []
    for seq in sequences:
        token_rows.append(list(seq.token_ids))
        masks.append([t != TOK_PAD for t in seq.token_ids])

    ids = torch.tensor(token_rows, dtype=torch.long, device=device)
    mask = torch.tensor(masks, dtype=torch.bool, device=device)
    with torch.no_grad():
        cls = model.encode(ids, key_padding_mask=~mask)
    return [row.detach().cpu().tolist() for row in cls]


async def _iter_hands_batched(
    session_factory: Any,
    *,
    batch_size: int,
    max_hands: int | None,
) -> Any:
    from poker_ai.store.loader import iter_parsed_hands_since

    batch: list[ParsedHand] = []
    n = 0
    async with session_factory() as session:
        async for hand in iter_parsed_hands_since(session):
            batch.append(hand)
            n += 1
            if len(batch) >= batch_size:
                yield batch
                batch = []
            if max_hands is not None and n >= max_hands:
                break
    if batch:
        yield batch


def export_embeddings_jsonl(
    session_factory: Any,
    out: Path,
    *,
    cfg: EmbedConfig,
) -> int:
    """Write one JSON object per hand: ``hand_id``, ``embedding``, optional ``hero_equity``."""
    import asyncio

    model, hcfg, device_name = load_hhformer(cfg.weights_dir, device=cfg.device)
    torch = require_torch()
    device = torch.device(device_name)

    out.parent.mkdir(parents=True, exist_ok=True)
    n_written = 0

    async def _run() -> int:
        nonlocal n_written
        with out.open("w", encoding="utf-8") as fp:
            async for batch_hands in _iter_hands_batched(
                session_factory,
                batch_size=cfg.batch_size,
                max_hands=cfg.max_hands,
            ):
                batch_seqs = [encode_hand_sequence(h) for h in batch_hands]
                vecs = _encode_batch(model, batch_seqs, device=device, max_len=hcfg.max_len)
                for hand, seq, emb in zip(batch_hands, batch_seqs, vecs, strict=True):
                    row: dict[str, object] = {
                        "hand_id": hand.hand_id,
                        "embedding": emb,
                        "hero_strength_class": seq.hero_strength_class,
                    }
                    if cfg.with_equity:
                        eq = hero_equity_vs_random(hand, mc_samples=cfg.mc_samples)
                        if eq is not None:
                            row["hero_equity"] = eq
                    fp.write(json.dumps(row, separators=(",", ":")))
                    fp.write("\n")
                    n_written += 1
        return n_written

    return asyncio.run(_run())
