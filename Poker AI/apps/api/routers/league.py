"""GET /league/* — leaderboard, checkpoints, replay report, AIVAT audit."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from deps import cached_settings
from schemas import (
    AivatAuditResponse,
    CheckpointsResponse,
    CheckpointRow,
    LeaderboardResponse,
    LeaderboardRow,
    ReplayAgentRow,
    ReplayLeagueResponse,
)

router = APIRouter(prefix="/league", tags=["league"])


def _resolve_report(path: Path) -> Path:
    if path.is_file():
        return path
    project = Path(__file__).resolve().parents[3] / "poker_ai" / path
    if project.is_file():
        return project
    repo = Path(__file__).resolve().parents[3]
    alt = repo / "poker_ai" / "reports" / path.name
    if alt.is_file():
        return alt
    return path


@router.get("/leaderboard", response_model=LeaderboardResponse)
def league_leaderboard(
    report: Path | None = Query(default=None, description="Override report path."),
) -> LeaderboardResponse:
    settings = cached_settings()
    path = _resolve_report(report or Path("reports/league_leaderboard.json"))
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="No league report — run `poker_ai league run` first.",
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = [
        LeaderboardRow(
            agent_id=str(r.get("agent_id", "")),
            elo=r.get("elo"),
            hands=r.get("hands"),
            bb_per_100=r.get("bb_per_100"),
            aivat_bb_per_100=r.get("aivat_bb_per_100"),
        )
        for r in data.get("leaderboard") or []
        if r.get("agent_id") != "_field"
    ]
    _ = settings
    return LeaderboardResponse(
        finished_at=data.get("finished_at"),
        hands_played=data.get("hands_played"),
        promoted=data.get("promoted"),
        rows=rows,
    )


@router.get("/checkpoints", response_model=CheckpointsResponse)
def league_checkpoints() -> CheckpointsResponse:
    from poker_ai.league.checkpoint_registry import current_checkpoint_id, list_checkpoints

    cur = current_checkpoint_id()
    rows = [
        CheckpointRow(
            checkpoint_id=cp.checkpoint_id,
            created_at=cp.created_at,
            main_elo=cp.main_elo,
            hands=cp.hands,
            promoted=cp.promoted,
            note=cp.note or None,
            is_current=cp.checkpoint_id == cur,
        )
        for cp in list_checkpoints()
    ]
    return CheckpointsResponse(current=cur, rows=rows)


@router.get("/replay-report", response_model=ReplayLeagueResponse)
def league_replay_report() -> ReplayLeagueResponse:
    path = _resolve_report(Path("reports/league_replay.json"))
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="No replay league report — run league on your library first.",
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    agents = [
        ReplayAgentRow(
            agent_id=str(a.get("agent_id", "")),
            hands=a.get("hands"),
            hero_decisions=a.get("hero_decisions"),
            bb_per_100=a.get("bb_per_100"),
            aivat_bb_per_100=a.get("aivat_bb_per_100"),
            action_match_pct=a.get("action_match_pct"),
        )
        for a in data.get("agents") or []
    ]
    return ReplayLeagueResponse(
        finished_at=data.get("finished_at"),
        hands_scored=data.get("hands_scored"),
        hero_decisions=data.get("hero_decisions"),
        aivat_mode=data.get("aivat_mode"),
        agents=agents,
        by_format=data.get("by_format") or {},
    )


@router.get("/aivat-audit", response_model=AivatAuditResponse)
def league_aivat_audit() -> AivatAuditResponse:
    path = _resolve_report(Path("reports/aivat_audit.json"))
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="No AIVAT audit yet — run AIVAT audit from Tasks first.",
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return AivatAuditResponse(
        finished_at=data.get("finished_at"),
        aivat_mode=data.get("aivat_mode"),
        hands=data.get("hands"),
        naive_stderr=data.get("naive_stderr"),
        full_stderr=data.get("full_stderr"),
        stderr_reduction_pct=data.get("stderr_reduction_pct"),
        report_path=data.get("report_path"),
    )
