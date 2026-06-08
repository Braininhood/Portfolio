"""Solver-distilled student head on HHFormer [CLS] embeddings (Phase 7)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from poker_ai.models.hhformer import HHFormerConfig
from poker_ai.solver.bridge.schemas import STUDENT_ACTIONS

# position (2) + spr_bucket (5) + board_texture (16) + tree_id_hash (4) + pot_norm (1)
STATE_EXTRAS_DIM = 28
N_STUDENT_ACTIONS = len(STUDENT_ACTIONS)


@dataclass(frozen=True, slots=True)
class StudentConfig:
    """Small MLP student (~5 M params with frozen HHFormer)."""

    hhformer_dim: int = 256
    state_extras_dim: int = STATE_EXTRAS_DIM
    hidden_dim: int = 512
    n_actions: int = N_STUDENT_ACTIONS
    dropout: float = 0.1


def spr_bucket_index(effective_stack: int, pot_chips: int) -> int:
    spr = effective_stack / max(1, pot_chips)
    if spr < 2:
        return 0
    if spr < 4:
        return 1
    if spr < 8:
        return 2
    if spr < 15:
        return 3
    return 4


def encode_state_extras(
    *,
    hero_is_ip: bool,
    effective_stack: int,
    pot_chips: int,
    board_texture: tuple[int, ...],
    sizing_tree_id: str,
) -> tuple[float, ...]:
    """Fixed-length extras for the student MLP (matches training rows)."""
    pos = [0.0, 0.0]
    pos[1 if hero_is_ip else 0] = 1.0
    spr = [0.0] * 5
    spr[spr_bucket_index(effective_stack, pot_chips)] = 1.0
    tex = [float(x) / 255.0 for x in board_texture[:16]]
    while len(tex) < 16:
        tex.append(0.0)
    tree_seed = abs(hash(sizing_tree_id)) & 0xFFFF
    tree_bits = [(tree_seed >> i) & 1 for i in range(4)]
    pot_norm = min(1.0, pot_chips / 200.0)
    return tuple(pos + spr + tex + [float(b) for b in tree_bits] + [pot_norm])


def _build_student_module(cfg: StudentConfig) -> Any:
    from poker_ai.learn._ml_deps import require_torch

    torch = require_torch()
    nn = torch.nn

    class _StudentHead(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            in_dim = cfg.hhformer_dim + cfg.state_extras_dim
            self.mlp = nn.Sequential(
                nn.Linear(in_dim, cfg.hidden_dim),
                nn.GELU(),
                nn.Dropout(cfg.dropout),
                nn.Linear(cfg.hidden_dim, cfg.hidden_dim // 2),
                nn.GELU(),
                nn.Dropout(cfg.dropout),
                nn.Linear(cfg.hidden_dim // 2, cfg.n_actions),
            )

        def forward(self, cls_embed: Any, state_extras: Any) -> Any:
            x = torch.cat([cls_embed, state_extras], dim=-1)
            return torch.softmax(self.mlp(x), dim=-1)

        def logits(self, cls_embed: Any, state_extras: Any) -> Any:
            x = torch.cat([cls_embed, state_extras], dim=-1)
            return self.mlp(x)

        def count_parameters(self) -> int:
            return sum(p.numel() for p in self.parameters() if p.requires_grad)

    return _StudentHead


class StudentHead:
    """Thin wrapper around the PyTorch student MLP."""

    def __init__(self, config: StudentConfig | None = None) -> None:
        self.config = config or StudentConfig()
        self._module: Any | None = None

    @property
    def module(self) -> Any:
        if self._module is None:
            self._module = _build_student_module(self.config)()
        return self._module

    def count_parameters(self) -> int:
        return int(self.module.count_parameters())

    @staticmethod
    def default_hhformer_config() -> HHFormerConfig:
        return HHFormerConfig()
