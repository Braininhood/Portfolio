"""GET /replay/{hand_id} — action-by-action replay with policy overlays."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_db
from schemas import ActionProb, ReplayActionOverlay, ReplayResponse
from services.policy_service import get_policy, propose_with_timing
from state_codec import action_dist_to_probs

from poker_ai.core.engine import IllegalActionError, legal_actions
from poker_ai.core.profiles import PlayerProfile
from poker_ai.core.replay import replay_parsed_hand, state_after_actions
from poker_ai.equity.backfill import hero_street_equity_from_hand
from poker_ai.equity.live import hero_equity_from_state
from poker_ai.store.loader import load_parsed_hand_by_id

router = APIRouter(tags=["replay"])


def _build_replay(
    hand: object,
    *,
    overlay: bool,
    policy_name: str,
    hero_only_overlay: bool,
    include_equity: bool = True,
) -> ReplayResponse:
    from poker_ai.ingest.records import ParsedHand

    if not isinstance(hand, ParsedHand):
        msg = "invalid hand"
        raise TypeError(msg)

    try:
        result = replay_parsed_hand(hand)
        pot_ok = result.pot_trace_ok
        seq_ok = result.action_sequence_ok
    except ValueError:
        pot_ok = False
        seq_ok = False
    pol = get_policy(policy_name) if overlay else None
    profile = PlayerProfile(profile_id="replay", display_name="Replay")
    hero_pid = next((p.player_id for p in hand.players if p.is_hero), None)

    overlays: list[ReplayActionOverlay] = []
    for idx, pa in enumerate(hand.actions):
        overlay_probs: list[ActionProb] | None = None
        if pol is not None and (not hero_only_overlay or pa.player_id == hero_pid):
            try:
                state = state_after_actions(hand, idx, lenient=True)
                if not state.hand_over and legal_actions(state):
                    dist, _ = propose_with_timing(pol, state, profile)
                    raw = action_dist_to_probs(dist.actions, dist.probs)
                    overlay_probs = [
                        ActionProb(
                            kind=str(r["kind"]),
                            amount_chips=int(r["amount_chips"]),
                            seat=int(r["seat"]),
                            prob=float(r["prob"]),
                        )
                        for r in raw
                    ]
            except (IllegalActionError, ValueError):
                overlay_probs = None
        bb = hand.big_blind if hand.big_blind > 0 else 1.0
        amount_bb = round(pa.amount / bb, 1) if pa.amount else 0.0
        desc = f"{pa.position}: {pa.action_type}"
        if pa.amount > 0:
            desc += f" {amount_bb} BB"
        hero_eq: float | None = None
        if include_equity and pa.player_id == hero_pid:
            hero_eq = hero_street_equity_from_hand(hand, street=pa.street)
            if hero_eq is None and pol is not None:
                try:
                    st = state_after_actions(hand, idx, lenient=True)
                    hero_eq = hero_equity_from_state(st)
                except (IllegalActionError, ValueError):
                    hero_eq = None
        overlays.append(
            ReplayActionOverlay(
                index=idx,
                street=pa.street,
                position=pa.position,
                action_type=pa.action_type,
                amount=pa.amount,
                amount_bb=amount_bb,
                description=desc,
                overlay=overlay_probs,
                hero_equity=round(hero_eq, 4) if hero_eq is not None else None,
            )
        )

    hero = hand.hero_cards or "unknown"
    board = hand.board_cards or "(no board shown)"
    summary = (
        f"You (hero) were in {hand.hero_position or '?'} with {hero}. "
        f"Final board: {board}. {len(hand.actions)} betting actions recorded."
    )

    overlay_steps = sum(1 for o in overlays if o.overlay)
    return ReplayResponse(
        hand_id=hand.hand_id,
        num_actions=len(hand.actions),
        pot_trace_ok=pot_ok,
        action_sequence_ok=seq_ok,
        hero_position=hand.hero_position,
        hero_cards=hand.hero_cards,
        board_cards=hand.board_cards,
        stakes=hand.stakes,
        big_blind=hand.big_blind,
        num_players=hand.num_players,
        actions=overlays,
        summary=summary,
        overlay_enabled=overlay,
        overlay_steps=overlay_steps,
    )


@router.get("/replay/{hand_id}", response_model=ReplayResponse)
async def replay_hand(
    hand_id: int,
    session: AsyncSession = Depends(get_db),
    overlay: bool = Query(
        default=False,
        description="Attach AI frequencies (slow — runs model per decision).",
    ),
    policy: str = Query(default="heuristic"),
    hero_only_overlay: bool = Query(
        default=True,
        description="When overlay=true, only score hero decision points.",
    ),
    include_equity: bool = Query(
        default=True,
        description="Attach hero equity on hero actions (DB backfill or live MC).",
    ),
) -> ReplayResponse:
    hand = await load_parsed_hand_by_id(session, hand_id)
    if hand is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Hand #{hand_id} is not in your database. "
                "Pick a hand from the list on the left."
            ),
        )

    if overlay:
        return await asyncio.to_thread(
            _build_replay,
            hand,
            overlay=True,
            policy_name=policy,
            hero_only_overlay=hero_only_overlay,
            include_equity=include_equity,
        )
    return _build_replay(
        hand,
        overlay=False,
        policy_name=policy,
        hero_only_overlay=hero_only_overlay,
        include_equity=include_equity,
    )
