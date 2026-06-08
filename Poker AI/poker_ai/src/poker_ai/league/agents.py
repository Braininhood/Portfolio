"""Backward-compatible re-exports — prefer ``poker_ai.league.agents`` package."""

from poker_ai.league.agents.baselines import (
    CallStationPolicy,
    FishPolicy,
    LAGPolicy,
    ManiacPolicy,
    NitPolicy,
    PassiveRegPolicy,
    RandomPolicy,
    RockPolicy,
    TagPolicy,
)
from poker_ai.league.agents.registry import LeagueAgent, build_default_roster

__all__ = [
    "CallStationPolicy",
    "FishPolicy",
    "LAGPolicy",
    "LeagueAgent",
    "ManiacPolicy",
    "NitPolicy",
    "PassiveRegPolicy",
    "RandomPolicy",
    "RockPolicy",
    "TagPolicy",
    "build_default_roster",
]
