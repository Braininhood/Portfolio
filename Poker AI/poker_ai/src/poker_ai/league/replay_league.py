"""League-style evaluation on ingested hands (hero replay scoring — v2)."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from poker_ai.core.profiles import PlayerProfile
from poker_ai.core.replay import state_after_actions
from poker_ai.eval.aivat import aivat_mode
from poker_ai.features.student_extras import _hero_result, hero_aivat_bb
from poker_ai.league.replay_sampler import iter_replay_samples
from poker_ai.learn.multiway_dataset import _hero_player_id
from poker_ai.policy.base import Policy
from poker_ai.policy.heuristic import HeuristicPolicy


ProgressFn = Callable[[dict[str, Any]], None] | None
CancelCheck = Callable[[], bool] | None


@dataclass(frozen=True, slots=True)
class AgentReplayScore:
    agent_id: str
    hero_decisions: int
    hands: int
    bb_per_100: float
    aivat_bb_per_100: float
    action_match_pct: float


@dataclass(frozen=True, slots=True)
class ReplayLeagueReport:
    finished_at: str
    hands_scored: int
    hero_decisions: int
    aivat_mode: str
    agents: tuple[AgentReplayScore, ...]
    by_format: dict[str, dict[str, float]]
    report_path: str


def _load_policy(agent_id: str) -> Policy:
    if agent_id in ("main_agent", "best"):
        try:
            from poker_ai.policy.distilled_policy import load_best_policy

            return load_best_policy()
        except Exception:
            pass
    if agent_id == "distilled_gto":
        from poker_ai.policy.distilled_policy import DistilledPolicy

        return DistilledPolicy.from_artifacts()
    return HeuristicPolicy()


def _hero_action_indices(hand) -> list[int]:
    hero_pid = _hero_player_id(hand)
    if hero_pid is None:
        return []
    return [i for i, pa in enumerate(hand.actions) if pa.player_id == hero_pid]


def _action_matches_policy(hand, idx: int, policy: Policy, profile: PlayerProfile) -> bool:
    try:
        state = state_after_actions(hand, idx, lenient=True)
    except (ValueError, KeyError, IndexError):
        return False
    if state.hand_over:
        return False
    pa = hand.actions[idx]
    dist = policy.propose(state, profile).normalized()
    if not dist.actions:
        return False
    best_i = max(range(len(dist.probs)), key=lambda i: dist.probs[i])
    top_kind = dist.actions[best_i][0].lower()
    kind = pa.action_type.lower()
    if kind == "fold":
        return top_kind == "fold"
    if kind in ("check", "call"):
        return top_kind in ("check", "call")
    return top_kind in ("bet", "raise")


async def _run_replay_league_async(
    *,
    limit: int,
    strata: frozenset[str],
    agent_ids: tuple[str, ...],
    since=None,
    progress: ProgressFn = None,
    cancel_check: CancelCheck = None,
) -> ReplayLeagueReport:
    from poker_ai.store.db import get_async_session_factory

    factory = get_async_session_factory()
    profile = PlayerProfile(profile_id="hero")
    policies = {aid: _load_policy(aid) for aid in agent_ids}

    stats: dict[str, dict[str, float]] = {
        aid: {
            "hands": 0.0,
            "hero_decisions": 0.0,
            "bb_sum": 0.0,
            "aivat_sum": 0.0,
            "matches": 0.0,
        }
        for aid in agent_ids
    }
    format_bb: dict[str, list[float]] = {"hu": [], "mw": []}
    hands_scored = 0
    total_decisions = 0

    async with factory() as session:
        async for sample in iter_replay_samples(
            session, limit=limit, strata=strata, since=since
        ):
            if cancel_check and cancel_check():
                from poker_ai.runtime.cancel import WorkCancelled

                raise WorkCancelled("Replay league stopped")
            hand = sample.hand
            hero_bb, _sd = _hero_result(hand)
            aivat_bb = hero_aivat_bb(hand)
            indices = _hero_action_indices(hand)
            if not indices:
                continue
            hands_scored += 1
            format_bb[sample.format_id].append(hero_bb)
            total_decisions += len(indices)

            for aid in agent_ids:
                pol = policies[aid]
                matches = sum(
                    1 for idx in indices if _action_matches_policy(hand, idx, pol, profile)
                )
                stats[aid]["hands"] += 1.0
                stats[aid]["hero_decisions"] += float(len(indices))
                stats[aid]["bb_sum"] += hero_bb
                stats[aid]["aivat_sum"] += aivat_bb
                stats[aid]["matches"] += float(matches)

            if progress and limit > 0:
                progress(
                    {
                        "pct": min(99, int(100 * hands_scored / limit)),
                        "msg": f"Replay league: {hands_scored}/{limit} hands",
                        "detail": {"hands_scored": hands_scored, "hero_decisions": total_decisions},
                    }
                )

    agents: list[AgentReplayScore] = []
    for aid in agent_ids:
        s = stats[aid]
        h = max(1.0, s["hands"])
        dec = max(1.0, s["hero_decisions"])
        agents.append(
            AgentReplayScore(
                agent_id=aid,
                hero_decisions=int(s["hero_decisions"]),
                hands=int(s["hands"]),
                bb_per_100=round(s["bb_sum"] / h * 100.0, 2),
                aivat_bb_per_100=round(s["aivat_sum"] / h * 100.0, 2),
                action_match_pct=round(s["matches"] / dec * 100.0, 2),
            )
        )

    by_format: dict[str, dict[str, float]] = {}
    for fmt, vals in format_bb.items():
        if vals:
            by_format[fmt] = {
                "hands": float(len(vals)),
                "bb_per_100": round(sum(vals) / len(vals) * 100.0, 2),
            }

    dest = Path("reports/league_replay.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    report = ReplayLeagueReport(
        finished_at=datetime.now(tz=UTC).isoformat(),
        hands_scored=hands_scored,
        hero_decisions=total_decisions,
        aivat_mode=aivat_mode(),
        agents=tuple(agents),
        by_format=by_format,
        report_path=str(dest.resolve()),
    )
    payload = {
        **asdict(report),
        "agents": [asdict(a) for a in agents],
    }
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report


def run_replay_league(
    *,
    limit: int = 500,
    strata: str = "hu,mw",
    agents: str = "main_agent,distilled_gto",
    since=None,
    progress: ProgressFn = None,
    cancel_check: CancelCheck = None,
) -> ReplayLeagueReport:
    """Sync entry — same module for CLI and web jobs."""
    parts = frozenset(s.strip() for s in strata.split(",") if s.strip())
    agent_ids = tuple(a.strip() for a in agents.split(",") if a.strip())
    return asyncio.run(
        _run_replay_league_async(
            limit=limit,
            strata=parts or frozenset({"hu", "mw"}),
            agent_ids=agent_ids or ("main_agent", "distilled_gto"),
            since=since,
            progress=progress,
            cancel_check=cancel_check,
        )
    )
