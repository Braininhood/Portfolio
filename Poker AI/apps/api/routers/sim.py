"""WebSocket /ws/sim — live league-style hand stream (local only)."""

from __future__ import annotations

import asyncio
import json
import random
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from poker_ai.core.profiles import PlayerProfile
from poker_ai.league.agents.registry import build_default_roster
from poker_ai.league.sim import new_table_hand, play_hand
from poker_ai.policy.base import Policy
from services.sim_bench import measure_sim_throughput
from services.sim_detail import build_sim_hand_detail

router = APIRouter(tags=["sim"])

# ~100 hands/min → one hand every 0.6s (override via query `interval=`)
_HAND_INTERVAL_SEC = 0.6
_MIX_TABLE_SIZES = (2, 6, 9)

_AGENT_LABELS: dict[str, str] = {
    "main_agent": "Main AI",
    "distilled_gto": "GTO Baseline",
    "main_exploiter": "Exploiter AI",
    "league_exploiter": "League Exploiter",
    # Standard poker archetypes — correct lexicon
    "tag": "TAG (Tight-Aggressive)",       # VPIP ~15-22%, bets strong hands
    "lag": "LAG (Loose-Aggressive)",       # VPIP ~25-35%, wide range + pressure
    "nit": "Nit (Rock)",                   # VPIP <14%, folds almost everything
    "rock": "Rock",                        # alias for nit
    "fish": "Fish (Loose-Passive)",        # VPIP 40%+, almost never folds, rarely raises
    "call_station": "Calling Station",     # similar to fish but slightly less extreme
    "maniac": "Maniac (Ultra-Aggressive)", # raises constantly regardless of hand strength
    "passive_reg": "Weak-Tight Reg",       # plays few pots, minimal postflop pressure
    "random": "Random",
}


def _friendly_agent(agent_id: str) -> str:
    return _AGENT_LABELS.get(agent_id, agent_id.replace("_", " ").title())


def _seat_player_name(seat: int, *, agent_a: str, agent_b: str) -> str:
    if seat == 0:
        return _friendly_agent(agent_a)
    if seat == 1:
        return _friendly_agent(agent_b)
    return f"{_friendly_agent(agent_a)} (seat {seat + 1})"


def _table_label(num_seats: int) -> str:
    if num_seats == 2:
        return "Heads-up (2 players)"
    if num_seats <= 6:
        return f"{num_seats}-player table"
    return f"{num_seats}-max table"


def _hand_summary(
    *,
    hand_no: int,
    num_seats: int,
    deltas: list[int],
    winner_seat: int | None,
    went_showdown: bool,
    agent_a: str,
    agent_b: str,
    big_blind_chips: int,
) -> dict[str, str | float | int | None]:
    """Plain-language fields for the dashboard (non-technical users)."""
    bb = max(big_blind_chips, 1)
    table = _table_label(num_seats)
    if winner_seat is None or winner_seat < 0 or winner_seat >= len(deltas):
        return {
            "summary": f"Hand {hand_no} finished on a {table}.",
            "winner_label": None,
            "result_bb": 0.0,
            "ending": "complete",
        }
    win_chips = deltas[winner_seat]
    win_bb = round(win_chips / bb, 1)
    winner = _seat_player_name(winner_seat, agent_a=agent_a, agent_b=agent_b)
    if win_bb > 0:
        result_phrase = f"won about +{win_bb:g} BB"
    elif win_bb < 0:
        result_phrase = f"lost about {win_bb:g} BB"
    else:
        result_phrase = "broke even"
    if went_showdown:
        ending = "after a showdown"
    else:
        ending = "when everyone else folded"
    summary = f"Hand {hand_no}: {winner} {result_phrase} on a {table}, {ending}."
    return {
        "summary": summary,
        "winner_label": winner,
        "result_bb": win_bb,
        "ending": ending,
    }


def _policy_for_agent(agent_id: str) -> Policy:
    roster = {a.agent_id: a.policy for a in build_default_roster()}
    return roster.get(agent_id) or roster["main_agent"]


