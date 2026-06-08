"""AlphaStar-style league roster — main, exploiters, frozen baselines (Phase 9)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from poker_ai.core.profiles import PlayerProfile
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
from poker_ai.policy.base import Policy


@dataclass(frozen=True, slots=True)
class LeagueAgent:
    """Named policy slot in the league."""

    agent_id: str
    role: str
    policy: Policy
    profile: PlayerProfile
    elo: float = 1500.0
    hands: int = 0
    chips_won: int = 0


def load_headline_policy() -> Policy:
    """Runtime router (HU + multi-way) when artifacts exist."""
    from poker_ai.policy.distilled_policy import load_best_policy

    return load_best_policy()


def _try_exploit_policy() -> Policy | None:
    """Phase 8 exploit wrapper when style encoder artifacts exist."""
    style_dir = Path("artifacts/style_encoder/v1")
    weights = style_dir / "style_encoder.safetensors"
    alt = style_dir / "model.pt"
    if not weights.is_file() and not alt.is_file():
        return None
    try:
        from poker_ai.policy.exploit_policy import ExploitPolicy

        return ExploitPolicy.from_artifacts()
    except (FileNotFoundError, OSError, ValueError):
        return None


def build_default_roster(
    *,
    student_dir: Path = Path("artifacts/student/v1"),
    multiway_student_dir: Path = Path("artifacts/student/multiway_v1"),
    cfr_hu: Path = Path("artifacts/solver/preflop_hu_real.json"),
    cfr_6: Path = Path("artifacts/solver/preflop_cfr.json"),
) -> list[LeagueAgent]:
    """Main + exploiters + frozen archetypes (TAG, LAG, NIT, fish, …)."""
    main_policy = load_headline_policy()
    main_exploiter_policy = _try_exploit_policy() or ManiacPolicy()
    roster: list[LeagueAgent] = [
        LeagueAgent("main_agent", "main", main_policy, PlayerProfile(profile_id="main")),
        LeagueAgent(
            "main_exploiter",
            "exploiter",
            main_exploiter_policy,
            PlayerProfile(profile_id="main_exploiter"),
        ),
        LeagueAgent(
            "distilled_gto",
            "frozen",
            main_policy,
            PlayerProfile(profile_id="distilled"),
        ),
        LeagueAgent("tag", "frozen", TagPolicy(), PlayerProfile(profile_id="tag")),
        LeagueAgent("lag", "frozen", LAGPolicy(), PlayerProfile(profile_id="lag")),
        LeagueAgent("nit", "frozen", NitPolicy(), PlayerProfile(profile_id="nit")),
        LeagueAgent("rock", "frozen", RockPolicy(), PlayerProfile(profile_id="rock")),
        LeagueAgent(
            "call_station",
            "frozen",
            CallStationPolicy(),
            PlayerProfile(profile_id="call"),
        ),
        LeagueAgent("fish", "frozen", FishPolicy(), PlayerProfile(profile_id="fish")),
        LeagueAgent(
            "passive_reg",
            "frozen",
            PassiveRegPolicy(),
            PlayerProfile(profile_id="passive_reg"),
        ),
        LeagueAgent(
            "random",
            "frozen",
            RandomPolicy(seed=1),
            PlayerProfile(profile_id="random"),
        ),
    ]

    from poker_ai.policy.cql_policy import CQLPolicy

    cql = CQLPolicy.from_artifacts()
    if cql is not None:
        roster.append(
            LeagueAgent(
                "cql_agent",
                "research",
                cql,
                PlayerProfile(profile_id="cql_agent"),
            )
        )

    if cfr_hu.is_file():
        from poker_ai.policy.stacked import StackedPolicy

        stacked = StackedPolicy.from_artifacts(preflop_hu=cfr_hu, student_dir=student_dir)
        roster.append(
            LeagueAgent(
                "cfr_stacked",
                "frozen",
                stacked,
                PlayerProfile(profile_id="cfr_stacked"),
            )
        )
        roster.append(
            LeagueAgent(
                "league_exploiter",
                "exploiter",
                stacked,
                PlayerProfile(profile_id="league_exploiter"),
            )
        )
    else:
        roster.append(
            LeagueAgent(
                "league_exploiter",
                "exploiter",
                LAGPolicy(),
                PlayerProfile(profile_id="league_exploiter"),
            )
        )

    _ = multiway_student_dir, cfr_6, student_dir
    return roster
