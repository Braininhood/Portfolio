"""PHH / PHHS ingest parser tests."""

from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poker_ai.ingest.canonical_id import INGEST_OHH_JSON, INGEST_PHH, resolve_hand_id
from poker_ai.ingest.phh_text import (
    looks_like_phh_text,
    parse_phh_block_dict,
    parse_phh_bytes,
    split_phh_blocks,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hands"


def test_iter_hand_files_missing_path_returns_empty() -> None:
    from poker_ai.ingest.service import _iter_hand_files

    assert _iter_hand_files(Path("/nonexistent/path/that/does/not/exist/zzz")) == []


def test_looks_like_phh_text() -> None:
    assert looks_like_phh_text("variant = 'NT'\nactions = []\n") is True
    assert looks_like_phh_text("PokerStars Hand #1\n") is False


def test_split_phh_blocks_two_hands() -> None:
    text = (FIXTURES / "sample_two_hands.phhs").read_text(encoding="utf-8")
    blocks = split_phh_blocks(text)
    assert len(blocks) == 2
    assert "p2 f" in blocks[0]
    assert "p2 f" in blocks[1]


def test_parse_phh_pluribus_fixture() -> None:
    raw = (FIXTURES / "sample_pluribus.phh").read_bytes()
    path = FIXTURES / "sample_pluribus.phh"
    hands = parse_phh_bytes(raw, path=path, uid_secret="fixture-secret")
    assert len(hands) == 1
    h = hands[0]
    assert h.ingest_source == INGEST_PHH
    assert h.game_type == "NLH"
    assert h.num_players == 6
    by_pos = {p.player_id: p.position for p in h.players}
    assert by_pos[1] == "SB" and by_pos[2] == "BB" and by_pos[6] == "BTN"
    assert h.actions[0].player_id == 3 and h.actions[0].position == "UTG"
    assert h.board_cards and "7c" in h.board_cards
    assert h.pot_preflop > 0
    assert any(a.action_type == "Fold" for a in h.actions)
    assert any(a.action_type == "Check" for a in h.actions)
    assert any(a.action_type == "Call" for a in h.actions)
    assert any(a.action_type == "Raise" for a in h.actions)
    assert len(h.results) == 6


def test_split_phh_single_file_no_brackets() -> None:
    assert split_phh_blocks("variant = 'NT'\nactions = []\nplayers = ['x']\n") == [
        "variant = 'NT'\nactions = []\nplayers = ['x']"
    ]


def test_parse_phh_bytes_utf8_error() -> None:
    p = Path("x.phh")
    assert parse_phh_bytes(b"\xff\xfe", path=p, uid_secret="k") == []


def test_parse_phh_bytes_not_nt_header() -> None:
    p = Path("x.phh")
    txt = "variant = 'PL'\nactions = []\nplayers = ['a']\nstarting_stacks = [1.0]\n"
    assert parse_phh_bytes(txt.encode(), path=p, uid_secret="k") == []


def test_parse_phh_block_dict_bad_inputs() -> None:
    assert parse_phh_block_dict({}, external_ref="x", uid_secret="k") is None
    assert (
        parse_phh_block_dict(
            {
                "variant": "NT",
                "players": ["a", "b"],
                "starting_stacks": [100.0],
                "actions": [],
            },
            external_ref="x",
            uid_secret="k",
        )
        is None
    )
    assert (
        parse_phh_block_dict(
            {
                "variant": "NT",
                "players": ["a"],
                "starting_stacks": [100.0],
                "actions": "nope",
            },
            external_ref="x",
            uid_secret="k",
        )
        is None
    )


def test_parse_actions_edge_tokens() -> None:
    from poker_ai.ingest.phh_text import _parse_actions_phh

    _acts, board, res, _pots = _parse_actions_phh(
        ["d db", "px f", "p99 f", "p1 cbr x", 123, "p1 sm", "p1x f"],
        n_players=2,
        starting_stacks=[1000.0, 1000.0],
        blinds_or_straddles=[5.0, 10.0],
        antes=[0.0, 0.0],
        seat_to_pid={1: 1, 2: 2},
    )
    assert board is None
    assert len(res) == 1 and res[0].player_id == 1


def test_parse_kv_literal_eval_fallback() -> None:
    from poker_ai.ingest.phh_text import _parse_kv_block

    d = _parse_kv_block("variant = 'NT'\nnote = not_a_python_literal\n")
    assert d["note"] == "not_a_python_literal"


def test_parse_phh_bytes_skips_empty_block_and_no_hand_key() -> None:
    txt = """[1]
variant = 'NT'
players = ['a']
starting_stacks = [100.0]
blinds_or_straddles = [5, 10]
actions = ['p1 f']

[2]

[3]
variant = 'NT'
players = ['b']
starting_stacks = [200.0]
blinds_or_straddles = [10, 20]
actions = ['p1 f']

"""
    p = Path("multi.phhs")
    hands = parse_phh_bytes(txt.encode(), path=p, uid_secret="k")
    assert len(hands) == 2


def test_parse_phh_sm_muck_two_tokens() -> None:
    from poker_ai.ingest.phh_text import _parse_actions_phh

    _acts, _b, res, _pots = _parse_actions_phh(
        ["d dh p1 AhKh", "d dh p2 QdQc", "p2 sm", "p1 sm AhKh"],
        n_players=2,
        starting_stacks=[100.0, 100.0],
        blinds_or_straddles=[1.0, 2.0],
        antes=[0.0, 0.0],
        seat_to_pid={1: 1, 2: 2},
    )
    assert len(res) == 2
    by = {r.player_id: r.cards for r in res}
    assert by[2] == ""


def test_phh_handhq_seat_order_maps_action_player() -> None:
    """``pN`` refers to seat N; ``seats`` lists seat per ``players`` index."""
    h = parse_phh_block_dict(
        {
            "variant": "NT",
            "players": ["a", "b", "c", "d", "e", "f"],
            "starting_stacks": [100.0] * 6,
            "blinds_or_straddles": [5, 10, 0, 0, 0, 0],
            "antes": [2.5] * 6,
            "seats": [3, 4, 5, 6, 1, 2],
            "actions": ["p3 cbr 20", "p4 f", "p5 f", "p6 f", "p1 f", "p2 f"],
            "winnings": [17.5, 0, 0, 0, 0, 0],
        },
        external_ref="hq#1",
        uid_secret="k",
    )
    assert h is not None
    assert h.actions[0].player_id == 1
    assert h.actions[0].action_type == "Raise"
    assert len(h.results) == 6
    assert h.results[0].net_result == 17.5


def test_parse_phh_path_wrapper() -> None:
    from poker_ai.ingest.phh_text import parse_phh_path

    raw = (FIXTURES / "sample_pluribus.phh").read_bytes()
    assert len(parse_phh_path(FIXTURES / "sample_pluribus.phh", raw, uid_secret="k")) == 1
    raw = (FIXTURES / "sample_two_hands.phhs").read_bytes()
    hands = parse_phh_bytes(raw, path=FIXTURES / "sample_two_hands.phhs", uid_secret="k")
    assert len(hands) == 2
    assert hands[0].external_ref.endswith("#10")
    assert hands[1].external_ref.endswith("#11")


def test_ingest_phh_tree_writes_two_games(
    tmp_path: Path,
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    import shutil

    from sqlalchemy import func, select

    from poker_ai.ingest.service import ingest_path
    from poker_ai.store.models import Game

    root = tmp_path / "corpus"
    sub = root / "sub"
    sub.mkdir(parents=True)
    shutil.copy(FIXTURES / "sample_two_hands.phhs", sub / "hands.phhs")

    async def _run() -> None:
        stats = await ingest_path(
            root,
            session_factory=migrated_session_factory,
            uid_secret="fixture-secret",
        )
        assert stats.files_processed == 1
        assert stats.hands_new == 2
        async with migrated_session_factory() as session:
            stmt = select(func.count()).select_from(Game).where(Game.ingest_source == INGEST_PHH)
            n = await session.scalar(stmt)
            assert int(n or 0) == 2

    asyncio.run(_run())


def test_parse_actions_phh_extends_short_blinds() -> None:
    from poker_ai.ingest.phh_text import _parse_actions_phh

    _parse_actions_phh(
        ["p6 f"],
        n_players=6,
        starting_stacks=[100.0] * 6,
        blinds_or_straddles=[0.5, 1.0],
        antes=[0.0],
        seat_to_pid={i: i for i in range(1, 7)},
    )


def test_parse_actions_empty_action_string() -> None:
    from poker_ai.ingest.phh_text import _parse_actions_phh

    _parse_actions_phh(
        ["", "p1 f"],
        n_players=2,
        starting_stacks=[100.0, 100.0],
        blinds_or_straddles=[1.0, 2.0],
        antes=[0.0, 0.0],
        seat_to_pid={1: 1, 2: 2},
    )


def test_parse_phh_block_empty_players() -> None:
    assert (
        parse_phh_block_dict(
            {"variant": "NT", "players": [], "starting_stacks": [], "actions": []},
            external_ref="z",
            uid_secret="k",
        )
        is None
    )


def _phhs_tail() -> str:
    return (
        "variant = 'NT'\n"
        "players = ['a']\n"
        "starting_stacks = [1.0]\n"
        "blinds_or_straddles = [0.1,0.2]\n"
        "actions = ['p1 f']\n"
        "hand = 2\n"
    )


def test_parse_phh_bytes_skips_no_kv_block() -> None:
    txt = "[1]\nfoo\n[2]\n" + _phhs_tail()
    hands = parse_phh_bytes(txt.encode(), path=Path("nokv.phhs"), uid_secret="k")
    assert len(hands) == 1


def test_parse_phh_bytes_skips_kv_only_block() -> None:
    txt = "[1]\n  \n  \n[2]\n" + _phhs_tail()
    hands = parse_phh_bytes(txt.encode(), path=Path("kv.phhs"), uid_secret="k")
    assert len(hands) == 1


def test_parse_phh_bytes_skips_block_without_variant() -> None:
    txt = "[1]\nx = 1\n\n[2]\n" + _phhs_tail()
    hands = parse_phh_bytes(txt.encode(), path=Path("skip.phhs"), uid_secret="k")
    assert len(hands) == 1


def test_parse_file_hands_empty_json_and_phh(tmp_path: Path) -> None:
    from poker_ai.ingest.service import _parse_file_hands

    bad = tmp_path / "bad.json"
    bad.write_text('{"ohh": "not-a-dict"}', encoding="utf-8")
    assert _parse_file_hands(bad, uid_secret="k") == []

    pl = tmp_path / "pl.json"
    pl.write_text(
        '{"ohh": {"game_number": "1", "small_blind_amount": 0.01, '
        '"big_blind_amount": 0.02, "bet_limit": {"bet_type": "PL"}, '
        '"players": [{"name": "a", "id": 0, "starting_stack": 1.0, "seat": 1}], '
        '"rounds": [], "pots": []}}',
        encoding="utf-8",
    )
    assert _parse_file_hands(pl, uid_secret="k") == []

    empty_phh = tmp_path / "empty.phh"
    empty_phh.write_text("not a phh file", encoding="utf-8")
    assert _parse_file_hands(empty_phh, uid_secret="k") == []

    ohh = tmp_path / "ok.json"
    ohh.write_text((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8"), encoding="utf-8")
    hs = _parse_file_hands(ohh, uid_secret="k")
    assert len(hs) == 1 and hs[0].ingest_source == INGEST_OHH_JSON


def test_parse_kv_skips_comment_and_no_equals() -> None:
    from poker_ai.ingest.phh_text import _parse_kv_block

    d = _parse_kv_block("# c\nfoo\nx = 1\n")
    assert d == {"x": 1}


def test_parse_phh_block_empty_variant() -> None:
    d = {
        "variant": "",
        "players": ["a"],
        "starting_stacks": [1.0],
        "actions": [],
    }
    assert parse_phh_block_dict(d, external_ref="z", uid_secret="k") is None


def test_parse_phh_bytes_empty_data_block() -> None:
    tail = (
        "variant = 'NT'\n"
        "players = ['a']\n"
        "starting_stacks = [1.0]\n"
        "blinds_or_straddles = [0.1,0.2]\n"
        "actions = ['p1 f']\n"
        "hand = 1\n"
    )
    txt = "[1]\n\n[2]\n" + tail
    hands = parse_phh_bytes(txt.encode(), path=Path("z.phhs"), uid_secret="k")
    assert len(hands) == 1


def test_parse_phh_block_dict_rejects_pl() -> None:
    d = {"variant": "PL", "players": ["a"], "starting_stacks": [100.0], "actions": []}
    assert parse_phh_block_dict(d, external_ref="x", uid_secret="k") is None


def test_parse_phh_seat_count_capped() -> None:
    h = parse_phh_block_dict(
        {
            "variant": "NT",
            "players": ["a", "b"],
            "seat_count": 99,
            "starting_stacks": [100.0, 200.0],
            "blinds_or_straddles": [5.0, 10.0],
            "actions": ["p1 f"],
        },
        external_ref="cap",
        uid_secret="k",
    )
    assert h is not None
    assert h.num_players == 2


def test_phh_seats_invalid_falls_back_to_identity() -> None:
    from poker_ai.ingest.phh_text import _phh_seat_to_player_id

    assert _phh_seat_to_player_id(2, ["x", 2]) == {1: 1, 2: 2}


def test_hole_cards_deal_parsing_edges() -> None:
    from poker_ai.ingest.phh_text import _hole_cards_from_deal_actions

    h = _hole_cards_from_deal_actions(
        [
            "d dh p1 AsKh",
            99,
            "d dh px KhKd",
            "d dh p9 AhAd",
            "d dh p1x AhAd",
            "d dh x1 AsKh",
            "d dh p1 ????",
        ],
        seat_to_pid={1: 1},
    )
    assert h == {1: "as kh"}


def test_parse_phh_min_bet_when_blinds_zero() -> None:
    h = parse_phh_block_dict(
        {
            "variant": "NT",
            "players": ["a", "b"],
            "starting_stacks": [100.0, 200.0],
            "blinds_or_straddles": [0, 0],
            "min_bet": 10,
            "actions": ["p1 f"],
        },
        external_ref="mbb",
        uid_secret="k",
    )
    assert h is not None
    assert h.big_blind == 10.0
    assert h.small_blind == 5.0


def test_parse_phh_min_bet_type_error() -> None:
    h = parse_phh_block_dict(
        {
            "variant": "NT",
            "players": ["a", "b"],
            "starting_stacks": [100.0, 200.0],
            "blinds_or_straddles": [0, 0],
            "min_bet": object(),
            "actions": ["p1 f"],
        },
        external_ref="mbt",
        uid_secret="k",
    )
    assert h is not None
    assert h.big_blind == 0.0


def test_parse_phh_finishing_stacks_bad_float_falls_back() -> None:
    h = parse_phh_block_dict(
        {
            "variant": "NT",
            "players": ["a", "b"],
            "starting_stacks": [400.0, 400.0],
            "blinds_or_straddles": [1, 2],
            "actions": ["p1 f"],
            "finishing_stacks": [400.0, "oops"],
        },
        external_ref="ff",
        uid_secret="k",
    )
    assert h is not None
    assert len(h.results) == 0


def test_parse_phh_short_antes_list_padded() -> None:
    h = parse_phh_block_dict(
        {
            "variant": "NT",
            "players": ["a", "b", "c"],
            "starting_stacks": [100.0, 200.0, 300.0],
            "blinds_or_straddles": [1, 2, 0],
            "antes": [1.0],
            "actions": ["p1 f"],
        },
        external_ref="pad",
        uid_secret="k",
    )
    assert h is not None
    assert h.antes == (1.0, 0.0, 0.0)
    assert h.pot_preflop == 4.0


def test_parse_phh_antes_default_when_not_list() -> None:
    h = parse_phh_block_dict(
        {
            "variant": "NT",
            "players": ["a", "b"],
            "starting_stacks": [100.0, 200.0],
            "blinds_or_straddles": [1, 2],
            "antes": "none",
            "actions": ["p1 f"],
        },
        external_ref="ante",
        uid_secret="k",
    )
    assert h is not None
    assert h.pot_preflop == 3.0


def test_parse_phh_results_from_underbar_results() -> None:
    h = parse_phh_block_dict(
        {
            "variant": "NT",
            "players": ["a", "b"],
            "starting_stacks": [400.0, 400.0],
            "blinds_or_straddles": [1, 2],
            "actions": ["p2 sm QdQc", "p1 sm AsAh"],
            "_results": [10.0, -10.0],
        },
        external_ref="rs",
        uid_secret="k",
    )
    assert h is not None
    assert len(h.results) == 2
    assert {r.position for r in h.results} == {"BTN", "BB"}
    assert abs(h.results[0].net_result + h.results[1].net_result) < 1e-6


def test_resolve_phh_external_ref_stable() -> None:
    a = resolve_hand_id(INGEST_PHH, "a/b.phhs#1")
    b = resolve_hand_id(INGEST_PHH, "a/b.phhs#2")
    assert a != b


def test_ingest_phh_file_roundtrip(
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    from sqlalchemy import func, select

    from poker_ai.ingest.service import ingest_path
    from poker_ai.store.models import Action, Game

    fp = FIXTURES / "sample_pluribus.phh"

    async def _run() -> None:
        stats = await ingest_path(
            fp,
            session_factory=migrated_session_factory,
            uid_secret="fixture-secret",
        )
        assert stats.files_processed == 1
        assert stats.hands_new == 1
        async with migrated_session_factory() as session:
            stmt = select(Game).where(Game.ingest_source == INGEST_PHH)
            rows = (await session.scalars(stmt)).all()
            assert len(rows) == 1
            hid = rows[0].hand_id
            cnt = select(func.count()).select_from(Action).where(Action.hand_id == hid)
            n = await session.scalar(cnt)
            assert n and int(n) > 0

    asyncio.run(_run())
