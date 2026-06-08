"""Tests for ``poker_ai.core.engine`` and ``poker_ai.core.replay``."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import poker_ai.core as core_pkg
import poker_ai.core.engine as eng
from poker_ai.core.cards import cards_from_space_separated
from poker_ai.core.engine import (
    IllegalActionError,
    chips_to_money,
    initial_state_from_parsed_hand,
    legal_actions,
    money_to_chips,
    pid_to_seat,
    ring_player_ids,
    step,
)
from poker_ai.core.game import EngineAction, EngineActionKind, GameState, Street
from poker_ai.core.replay import parsed_action_to_engine, replay_parsed_hand
from poker_ai.ingest.ohh_json import parse_ohh_dict
from poker_ai.ingest.pokerstars_text import parse_text
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer
from poker_ai.ingest.service import ingest_path
from poker_ai.store.models import Action

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hands"


def _wealth(s: GameState) -> int:
    return sum(s.stacks) + s.pot


def test_core_package_exports() -> None:
    assert core_pkg.hand_rank_value is not None
    assert core_pkg.replay_parsed_hand is not None


def test_money_chips_round_trip() -> None:
    assert chips_to_money(money_to_chips(0.06)) == pytest.approx(0.06)


def test_replay_illegal_action_sets_flags() -> None:
    h = ParsedHand(
        hand_id=1,
        stakes="0.01/0.02",
        game_type="NLH",
        num_players=2,
        small_blind=0.01,
        big_blind=0.02,
        hero_position="BTN",
        hero_cards=None,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(
            ParsedPlayer(1, "BTN", 2.0, 100.0, True, "u1", None),
            ParsedPlayer(2, "BB", 2.0, 100.0, False, "u2", None),
        ),
        actions=(
            ParsedAction(
                1,
                "BTN",
                "Preflop",
                "Check",
                0.0,
                False,
                2.0,
                0.03,
                0.03,
                None,
            ),
        ),
    )
    r = replay_parsed_hand(h)
    assert not r.action_sequence_ok


def test_ring_player_ids_error() -> None:
    p = ParsedPlayer(1, "BTN", 1.0, 1.0, True, "u", None)
    with pytest.raises(ValueError, match="missing positions"):
        ring_player_ids((p,), 6)


def test_initial_state_bad_player_count() -> None:
    h = ParsedHand(
        hand_id=1,
        stakes="1/2",
        game_type="NLH",
        num_players=1,
        small_blind=1.0,
        big_blind=2.0,
        hero_position=None,
        hero_cards=None,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(ParsedPlayer(1, "BTN", 100.0, 50.0, True, "u", None),),
    )
    with pytest.raises(ValueError, match="out of range"):
        initial_state_from_parsed_hand(h)


def test_initial_state_blinds_too_large() -> None:
    h = ParsedHand(
        hand_id=1,
        stakes="1/2",
        game_type="NLH",
        num_players=2,
        small_blind=1.0,
        big_blind=2.0,
        hero_position=None,
        hero_cards=None,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(
            ParsedPlayer(1, "BTN", 0.5, 25.0, True, "u1", None),
            ParsedPlayer(2, "BB", 0.5, 25.0, False, "u2", None),
        ),
    )
    with pytest.raises(ValueError, match="stack smaller than blinds"):
        initial_state_from_parsed_hand(h)


def test_pid_to_seat() -> None:
    assert pid_to_seat((3, 1, 2), 1) == 1


def test_illegal_actor_and_illegal_moves() -> None:
    h = parse_text(
        (FIXTURES / "hand_900006.txt").read_text(encoding="utf-8"),
        hand_id=900006,
        uid_secret="x",
    )
    assert h is not None
    s0 = initial_state_from_parsed_hand(h)
    bad = EngineAction(0, EngineActionKind.FOLD, 1)
    with pytest.raises(IllegalActionError):
        step(s0, bad)
    s1 = initial_state_from_parsed_hand(h)
    ok = EngineAction(s1.acting_seat or 0, EngineActionKind.FOLD, 0)
    s1b = step(s1, ok)
    with pytest.raises(IllegalActionError):
        step(s1b, ok)


def test_illegal_check_call_bet_raise() -> None:
    h = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert h is not None
    s = initial_state_from_parsed_hand(h)
    seat = s.acting_seat or 0
    with pytest.raises(IllegalActionError):
        eng.apply_action(s, EngineAction(seat, EngineActionKind.CHECK, 0))
    with pytest.raises(IllegalActionError):
        eng.apply_action(s, EngineAction(seat, EngineActionKind.CALL, 999))
    s2 = initial_state_from_parsed_hand(h)
    s2.current_max = 0
    s2.acting_seat = seat
    with pytest.raises(IllegalActionError):
        eng.apply_action(s2, EngineAction(seat, EngineActionKind.BET, 0))
    s3 = initial_state_from_parsed_hand(h)
    s3.current_max = 10
    s3.acting_seat = seat
    with pytest.raises(IllegalActionError):
        eng.apply_action(s3, EngineAction(seat, EngineActionKind.BET, 5))
    s4 = initial_state_from_parsed_hand(h)
    s4.acting_seat = seat
    with pytest.raises(IllegalActionError):
        eng.apply_action(s4, EngineAction(seat, EngineActionKind.RAISE, 1))
    s5 = initial_state_from_parsed_hand(h)
    s5.acting_seat = seat
    with pytest.raises(IllegalActionError):
        eng.apply_action(s5, EngineAction(seat, EngineActionKind.RAISE, 9999))


def test_fold_must_be_zero_amount() -> None:
    h = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert h is not None
    s = initial_state_from_parsed_hand(h)
    seat = s.acting_seat or 0
    with pytest.raises(IllegalActionError):
        eng.apply_action(s, EngineAction(seat, EngineActionKind.FOLD, 1))


def test_hand_over_step_rejected() -> None:
    h = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert h is not None
    r = replay_parsed_hand(h)
    assert r.final_state.hand_over
    with pytest.raises(IllegalActionError):
        step(r.final_state, EngineAction(0, EngineActionKind.CHECK, 0))


def test_legal_actions_branches() -> None:
    h = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert h is not None
    s = initial_state_from_parsed_hand(h)
    assert len(legal_actions(s)) >= 2
    s2 = replay_parsed_hand(h).final_state
    assert legal_actions(s2) == ()
    s3 = initial_state_from_parsed_hand(h)
    s3.hand_over = True
    assert legal_actions(s3) == ()
    s4 = initial_state_from_parsed_hand(h)
    s4.acting_seat = 0
    s4.folded[0] = True
    assert legal_actions(s4) == ()


def test_close_showdown_from_river() -> None:
    h = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert h is not None
    s = initial_state_from_parsed_hand(h)
    s.full_board = tuple(cards_from_space_separated("2d 3d 4d 5d 6d"))
    s.street = Street.RIVER
    s.board = list(s.full_board[:5])
    s.street_commit = [0, 0]
    s.current_max = 0
    s.acted_this_round = [True, True]
    s.acting_seat = None
    eng._close_betting_round(s)
    assert s.street == Street.SHOWDOWN
    assert len(s.board) == 5


def test_advance_turn_to_river_reveals_board() -> None:
    h = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert h is not None
    s = initial_state_from_parsed_hand(h)
    s.full_board = tuple(cards_from_space_separated("2d 3d 4d 5d 6d"))
    s.street = Street.TURN
    s.board = list(s.full_board[:4])
    s.street_commit = [0, 0]
    s.current_max = 0
    s.acted_this_round = [True, True]
    eng._advance_street(s)
    assert s.street == Street.RIVER
    assert len(s.board) == 5


def test_award_fold_win_idempotent() -> None:
    hand = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert hand is not None
    s = initial_state_from_parsed_hand(hand)
    s.folded = [True, False]
    eng._award_fold_win(s)
    assert s.hand_over
    eng._award_fold_win(s)


def test_return_uncalled_short_stack() -> None:
    hand = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert hand is not None
    s = initial_state_from_parsed_hand(hand)
    s.street_commit = [100, 50]
    s.stacks = [0, 150]
    s.pot = 150
    eng._return_uncalled_bet(s)
    assert s.pot == 100


def test_replay_bad_action_type() -> None:
    h = ParsedHand(
        hand_id=1,
        stakes="0.01/0.02",
        game_type="NLH",
        num_players=2,
        small_blind=0.01,
        big_blind=0.02,
        hero_position="BTN",
        hero_cards=None,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(
            ParsedPlayer(1, "BTN", 2.0, 100.0, True, "u1", None),
            ParsedPlayer(2, "BB", 2.0, 100.0, False, "u2", None),
        ),
        actions=(
            ParsedAction(
                1,
                "BTN",
                "Preflop",
                "Shove",
                1.0,
                False,
                2.0,
                0.0,
                0.03,
                None,
            ),
        ),
    )
    with pytest.raises(ValueError, match="unsupported"):
        replay_parsed_hand(h)


def test_parsed_action_to_engine_roundtrip() -> None:
    h = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert h is not None
    s = initial_state_from_parsed_hand(h)
    pa = h.actions[0]
    act = parsed_action_to_engine(s, pa)
    assert act.kind == EngineActionKind.RAISE


def test_replay_golden_hands() -> None:
    h_txt = parse_text(
        (FIXTURES / "hand_900006.txt").read_text(encoding="utf-8"),
        hand_id=900006,
        uid_secret="x",
    )
    assert h_txt is not None
    r_txt = replay_parsed_hand(h_txt)
    assert r_txt.pot_trace_ok and r_txt.action_sequence_ok

    h_json = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert h_json is not None
    r_json = replay_parsed_hand(h_json)
    assert r_json.pot_trace_ok and r_json.action_sequence_ok


@given(st=st.integers(50, 500_000))
def test_wealth_invariant_random_start(st: int) -> None:
    h = ParsedHand(
        hand_id=1,
        stakes="1/2",
        game_type="NLH",
        num_players=2,
        small_blind=1.0,
        big_blind=2.0,
        hero_position="BTN",
        hero_cards=None,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(
            ParsedPlayer(1, "BTN", float(st), float(st / 2.0), True, "u1", None),
            ParsedPlayer(2, "BB", float(st), float(st / 2.0), False, "u2", None),
        ),
        actions=(),
    )
    s = initial_state_from_parsed_hand(h)
    w0 = _wealth(s)
    assert all(x >= 0 for x in s.stacks)
    assert s.pot <= w0
    assert w0 == _wealth(s)


def test_replay_pot_mismatch_flag() -> None:
    h = ParsedHand(
        hand_id=1,
        stakes="0.01/0.02",
        game_type="NLH",
        num_players=2,
        small_blind=0.01,
        big_blind=0.02,
        hero_position="BTN",
        hero_cards=None,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(
            ParsedPlayer(1, "BTN", 2.0, 100.0, True, "u1", None),
            ParsedPlayer(2, "BB", 2.0, 100.0, False, "u2", None),
        ),
        actions=(
            ParsedAction(
                1,
                "BTN",
                "Preflop",
                "Raise",
                0.06,
                False,
                2.0,
                0.03,
                9.99,
                None,
            ),
        ),
    )
    r = replay_parsed_hand(h)
    assert not r.pot_trace_ok


def test_apply_non_strict_wrong_actor() -> None:
    h = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert h is not None
    s = initial_state_from_parsed_hand(h)
    act = EngineAction(1, EngineActionKind.FOLD, 0)
    s2 = eng.apply_action(s, act, strict_actor=False)
    assert s2.folded[1]


def test_apply_folded_seat_raises() -> None:
    h = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert h is not None
    s = initial_state_from_parsed_hand(h)
    s.folded[0] = True
    s.acting_seat = 0
    with pytest.raises(IllegalActionError):
        eng.apply_action(s, EngineAction(0, EngineActionKind.CHECK, 0), strict_actor=False)


def test_engine_internal_branches() -> None:
    h = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert h is not None
    s = initial_state_from_parsed_hand(h)
    s.folded = [True, True]
    assert eng._max_street_commit(s) == 0
    assert eng._needs_to_add_chips(s, 0) == 0

    s2 = initial_state_from_parsed_hand(h)
    eng._reveal_board_for_current_street(s2)
    assert s2.board == []

    s3 = initial_state_from_parsed_hand(h)
    s3.full_board = tuple(cards_from_space_separated("2d 3d 4d 5d 6d"))
    s3.street = Street.SHOWDOWN
    eng._reveal_board_for_current_street(s3)
    assert len(s3.board) == 5

    s4 = initial_state_from_parsed_hand(h)
    s4.street = Street.RIVER
    eng._advance_street(s4)
    assert s4.street == Street.RIVER

    s5 = initial_state_from_parsed_hand(h)
    s5.folded = [True, True]
    assert eng._first_live_from(s5, 0) is None

    s6 = initial_state_from_parsed_hand(h)
    s6.acted_this_round = [True, True]
    assert eng._next_checkdown_seat(s6, 0) is None

    s7 = initial_state_from_parsed_hand(h)
    s7.hand_over = True
    eng._compute_next_acting(s7, 0)
    assert s7.acting_seat is None

    s8 = initial_state_from_parsed_hand(h)
    s8.folded = [True, False]
    eng._compute_next_acting(s8, 0)
    assert s8.hand_over

    s9 = initial_state_from_parsed_hand(h)
    s9.street = Street.FLOP
    s9.full_board = tuple(cards_from_space_separated("2d 3d 4d 5d 6d"))
    s9.board = list(s9.full_board[:3])
    s9.street_commit = [0, 0]
    s9.current_max = 0
    s9.acted_this_round = [True, False]
    eng._compute_next_acting(s9, 0)
    assert s9.acting_seat == 1

    s10 = initial_state_from_parsed_hand(h)
    s10.street_commit = [s10.big_blind, s10.big_blind]
    s10.current_max = s10.big_blind
    s10.raise_count_street = 0
    s10.bb_checked_preflop = False
    s10.acted_this_round = [True, True]
    eng._compute_next_acting(s10, 0)
    assert s10.acting_seat == s10.bb_seat


def test_engine_coverage_remainder() -> None:
    """Target remaining branches in ``engine.py`` for full coverage."""
    h = parse_ohh_dict(
        json.loads((FIXTURES / "sample_ohh.json").read_text(encoding="utf-8")),
        uid_secret="x",
    )
    assert h is not None
    s_gap = initial_state_from_parsed_hand(h)
    s_gap.current_max = 10
    s_gap.street_commit[0] = 10
    assert eng._needs_to_add_chips(s_gap, 0) == 0

    h3 = ParsedHand(
        hand_id=99,
        stakes="1/2",
        game_type="NLH",
        num_players=3,
        small_blind=1.0,
        big_blind=2.0,
        hero_position=None,
        hero_cards=None,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(
            ParsedPlayer(1, "BTN", 200.0, 100.0, True, "a", None),
            ParsedPlayer(2, "SB", 200.0, 100.0, False, "b", None),
            ParsedPlayer(3, "BB", 200.0, 100.0, False, "c", None),
        ),
    )
    s3p = initial_state_from_parsed_hand(h3)
    assert eng._first_postflop_actor(s3p) == s3p.sb_seat

    s_fold = initial_state_from_parsed_hand(h3)
    s_fold.street_commit = [5, 20, 10]
    s_fold.stacks = [50, 50, 50]
    s_fold.folded[0] = True
    assert eng._next_seat_needing_chips(s_fold, start_after=2) == 2

    s3p2 = initial_state_from_parsed_hand(h3)
    s3p2.street_commit = [5, 20, 20]
    s3p2.stacks = [50, 0, 50]
    s3p2.folded = [False, False, False]
    assert eng._next_seat_needing_chips(s3p2, start_after=2) == 0

    s_sk0 = initial_state_from_parsed_hand(h3)
    s_sk0.street_commit = [5, 15, 10]
    s_sk0.stacks = [50, 0, 50]
    s_sk0.folded = [False, False, False]
    assert eng._next_seat_needing_chips(s_sk0, 0) == 2

    s_em = initial_state_from_parsed_hand(h)
    s_em.current_max = 10
    s_em.street_commit[0] = 10
    assert eng._everyone_matched_or_all_in(s_em) is False
    sm = initial_state_from_parsed_hand(h)
    sm.street_commit = [0, 0]
    assert eng._everyone_matched_or_all_in(sm) is False
    sm2 = initial_state_from_parsed_hand(h)
    sm2.street_commit = [10, 5]
    assert eng._everyone_matched_or_all_in(sm2) is False
    sm2.street_commit = [10, 10]
    sm2.current_max = 10
    assert eng._everyone_matched_or_all_in(sm2) is True

    sturn = initial_state_from_parsed_hand(h)
    sturn.full_board = tuple(cards_from_space_separated("2d 3d 4d 5d 6d"))
    sturn.street = Street.TURN
    eng._reveal_board_for_current_street(sturn)
    assert len(sturn.board) == 4

    sfl = initial_state_from_parsed_hand(h)
    sfl.full_board = tuple(cards_from_space_separated("2d 3d 4d 5d 6d"))
    sfl.street = Street.FLOP
    sfl.board = list(sfl.full_board[:3])
    eng._advance_street(sfl)
    assert sfl.street == Street.TURN

    sru = initial_state_from_parsed_hand(h)
    sru.street_commit = [20, 10]
    sru.folded[1] = True
    eng._return_uncalled_bet(sru)

    s_aw = initial_state_from_parsed_hand(h)
    eng._award_fold_win(s_aw)

    s_cl = initial_state_from_parsed_hand(h)
    s_cl.folded = [True, False]
    eng._close_betting_round(s_cl)
    assert s_cl.hand_over

    s_cd = initial_state_from_parsed_hand(h)
    s_cd.street = Street.FLOP
    s_cd.full_board = tuple(cards_from_space_separated("2d 3d 4d 5d 6d"))
    s_cd.board = list(s_cd.full_board[:3])
    s_cd.folded[0] = True
    s_cd.stacks[1] = 0
    s_cd.acted_this_round = [True, True]
    assert eng._next_checkdown_seat(s_cd, 0) is None

    s_z = initial_state_from_parsed_hand(h)
    s_z.street = Street.FLOP
    s_z.full_board = tuple(cards_from_space_separated("2d 3d 4d 5d 6d"))
    s_z.board = list(s_z.full_board[:3])
    s_z.street_commit = [0, 0]
    s_z.current_max = 0
    s_z.acted_this_round = [True, True]
    eng._compute_next_acting(s_z, 0)
    assert s_z.street == Street.TURN

    s_bb = initial_state_from_parsed_hand(h)
    s_bb.acting_seat = s_bb.bb_seat
    with pytest.raises(IllegalActionError):
        bad_check = EngineAction(s_bb.bb_seat, EngineActionKind.CHECK, 1)
        eng.apply_action(s_bb, bad_check, strict_actor=False)

    s_bc = initial_state_from_parsed_hand(h)
    s_bc = eng.step(s_bc, EngineAction(s_bc.acting_seat or 0, EngineActionKind.CALL, 1))
    assert s_bc.acting_seat == s_bc.bb_seat
    s_bc = eng.apply_action(
        s_bc,
        EngineAction(s_bc.bb_seat, EngineActionKind.CHECK, 0),
        strict_actor=False,
    )
    assert s_bc.street == Street.FLOP

    s_bcall = initial_state_from_parsed_hand(h)
    s_bcall.street_commit = [s_bcall.big_blind, s_bcall.big_blind]
    s_bcall.current_max = s_bcall.big_blind
    s_bcall.raise_count_street = 0
    s_bcall.acting_seat = s_bcall.bb_seat
    eng.apply_action(
        s_bcall,
        EngineAction(s_bcall.bb_seat, EngineActionKind.CALL, 0),
        strict_actor=False,
    )

    s_la = initial_state_from_parsed_hand(h)
    s_la.current_max = 8
    s_la.street_commit = [0, 4]
    s_la.stacks = [196, 194]
    s_la.acting_seat = 1
    acts = eng.legal_actions(s_la)
    kinds = {a.kind for a in acts}
    assert EngineActionKind.RAISE in kinds

    s_pf = initial_state_from_parsed_hand(h)
    s_pf.street = Street.FLOP
    s_pf.current_max = 0
    s_pf.street_commit = [0, 0]
    s_pf.stacks = [200, 200]
    s_pf.pot = 300
    s_pf.acting_seat = 0
    acts_pf = eng.legal_actions(s_pf)
    assert any(a.kind == EngineActionKind.CHECK for a in acts_pf)
    bets = [a for a in acts_pf if a.kind == EngineActionKind.BET]
    assert len(bets) == 2
    assert bets[0].amount_chips != bets[1].amount_chips


def test_initial_state_antes_length_mismatch_raises() -> None:
    h = ParsedHand(
        hand_id=1,
        stakes="1/2",
        game_type="NLH",
        num_players=2,
        small_blind=1.0,
        big_blind=2.0,
        hero_position="BTN",
        hero_cards=None,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        antes=(0.5,),
        players=(
            ParsedPlayer(1, "BTN", 100.0, 50.0, True, "u1", None),
            ParsedPlayer(2, "BB", 100.0, 50.0, False, "u2", None),
        ),
        actions=(),
    )
    with pytest.raises(ValueError, match="antes length"):
        initial_state_from_parsed_hand(h)


def test_initial_state_ante_exceeds_stack_raises() -> None:
    h = ParsedHand(
        hand_id=1,
        stakes="1/2",
        game_type="NLH",
        num_players=2,
        small_blind=1.0,
        big_blind=2.0,
        hero_position="BTN",
        hero_cards=None,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        antes=(200.0, 0.0),
        players=(
            ParsedPlayer(1, "BTN", 100.0, 50.0, True, "u1", None),
            ParsedPlayer(2, "BB", 100.0, 50.0, False, "u2", None),
        ),
        actions=(),
    )
    with pytest.raises(ValueError, match="stack smaller than ante"):
        initial_state_from_parsed_hand(h)


def test_initial_state_negative_ante_raises() -> None:
    h = ParsedHand(
        hand_id=1,
        stakes="1/2",
        game_type="NLH",
        num_players=2,
        small_blind=1.0,
        big_blind=2.0,
        hero_position="BTN",
        hero_cards=None,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        antes=(-1.0, 0.0),
        players=(
            ParsedPlayer(1, "BTN", 100.0, 50.0, True, "u1", None),
            ParsedPlayer(2, "BB", 100.0, 50.0, False, "u2", None),
        ),
        actions=(),
    )
    with pytest.raises(ValueError, match="negative ante"):
        initial_state_from_parsed_hand(h)


def test_replay_phh_hu_with_antes_fold() -> None:
    from poker_ai.ingest.phh_text import parse_phh_block_dict

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
        external_ref="hu-antes-fold",
        uid_secret="k",
    )
    assert h is not None
    assert h.antes == (1.0, 1.0)
    s0 = initial_state_from_parsed_hand(h)
    assert s0.pot == money_to_chips(5.0)
    r = replay_parsed_hand(h)
    assert r.action_sequence_ok and r.pot_trace_ok


def test_store_replay_matches_file_parse(
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    path = FIXTURES / "hand_900006.txt"

    async def _run() -> None:
        await ingest_path(
            path,
            session_factory=migrated_session_factory,
            uid_secret="test-secret-not-for-production",
        )
        async with migrated_session_factory() as session:
            hid = 900006
            ac = (
                (
                    await session.execute(
                        select(Action).where(Action.hand_id == hid).order_by(Action.id)
                    )
                )
                .scalars()
                .all()
            )
            assert len(ac) > 0
        h_file = parse_text(
            path.read_text(encoding="utf-8"),
            hand_id=hid,
            uid_secret="test-secret-not-for-production",
        )
        assert h_file is not None
        assert len(ac) == len(h_file.actions)
        r = replay_parsed_hand(h_file)
        assert r.action_sequence_ok

    asyncio.run(_run())
