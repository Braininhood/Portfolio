"""Tests for ``poker_ai.core.evaluator``."""

from __future__ import annotations

import os
import time

import pytest

from poker_ai.core.cards import parse_card
from poker_ai.core.evaluator import evaluate_ohh_cards, hand_rank_value


def test_hand_rank_value_int_cards() -> None:
    r = hand_rank_value(*[parse_card(x) for x in ("ah", "kh", "qh", "jh", "th", "2c", "3d")])
    assert r == 1


def test_hand_rank_value_str_cards() -> None:
    r = evaluate_ohh_cards("9c", "4c", "4s", "9d", "4h", "Qc", "6c")
    assert isinstance(r, int)


def test_hand_rank_value_bad_count() -> None:
    with pytest.raises(ValueError):
        hand_rank_value("2c", "3d", "4h")


def test_evaluator_bad_string_token() -> None:
    with pytest.raises(ValueError):
        hand_rank_value("bad")


@pytest.mark.skipif(os.environ.get("POKER_AI_SKIP_PERF") == "1", reason="perf skipped")
def test_evaluator_seven_card_throughput() -> None:
    cards = tuple(parse_card(x) for x in ("as", "ks", "qs", "js", "ts", "2c", "3d"))
    n = 200_000
    t0 = time.perf_counter()
    for _ in range(n):
        hand_rank_value(*cards)
    elapsed = time.perf_counter() - t0
    rate = n / elapsed
    floor = float(os.environ.get("POKER_AI_PERF_EVAL_MIN_RATE", "100000"))
    assert rate >= floor, f"eval/sec too low: {rate:.0f} (set POKER_AI_PERF_EVAL_MIN_RATE)"
