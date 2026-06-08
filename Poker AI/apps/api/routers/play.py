"""Play vs AI — REST + WebSocket (Phase W7)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_db
from schemas import (
    PlayBotsResponse,
    PlayHandDetail,
    PlayHandSummary,
    PlaySessionConfigRequest,
    PlaySessionCreateResponse,
    PlaySessionDetailResponse,
    PlaySessionEndResponse,
    PlaySessionListResponse,
    PlaySessionResumeResponse,
    PlaySessionSummary,
    PlayStudyCatalogResponse,
    PlayStudyExportResponse,
    PlayStudyHandsResponse,
    PlayStudyPrepareResponse,
    PlayStudyTrainJobInfo,
    PlayStudyTrainResponse,
    PlayStudyStatusResponse,
)
from services.play_coaching import session_summary_payload
from services.play_study_service import get_play_study_status
from services.play_session import (
    PlaySessionConfig,
    create_session,
    get_or_restore_session,
    get_session,
    list_play_bots,
    remove_session,
)

from poker_ai.store import jobs_store
from poker_ai.store.play_sessions_store import (
    count_play_hands,
    fetch_play_session,
    insert_play_hand,
    insert_play_session,
    list_active_play_sessions,
    list_all_play_sessions,
    list_all_study_hands,
    list_play_hands,
    list_play_hands_asc,
    save_session_snapshot,
    update_play_session_stats,
    utc_now,
)

from services.job_gate import JobConflictError, assert_no_active_job
from services.job_runner import run_job_async

router = APIRouter(tags=["play"])


def _config_from_request(body: PlaySessionConfigRequest) -> PlaySessionConfig:
    return PlaySessionConfig(
        seats=body.seats,
        user_seat=body.user_seat,
        bots=list(body.bots),
        buy_in_bb=body.buy_in_bb,
        small_blind_bb=body.small_blind_bb,
        big_blind_bb=body.big_blind_bb,
        ante_bb=body.ante_bb,
        timeout_ms=body.timeout_ms,
    )


def _session_summary(row: dict[str, Any]) -> PlaySessionSummary:
    config_raw = row.get("table_config_json")
    config: dict[str, Any] = {}
    if config_raw:
        try:
            config = json.loads(config_raw)
        except json.JSONDecodeError:
            config = {}
    hands = int(row.get("hands_played") or 0)
    vpip = int(row.get("vpip_count") or 0)
    pfr = int(row.get("pfr_count") or 0)
    decisions = int(row.get("total_decisions") or 0)
    denom = max(decisions, 1)
    return PlaySessionSummary(
        session_id=str(row["session_id"]),
        created_at=str(row.get("created_at") or ""),
        status=str(row.get("status") or "in_progress"),
        hands_played=hands,
        net_bb=float(row.get("net_bb") or 0.0),
        vpip_pct=round(100.0 * vpip / denom, 1),
        pfr_pct=round(100.0 * pfr / denom, 1),
        table_config=config,
    )


@router.get("/play/bots", response_model=PlayBotsResponse)
async def play_bots() -> PlayBotsResponse:
    from schemas import PlayBotInfo

    return PlayBotsResponse(bots=[PlayBotInfo(**b) for b in list_play_bots()])


@router.post("/play/sessions", response_model=PlaySessionCreateResponse)
async def create_play_session(
    body: PlaySessionConfigRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaySessionCreateResponse:
    config = _config_from_request(body)
    try:
        config.validate()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session = await create_session(config)
    await insert_play_session(
        db,
        session_id=session.session_id,
        table_config={
            "seats": config.seats,
            "user_seat": config.user_seat,
            "bots": config.bots,
            "buy_in_bb": config.buy_in_bb,
            "small_blind_bb": config.small_blind_bb,
            "big_blind_bb": config.big_blind_bb,
            "ante_bb": config.ante_bb,
            "timeout_ms": config.timeout_ms,
        },
    )
    await db.commit()
    await session.persist_to_db()
    return PlaySessionCreateResponse(session_id=session.session_id)


def _resume_from_snapshot(row: dict[str, Any]) -> dict[str, Any] | None:
    raw = row.get("state_snapshot_json")
    if not raw:
        return None
    try:
        snap = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except json.JSONDecodeError:
        return None
    engine = snap.get("engine") or {}
    return {
        "phase": snap.get("phase"),
        "hand_no": snap.get("hand_no"),
        "street": (engine.get("street") or "").lower() if engine else None,
        "updated_at": str(row.get("updated_at") or row.get("created_at") or ""),
    }


@router.get("/play/sessions/{session_id}/resume", response_model=PlaySessionResumeResponse)
async def get_session_resume_info(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaySessionResumeResponse:
    row = await fetch_play_session(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    hand_count = await count_play_hands(db, session_id)
    resume = _resume_from_snapshot(row)
    summary = _session_summary(row)
    from schemas import PlaySessionResumeInfo, PlayStudyExportHand, PlayStudySessionCatalogItem

    resume_info = PlaySessionResumeInfo(**resume) if resume else None
    return PlaySessionResumeResponse(
        session=summary,
        persisted_hands=hand_count,
        resume=resume_info,
        can_resume=str(row.get("status")) == "in_progress" and resume is not None,
    )


@router.get("/play/study/status", response_model=PlayStudyStatusResponse)
async def get_study_status() -> PlayStudyStatusResponse:
    """DB-backed training pool status — hands stay in ``play_hands``, not exported files."""
    return PlayStudyStatusResponse(**get_play_study_status())


@router.post("/play/study/prepare", response_model=PlayStudyPrepareResponse)
async def prepare_study_for_training(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlayStudyPrepareResponse:
    """Refresh training manifest from DB (no duplicate hand dump)."""
    import uuid

    from poker_ai.store.db import get_async_session_factory

    stats = get_play_study_status()
    if not stats.get("ready_for_training"):
        raise HTTPException(status_code=400, detail="No play hands in database yet — finish a session first.")

    try:
        await assert_no_active_job(db)
    except JobConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    job_id = uuid.uuid4().hex
    jobs_store.sync_insert_job(
        job_id=job_id,
        job_type="play_study_materialize",
        status="queued",
        params={"output": "artifacts/play_study"},
    )
    await db.commit()
    factory = get_async_session_factory()
    asyncio.create_task(
        run_job_async(job_id, "play_study_materialize", {"output": "artifacts/play_study"}, session_factory=factory)
    )
    return PlayStudyPrepareResponse(
        job_id=job_id,
        message="Updating training manifest from play_hands in DB — watch progress on Tasks.",
    )


@router.post("/play/study/train", response_model=PlayStudyTrainResponse)
async def train_from_play_study(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlayStudyTrainResponse:
    """Queue sequential HU + MW play-study training and router promotion."""
    import uuid

    from poker_ai.store.db import get_async_session_factory

    stats = get_play_study_status()
    if not stats.get("ready_for_training"):
        raise HTTPException(status_code=400, detail="No play hands in database yet — finish a session first.")

    hu_n = int(stats.get("hero_decisions_hu") or 0)
    mw_n = int(stats.get("hero_decisions_multiway") or 0)
    if hu_n < 1 and mw_n < 1:
        raise HTTPException(
            status_code=400,
            detail=(
                "No trainable play decisions yet. Need heads-up spots (2 in pot) or "
                "multi-way postflop spots (3+ in pot on flop+). Play more hands at /play."
            ),
        )

    try:
        await assert_no_active_job(db)
    except JobConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    job_id = uuid.uuid4().hex
    params = {
        "auto_promote": True,
        "hu_epochs": 30,
        "mw_epochs": 20,
        "batch_size": 128,
        "device": "auto",
    }
    jobs_store.sync_insert_job(
        job_id=job_id,
        job_type="play_auto_learn",
        status="queued",
        params=params,
    )
    factory = get_async_session_factory()
    await db.commit()
    asyncio.create_task(run_job_async(job_id, "play_auto_learn", params, session_factory=factory))

    queued = [
        PlayStudyTrainJobInfo(
            job_id=job_id,
            job_type="play_auto_learn",
            route="hu+multiway",
            output="artifacts/student/play_study_*",
            decision_count=hu_n + mw_n,
        )
    ]
    parts = []
    if hu_n:
        parts.append(f"{hu_n} HU")
    if mw_n:
        parts.append(f"{mw_n} multi-way postflop")
    manifest_path = stats.get("manifest_path") or "artifacts/play_study/manifest.json"
    return PlayStudyTrainResponse(
        job_id=job_id,
        message=f"Training from play sessions (sequential): {', '.join(parts)} — watch Tasks.",
        manifest_path=str(manifest_path),
        hero_decisions=hu_n + mw_n,
        hero_decisions_hu=hu_n,
        hero_decisions_multiway=mw_n,
        jobs=queued,
    )


@router.get("/play/study/catalog", response_model=PlayStudyCatalogResponse)
async def get_study_catalog(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlayStudyCatalogResponse:
    """Overview of all play sessions and persisted hand counts for AI study."""
    from schemas import PlayStudySessionCatalogItem

    rows = await list_all_play_sessions(db, limit=100, include_finished=True)
    sessions: list[dict[str, Any]] = []
    total_hands = 0
    for row in rows:
        sid = str(row["session_id"])
        n = await count_play_hands(db, sid)
        total_hands += n
        config: dict[str, Any] = {}
        raw = row.get("table_config_json")
        if raw:
            try:
                config = json.loads(raw) if isinstance(raw, str) else dict(raw)
            except json.JSONDecodeError:
                config = {}
        sessions.append(
            {
                "session_id": sid,
                "status": row.get("status"),
                "hands_played": int(row.get("hands_played") or 0),
                "persisted_hands": n,
                "net_bb": float(row.get("net_bb") or 0.0),
                "table_config": config,
                "updated_at": str(row.get("updated_at") or row.get("created_at") or ""),
            }
        )
    return PlayStudyCatalogResponse(
        sessions=[PlayStudySessionCatalogItem(**s) for s in sessions],
        total_sessions=len(sessions),
        total_persisted_hands=total_hands,
        note=(
            "Each completed hand stores full action_log, showdown, bot_lineup, and hero decisions "
            "in play_hands.summary_json. Use POST /play/study/prepare to register for NN training."
        ),
    )


@router.get("/play/study/export", response_model=PlayStudyExportResponse)
async def export_study_hands(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit_sessions: int = 50,
) -> PlayStudyExportResponse:
    """Optional JSON dump for inspection — primary store is ``play_hands`` in DB."""
    from schemas import PlayStudyExportHand

    rows = await list_all_study_hands(db, limit_sessions=limit_sessions)
    hands = [PlayStudyExportHand(**r) for r in rows]
    return PlayStudyExportResponse(hands=hands, count=len(hands))


@router.get("/play/sessions", response_model=PlaySessionListResponse)
async def list_play_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaySessionListResponse:
    rows = await list_active_play_sessions(db)
    return PlaySessionListResponse(sessions=[_session_summary(r) for r in rows])


def _parse_hand_summary(h: dict[str, Any]) -> PlayHandSummary:
    summary: dict[str, Any] = {}
    raw = h.get("summary_json")
    if raw:
        try:
            summary = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except json.JSONDecodeError:
            summary = {}
    record = summary.get("hand_record") or summary
    hero_hand = record.get("hero_hand") or {}
    winner = record.get("winner") or {}
    return PlayHandSummary(
        hand_no=int(h["hand_no"]),
        result_bb=float(h["result_bb"]),
        went_showdown=bool(h["went_showdown"]),
        board=h.get("board"),
        hero_cards=h.get("hero_cards"),
        hero_hand_name=hero_hand.get("name"),
        winner_name=winner.get("name"),
        all_in_count=int(record.get("all_in_count") or summary.get("all_in_count") or 0),
    )


def _parse_hand_detail(h: dict[str, Any]) -> PlayHandDetail:
    summary: dict[str, Any] = {}
    raw = h.get("summary_json")
    if raw:
        try:
            summary = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except json.JSONDecodeError:
            summary = {}
    record = summary.get("hand_record") or summary
    return PlayHandDetail(
        hand_no=int(h["hand_no"]),
        result_bb=float(h["result_bb"]),
        went_showdown=bool(h["went_showdown"]),
        board=h.get("board"),
        hero_cards=h.get("hero_cards"),
        hero_hand=record.get("hero_hand") or {},
        action_log=list(record.get("action_log") or []),
        showdown=list(record.get("showdown") or []),
        winner=record.get("winner"),
        all_in_count=int(record.get("all_in_count") or 0),
        bot_lineup=record.get("bot_lineup") or {},
        ending_street=record.get("ending_street"),
    )


@router.get("/play/sessions/{session_id}/study", response_model=PlayStudyHandsResponse)
async def get_study_hands(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlayStudyHandsResponse:
    """Full hand histories for AI study — action logs, showdowns, bot lineups."""
    row = await fetch_play_session(db, session_id)
    live = await get_session(session_id)
    if row is None and live is None:
        raise HTTPException(status_code=404, detail="Session not found")

    hands: list[PlayHandDetail] = []
    if live and live.completed_hands:
        for rec in live.completed_hands:
            hands.append(
                PlayHandDetail(
                    hand_no=int(rec["hand_no"]),
                    result_bb=float(rec["result_bb"]),
                    went_showdown=bool(rec.get("went_showdown")),
                    board=rec.get("board"),
                    hero_cards=rec.get("hero_cards"),
                    hero_hand=rec.get("hero_hand") or {},
                    action_log=list(rec.get("action_log") or []),
                    showdown=list(rec.get("showdown") or []),
                    winner=rec.get("winner"),
                    all_in_count=int(rec.get("all_in_count") or 0),
                    bot_lineup=rec.get("bot_lineup") or {},
                    ending_street=rec.get("ending_street"),
                )
            )
    else:
        hand_rows = await list_play_hands_asc(db, session_id)
        hands = [_parse_hand_detail(h) for h in hand_rows]

    return PlayStudyHandsResponse(
        session_id=session_id,
        hands=hands,
        note="Use these hands to compare bot styles, review all-in spots, and feed future student training.",
    )


@router.get("/play/sessions/{session_id}", response_model=PlaySessionDetailResponse)
async def get_play_session_detail(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaySessionDetailResponse:
    row = await fetch_play_session(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    hand_rows = await list_play_hands(db, session_id)
    hands = [_parse_hand_summary(h) for h in hand_rows]
    return PlaySessionDetailResponse(session=_session_summary(row), hands=hands)


@router.post("/play/sessions/{session_id}/end", response_model=PlaySessionEndResponse)
async def end_play_session(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaySessionEndResponse:
    row = await fetch_play_session(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    live = await get_session(session_id)
    sd_wins = 0
    sd_total = 0
    if live:
        for rec in live.completed_hands:
            if rec.get("went_showdown"):
                sd_total += 1
                if float(rec.get("result_bb") or 0) > 0:
                    sd_wins += 1
        summary = session_summary_payload(live, showdown_wins=sd_wins, showdown_hands=sd_total)
    else:
        summary = {
            "hands_played": int(row.get("hands_played") or 0),
            "net_bb": float(row.get("net_bb") or 0),
            "coaching_tips": ["Session ended."],
        }
    await update_play_session_stats(
        db,
        session_id,
        status="finished",
        finished_at=utc_now(),
    )
    await db.commit()
    await remove_session(session_id)
    return PlaySessionEndResponse(status="finished", summary=summary)


async def _persist_hand(
    db: AsyncSession,
    *,
    session: Any,
    hand_no: int,
    result_bb: float,
    went_showdown: bool,
    board: str | None,
    hero_cards: str | None,
    summary: dict[str, Any],
) -> None:
    table_config = {
        "seats": session.config.seats,
        "user_seat": session.config.user_seat,
        "bots": session.config.bots,
        "buy_in_bb": session.config.buy_in_bb,
        "small_blind_bb": session.config.small_blind_bb,
        "big_blind_bb": session.config.big_blind_bb,
        "ante_bb": session.config.ante_bb,
        "timeout_ms": session.config.timeout_ms,
        "seat_bot_ids": {str(k): v for k, v in session.seat_bot_ids.items()},
    }
    summary = {
        **summary,
        "table_config": table_config,
        "session_stats": session.session_stats(),
    }
    await insert_play_hand(
        db,
        session_id=session.session_id,
        hand_no=hand_no,
        result_bb=result_bb,
        went_showdown=went_showdown,
        board=board,
        hero_cards=hero_cards,
        summary=summary,
    )
    await update_play_session_stats(
        db,
        session.session_id,
        hands_played=session.hands_played,
        net_bb=session.net_bb,
        vpip_count=session.vpip_count,
        pfr_count=session.pfr_count,
        total_decisions=session.total_decisions,
    )
    await db.commit()
    from services.play_auto_learn import schedule_play_auto_learn

    await schedule_play_auto_learn()


@router.websocket("/ws/play/{session_id}")
async def play_websocket(ws: WebSocket, session_id: str) -> None:
    await ws.accept()

    from poker_ai.store.db import session_scope

    async with session_scope() as db:
        row = await fetch_play_session(db, session_id)
        hand_rows = await list_play_hands_asc(db, session_id) if row else []
        session = await get_or_restore_session(session_id, row=row, hand_rows=hand_rows)

    if session is None:
        await ws.send_json({"type": "error", "message": "Session not found or not resumable"})
        await ws.close()
        return

    session.mark_ws_connected()
    outbound = await session.outbound_messages()
    await session.ensure_loop()

    if session.engine_state is not None:
        await session._emit_session_sync()
        state = session.engine_state
        if (
            state.acting_seat == session.config.user_seat
            and not state.hand_over
            and not session._await_next_hand
        ):
            await session._send_your_turn()

    async def _forward_outbound() -> None:
        while True:
            msg = await outbound.get()
            try:
                await ws.send_json(msg)
            except WebSocketDisconnect:
                break
            except Exception:
                pass
            if msg.get("type") == "hand_complete":
                from poker_ai.store.db import session_scope

                record = msg.get("hand_record") or {}
                async with session_scope() as db:
                    await _persist_hand(
                        db,
                        session=session,
                        hand_no=int(msg["hand_no"]),
                        result_bb=float(msg["result_bb"]),
                        went_showdown=bool(msg.get("went_showdown")),
                        board=record.get("board"),
                        hero_cards=record.get("hero_cards"),
                        summary={"hand_record": record, "all_in_count": msg.get("all_in_count", 0)},
                    )

    forward_task = asyncio.create_task(_forward_outbound())
    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")
            if msg_type == "action":
                await session.apply_user_action(
                    str(data.get("action", "")),
                    data.get("amount"),
                )
            elif msg_type == "next_hand":
                await session.request_next_hand()
            elif msg_type == "hint_request":
                hint = await session.get_hint()
                if hint:
                    await ws.send_json({"type": "hint", **hint})
            elif msg_type == "end_session":
                await session.apply_user_action("__end_session__", None)
                break
    except WebSocketDisconnect:
        session.mark_ws_disconnected()
    except Exception:
        session.mark_ws_disconnected()
    finally:
        forward_task.cancel()
        try:
            await forward_task
        except asyncio.CancelledError:
            pass
