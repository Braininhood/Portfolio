"""Tests for ``poker_ai.core.profiles``."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from poker_ai.core.profiles import PlayerProfile


def test_player_profile() -> None:
    p = PlayerProfile(profile_id="p1", display_name="Alice", notes="tag")
    assert p.profile_id == "p1"


def test_player_profile_requires_id() -> None:
    with pytest.raises(ValidationError):
        PlayerProfile(profile_id="", display_name="x")
