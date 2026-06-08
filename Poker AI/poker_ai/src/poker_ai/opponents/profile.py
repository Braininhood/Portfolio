"""Style index + player profile lookup (Phase 8)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from poker_ai.ingest.records import ParsedHand
from poker_ai.learn.style_contrastive import encode_windows, load_style_encoder
from poker_ai.learn.style_dataset import StyleWindow, build_windows_from_hands, windows_from_hand
from poker_ai.opponents.metrics import ClassicalStats, compute_classical_stats


@dataclass(frozen=True, slots=True)
class NeighbourHit:
    player_uid: str
    similarity: float
    hand_id: int


@dataclass(frozen=True, slots=True)
class PlayerStyleProfile:
    player_uid: str
    style_vector: tuple[float, ...]
    classical: ClassicalStats
    neighbours: tuple[NeighbourHit, ...]


@dataclass
class StyleIndex:
    """In-memory embedding bank for kNN retrieval."""

    embeddings: np.ndarray
    windows: list[StyleWindow]

    def nearest(
        self,
        query: np.ndarray,
        *,
        k: int = 5,
        exclude_uid: str | None = None,
    ) -> list[NeighbourHit]:
        if len(self.embeddings) == 0:
            return []
        q = query.astype(np.float32)
        q = q / (np.linalg.norm(q) + 1e-8)
        sims = self.embeddings @ q
        order = np.argsort(-sims)
        hits: list[NeighbourHit] = []
        for idx in order:
            w = self.windows[idx]
            if exclude_uid and w.player_uid == exclude_uid:
                continue
            hits.append(
                NeighbourHit(
                    player_uid=w.player_uid,
                    similarity=float(sims[idx]),
                    hand_id=w.hand_id,
                )
            )
            if len(hits) >= k:
                break
        return hits


def build_style_index(
    hands: list[ParsedHand],
    *,
    artifact_dir: Path | None = None,
    device: str = "cpu",
) -> StyleIndex:
    windows = build_windows_from_hands(hands)
    module, _ = load_style_encoder(artifact_dir, device=device)
    from poker_ai.learn._ml_deps import require_torch

    dev = require_torch().device(device)
    emb, _ = encode_windows(module, windows, device=dev)
    return StyleIndex(embeddings=emb, windows=windows)


def profile_for_player(
    player_uid: str,
    hands: list[ParsedHand],
    *,
    artifact_dir: Path | None = None,
    device: str = "cpu",
    k_neighbours: int = 5,
) -> PlayerStyleProfile | None:
    """Aggregate style vector + kNN neighbours + classical stats."""
    player_hands = [h for h in hands if any(p.player_uid == player_uid for p in h.players)]
    if not player_hands:
        return None

    classical = compute_classical_stats(player_uid, player_hands)
    try:
        module, _ = load_style_encoder(artifact_dir, device=device)
    except FileNotFoundError:
        zero = tuple(0.0 for _ in range(64))
        return PlayerStyleProfile(
            player_uid=player_uid,
            style_vector=zero,
            classical=classical,
            neighbours=(),
        )

    from poker_ai.learn._ml_deps import require_torch
    from poker_ai.learn.style_dataset import collate_style_batch

    dev = require_torch().device(device)
    # Representative window: last actions across recent hands.
    recent_windows = []
    for hand in player_hands[-50:]:
        recent_windows.extend(windows_from_hand(hand))
    player_windows = [w for w in recent_windows if w.player_uid == player_uid]
    if not player_windows:
        style_vec = tuple(0.0 for _ in range(64))
    else:
        w = player_windows[-1]
        slots, tokens, pad = collate_style_batch([w], device=dev)
        with require_torch().no_grad():
            z = module(slots, tokens, key_padding_mask=pad)
        style_vec = tuple(float(x) for x in z[0].cpu().numpy())

    index = build_style_index(hands, artifact_dir=artifact_dir, device=device)
    q = np.asarray(style_vec, dtype=np.float32)
    neighbours = tuple(index.nearest(q, k=k_neighbours, exclude_uid=player_uid))

    return PlayerStyleProfile(
        player_uid=player_uid,
        style_vector=style_vec,
        classical=classical,
        neighbours=neighbours,
    )


def format_profile_report(profile: PlayerStyleProfile) -> str:
    """Human-readable CLI report."""
    lines = [
        f"player_uid: {profile.player_uid}",
        f"style_dim: {len(profile.style_vector)}",
        f"style_vector: {json.dumps([round(x, 4) for x in profile.style_vector[:8]])} …",
        "",
        "classical_stats:",
        f"  hands_dealt: {profile.classical.hands_dealt}",
        f"  VPIP: {profile.classical.vpip * 100:.1f}%",
        f"  PFR: {profile.classical.pfr * 100:.1f}%",
        f"  AF: {profile.classical.aggression_factor:.2f}",
        "",
        "nearest_style_neighbours:",
    ]
    if not profile.neighbours:
        lines.append("  (none — train style encoder or ingest more hands)")
    for n in profile.neighbours:
        lines.append(f"  uid={n.player_uid[:12]}… sim={n.similarity:.3f} hand_id={n.hand_id}")
    return "\n".join(lines)
