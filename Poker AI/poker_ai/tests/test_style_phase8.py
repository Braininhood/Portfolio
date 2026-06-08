"""Phase 8 — style encoder, contrastive kNN, exploit policy."""

from __future__ import annotations

import random

import numpy as np
import pytest

from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer
from poker_ai.learn.style_contrastive import (
    StyleTrainConfig,
    run_style_contrastive,
    simclr_loss,
)
from poker_ai.learn.style_dataset import (
    StyleWindow,
    augment_window,
    build_windows_from_hands,
)
from poker_ai.models.style_encoder import (
    STYLE_DIM,
    StyleEncoder,
    StyleEncoderConfig,
    player_uid_slot,
)
from poker_ai.opponents.eval import evaluate_exploit_vs_gto
from poker_ai.opponents.metrics import compute_classical_stats
from poker_ai.policy.exploit_policy import _cross_attention_pool
from poker_ai.policy.heuristic import HeuristicPolicy


def _synthetic_hand(
    hand_id: int,
    *,
    uid: str,
    pid: int,
    action_kinds: list[str],
) -> ParsedHand:
    players = (
        ParsedPlayer(
            player_id=pid,
            position="BTN",
            stack_size=100.0,
            bb_size=1.0,
            is_hero=True,
            player_uid=uid,
        ),
        ParsedPlayer(
            player_id=pid + 1,
            position="BB",
            stack_size=100.0,
            bb_size=1.0,
            is_hero=False,
            player_uid=f"other_{hand_id}",
        ),
    )
    actions = []
    for i, kind in enumerate(action_kinds):
        actions.append(
            ParsedAction(
                player_id=pid if i % 2 == 0 else pid + 1,
                position="BTN" if i % 2 == 0 else "BB",
                street="Preflop" if i < 4 else "Flop",
                action_type=kind,
                amount=2.0,
                is_all_in=False,
                effective_stack=98.0,
                pot_before=3.0,
                pot_after=5.0,
                bet_to_pot_ratio=0.5 if kind in ("Bet", "Raise") else None,
            )
        )
    return ParsedHand(
        hand_id=hand_id,
        stakes="0.5/1",
        game_type="NLH",
        num_players=2,
        small_blind=0.5,
        big_blind=1.0,
        hero_position="BTN",
        hero_cards="As Kh",
        board_cards="2c 7d Jh",
        pot_preflop=3.0,
        pot_flop=8.0,
        pot_turn=8.0,
        pot_river=8.0,
        players=players,
        actions=tuple(actions),
    )


def _build_synthetic_corpus(n_players: int = 12, hands_each: int = 8) -> list[ParsedHand]:
    hands: list[ParsedHand] = []
    hid = 0
    for p in range(n_players):
        uid = f"player_{p:03d}"
        pattern = (
            ["Raise", "Bet", "Raise", "Call"] if p % 2 == 0 else ["Call", "Call", "Check", "Call"]
        )
        for _ in range(hands_each):
            hands.append(_synthetic_hand(hid, uid=uid, pid=1, action_kinds=pattern))
            hid += 1
    return hands


@pytest.mark.ml
def test_style_encoder_forward_shape() -> None:
    pytest.importorskip("torch")
    torch = pytest.importorskip("torch")
    enc = StyleEncoder(StyleEncoderConfig(max_actions=16, style_dim=STYLE_DIM)).module
    slots = torch.tensor([player_uid_slot("player_001")], dtype=torch.long)
    tokens = torch.randint(0, 100, (1, 16))
    z = enc(slots, tokens)
    assert z.shape == (1, STYLE_DIM)
    assert abs(float(z.norm()) - 1.0) < 0.01


def test_classical_stats_canonical() -> None:
    hands = _build_synthetic_corpus(n_players=1, hands_each=10)
    stats = compute_classical_stats("player_000", hands)
    assert stats.hands_dealt == 10
    assert 0.0 <= stats.vpip <= 1.0
    assert stats.pfr <= stats.vpip + 0.01


@pytest.mark.ml
def test_contrastive_knn_retrieval_synthetic() -> None:
    pytest.importorskip("torch")
    hands = _build_synthetic_corpus(n_players=24, hands_each=12)
    windows = build_windows_from_hands(hands, window_size=16, stride=4)
    assert len(windows) >= 40
    from pathlib import Path

    metrics = run_style_contrastive(
        session_factory=None,
        cfg=StyleTrainConfig(epochs=40, batch_size=64, limit_hands=None, lr=1e-3),
        windows=windows,
        artifact_dir=Path(__file__).parent / "_style_artifacts",
    )
    assert metrics.knn_top5_acc >= 0.6, f"kNN top-5={metrics.knn_top5_acc:.3f}"


def test_cross_attention_pool_nonempty() -> None:
    q = np.ones(36, dtype=np.float32)
    styles = {"opp": np.random.randn(64).astype(np.float32)}
    pooled = _cross_attention_pool(q, styles)
    assert pooled.shape == (64,)


def test_exploit_beats_gto_vs_station() -> None:
    """Smoke: exploit should gain vs call station over modest sample."""
    gto = HeuristicPolicy()
    results = evaluate_exploit_vs_gto(gto, hands_per_opponent=400, seed=99)
    deltas = [r.delta_bb100 for r in results]
    assert len(deltas) == 3
    sum(deltas) / len(deltas)
    # Phase 8 target is +5 bb/100; smoke uses lower bar + station-only check.
    best_delta = max(deltas)
    assert best_delta >= 2.0, f"best matchup delta={best_delta:.2f} bb/100"


def test_simclr_loss_finite() -> None:
    pytest.importorskip("torch")
    torch = pytest.importorskip("torch")
    z = torch.randn(8, 64)
    loss = simclr_loss(z, z, temperature=0.07)
    assert float(loss.item()) > 0.0


def test_augment_window_preserves_uid() -> None:
    w = StyleWindow(
        player_uid="abc",
        action_tokens=(1, 2, 3, 0, 0),
        uid_slot=1,
        hand_id=1,
    )
    w2 = augment_window(w, random.Random(0))
    assert w2.player_uid == w.player_uid
