"""Canonical hand-anchored VPIP / PFR / AF (Phase 8 — see doc/POKER_METRICS_GLOSSARY.md)."""

from __future__ import annotations

from dataclasses import dataclass

from poker_ai.ingest.records import ParsedAction, ParsedHand


@dataclass(frozen=True, slots=True)
class ClassicalStats:
    """Population stats for one ``player_uid`` over a hand sample."""

    hands_dealt: int
    vpip: float
    pfr: float
    aggression_factor: float
    hands_with_voluntary_preflop: int
    hands_with_preflop_raise: int
    postflop_bets_raises: int
    postflop_calls: int


def _voluntary_preflop(act: ParsedAction) -> bool:
    return act.street == "Preflop" and act.action_type in ("Call", "Raise")


def _preflop_raise(act: ParsedAction) -> bool:
    return act.street == "Preflop" and act.action_type == "Raise"


def compute_classical_stats(
    player_uid: str,
    hands: list[ParsedHand],
) -> ClassicalStats:
    """Hand-anchored VPIP / PFR / AF for one player across parsed hands."""
    hands_dealt = 0
    vpip_hands = 0
    pfr_hands = 0
    bets_raises = 0
    calls = 0

    for hand in hands:
        pid = next((p.player_id for p in hand.players if p.player_uid == player_uid), None)
        if pid is None:
            continue
        hands_dealt += 1
        player_acts = [a for a in hand.actions if a.player_id == pid]
        if any(_voluntary_preflop(a) for a in player_acts):
            vpip_hands += 1
        if any(_preflop_raise(a) for a in player_acts):
            pfr_hands += 1
        for a in player_acts:
            if a.street == "Preflop":
                continue
            if a.action_type in ("Bet", "Raise"):
                bets_raises += 1
            elif a.action_type == "Call":
                calls += 1

    vpip = vpip_hands / hands_dealt if hands_dealt else 0.0
    pfr = pfr_hands / hands_dealt if hands_dealt else 0.0
    af = bets_raises / calls if calls > 0 else float(bets_raises)

    return ClassicalStats(
        hands_dealt=hands_dealt,
        vpip=vpip,
        pfr=pfr,
        aggression_factor=af,
        hands_with_voluntary_preflop=vpip_hands,
        hands_with_preflop_raise=pfr_hands,
        postflop_bets_raises=bets_raises,
        postflop_calls=calls,
    )
