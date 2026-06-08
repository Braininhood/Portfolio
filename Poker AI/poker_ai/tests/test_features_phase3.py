"""Phase 3 feature layer — ranges, textures, info sets, CLI."""

from __future__ import annotations

import asyncio
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typer.testing import CliRunner

from poker_ai.apps.cli.main import app
from poker_ai.core.cards import card_to_int
from poker_ai.features.board_texture import (
    compute_board_flags,
    texture_embedding_16,
    texture_from_int16,
    texture_int16,
)
from poker_ai.features.build import write_feature_jsonl
from poker_ai.features.info_set import (
    MAX_ACTION_SLOTS,
    UNKNOWN_PREFLOP,
    InfoSetParts,
    parts_flat_ints,
    parts_from_flat_ints,
    parts_from_hand,
    parts_from_tensor,
    parts_to_tensor,
)
from poker_ai.features.range import (
    NUM_HOLE_COMBOS,
    combo_at_index,
    combo_from_index,
    combo_index,
    combo_index_from_string,
    isomorphic_preflop_id,
    l1_sum,
    normalize_l1,
    one_hot_range,
    one_hot_range_from_hole_string,
    uniform_range,
)
from poker_ai.features.sequence import (
    decode_action_sequence,
    encode_action_sequence,
    pack_action_token,
    position_index,
    unpack_action_token,
)
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer
from poker_ai.ingest.service import ingest_path
from poker_ai.store.db import dispose_async_store
from poker_ai.store.loader import iter_parsed_hands_since, parsed_hand_from_game
from poker_ai.store.models import Game

runner = CliRunner()


def test_combo_index_bijection() -> None:
    seen: set[int] = set()
    for lo in range(51):
        for hi in range(lo + 1, 52):
            idx = combo_index(lo, hi)
            assert idx not in seen
            seen.add(idx)
            assert combo_at_index(idx) == (lo, hi)
    assert len(seen) == NUM_HOLE_COMBOS


def test_one_hot_range_l1() -> None:
    u = uniform_range()
    assert len(u) == NUM_HOLE_COMBOS
    assert l1_sum(u) == pytest.approx(1.0)
    oh = one_hot_range(0, 1)
    assert l1_sum(oh) == pytest.approx(1.0)
    n = normalize_l1([0.0, 2.0, 2.0])
    assert l1_sum(n) == pytest.approx(1.0)


def test_texture_int16_round_trip() -> None:
    board = (card_to_int("A", "h"), card_to_int("K", "h"), card_to_int("9", "h"))
    t16 = texture_int16(board)
    emb = texture_embedding_16(board)
    assert len(t16) == 16
    assert len(emb) == 16
    back = texture_from_int16(t16)
    assert all(abs(float(a) - float(b)) < 0.02 for a, b in zip(emb, back, strict=True))


def test_action_token_pack_round_trip() -> None:
    pa = ParsedAction(
        1,
        "BTN",
        "Flop",
        "Raise",
        4.0,
        False,
        90.0,
        10.0,
        18.0,
        0.4,
    )
    tok = pack_action_token(pa, num_players=2)
    st, pos, kind, bpr = unpack_action_token(tok, num_players=2)
    assert st == "Flop"
    assert pos == "BTN"
    assert kind == "Raise"
    assert bpr == pytest.approx(0.4)


def test_info_set_parts_round_trip() -> None:
    hand = ParsedHand(
        hand_id=42,
        stakes="1/2",
        game_type="NLH",
        num_players=2,
        small_blind=1.0,
        big_blind=2.0,
        hero_position="BTN",
        hero_cards="AhKd",
        board_cards="2h 3h 4c",
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(
            ParsedPlayer(1, "BTN", 200.0, 100.0, True, "u1", None),
            ParsedPlayer(2, "BB", 200.0, 100.0, False, "u2", None),
        ),
        actions=(
            ParsedAction(
                1,
                "BTN",
                "Preflop",
                "Raise",
                6.0,
                False,
                200.0,
                3.0,
                9.0,
                1.0,
            ),
        ),
    )
    p0 = parts_from_hand(hand)
    wire = parts_flat_ints(p0)
    p1 = parts_from_flat_ints(wire)
    assert p1 == p0
    t = parts_to_tensor(p0)
    p2 = parts_from_tensor(t)
    assert p2 == p0


