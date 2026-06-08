"""Golden ingest tests (doc/ROADMAP.md Phase 1 exit criteria)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poker_ai.ingest.canonical_id import INGEST_NORMALIZED_TXT, INGEST_OHH_JSON
from poker_ai.ingest.identity import player_uid_hmac
from poker_ai.ingest.ohh_json import parse_ohh_dict, parse_ohh_json_bytes
from poker_ai.ingest.pokerstars_text import parse_text
from poker_ai.ingest.service import ingest_path
from poker_ai.store.models import Action, Game, Player, Result
from poker_ai.store.repository import upsert_hand

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hands"


@pytest.mark.parametrize(
    "filename,expected_players,hid",
    [
        ("hand_900006.txt", 6, 900006),
        ("hand_900008.txt", 8, 900008),
        ("hand_900009.txt", 9, 900009),
    ],
)
def test_golden_seat_counts(
    migrated_session_factory: async_sessionmaker[AsyncSession],
    filename: str,
    expected_players: int,
    hid: int,
) -> None:
    text = (FIXTURES / filename).read_text(encoding="utf-8")
    hand = parse_text(text, hand_id=hid, uid_secret="test-secret-not-for-production")
    assert hand is not None
    assert hand.ingest_source == INGEST_NORMALIZED_TXT
    assert hand.external_ref == str(hid)
    assert hand.num_players == expected_players
    assert len(hand.players) == expected_players

    async def _run() -> None:
        stats = await ingest_path(
            FIXTURES / filename,
            session_factory=migrated_session_factory,
            uid_secret="test-secret-not-for-production",
        )
        assert stats.files_processed == 1
        assert stats.hands_new == 1
        async with migrated_session_factory() as session:
            stmt = select(func.count()).select_from(Player).where(Player.hand_id == hid)
            n = await session.scalar(stmt)
            assert n == expected_players

    asyncio.run(_run())


def test_idempotent_reingest(
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    text = (FIXTURES / "hand_900006.txt").read_text(encoding="utf-8")
    hand = parse_text(text, hand_id=910001, uid_secret="test-secret-not-for-production")
    assert hand is not None

    async def _run() -> None:
        for _ in range(2):
            async with migrated_session_factory() as session:
                async with session.begin():
                    await upsert_hand(session, hand)
            async with migrated_session_factory() as session:
                stmt = select(func.count()).select_from(Action).where(Action.hand_id == 910001)
                ac = await session.scalar(stmt)
                assert ac == len(hand.actions)

    asyncio.run(_run())


def test_directory_ingest_one_row_per_duplicate_filename(
    tmp_path: Path,
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Same ``hand_<id>.txt`` name under two subfolders must not collapse to one ``games`` row."""
    text = (FIXTURES / "hand_900006.txt").read_text(encoding="utf-8")
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "hand_990099.txt").write_text(text, encoding="utf-8")
    (tmp_path / "b" / "hand_990099.txt").write_text(text, encoding="utf-8")

    async def _run() -> None:
        stats = await ingest_path(
            tmp_path,
            session_factory=migrated_session_factory,
            uid_secret="test-secret-not-for-production",
        )
        assert stats.files_processed == 2
        assert stats.hands_new == 2
        async with migrated_session_factory() as session:
            stmt = select(func.count()).select_from(Game)
            n = await session.scalar(stmt)
            assert n == 2

    asyncio.run(_run())


def test_player_uid_stable_named_vs_ephemeral() -> None:
    secret = "s"
    a = player_uid_hmac(secret, nickname="Villain_1", hand_id=1, seat_player_id=1)
    b = player_uid_hmac(secret, nickname="Villain_1", hand_id=2, seat_player_id=3)
    assert a == b
    c = player_uid_hmac(secret, nickname=None, hand_id=1, seat_player_id=1)
    d = player_uid_hmac(secret, nickname=None, hand_id=2, seat_player_id=1)
    assert c != d


def test_ohh_minimal_roundtrip() -> None:
    raw = {
        "ohh": {
            "game_number": "123456789",
            "small_blind_amount": 0.01,
            "big_blind_amount": 0.02,
            "bet_limit": {"bet_type": "NL"},
            "hero_player_id": 0,
            "players": [
                {"name": "HeroName", "id": 0, "starting_stack": 2.0, "seat": 1},
                {"name": "Villain", "id": 1, "starting_stack": 2.0, "seat": 2},
            ],
            "rounds": [
                {
                    "street": "Preflop",
                    "cards": [],
                    "actions": [
                        {"player_id": 0, "action": "Fold", "amount": 0.0, "is_allin": False},
                    ],
                }
            ],
            "pots": [],
        }
    }
    hand = parse_ohh_dict(raw, uid_secret="secret")
    assert hand is not None
    assert hand.num_players == 2
    assert hand.players[0].screen_name == "HeroName"


def test_ohh_json_bytes_invalid_returns_none() -> None:
    assert parse_ohh_json_bytes(b"not json", uid_secret="x") is None


def test_sample_ohh_fixture_parses() -> None:
    raw = (FIXTURES / "sample_ohh.json").read_bytes()
    hand = parse_ohh_json_bytes(raw, uid_secret="fixture-secret")
    assert hand is not None
    assert hand.ingest_source == INGEST_OHH_JSON
    assert hand.external_ref == "999888777"
    assert hand.num_players == 2
    assert {p.position for p in hand.players} == {"BTN", "BB"}
    assert hand.hero_position == "BTN"
    assert hand.board_cards and "2d" in hand.board_cards
    assert len(hand.actions) >= 2


def test_gg_placeholder() -> None:
    from poker_ai.ingest.gg_text import looks_like_gg_text, parse_gg_text

    assert looks_like_gg_text("GGPoker Hand #1 - ") is True
    assert parse_gg_text("", _hand_id=1, _uid_secret="x") is None


def test_upsert_persists_showdown_results(
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Covers ``Result`` rows in ``repository.upsert_hand`` (showdown lines)."""
    text = (FIXTURES / "hand_37937077.txt").read_text(encoding="utf-8")
    hand = parse_text(text, hand_id=37937077, uid_secret="test-secret-not-for-production")
    assert hand is not None
    assert len(hand.results) >= 1

    async def _run() -> None:
        async with migrated_session_factory() as session:
            async with session.begin():
                await upsert_hand(session, hand)
        async with migrated_session_factory() as session:
            stmt = select(func.count()).select_from(Result).where(Result.hand_id == 37937077)
            n = await session.scalar(stmt)
            assert n == len(hand.results)

    asyncio.run(_run())


def test_repo_hand_from_sample_file(
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Fixture copy of ``hand/5/hand_37937077`` without the duplicate ``Turn`` export line."""
    sample = FIXTURES / "hand_37937077.txt"
    assert sample.is_file()

    async def _run() -> None:
        stats = await ingest_path(
            sample,
            session_factory=migrated_session_factory,
            uid_secret="test-secret-not-for-production",
        )
        assert stats.files_processed == 1
        assert stats.hands_new == 1
        async with migrated_session_factory() as session:
            hid = 37937077
            g = await session.get(Game, hid)
            assert g is not None
            assert g.ingest_source == INGEST_NORMALIZED_TXT
            assert g.external_ref == str(hid)
            assert g.num_players == 6

    asyncio.run(_run())
