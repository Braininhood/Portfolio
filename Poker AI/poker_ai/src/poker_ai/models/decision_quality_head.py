"""Hero decision audit head — predicts GTO agreement score (blueprint v2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from poker_ai.models.student import STATE_EXTRAS_DIM, N_STUDENT_ACTIONS


@dataclass(frozen=True, slots=True)
class DecisionQualityConfig:
    hhformer_dim: int = 256
    state_extras_dim: int = STATE_EXTRAS_DIM
    hidden_dim: int = 256
    n_actions: int = N_STUDENT_ACTIONS
    dropout: float = 0.1


def _build_quality_module(cfg: DecisionQualityConfig) -> Any:
    from poker_ai.learn._ml_deps import require_torch

    torch = require_torch()
    nn = torch.nn

    class _QualityHead(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            in_dim = cfg.hhformer_dim + cfg.state_extras_dim
            self.mlp = nn.Sequential(
                nn.Linear(in_dim, cfg.hidden_dim),
                nn.GELU(),
                nn.Dropout(cfg.dropout),
                nn.Linear(cfg.hidden_dim, cfg.hidden_dim // 2),
                nn.GELU(),
                nn.Linear(cfg.hidden_dim // 2, 1),
            )

        def forward(self, cls_embed: Any, state_extras: Any) -> Any:
            x = torch.cat([cls_embed, state_extras], dim=-1)
            return torch.sigmoid(self.mlp(x).squeeze(-1))

    return _QualityHead


class DecisionQualityHead:
    """Predicts hero decision quality vs teacher (0 = leak, 1 = GTO-aligned)."""

    def __init__(self, config: DecisionQualityConfig | None = None) -> None:
        self.config = config or DecisionQualityConfig()
        self._module: Any | None = None

    @property
    def module(self) -> Any:
        if self._module is None:
            self._module = _build_quality_module(self.config)()
        return self._module

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.module.parameters() if p.requires_grad)