def test_encode_hand_perf_budget() -> None:
    hand = ParsedHand(
        hand_id=1,
        stakes="1/2",
        game_type="NLH",
        num_players=6,
        small_blind=1.0,
        big_blind=2.0,
        hero_position="CO",
        hero_cards="ThTc",
        board_cards="Jh Qh Kh",
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=tuple(
            ParsedPlayer(i, "BTN", 100.0, 50.0, i == 3, f"u{i}", None) for i in range(1, 7)
        ),
        actions=tuple(
            ParsedAction(
                (i % 6) + 1,
                "BTN",
                "Preflop",
                "Call",
                2.0,
                False,
                100.0,
                float(3 + i),
                float(5 + i),
                None,
            )
            for i in range(40)
        ),
    )
    t0 = time.perf_counter()
    for _ in range(200):
        parts_to_tensor(parts_from_hand(hand))
    elapsed = time.perf_counter() - t0
    assert elapsed < 1.0


def test_parsed_hand_from_game_requires_hand_row() -> None:
    g = Game(
        hand_id=99,
        ingest_source="unit",
        external_ref="x",
        stakes="1/2",
        game_type="NLH",
        num_players=2,
        small_blind=1.0,
        big_blind=2.0,
        uses_antes=False,
        total_ante_amount=0.0,
    )
    g.players = []
    g.hand_row = None
    assert parsed_hand_from_game(g) is None


def test_isomorphic_preflop_id_bounds() -> None:
    for lo in range(51):
        for hi in range(lo + 1, 52):
            pid = isomorphic_preflop_id(lo, hi)
            assert 0 <= pid <= 168


def test_store_features_round_trip_and_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    monkeypatch.setenv("POKER_AI_PLAYER_UID_HMAC_SECRET", "feat-secret")
    from poker_ai.config.settings import get_settings

    get_settings.cache_clear()
    fx = Path(__file__).resolve().parent / "fixtures" / "hands" / "hand_900006.txt"

    async def _ingest() -> None:
        await ingest_path(
            fx,
            session_factory=migrated_session_factory,
            uid_secret="feat-secret",
        )

    asyncio.run(_ingest())

    out = tmp_path / "out.jsonl"

    async def _write() -> int:
        async with migrated_session_factory() as session:
            return await write_feature_jsonl(session, out, since=None)

    n = asyncio.run(_write())
    assert n == 1
    line = out.read_text(encoding="utf-8").strip().splitlines()[0]
    row = json.loads(line)
    assert row["range_l1"] == pytest.approx(1.0)
    assert len(row["tensor"]) == 4 + 16 + 32

    async def _load() -> None:
        async with migrated_session_factory() as session:
            hands = [h async for h in iter_parsed_hands_since(session)]
        assert len(hands) == 1
        p_store = parts_from_hand(hands[0])
        p_json = parts_from_tensor(tuple(float(x) for x in row["tensor"]))
        assert parts_flat_ints(p_store) == parts_flat_ints(p_json)

    asyncio.run(_load())

    r = runner.invoke(app, ["features", "build", "--output", str(tmp_path / "cli_out.jsonl")])
    assert r.exit_code == 0
    assert "hands=1" in r.stdout

    r2 = runner.invoke(
        app,
        ["features", "build", "--since", "2099-01-01", "--output", str(tmp_path / "empty.jsonl")],
    )
    assert r2.exit_code == 0
    assert "hands=0" in r2.stdout

    async def _since_filter() -> None:
        async with migrated_session_factory() as session:
            n = 0
            async for _ in iter_parsed_hands_since(
                session,
                since=datetime(2099, 1, 1, tzinfo=UTC),
            ):
                n += 1
        assert n == 0

    asyncio.run(_since_filter())

    asyncio.run(dispose_async_store())
    get_settings.cache_clear()


def test_range_and_info_set_edges() -> None:
    with pytest.raises(ValueError):
        combo_index(0, 0)
    with pytest.raises(ValueError):
        combo_at_index(-1)
    with pytest.raises(ValueError):
        combo_at_index(NUM_HOLE_COMBOS)
    with pytest.raises(ValueError):
        combo_index_from_string("ah")
    assert combo_from_index(0) == combo_at_index(0)
    assert normalize_l1(()) == ()
    zu2 = normalize_l1([0.0, 0.0])
    assert len(zu2) == NUM_HOLE_COMBOS
    assert l1_sum(zu2) == pytest.approx(1.0)
    oh2 = one_hot_range_from_hole_string("AhQs")
    assert l1_sum(oh2) == pytest.approx(1.0)


def test_compute_board_flags_empty() -> None:
    f = compute_board_flags(())
    assert f["paired"] is False
    assert len(texture_embedding_16(())) == 16


