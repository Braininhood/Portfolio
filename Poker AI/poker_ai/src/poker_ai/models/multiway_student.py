"""Multi-way student head (DB imitation + optional Monker labels, Phase 7b)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from poker_ai.solver.bridge.schemas import STUDENT_ACTIONS

# 28 base extras + 4 n_active bucket + 3 table-size bucket
MULTIWAY_STATE_EXTRAS_DIM = 35
N_MULTIWAY_ACTIONS = len(STUDENT_ACTIONS)


@dataclass(frozen=True, slots=True)
class MultiwayStudentConfig:
    hhformer_dim: int = 256
    state_extras_dim: int = MULTIWAY_STATE_EXTRAS_DIM
    hidden_dim: int = 512
    n_actions: int = N_MULTIWAY_ACTIONS
    dropout: float = 0.1


def _active_bucket(n_active: int) -> list[float]:
    """One-hot: 3, 4, 5, 6+ players."""
    b = [0.0, 0.0, 0.0, 0.0]
    if n_active <= 3:
        b[0] = 1.0
    elif n_active == 4:
        b[1] = 1.0
    elif n_active == 5:
        b[2] = 1.0
    else:
        b[3] = 1.0
    return b


def _table_bucket(num_seats: int) -> list[float]:
    """One-hot: short (2-6), medium (7-8), full (9-10)."""
    if num_seats <= 6:
        return [1.0, 0.0, 0.0]
    if num_seats <= 8:
        return [0.0, 1.0, 0.0]
    return [0.0, 0.0, 1.0]


def encode_multiway_extras(
    *,
    hero_is_ip: bool,
    effective_stack: int,
    pot_chips: int,
    board_texture: tuple[int, ...],
    n_active: int,
    num_seats: int,
    sizing_tree_id: str = "multiway_v1",
) -> tuple[float, ...]:
    from poker_ai.models.student import encode_state_extras

    base = encode_state_extras(
        hero_is_ip=hero_is_ip,
        effective_stack=effective_stack,
        pot_chips=pot_chips,
        board_texture=board_texture,
        sizing_tree_id=sizing_tree_id,
    )
    return tuple(base) + tuple(_active_bucket(n_active)) + tuple(_table_bucket(num_seats))


class MultiwayStudentHead:
    """Wrapper matching :class:`~poker_ai.models.student.StudentHead` API."""

    def __init__(self, cfg: MultiwayStudentConfig | None = None) -> None:
        self.cfg = cfg or MultiwayStudentConfig()
        self.module = _build_module(self.cfg)


def _build_module(cfg: MultiwayStudentConfig) -> Any:
    from poker_ai.learn._ml_deps import require_torch

    torch = require_torch()
    nn = torch.nn

    class _Head(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            in_dim = cfg.hhformer_dim + cfg.state_extras_dim
            self.mlp = nn.Sequential(
                nn.Linear(in_dim, cfg.hidden_dim),
                nn.GELU(),
                nn.Dropout(cfg.dropout),
                nn.Linear(cfg.hidden_dim, cfg.hidden_dim // 2),
                nn.GELU(),
                nn.Linear(cfg.hidden_dim // 2, cfg.n_actions),
            )

        def forward(self, cls: Any, extras: Any) -> Any:
            x = torch.cat([cls, extras], dim=-1)
            return torch.softmax(self.mlp(x), dim=-1)

    return _Head()
