"""Player profiles from the canonical store + style encoder."""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from deps import cached_settings, get_db
from schemas import (
    ChangepointBrief,
    NeighbourRow,
    PlayerCausalResponse,
    PlayerListResponse,
    PlayerProfileResponse,
    PlayerRangeResponse,
    PlayerSummaryRow,
    RangeBucketRow,
    StyleStatsRow,
    CounterfactualExampleSchema,
    LeakRowSchema,
)

from poker_ai.opponents.profile import profile_for_player
from poker_ai.store.loader import list_player_summaries, load_hands_for_player

router = APIRouter(prefix="/players", tags=["players"])


def _player_type(vpip: float, pfr: float, af: float) -> str:
    """Classify a player's style from their observed VPIP / PFR / aggression factor.

    Thresholds are calibrated against live NLH population data:
      TAG:   VPIP 15-25%, PFR 12-20%, AF 2-4  — selective preflop, bets strong hands
      LAG:   VPIP 25-40%, PFR 18-30%, AF 2.5+ — wide range, applies constant pressure
      Nit:   VPIP <18%, PFR <14%              — rock-solid, folds almost everything
      Fish:  VPIP 40%+, PFR <12%             — calls everything, almost never folds
      Maniac: VPIP 40%+, AF 4+               — wide range + hyper-aggressive betting
    """
    if vpip > 0.40 and af > 4.0:
        return "Maniac"                       # wide + hyper-aggressive
    if vpip > 0.40 and pfr < 0.12:
        return "Fish (Loose-Passive)"         # calling station, almost never raises
    if vpip > 0.32 and af > 2.5:
        return "LAG (Loose-Aggressive)"       # wide range + consistent pressure
    if vpip < 0.18 and pfr < 0.14:
        return "Nit (Rock)"                   # barely enters pots, passive when in
    if vpip < 0.26:
        return "TAG (Tight-Aggressive)"       # selective preflop, bets strong holdings
    if af > 3.0:
        return "Aggro Reg"                    # moderate range but high aggression
    return "Balanced Reg"                     # solid all-around player


def _changepoint_brief(player_uid: str) -> ChangepointBrief | None:
    from poker_ai.learn.changepoint import changepoint_for_player

    cp = changepoint_for_player(player_uid)
    if cp is None:
        return None
    return ChangepointBrief(
        detected_at=cp.detected_at,
        description=cp.description,
        confidence=cp.confidence,
    )


def _stats_summary(vpip: float, pfr: float, af: float, hands: int) -> str:
    kind = _player_type(vpip, pfr, af)
    return (
        f"Over {hands} hands in your database, this player looks **{kind.lower()}**: "
        f"plays about **{vpip * 100:.0f}%** of pots (VPIP), raises preflop **{pfr * 100:.0f}%** "
        f"of the time (PFR), aggression factor **{af:.1f}**."
    )


@router.get("", response_model=PlayerListResponse)
async def list_players(
    session: AsyncSession = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    include_play: Annotated[bool, Query(description="Include Play vs AI bot stats")] = True,
) -> PlayerListResponse:
    rows = await list_player_summaries(session, limit=limit)
    players = [
        PlayerSummaryRow(
            player_uid=r.player_uid,
            display_name=r.screen_name or f"Player {r.player_uid[:8]}…",
            hands=r.hands,
            source="import",
        )
        for r in rows
    ]
    if include_play:
        from poker_ai.learn.play_study_loader import collect_play_opponent_stats

        for opp in collect_play_opponent_stats()[:limit]:
            players.append(
                PlayerSummaryRow(
                    player_uid=str(opp["player_uid"]),
                    display_name=str(opp["display_name"]),
                    hands=int(opp.get("decisions") or 0),
                    source="play",
                )
            )
    hint = None
    if len([p for p in players if p.source == "import"]) < 10:
        hint = (
            "Few imported opponents — add hand histories from more sites/stakes on Import. "
            "Play vs AI bots appear here after sessions on /play."
        )
    return PlayerListResponse(total=len(players), players=players, hint=hint)


