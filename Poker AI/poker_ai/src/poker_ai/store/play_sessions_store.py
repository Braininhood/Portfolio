"""Async CRUD for interactive play sessions (Phase W7)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def insert_play_session(
    session: AsyncSession,
    *,
    session_id: str,
    table_config: dict[str, Any],
) -> None:
    await session.execute(
        text(
            "INSERT INTO play_sessions (session_id, status, table_config_json) "
            "VALUES (:session_id, 'in_progress', :config_json)"
        ),
        {
            "session_id": session_id,
            "config_json": json.dumps(table_config, separators=(",", ":")),
        },
    )


async def fetch_play_session(session: AsyncSession, session_id: str) -> dict[str, Any] | None:
    row = (
        await session.execute(
            text(
                "SELECT session_id, created_at, status, table_config_json, hands_played, "
                "net_bb, vpip_count, pfr_count, total_decisions, finished_at, "
                "state_snapshot_json, updated_at "
                "FROM play_sessions WHERE session_id = :session_id"
            ),
            {"session_id": session_id},
        )
    ).mappings().first()
    return dict(row) if row else None


async def list_active_play_sessions(
    session: AsyncSession,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            text(
                "SELECT session_id, created_at, status, table_config_json, hands_played, "
                "net_bb, vpip_count, pfr_count, total_decisions, finished_at, "
                "state_snapshot_json, updated_at "
                "FROM play_sessions WHERE status = 'in_progress' AND finished_at IS NULL "
                "ORDER BY datetime(created_at) DESC LIMIT :lim"
            ),
            {"lim": limit},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def update_play_session_stats(
    session: AsyncSession,
    session_id: str,
    *,
    hands_played: int | None = None,
    net_bb: float | None = None,
    vpip_count: int | None = None,
    pfr_count: int | None = None,
    total_decisions: int | None = None,
    status: str | None = None,
    finished_at: datetime | None = None,
) -> None:
    parts: list[str] = []
    bind: dict[str, Any] = {"session_id": session_id}
    if hands_played is not None:
        parts.append("hands_played = :hands_played")
        bind["hands_played"] = hands_played
    if net_bb is not None:
        parts.append("net_bb = :net_bb")
        bind["net_bb"] = net_bb
    if vpip_count is not None:
        parts.append("vpip_count = :vpip_count")
        bind["vpip_count"] = vpip_count
    if pfr_count is not None:
        parts.append("pfr_count = :pfr_count")
        bind["pfr_count"] = pfr_count
    if total_decisions is not None:
        parts.append("total_decisions = :total_decisions")
        bind["total_decisions"] = total_decisions
    if status is not None:
        parts.append("status = :status")
        bind["status"] = status
    if finished_at is not None:
        parts.append("finished_at = :finished_at")
        bind["finished_at"] = finished_at
    if not parts:
        return
    sql = "UPDATE play_sessions SET " + ", ".join(parts) + " WHERE session_id = :session_id"
    await session.execute(text(sql), bind)


async def save_session_snapshot(
    session: AsyncSession,
    session_id: str,
    *,
    snapshot: dict[str, Any],
    hands_played: int | None = None,
    net_bb: float | None = None,
    vpip_count: int | None = None,
    pfr_count: int | None = None,
    total_decisions: int | None = None,
) -> None:
    parts = [
        "state_snapshot_json = :snapshot_json",
        "updated_at = :updated_at",
    ]
    bind: dict[str, Any] = {
        "session_id": session_id,
        "snapshot_json": json.dumps(snapshot, separators=(",", ":")),
        "updated_at": utc_now(),
    }
    if hands_played is not None:
        parts.append("hands_played = :hands_played")
        bind["hands_played"] = hands_played
    if net_bb is not None:
        parts.append("net_bb = :net_bb")
        bind["net_bb"] = net_bb
    if vpip_count is not None:
        parts.append("vpip_count = :vpip_count")
        bind["vpip_count"] = vpip_count
    if pfr_count is not None:
        parts.append("pfr_count = :pfr_count")
        bind["pfr_count"] = pfr_count
    if total_decisions is not None:
        parts.append("total_decisions = :total_decisions")
        bind["total_decisions"] = total_decisions
    sql = "UPDATE play_sessions SET " + ", ".join(parts) + " WHERE session_id = :session_id"
    await session.execute(text(sql), bind)


async def list_all_play_sessions(
    session: AsyncSession,
    *,
    limit: int = 100,
    include_finished: bool = True,
) -> list[dict[str, Any]]:
    where = "" if include_finished else "WHERE status = 'in_progress' AND finished_at IS NULL"
    rows = (
        await session.execute(
            text(
                f"SELECT session_id, created_at, status, table_config_json, hands_played, "
                f"net_bb, vpip_count, pfr_count, total_decisions, finished_at, updated_at "
                f"FROM play_sessions {where} "
                f"ORDER BY datetime(COALESCE(updated_at, created_at)) DESC LIMIT :lim"
            ),
            {"lim": limit},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def count_play_hands(session: AsyncSession, session_id: str) -> int:
    row = (
        await session.execute(
            text("SELECT COUNT(*) AS n FROM play_hands WHERE session_id = :session_id"),
            {"session_id": session_id},
        )
    ).mappings().first()
    return int(row["n"]) if row else 0


async def list_all_study_hands(
    session: AsyncSession,
    *,
    limit_sessions: int = 50,
    limit_hands_per_session: int = 500,
) -> list[dict[str, Any]]:
    """All persisted hands across sessions for NN / student training export."""
    sessions = await list_all_play_sessions(session, limit=limit_sessions, include_finished=True)
    out: list[dict[str, Any]] = []
    for srow in sessions:
        sid = str(srow["session_id"])
        config: dict[str, Any] = {}
        raw_cfg = srow.get("table_config_json")
        if raw_cfg:
            try:
                config = json.loads(raw_cfg) if isinstance(raw_cfg, str) else dict(raw_cfg)
            except json.JSONDecodeError:
                config = {}
        hands = await list_play_hands_asc(session, sid, limit=limit_hands_per_session)
        for h in hands:
            summary: dict[str, Any] = {}
            raw_sum = h.get("summary_json")
            if raw_sum:
                try:
                    summary = json.loads(raw_sum) if isinstance(raw_sum, str) else dict(raw_sum)
                except json.JSONDecodeError:
                    summary = {}
            record = summary.get("hand_record") or summary
            out.append(
                {
                    "session_id": sid,
                    "session_status": srow.get("status"),
                    "table_config": config,
                    "hand_no": int(h["hand_no"]),
                    "result_bb": float(h["result_bb"]),
                    "went_showdown": bool(h["went_showdown"]),
                    "board": h.get("board"),
                    "hero_cards": h.get("hero_cards"),
                    "hand_record": record,
                }
            )
    return out


async def insert_play_hand(
    session: AsyncSession,
    *,
    session_id: str,
    hand_no: int,
    result_bb: float,
    went_showdown: bool,
    board: str | None,
    hero_cards: str | None,
    summary: dict[str, Any],
) -> None:
    await session.execute(
        text(
            "INSERT INTO play_hands "
            "(session_id, hand_no, result_bb, went_showdown, board, hero_cards, summary_json) "
            "VALUES (:session_id, :hand_no, :result_bb, :went_showdown, :board, :hero_cards, :summary_json)"
        ),
        {
            "session_id": session_id,
            "hand_no": hand_no,
            "result_bb": result_bb,
            "went_showdown": went_showdown,
            "board": board,
            "hero_cards": hero_cards,
            "summary_json": json.dumps(summary, separators=(",", ":")),
        },
    )


async def list_play_hands(
    session: AsyncSession,
    session_id: str,
    *,
    limit: int = 100,
) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            text(
                "SELECT id, session_id, hand_no, result_bb, went_showdown, board, hero_cards, summary_json "
                "FROM play_hands WHERE session_id = :session_id "
                "ORDER BY hand_no DESC LIMIT :lim"
            ),
            {"session_id": session_id, "lim": limit},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def fetch_play_hand(
    session: AsyncSession,
    session_id: str,
    hand_no: int,
) -> dict[str, Any] | None:
    row = (
        await session.execute(
            text(
                "SELECT id, session_id, hand_no, result_bb, went_showdown, board, hero_cards, summary_json "
                "FROM play_hands WHERE session_id = :session_id AND hand_no = :hand_no"
            ),
            {"session_id": session_id, "hand_no": hand_no},
        )
    ).mappings().first()
    return dict(row) if row else None


async def list_play_hands_asc(
    session: AsyncSession,
    session_id: str,
    *,
    limit: int = 500,
) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            text(
                "SELECT id, session_id, hand_no, result_bb, went_showdown, board, hero_cards, summary_json "
                "FROM play_hands WHERE session_id = :session_id "
                "ORDER BY hand_no ASC LIMIT :lim"
            ),
            {"session_id": session_id, "lim": limit},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
