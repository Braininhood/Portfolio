"""Phase 7b replay gate — DB 3-way flop spots must not route to HU student."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from poker_ai.core.context import count_active_players
from poker_ai.core.game import Street
from poker_ai.core.profiles import PlayerProfile
from poker_ai.core.replay import state_after_actions
from poker_ai.learn.multiway_dataset import _count_active_before_action, _hero_player_id
from poker_ai.policy.router_policy import RouterPolicy


_POSTFLOP = frozenset({"Flop", "Turn", "River"})


def _three_way_flop_spots(hand: object) -> list[int]:
    """Action indices where hero acts with >=3 active on postflop streets."""
    from poker_ai.ingest.records import ParsedHand

    assert isinstance(hand, ParsedHand)
    hero_pid = _hero_player_id(hand)
    if hero_pid is None:
        return []
    spots: list[int] = []
    for i, pa in enumerate(hand.actions):
        if pa.street not in _POSTFLOP:
            continue
        if _count_active_before_action(hand, i) < 3:
            continue
        if pa.player_id != hero_pid:
            continue
        spots.append(i)
    return spots


async def _collect_router_gate_spots(
    *,
    min_spots: int,
    max_hands: int = 50_000,
) -> tuple[int, int]:
    from poker_ai.config.settings import get_settings
    from poker_ai.store.db import create_engine_and_session_factory
    from poker_ai.store.loader import iter_parsed_hands_since

    router = RouterPolicy.from_artifacts()
    profile = PlayerProfile(profile_id="hero")
    checked = 0
    hu_hits = 0
    hands_scanned = 0

    engine, factory = create_engine_and_session_factory(get_settings().database_url)
    try:
        async with factory() as session:
            async for hand in iter_parsed_hands_since(session):
                hands_scanned += 1
                for idx in _three_way_flop_spots(hand):
                    try:
                        state = state_after_actions(hand, idx, lenient=True)
                    except (ValueError, KeyError, IndexError):
                        continue
                    if state.hand_over or count_active_players(state) < 3:
                        continue
                    if state.street == Street.PREFLOP:
                        continue
                    router.propose(state, profile)
                    checked += 1
                    if router._last_brain == "hu":
                        hu_hits += 1
                    if checked >= min_spots:
                        return checked, hu_hits
                if hands_scanned >= max_hands:
                    break
    finally:
        await engine.dispose()
    return checked, hu_hits


def test_router_gate_three_way_flop_db() -> None:
    """≥100 ingested 3-way flop decisions → router uses multi-way brain only."""
    if os.environ.get("POKER_AI_ROUTER_GATE", "").strip() != "1":
        pytest.skip("Set POKER_AI_ROUTER_GATE=1 to run the DB replay router gate.")

    from poker_ai.config.settings import get_settings

    url = get_settings().database_url
    if "sqlite" in url:
        path_part = url.split("///", 1)[-1]
        db_path = Path(path_part)
        if not db_path.is_file():
            pytest.skip(f"Database missing: {db_path}")

    min_spots = int(os.environ.get("POKER_AI_ROUTER_GATE_MIN", "100"))
    checked, hu_hits = asyncio.run(_collect_router_gate_spots(min_spots=min_spots))
    assert checked >= min_spots, f"Only {checked} valid 3-way flop spots (need {min_spots})"
    assert hu_hits == 0, f"HU brain used on {hu_hits}/{checked} multi-way replay spots"
