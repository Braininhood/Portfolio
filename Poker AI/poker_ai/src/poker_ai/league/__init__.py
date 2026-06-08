"""Self-play league (Phase 9) — HU and multi-way table formats."""

from poker_ai.league.agents import LeagueAgent, build_default_roster
from poker_ai.league.evaluator import LeagueBoard, leaderboard_rows, promotion_significant
from poker_ai.league.formats import (
    DEFAULT_FORMATS,
    TableFormat,
    formats_from_seats,
    parse_table_sizes,
)
from poker_ai.league.orchestrator import LeagueConfig, LeagueRunResult, load_leaderboard, run_league
from poker_ai.league.sim import HandResult, new_hu_hand, new_table_hand, play_hand

__all__ = [
    "DEFAULT_FORMATS",
    "HandResult",
    "LeagueAgent",
    "LeagueBoard",
    "LeagueConfig",
    "LeagueRunResult",
    "TableFormat",
    "build_default_roster",
    "formats_from_seats",
    "leaderboard_rows",
    "load_leaderboard",
    "new_hu_hand",
    "new_table_hand",
    "parse_table_sizes",
    "play_hand",
    "promotion_significant",
    "run_league",
]