@router.get("/{player_uid}/profile", response_model=PlayerProfileResponse)
async def get_player_profile(
    player_uid: str,
    session: AsyncSession = Depends(get_db),
    max_hands: Annotated[int, Query(ge=10, le=2000)] = 300,
) -> PlayerProfileResponse:
    settings = cached_settings()
    if player_uid.startswith("play_bot:"):
        from poker_ai.learn.play_study_loader import collect_play_opponent_stats

        for opp in collect_play_opponent_stats():
            if opp["player_uid"] == player_uid:
                vpip = float(opp.get("vpip_pct") or 0) / 100.0
                pfr = float(opp.get("pfr_pct") or 0) / 100.0
                af = float(opp.get("aggression_factor") or 0)
                hands_n = int(opp.get("decisions") or 0)
                return PlayerProfileResponse(
                    player_uid=player_uid,
                    display_name=str(opp["display_name"]),
                    hands_in_sample=hands_n,
                    summary=_stats_summary(vpip, pfr, af, hands_n),
                    player_type=_player_type(vpip, pfr, af),
                    stats=StyleStatsRow(
                        vpip_pct=float(opp.get("vpip_pct") or 0),
                        pfr_pct=float(opp.get("pfr_pct") or 0),
                        aggression_factor=af,
                        hands_dealt=hands_n,
                    ),
                    similar_players=[],
                    changepoint=_changepoint_brief(player_uid),
                )
        raise HTTPException(status_code=404, detail="Play bot not found — play more hands at /play")

    hands = await load_hands_for_player(session, player_uid, max_hands=max_hands)
    if not hands:
        raise HTTPException(status_code=404, detail="No hands found for this player")

    art = settings.style_encoder_artifact_dir

    def _build() -> PlayerProfileResponse | None:
        profile = profile_for_player(
            player_uid,
            hands,
            artifact_dir=art,
            device="cpu",
        )
        if profile is None:
            return None
        c = profile.classical
        vpip, pfr, af = c.vpip, c.pfr, c.aggression_factor
        screen = next(
            (p.screen_name for h in hands for p in h.players if p.player_uid == player_uid and p.screen_name),
            None,
        )
        return PlayerProfileResponse(
            player_uid=player_uid,
            display_name=screen or f"Player {player_uid[:8]}…",
            hands_in_sample=c.hands_dealt,
            summary=_stats_summary(vpip, pfr, af, c.hands_dealt),
            player_type=_player_type(vpip, pfr, af),
            stats=StyleStatsRow(
                vpip_pct=round(vpip * 100, 1),
                pfr_pct=round(pfr * 100, 1),
                aggression_factor=round(af, 2),
                hands_dealt=c.hands_dealt,
            ),
            similar_players=[
                NeighbourRow(
                    player_uid=n.player_uid,
                    display_name=f"Player {n.player_uid[:8]}…",
                    similarity_pct=round(n.similarity * 100, 1),
                    example_hand_id=n.hand_id,
                )
                for n in profile.neighbours
            ],
            changepoint=_changepoint_brief(player_uid),
        )

    try:
        result = await asyncio.to_thread(_build)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Style encoder not trained — run: poker_ai train style",
        ) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Could not build profile")
    return result


@router.get("/{player_uid}/range", response_model=PlayerRangeResponse)
async def get_player_range(
    player_uid: str,
    session: AsyncSession = Depends(get_db),
    max_hands: Annotated[int, Query(ge=10, le=2000)] = 500,
) -> PlayerRangeResponse:
    if player_uid.startswith("play_bot:"):
        raise HTTPException(
            status_code=400,
            detail="Range inference requires imported hand history (not Play vs AI bots).",
        )
    hands = await load_hands_for_player(session, player_uid, max_hands=max_hands)
    if not hands:
        raise HTTPException(status_code=404, detail="No hands found for this player")

    def _build() -> PlayerRangeResponse:
        from poker_ai.opponents.range_inference import infer_range_from_hands

        result = infer_range_from_hands(player_uid, hands)
        return PlayerRangeResponse(
            player_uid=result.player_uid,
            observed_actions=result.observed_actions,
            buckets=[
                RangeBucketRow(tier=b.tier, label=b.label, mass_pct=b.mass_pct)
                for b in result.buckets
            ],
            confidence_label=result.confidence_label,
            confidence_pct=result.confidence_pct,
            last_updated_at=result.last_updated_at,
            last_hand_id=result.last_hand_id,
            note=result.note,
        )

    return await asyncio.to_thread(_build)


@router.get("/{player_uid}/causal", response_model=PlayerCausalResponse)
async def get_player_causal(
    player_uid: str,
    session: AsyncSession = Depends(get_db),
    max_hands: Annotated[int, Query(ge=10, le=2000)] = 500,
) -> PlayerCausalResponse:
    if player_uid.startswith("play_bot:"):
        raise HTTPException(
            status_code=400,
            detail="Causal evaluation requires imported hand history.",
        )
    hands = await load_hands_for_player(session, player_uid, max_hands=max_hands)
    if not hands:
        raise HTTPException(status_code=404, detail="No hands found for this player")

    def _build() -> PlayerCausalResponse:
        from poker_ai.opponents.causal_eval import evaluate_causal_leaks

        result = evaluate_causal_leaks(player_uid, hands)
        cf = result.counterfactual
        return PlayerCausalResponse(
            player_uid=result.player_uid,
            hands_analyzed=result.hands_analyzed,
            counterfactual=(
                CounterfactualExampleSchema(
                    hand_id=cf.hand_id,
                    street=cf.street,
                    actual_action=cf.actual_action,
                    counterfactual_action=cf.counterfactual_action,
                    ev_delta_bb=cf.ev_delta_bb,
                    narrative=cf.narrative,
                )
                if cf
                else None
            ),
            leaks=[
                LeakRowSchema(
                    rank=r.rank,
                    title=r.title,
                    bb_per_100=r.bb_per_100,
                    description=r.description,
                )
                for r in result.leaks
            ],
            total_leak_bb_per_100=result.total_leak_bb_per_100,
            note=result.note,
        )

    return await asyncio.to_thread(_build)
