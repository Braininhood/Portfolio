"""Rule-based coaching tips for play sessions (W7 Day 26)."""

from __future__ import annotations

from typing import Any


def _bot_display_name(bot_id: str) -> str:
    labels = {
        "main_agent": "Main AI",
        "distilled_gto": "GTO Bot",
        "main_exploiter": "Maniac",
        "cfr_stacked": "CFR Stacked",
        "tag": "TAG Bot",
        "lag": "LAG Bot",
        "nit": "Nit",
        "rock": "Rock",
        "fish": "Calling Fish",
        "call_station": "Calling Station",
        "passive_reg": "Passive Reg",
        "random": "Random Bot",
        "league_exploiter": "League Exploiter",
    }
    return labels.get(bot_id, bot_id.replace("_", " ").title())


def aggregate_opponent_bb(completed_hands: list[dict[str, Any]]) -> dict[str, float]:
    """Sum hero net BB won from each bot type across completed hands."""
    agg: dict[str, float] = {}
    for rec in completed_hands:
        for bot_id, bb in (rec.get("opponent_bb") or {}).items():
            if not bot_id:
                continue
            agg[str(bot_id)] = agg.get(str(bot_id), 0.0) + float(bb)
    return agg


def opponent_results_payload(completed_hands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    agg = aggregate_opponent_bb(completed_hands)
    return [
        {
            "bot_id": bot_id,
            "name": _bot_display_name(bot_id),
            "net_bb": round(net, 1),
            "beaten": net >= 0,
        }
        for bot_id, net in sorted(agg.items(), key=lambda x: (-x[1], x[0]))
    ]


def coaching_tips(
    *,
    hands: int,
    net_bb: float,
    vpip_pct: float,
    pfr_pct: float,
    opponent_results: dict[str, float] | None = None,
    showdown_win_pct: float | None = None,
) -> list[str]:
    tips: list[str] = []
    if hands < 3:
        return ["Play a few more hands for meaningful stats."]

    if vpip_pct > 55:
        tips.append(
            "You're playing too many hands preflop. Try folding weak hands like 72o and J4o.",
        )
    if vpip_pct > 10 and pfr_pct / max(vpip_pct, 1) < 0.4:
        tips.append("You call too often. Raise more with your good hands to build the pot.")
    if net_bb < -20 and hands >= 8:
        tips.append("Session is running negative — tighten up and avoid marginal calls.")
    if opponent_results:
        for bot_id, bb in opponent_results.items():
            if bot_id in ("distilled_gto", "main_agent", "cfr_stacked") and bb < -10 and hands >= 10:
                tips.append("The GTO Bot is tough — practice against easier bots first.")
                break
    if showdown_win_pct is not None and hands >= 5 and showdown_win_pct < 40:
        tips.append("You're showing down too many losing hands. Consider folding earlier.")
    if not tips:
        if net_bb >= 0:
            tips.append("Solid session — keep applying pressure with strong hands.")
        else:
            tips.append("Review the Study tabs for spots where you overcommitted chips.")
    return tips


def session_summary_payload(
    session: Any,
    *,
    showdown_wins: int = 0,
    showdown_hands: int = 0,
) -> dict[str, Any]:
    stats = session.session_stats()
    hands = int(stats["hands"])
    vpip = float(stats["vpip_pct"])
    pfr = float(stats["pfr_pct"])
    net = float(stats["net_bb"])
    sd_pct = round(100.0 * showdown_wins / max(showdown_hands, 1), 1) if showdown_hands else None
    bb_per_100 = round(net / max(hands, 1) * 100, 1)

    completed = getattr(session, "completed_hands", [])
    opp_agg = aggregate_opponent_bb(completed)
    opponent_results = opponent_results_payload(completed)

    tips = coaching_tips(
        hands=hands,
        net_bb=net,
        vpip_pct=vpip,
        pfr_pct=pfr,
        opponent_results=opp_agg,
        showdown_win_pct=sd_pct,
    )

    return {
        "hands_played": hands,
        "net_bb": net,
        "bb_per_100": bb_per_100,
        "vpip_pct": vpip,
        "pfr_pct": pfr,
        "af": round(pfr / max(vpip - pfr, 1), 1) if vpip > pfr else round(pfr / max(vpip, 1), 1),
        "showdown_win_pct": sd_pct,
        "coaching_tips": tips,
        "opponent_results": opponent_results,
        "table_config": {
            "seats": session.config.seats,
            "buy_in_bb": session.config.buy_in_bb,
            "ante_bb": session.config.ante_bb,
            "small_blind_bb": session.config.small_blind_bb,
            "big_blind_bb": session.config.big_blind_bb,
        },
    }