def test_info_set_hand_variants() -> None:
    base: dict[str, Any] = {
        "hand_id": 1,
        "stakes": "1/2",
        "game_type": "NLH",
        "num_players": 2,
        "small_blind": 1.0,
        "big_blind": 2.0,
        "hero_position": None,
        "pot_preflop": 0.0,
        "pot_flop": 0.0,
        "pot_turn": 0.0,
        "pot_river": 0.0,
        "players": (
            ParsedPlayer(1, "BTN", 200.0, 100.0, True, "u1", None),
            ParsedPlayer(2, "BB", 200.0, 100.0, False, "u2", None),
        ),
        "actions": (),
    }
    h0 = ParsedHand(**base, hero_cards=None, board_cards=None)
    assert parts_from_hand(h0).preflop_id == UNKNOWN_PREFLOP
    h1 = ParsedHand(**base, hero_cards="  ", board_cards=None)
    assert parts_from_hand(h1).preflop_id == UNKNOWN_PREFLOP
    h2 = ParsedHand(**base, hero_cards="xxxx", board_cards=None)
    assert parts_from_hand(h2).preflop_id == UNKNOWN_PREFLOP
    h_bad = ParsedHand(**base, hero_cards="Ahxx", board_cards=None)
    assert parts_from_hand(h_bad).preflop_id == UNKNOWN_PREFLOP
    h_short = ParsedHand(**base, hero_cards="AhKdQ", board_cards=None)
    assert parts_from_hand(h_short).preflop_id == UNKNOWN_PREFLOP
    h3 = ParsedHand(**base, hero_cards="AhKd", board_cards="As Ks Qh Jh Th")
    assert parts_from_hand(h3).street == 3
    nb = {**base, "big_blind": 0.0}
    h4 = ParsedHand(**nb, hero_cards="AhKd", board_cards=None)
    assert parts_from_hand(h4).stack_bb_milli == 0
    h5 = ParsedHand(**{**base, "hero_cards": None, "board_cards": "2h 3h 4c 5d"})
    assert parts_from_hand(h5).street == 2
    h6 = ParsedHand(
        **{
            **base,
            "hero_cards": None,
            "board_cards": None,
            "actions": (
                ParsedAction(1, "BTN", "Showdown", "Check", 0.0, False, 1.0, 1.0, 1.0, None),
            ),
        }
    )
    assert parts_from_hand(h6).street == 0
    h7 = ParsedHand(
        **{
            **base,
            "hero_cards": "AhKd",
            "board_cards": None,
            "big_blind": 0.001,
            "players": (
                ParsedPlayer(1, "BTN", 1e9, 1.0, True, "u1", None),
                ParsedPlayer(2, "BB", 1e9, 1.0, False, "u2", None),
            ),
        }
    )
    assert parts_from_hand(h7).stack_bb_milli == 2_000_000


def test_parts_wire_errors() -> None:
    bad = InfoSetParts(0, 0, 0, 0, (0,) * 15, (0,) * MAX_ACTION_SLOTS)
    with pytest.raises(ValueError):
        parts_flat_ints(bad)
    with pytest.raises(ValueError):
        parts_from_flat_ints((0,))


def test_sequence_helpers() -> None:
    hand = ParsedHand(
        hand_id=1,
        stakes="1/2",
        game_type="NLH",
        num_players=2,
        small_blind=1.0,
        big_blind=2.0,
        hero_position="BTN",
        hero_cards="AhKd",
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(
            ParsedPlayer(1, "BTN", 200.0, 100.0, True, "u1", None),
            ParsedPlayer(2, "BB", 200.0, 100.0, False, "u2", None),
        ),
        actions=(
            ParsedAction(1, "BTN", "Flop", "Check", 0.0, False, 200.0, 1.0, 1.0, None),
            ParsedAction(2, "BB", "Flop", "Shove", 200.0, True, 200.0, 1.0, 201.0, 2.0),
        ),
    )
    toks = encode_action_sequence(hand, include_bos=True, max_actions=10)
    dec = decode_action_sequence(toks, num_players=2, include_bos=True)
    assert dec[0][0] == "Flop"
    assert dec[1][2] == "Fold"
    assert position_index(11, "BTN") == 0
    with pytest.raises(ValueError):
        decode_action_sequence((0,), num_players=2, include_bos=True)
    pa_edge = ParsedAction(1, "ZZZ", "WeirdStreet", "Unknown", 0.0, False, 1.0, 1.0, 1.0, None)
    pack_action_token(pa_edge, num_players=2)
    tok_wide = (15 << 2) | (7 << 6) | (500 << 9)
    _s, pos_l, act_l, _b = unpack_action_token(tok_wide, num_players=2)
    assert pos_l == "BTN"
    assert act_l == "Fold"
    t0 = pack_action_token(hand.actions[0], num_players=2)
    toks_pad = (1, t0, 0, 99)
    dec2 = decode_action_sequence(toks_pad, num_players=2, include_bos=True)
    assert len(dec2) == 1
    assert position_index(11, "ZZZ") == 0
    toks_nb = encode_action_sequence(hand, include_bos=False)
    dec_nb = decode_action_sequence(toks_nb, num_players=2, include_bos=False)
    assert len(dec_nb) == 2
