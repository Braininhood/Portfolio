"""Store gate and provenance-aware upsert."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import replace
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poker_ai.ingest.canonical_id import (
    INGEST_GG_NETWORK,
    INGEST_NORMALIZED_TXT,
    INGEST_OHH_JSON,
    INGEST_PHH,
    resolve_hand_id,
)
from poker_ai.ingest.phh_text import parse_phh_block_dict
from poker_ai.ingest.records import (
    ParsedAction,
    ParsedHand,
    ParsedPlayer,
    ParsedResult,
    hand_uses_antes,
    total_ante_amount,
)
from poker_ai.ingest.service import ingest_path
from poker_ai.ingest.store_gate import parsed_hand_passes_store_gate
from poker_ai.store.models import Game, Player
from poker_ai.store.repository import upsert_hand


def test_store_gate_phh_requires_results_when_complete() -> None:
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
    assert parsed_hand_passes_store_gate(h, require_complete=True) is False
    assert parsed_hand_passes_store_gate(h, require_complete=False) is True


def test_store_gate_normalized_lenient_on_results() -> None:
    from poker_ai.ingest.pokerstars_text import parse_text

    text = (Path(__file__).parent / "fixtures" / "hands" / "hand_900006.txt").read_text(
        encoding="utf-8"
    )
    h = parse_text(text, hand_id=900006, uid_secret="k")
    assert h is not None
    assert parsed_hand_passes_store_gate(h, require_complete=True) is True


def test_upsert_deletes_stale_row_same_provenance(
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    ref = f"provenance-stale-{uuid.uuid4().hex}#0"
    hid_real = resolve_hand_id(INGEST_PHH, ref)
    orphan_id = 9_008_007_001 if hid_real != 9_008_007_001 else 9_008_007_002

    hand = parse_phh_block_dict(
        {
            "variant": "NT",
            "players": ["a", "b"],
            "starting_stacks": [200.0, 200.0],
            "blinds_or_straddles": [1, 2],
            "actions": ["d dh p1 AsKh", "d dh p2 QdQc", "p2 f"],
            "winnings": [2.0, -2.0],
        },
        external_ref=ref,
        uid_secret="k",
    )
    assert hand is not None
    assert hand.hand_id == hid_real

    async def _run() -> None:
        async with migrated_session_factory() as session:
            async with session.begin():
                session.add(
                    Game(
                        hand_id=orphan_id,
                        ingest_source=INGEST_PHH,
                        external_ref=ref,
                        stakes="1/2",
                        game_type="NLH",
                        num_players=2,
                        small_blind=1.0,
                        big_blind=2.0,
                        uses_antes=False,
                        total_ante_amount=0.0,
                    )
                )
        async with migrated_session_factory() as session:
            async with session.begin():
                await upsert_hand(session, hand)
        async with migrated_session_factory() as session:
            n_orphan = await session.scalar(
                select(func.count()).select_from(Game).where(Game.hand_id == orphan_id)
            )
            assert int(n_orphan or 0) == 0
            n_real = await session.scalar(
                select(func.count()).select_from(Game).where(Game.hand_id == hid_real)
            )
            assert int(n_real or 0) == 1
            np = await session.scalar(
                select(func.count()).select_from(Player).where(Player.hand_id == hid_real)
            )
            assert int(np or 0) == 2

    asyncio.run(_run())


def _phh_min_complete() -> ParsedHand:
    uid1 = "a" * 64
    uid2 = "b" * 64
    return ParsedHand(
        hand_id=42,
        stakes="1/2",
        game_type="NLH",
        num_players=2,
        small_blind=1.0,
        big_blind=2.0,
        hero_position=None,
        hero_cards=None,
        board_cards=None,
        pot_preflop=3.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(
            ParsedPlayer(1, "SB", 100.0, 50.0, False, uid1),
            ParsedPlayer(2, "BB", 100.0, 50.0, False, uid2),
        ),
        actions=(ParsedAction(1, "SB", "Preflop", "Fold", 0.0, False, 100.0, 3.0, 3.0, None),),
        results=(
            ParsedResult(1, "SB", "", 0.0, 0.0, False),
            ParsedResult(2, "BB", "", 0.0, 0.0, False),
        ),
        ingest_source=INGEST_PHH,
        external_ref="t",
    )


def test_store_gate_synthetic_variants() -> None:
    h = _phh_min_complete()
    assert parsed_hand_passes_store_gate(h, require_complete=True) is True
    assert (
        parsed_hand_passes_store_gate(
            replace(h, num_players=1, players=h.players[:1]),
            require_complete=True,
        )
        is False
    )
    assert (
        parsed_hand_passes_store_gate(
            replace(h, big_blind=0.0, small_blind=0.0), require_complete=False
        )
        is False
    )
    assert parsed_hand_passes_store_gate(replace(h, actions=()), require_complete=False) is False
    assert (
        parsed_hand_passes_store_gate(
            replace(h, players=(*h.players, h.players[0])),
            require_complete=False,
        )
        is False
    )
    assert (
        parsed_hand_passes_store_gate(
            replace(
                h,
                players=(
                    ParsedPlayer(2, "A", 100.0, 50.0, False, "c" * 64),
                    ParsedPlayer(3, "B", 100.0, 50.0, False, "d" * 64),
                ),
            ),
            require_complete=True,
        )
        is False
    )
    assert (
        parsed_hand_passes_store_gate(
            replace(h, results=h.results[:1]),
            require_complete=True,
        )
        is False
    )
    h_ohh_ok = replace(h, ingest_source=INGEST_OHH_JSON, results=(h.results[0],))
    assert parsed_hand_passes_store_gate(h_ohh_ok, require_complete=True) is True
    h_ohh_bad = replace(h, ingest_source=INGEST_OHH_JSON, results=())
    assert parsed_hand_passes_store_gate(h_ohh_bad, require_complete=True) is False
    h_txt = replace(h, ingest_source=INGEST_NORMALIZED_TXT)
    assert parsed_hand_passes_store_gate(h_txt, require_complete=True) is True
    h_gg = replace(h, ingest_source=INGEST_GG_NETWORK)
    assert parsed_hand_passes_store_gate(h_gg, require_complete=True) is True


def test_ingest_skips_phh_when_store_gate_fails(
    tmp_path: Path,
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    bad = tmp_path / "bad.phh"
    bad.write_text(
        "variant = 'NT'\n"
        "players = ['a', 'b']\n"
        "starting_stacks = [400.0, 400.0]\n"
        "blinds_or_straddles = [1, 2]\n"
        "actions = ['p1 f']\n"
        "finishing_stacks = [400.0, 'oops']\n",
        encoding="utf-8",
    )

    async def _run() -> None:
        stats = await ingest_path(
            bad,
            session_factory=migrated_session_factory,
            uid_secret="k",
        )
        assert stats.files_processed == 1
        assert stats.hands_new == 0

    asyncio.run(_run())


def test_total_ante_amount_phh_without_antes_field() -> None:
    h = parse_phh_block_dict(
        {
            "variant": "NT",
            "players": ["a", "b"],
            "starting_stacks": [100.0, 100.0],
            "blinds_or_straddles": [1, 2],
            "actions": ["p1 f"],
            "winnings": [-1.0, 1.0],
        },
        external_ref="no-ante-total",
        uid_secret="k",
    )
    assert h is not None
    assert total_ante_amount(h) == 0.0
    assert hand_uses_antes(h) is False


def test_upsert_persists_ante_flags(
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    ref = f"ante-flags-{uuid.uuid4().hex}"
    h = parse_phh_block_dict(
        {
            "variant": "NT",
            "players": ["a", "b"],
            "starting_stacks": [100.0, 100.0],
            "blinds_or_straddles": [1, 2],
            "antes": [1.0, 1.0],
            "actions": ["p1 f"],
            "winnings": [-2.0, 2.0],
        },
        external_ref=ref,
        uid_secret="k",
    )
    assert h is not None
    assert total_ante_amount(h) == 2.0
    assert hand_uses_antes(h) is True

    async def _run() -> None:
        async with migrated_session_factory() as session:
            async with session.begin():
                await upsert_hand(session, h)
        async with migrated_session_factory() as session:
            g = await session.get(Game, h.hand_id)
            assert g is not None
            assert g.uses_antes is True
            assert abs(g.total_ante_amount - 2.0) < 1e-9

    asyncio.run(_run())
