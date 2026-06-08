"""HHFormer — Pre-LN transformer encoder for hand-history sequences (Phase 5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from poker_ai.features.hhformer_tokens import (
    _ACTION_VOCAB_SIZE,
    _MAX_WINNER_SEATS,
    MAX_SEQ_LEN,
    VOCAB_SIZE,
)


@dataclass(frozen=True, slots=True)
class HHFormerConfig:
    """Architecture hyper-parameters (~10 M params at defaults)."""

    vocab_size: int = VOCAB_SIZE
    dim: int = 256
    depth: int = 6
    heads: int = 8
    ff_mult: int = 4
    max_len: int = MAX_SEQ_LEN
    dropout: float = 0.1
    action_vocab_size: int = _ACTION_VOCAB_SIZE
    max_winner_seats: int = _MAX_WINNER_SEATS
    num_cards: int = 52


def _build_torch_module(cfg: HHFormerConfig) -> Any:
    from poker_ai.learn._ml_deps import require_torch

    torch = require_torch()
    nn = torch.nn

    class _PreLNBlock(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.ln1 = nn.LayerNorm(cfg.dim)
            self.attn = nn.MultiheadAttention(
                cfg.dim,
                cfg.heads,
                dropout=cfg.dropout,
                batch_first=True,
            )
            self.ln2 = nn.LayerNorm(cfg.dim)
            hidden = cfg.dim * cfg.ff_mult
            self.ff = nn.Sequential(
                nn.Linear(cfg.dim, hidden),
                nn.GELU(),
                nn.Dropout(cfg.dropout),
                nn.Linear(hidden, cfg.dim),
                nn.Dropout(cfg.dropout),
            )

        def forward(self, x: Any, key_padding_mask: Any | None) -> Any:
            h = self.ln1(x)
            attn_out, _ = self.attn(h, h, h, key_padding_mask=key_padding_mask, need_weights=False)
            x = x + attn_out
            x = x + self.ff(self.ln2(x))
            return x

    class _HHFormer(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.cfg = cfg
            self.tok = nn.Embedding(cfg.vocab_size, cfg.dim)
            self.pos = nn.Embedding(cfg.max_len, cfg.dim)
            self.blocks = nn.ModuleList([_PreLNBlock() for _ in range(cfg.depth)])
            self.ln = nn.LayerNorm(cfg.dim)
            self.head_act = nn.Linear(cfg.dim, cfg.action_vocab_size)
            self.head_card = nn.Linear(cfg.dim, cfg.num_cards)
            self.head_show = nn.Linear(cfg.dim, cfg.max_winner_seats)

        def forward(
            self,
            token_ids: Any,
            *,
            key_padding_mask: Any | None = None,
        ) -> dict[str, Any]:
            b, seq_len = token_ids.shape
            pos = torch.arange(seq_len, device=token_ids.device).unsqueeze(0).expand(b, -1)
            x = self.tok(token_ids) + self.pos(pos)
            for block in self.blocks:
                x = block(x, key_padding_mask)
            x = self.ln(x)
            return {
                "hidden": x,
                "cls": x[:, 0, :],
                "action_logits": self.head_act(x),
                "card_logits": self.head_card(x),
                "show_logits": self.head_show(x[:, 0, :]),
            }

        def encode(self, token_ids: Any, *, key_padding_mask: Any | None = None) -> Any:
            return self.forward(token_ids, key_padding_mask=key_padding_mask)["cls"]

        def count_parameters(self) -> int:
            return sum(p.numel() for p in self.parameters() if p.requires_grad)

    return _HHFormer


class HHFormer:
    """Thin wrapper exposing config + optional PyTorch module."""

    def __init__(self, config: HHFormerConfig | None = None) -> None:
        self.config = config or HHFormerConfig()
        self._module: Any | None = None

    @property
    def module(self) -> Any:
        if self._module is None:
            self._module = _build_torch_module(self.config)()
        return self._module

    def count_parameters(self) -> int:
        return int(self.module.count_parameters())
