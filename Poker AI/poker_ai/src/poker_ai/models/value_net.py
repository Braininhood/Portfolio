"""DeepStack-lite value head on HHFormer [CLS] + state extras (blueprint v2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from poker_ai.models.student import STATE_EXTRAS_DIM, StudentConfig

# Teacher-implied action values (pot-normalized EV proxy for regression targets).
ACTION_VALUE_PROXY: dict[str, float] = {
    "fold": -0.55,
    "check_call": 0.0,
    "bet_33": 0.12,
    "bet_66": 0.22,
    "allin": 0.35,
}


@dataclass(frozen=True, slots=True)
class ValueNetConfig:
    hhformer_dim: int = 256
    state_extras_dim: int = STATE_EXTRAS_DIM
    hidden_dim: int = 256
    dropout: float = 0.1


def teacher_value_target(action_labels: tuple[str, ...], frequencies: tuple[float, ...]) -> float:
    """Scalar target in [-1, 1] from teacher action frequencies."""
    total = 0.0
    weight = 0.0
    for label, freq in zip(action_labels, frequencies, strict=False):
        v = ACTION_VALUE_PROXY.get(label, 0.0)
        total += float(freq) * v
        weight += float(freq)
    if weight <= 0:
        return 0.0
    return max(-1.0, min(1.0, total / weight))


def _build_value_module(cfg: ValueNetConfig) -> Any:
    from poker_ai.learn._ml_deps import require_torch

    torch = require_torch()
    nn = torch.nn

    class _ValueHead(nn.Module):
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
            return torch.tanh(self.mlp(x).squeeze(-1))

    return _ValueHead


class ValueNetHead:
    """Scalar state-value regressor."""

    def __init__(self, config: ValueNetConfig | None = None) -> None:
        self.config = config or ValueNetConfig()
        self._module: Any | None = None

    @property
    def module(self) -> Any:
        if self._module is None:
            self._module = _build_value_module(self.config)()
        return self._module

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.module.parameters() if p.requires_grad)
