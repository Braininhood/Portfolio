"""Style encoder — small transformer over (player_uid, last N actions) → 64-dim (Phase 8)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from poker_ai.features.sequence import TOK_PAD, pack_action_token
from poker_ai.ingest.records import ParsedAction, ParsedHand

STYLE_DIM = 64
DEFAULT_MAX_ACTIONS = 32
# Packed action tokens fit in ~20 bits; reserve PAD + BOS.
ACTION_VOCAB_SIZE = 4096
PLAYER_UID_SLOTS = 16_384


def player_uid_slot(player_uid: str, *, n_slots: int = PLAYER_UID_SLOTS) -> int:
    """Stable embedding index for an HMAC player uid."""
    digest = hashlib.sha256(player_uid.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % n_slots


def actions_to_tokens(
    actions: tuple[ParsedAction, ...],
    *,
    num_players: int,
    max_actions: int = DEFAULT_MAX_ACTIONS,
) -> tuple[int, ...]:
    """Pack the last ``max_actions`` actions into fixed-length token ids (PAD=0)."""
    tail = actions[-max_actions:] if len(actions) > max_actions else actions
    tokens = [pack_action_token(a, num_players=num_players) % ACTION_VOCAB_SIZE for a in tail]
    while len(tokens) < max_actions:
        tokens.insert(0, TOK_PAD)
    return tuple(tokens[-max_actions:])


@dataclass(frozen=True, slots=True)
class StyleEncoderConfig:
    """Small transformer (~1–2 M params at defaults)."""

    dim: int = 128
    depth: int = 2
    heads: int = 4
    ff_mult: int = 4
    max_actions: int = DEFAULT_MAX_ACTIONS
    style_dim: int = STYLE_DIM
    action_vocab_size: int = ACTION_VOCAB_SIZE
    player_uid_slots: int = PLAYER_UID_SLOTS
    dropout: float = 0.1


def _build_style_encoder_module(cfg: StyleEncoderConfig) -> Any:
    from poker_ai.learn._ml_deps import require_torch

    torch = require_torch()
    nn = torch.nn
    F = torch.nn.functional

    class _StyleBlock(nn.Module):
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

    class _StyleEncoder(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.cfg = cfg
            self.player_emb = nn.Embedding(cfg.player_uid_slots, cfg.dim)
            self.action_emb = nn.Embedding(cfg.action_vocab_size, cfg.dim)
            self.pos = nn.Embedding(cfg.max_actions + 1, cfg.dim)
            self.blocks = nn.ModuleList([_StyleBlock() for _ in range(cfg.depth)])
            self.ln = nn.LayerNorm(cfg.dim)
            self.proj = nn.Linear(cfg.dim, cfg.style_dim)

        def forward(
            self,
            player_slots: Any,
            action_tokens: Any,
            *,
            key_padding_mask: Any | None = None,
        ) -> Any:
            """Return L2-normalized style vectors ``[B, style_dim]``."""
            b, seq_len = action_tokens.shape
            uid_vec = self.player_emb(player_slots).unsqueeze(1)
            act = self.action_emb(action_tokens.clamp(0, cfg.action_vocab_size - 1))
            pos_ids = torch.arange(seq_len, device=action_tokens.device).unsqueeze(0).expand(b, -1)
            act = act + self.pos(pos_ids + 1)
            x = torch.cat([uid_vec, act], dim=1)
            if key_padding_mask is not None:
                uid_pad = torch.zeros(b, 1, dtype=torch.bool, device=action_tokens.device)
                key_padding_mask = torch.cat([uid_pad, key_padding_mask], dim=1)
            for block in self.blocks:
                x = block(x, key_padding_mask)
            x = self.ln(x[:, 0, :])
            z = F.normalize(self.proj(x), dim=-1)
            return z

        def count_parameters(self) -> int:
            return sum(p.numel() for p in self.parameters() if p.requires_grad)

    return _StyleEncoder


class StyleEncoder:
    """Thin wrapper around the PyTorch style encoder."""

    def __init__(self, config: StyleEncoderConfig | None = None) -> None:
        self.config = config or StyleEncoderConfig()
        self._module: Any | None = None

    @property
    def module(self) -> Any:
        if self._module is None:
            self._module = _build_style_encoder_module(self.config)()
        return self._module

    def count_parameters(self) -> int:
        return int(self.module.count_parameters())


def encode_hand_player_styles(
    hand: ParsedHand,
    *,
    max_actions: int = DEFAULT_MAX_ACTIONS,
) -> dict[str, tuple[int, ...]]:
    """Per ``player_uid`` token window for actions in this hand (chronological)."""
    by_pid: dict[int, str] = {p.player_id: p.player_uid for p in hand.players}
    per_uid: dict[str, list[ParsedAction]] = {}
    for act in hand.actions:
        uid = by_pid.get(act.player_id)
        if uid is None:
            continue
        per_uid.setdefault(uid, []).append(act)
    return {
        uid: actions_to_tokens(tuple(acts), num_players=hand.num_players, max_actions=max_actions)
        for uid, acts in per_uid.items()
    }
