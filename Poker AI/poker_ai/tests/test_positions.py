"""Unit tests for canonical seat labels (``positions`` module)."""

from __future__ import annotations

from unittest.mock import patch

from poker_ai.ingest import positions as pos


def test_physical_clockwise_pids_fallbacks() -> None:
    assert pos.physical_clockwise_pids({}, 4) == [1, 2, 3, 4]
    assert pos.physical_clockwise_pids({1: 1}, 4) == [1, 2, 3, 4]
    m = {3: 1, 1: 2, 4: 3, 2: 4}
    assert pos.physical_clockwise_pids(m, 4) == [2, 4, 1, 3]


def test_infer_sb_bb_pids() -> None:
    assert pos.infer_sb_bb_pids([0, 0, 5, 10], 4) == (3, 4)
    assert pos.infer_sb_bb_pids([10, 5, 0, 0], 4) is None
    assert pos.infer_sb_bb_pids([0.0, 0.0], 2) is None


def test_infer_button_pid() -> None:
    assert pos.infer_button_pid([1, 2, 3, 4], sb_pid=2, n=4) == 1
    assert pos.infer_button_pid([1, 2, 3, 4], sb_pid=99, n=4) is None
    assert pos.infer_button_pid([1, 2], sb_pid=1, n=2) == 1


def test_ring_starting_button() -> None:
    assert pos.ring_starting_button([1, 2, 3, 4], 99) == [1, 2, 3, 4]
    assert pos.ring_starting_button([1, 2, 3, 4], 3) == [3, 4, 1, 2]


def test_phh_position_label_edges() -> None:
    assert pos.phh_position_label(n=1, player_id=1, blinds=[1], seat_to_pid={1: 1}) == "S1"
    blinds_11 = [1.0, 2.0] + [0.0] * 9
    assert pos.phh_position_label(n=11, player_id=1, blinds=blinds_11, seat_to_pid={}) == ("S1")
    assert (
        pos.phh_position_label(n=3, player_id=1, blinds=[0, 0, 0], seat_to_pid={1: 1, 2: 2, 3: 3})
        == "S1"
    )
    assert (
        pos.phh_position_label(n=3, player_id=9, blinds=[1, 2, 0], seat_to_pid={1: 1, 2: 2, 3: 3})
        == "S9"
    )


def test_phh_position_label_btn_none() -> None:
    bad_map = {1: 1, 2: 2, 3: 3, 4: 4}
    with patch.object(pos, "physical_clockwise_pids", return_value=[1, 2, 3, 4]):
        with patch.object(pos, "infer_button_pid", return_value=None):
            assert (
                pos.phh_position_label(n=4, player_id=2, blinds=[1, 2, 0, 0], seat_to_pid=bad_map)
                == "S2"
            )


def test_phh_position_label_ring_missing() -> None:
    pr = dict(pos.POSITION_RING)
    del pr[6]
    with patch.object(pos, "POSITION_RING", pr):
        assert (
            pos.phh_position_label(
                n=6,
                player_id=1,
                blinds=[50, 100, 0, 0, 0, 0],
                seat_to_pid={i: i for i in range(1, 7)},
            )
            == "S1"
        )


def test_phh_position_label_idx_guard_with_short_ring() -> None:
    with patch.dict(pos.POSITION_RING, {2: ("BTN",)}, clear=False):
        assert (
            pos.phh_position_label(n=2, player_id=2, blinds=[1, 2], seat_to_pid={1: 1, 2: 2})
            == "S2"
        )


def test_ohh_position_label_edges() -> None:
    assert pos.ohh_position_label(n=1, seat_num=1, phys_order=[1], sb_seat=1, bb_seat=1) == "S1"
    assert (
        pos.ohh_position_label(n=2, seat_num=1, phys_order=[1, 2], sb_seat=None, bb_seat=2) == "S1"
    )
    assert (
        pos.ohh_position_label(
            n=11, seat_num=1, phys_order=list(range(1, 12)), sb_seat=1, bb_seat=2
        )
        == "S1"
    )
    assert (
        pos.ohh_position_label(n=3, seat_num=1, phys_order=[1, 2, 3], sb_seat=9, bb_seat=2) == "S1"
    )
    with patch.object(pos, "infer_button_pid", return_value=None):
        assert (
            pos.ohh_position_label(n=3, seat_num=1, phys_order=[1, 2, 3], sb_seat=1, bb_seat=2)
            == "S1"
        )
    assert (
        pos.ohh_position_label(n=3, seat_num=9, phys_order=[1, 2, 3], sb_seat=1, bb_seat=2) == "S9"
    )


def test_ohh_position_label_ring_missing() -> None:
    pr = dict(pos.POSITION_RING)
    del pr[3]
    with patch.object(pos, "POSITION_RING", pr):
        assert (
            pos.ohh_position_label(n=3, seat_num=1, phys_order=[1, 2, 3], sb_seat=1, bb_seat=2)
            == "S1"
        )


def test_ohh_position_label_idx_guard_with_short_ring() -> None:
    with patch.dict(pos.POSITION_RING, {2: ("BTN",)}, clear=False):
        assert (
            pos.ohh_position_label(n=2, seat_num=2, phys_order=[1, 2], sb_seat=1, bb_seat=2) == "S2"
        )


def test_normalize_text_position() -> None:
    assert pos.normalize_text_position("") == ""
    assert pos.normalize_text_position("  hero ( BTN ) ") == "BTN"
    assert pos.normalize_text_position("Hero ()") == "BTN"
    assert pos.normalize_text_position("utg + 1") == "UTG1"
    assert pos.normalize_text_position("UTG+1") == "UTG1"
    assert pos.normalize_text_position("UTG+2") == "UTG2"