@router.get("/sim/throughput")
def sim_throughput(
    wall_sec: float = 60.0,
    min_hands_per_minute: float = 100.0,
) -> dict[str, object]:
    """Measure raw league sim hand rate (Phase 10 exit gate; no WS pacing delay)."""
    stats = measure_sim_throughput(wall_sec=min(wall_sec, 120.0))
    stats["min_hands_per_minute"] = min_hands_per_minute
    stats["passed"] = float(stats["hands_per_minute"]) >= min_hands_per_minute
    return stats


@router.websocket("/ws/sim")
async def sim_stream(ws: WebSocket) -> None:
    await ws.accept()
    seats_param = ws.query_params.get("seats", "6").strip().lower()
    mix_tables = seats_param in ("mix", "mixed", "rotate")
    fixed_seats = 6
    if not mix_tables:
        try:
            fixed_seats = int(seats_param)
        except ValueError:
            fixed_seats = 6
    agent_a = ws.query_params.get("agent_a", "main_agent")
    agent_b = ws.query_params.get("agent_b", "distilled_gto")
    interval_raw = ws.query_params.get("interval", str(_HAND_INTERVAL_SEC)).strip()
    try:
        hand_interval = max(0.0, float(interval_raw))
    except ValueError:
        hand_interval = _HAND_INTERVAL_SEC
    rng = random.Random(42)
    hand_no = 0
    try:
        while True:
            num_seats = (
                _MIX_TABLE_SIZES[hand_no % len(_MIX_TABLE_SIZES)] if mix_tables else fixed_seats
            )
            seed = rng.randint(0, 2**31 - 1)
            pol_a = _policy_for_agent(agent_a)
            pol_b = _policy_for_agent(agent_b)
            policies: list[Policy] = [pol_a] * num_seats
            policies[1] = pol_b
            profiles = [PlayerProfile(profile_id=f"p{i}") for i in range(num_seats)]
            seat_names = [
                _seat_player_name(i, agent_a=agent_a, agent_b=agent_b) for i in range(num_seats)
            ]

            def _play_one() -> dict[str, Any]:
                state = new_table_hand(num_seats=num_seats, seed=seed)
                result = play_hand(
                    state,
                    policies,
                    profiles,
                    rng,
                    record_timeline=True,
                )
                deltas = list(result.deltas)
                plain = _hand_summary(
                    hand_no=hand_no + 1,
                    num_seats=num_seats,
                    deltas=deltas,
                    winner_seat=result.winner_seat,
                    went_showdown=result.went_showdown,
                    agent_a=agent_a,
                    agent_b=agent_b,
                    big_blind_chips=state.big_blind,
                )
                seat_note = (
                    f"{_friendly_agent(agent_a)} fills seats 1, 3–{num_seats}; "
                    f"{_friendly_agent(agent_b)} is seat 2."
                    if num_seats > 2
                    else f"{_friendly_agent(agent_a)} (seat 1) vs {_friendly_agent(agent_b)} (seat 2)."
                )
                detail = build_sim_hand_detail(
                    state,
                    result,
                    seat_names=seat_names,
                    agent_a=agent_a,
                    agent_b=agent_b,
                )
                return {
                    "num_seats": num_seats,
                    "table_label": _table_label(num_seats),
                    "matchup": f"{_friendly_agent(agent_a)} vs {_friendly_agent(agent_b)}",
                    "table_explanation": seat_note,
                    "mixed_table": mix_tables,
                    "deltas": deltas,
                    "went_showdown": result.went_showdown,
                    "winner_seat": result.winner_seat,
                    **plain,
                    "detail": detail,
                    "seed": seed,
                }

            payload = await asyncio.to_thread(_play_one)
            hand_no += 1
            payload["hand_no"] = hand_no
            await ws.send_text(json.dumps({"event": "hand_complete", "payload": payload}))
            if hand_interval > 0:
                await asyncio.sleep(hand_interval)
    except WebSocketDisconnect:
        return
    except Exception:
        await ws.close()
        return
