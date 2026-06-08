"""Tests for ``poker_ai.core.cards``."""

from __future__ import annotations

import pytest

from poker_ai.core import cards as c


def test_card_round_trip() -> None:
    i = c.card_to_int("A", "h")
    assert c.card_from_int(i) == ("A", "h")


def test_parse_card_variants() -> None:
    assert c.parse_card("th") == c.card_to_int("T", "h")
    assert c.parse_card("2c") == 0


def test_cards_from_space_separated() -> None:
    assert c.cards_from_space_separated("") == ()
    assert c.cards_from_space_separated(None) == ()
    assert len(c.cards_from_space_separated("ah kh")) == 2


def test_card_from_int_bad() -> None:
    with pytest.raises(ValueError):
        c.card_from_int(52)


def test_parse_card_bad() -> None:
    with pytest.raises(ValueError):
        c.parse_card("xxx")
    with pytest.raises(ValueError):
        c.parse_card("Xh")


def test_cards_from_space_bad() -> None:
    with pytest.raises(ValueError):
        c.cards_from_space_separated("ahh")
