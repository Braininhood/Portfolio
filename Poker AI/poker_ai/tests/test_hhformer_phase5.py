"""Phase 5 — HHFormer tokenisation, model, CLI."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from poker_ai.apps.cli.main import app
from poker_ai.features.hhformer_tokens import (
    KIND_ACTION,
    KIND_CARD,
    TOK_CLS,
    TOK_PAD,
    encode_hand_sequence,
    meta_players_token,
    packed_to_action_vocab,
    winner_seat_index,
)
from poker_ai.features.sequence import pack_action_token
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer, ParsedResult
from poker_ai.learn.dataset import collate_sequences, sequence_targets, train_val_split

runner = CliRunner()


def _sample_hand(*, with_showdown: bool = True) -> ParsedHand:
    players = (
        ParsedPlayer(1, "BTN", 200.0, 100.0, True, "u1", None),
        ParsedPlayer(2, "BB", 200.0, 100.0, False, "u2", None),
    )
    results: tuple[ParsedResult, ...] = ()
    if with_showdown:
        results = (
            ParsedResult(1, "BTN", "AhKd", 10.0, 10.0, True),
            ParsedResult(2, "BB", "", -10.0, 0.0, False),
        )
    return ParsedHand(
        hand_id=7,
        stakes="1/2",
        game_type="NLH",
        num_players=2,
        small_blind=1.0,
        big_blind=2.0,
        hero_position="BTN",
        hero_cards="AhKd",
        board_cards="2h 3h 4c 5d 6c",
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=players,
        actions=(
            ParsedAction(1, "BTN", "Preflop", "Raise", 6.0, False, 200.0, 3.0, 9.0, 1.0),
            ParsedAction(2, "BB", "Preflop", "Call", 6.0, False, 200.0, 9.0, 15.0, None),
            ParsedAction(2, "BB", "Flop", "Check", 0.0, False, 194.0, 15.0, 15.0, None),
            ParsedAction(1, "BTN", "Flop", "Bet", 10.0, False, 194.0, 15.0, 25.0, 0.66),
            ParsedAction(2, "BB", "River", "Fold", 0.0, False, 184.0, 25.0, 25.0, None),
        ),
        results=results,
    )


def test_encode_hand_sequence_shape() -> None:
    seq = encode_hand_sequence(_sample_hand())
    assert seq.token_ids[0] == TOK_CLS
    assert seq.length > 3
    assert len(seq.token_ids) == len(seq.token_kinds)
    assert seq.token_ids[-1] == TOK_PAD
    assert KIND_ACTION in seq.token_kinds
    assert KIND_CARD in seq.token_kinds


def test_winner_seat_index() -> None:
    hand = _sample_hand()
    assert winner_seat_index(hand) == 0


def test_action_vocab_in_range() -> None:
    hand = _sample_hand()
    pa = hand.actions[0]
    packed = pack_action_token(pa, num_players=hand.num_players)
    vid = packed_to_action_vocab(packed, num_players=hand.num_players)
    assert 32 <= vid < 32 + 512


def test_meta_players_token() -> None:
    assert meta_players_token(2) != meta_players_token(6)


def test_collate_masks_and_targets() -> None:
    import random

    seq = encode_hand_sequence(_sample_hand())
    batch = collate_sequences([seq], map_prob=1.0, mcp_prob=0.0, rng=random.Random(0))
    assert any(any(row) for row in batch.map_mask)
    act, card = sequence_targets(seq)
    assert any(a >= 0 for a in act)
    assert any(c >= 0 for c in card)


def test_train_val_split_reproducible() -> None:
    seqs = [encode_hand_sequence(_sample_hand()) for _ in range(20)]
    a, b = train_val_split(seqs, seed=99)
    c, d = train_val_split(seqs, seed=99)
    assert len(a) == len(c)
    assert len(b) == len(d)


def test_hhformer_forward() -> None:
    torch = pytest.importorskip("torch")
    from poker_ai.models.hhformer import HHFormer, HHFormerConfig

    cfg = HHFormerConfig(dim=64, depth=2, heads=4, max_len=32)
    model = HHFormer(cfg).module
    seq = encode_hand_sequence(_sample_hand(), max_len=32)
    ids = torch.tensor([list(seq.token_ids)], dtype=torch.long)
    mask = torch.tensor([[t != TOK_PAD for t in seq.token_ids]])
    out = model(ids, key_padding_mask=~mask)
    assert out["cls"].shape == (1, 64)
    assert out["action_logits"].shape[:2] == (1, 32)


def test_hhformer_parameter_budget() -> None:
    pytest.importorskip("torch")
    from poker_ai.models.hhformer import HHFormer, HHFormerConfig

    model = HHFormer(HHFormerConfig()).module
    n = sum(p.numel() for p in model.parameters())
    assert 5_000_000 <= n <= 15_000_000


def test_cli_train_hhformer_help() -> None:
    result = runner.invoke(app, ["train", "hhformer", "--help"])
    assert result.exit_code == 0
    assert "--epochs" in result.stdout


def test_cli_hhformer_embed_help() -> None:
    result = runner.invoke(app, ["features", "hhformer-embed", "--help"])
    assert result.exit_code == 0
    assert "--with-equity" in result.stdout


def test_hero_equity_vs_random_preflop() -> None:
    from poker_ai.learn.hhformer_inference import hero_equity_vs_random

    hand = _sample_hand()
    eq = hero_equity_vs_random(hand, mc_samples=200)
    assert eq is not None
    assert 0.0 <= eq <= 1.0
