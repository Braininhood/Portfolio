"""Exploit policy evaluation vs scripted opponents (Phase 8 exit criteria)."""

from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np

from poker_ai.core.profiles import PlayerProfile
from poker_ai.league.agents import CallStationPolicy, ManiacPolicy
from poker_ai.league.evaluator import _aivat_adjusted_delta
from poker_ai.league.sim import new_hu_hand, play_hand
from poker_ai.policy.base import Policy
from poker_ai.policy.exploit_policy import ExploitPolicy
from poker_ai.policy.heuristic import HeuristicPolicy


@dataclass(frozen=True, slots=True)
class ExploitEvalResult:
    opponent: str
    hands: int
    gto_aivat_bb100: float
    exploit_aivat_bb100: float
    delta_bb100: float
    baseline_name: str


def load_gto_baseline(*, use_best: bool = True) -> Policy:
    """Phase 7 router/student when artifacts exist; else heuristic fallback."""
    if not use_best:
        return HeuristicPolicy()
    try:
        from poker_ai.policy.distilled_policy import load_best_policy

        return load_best_policy()
    except Exception:
        return HeuristicPolicy()


def _villain_hints(name: str) -> tuple[float, float, float]:
    if name == "call_station":
        return (0.55, 0.08, 0.6)
    if name == "maniac":
        return (0.48, 0.38, 3.5)
    return (0.22, 0.19, 1.2)


def _archetype_style(name: str) -> np.ndarray:
    v = np.zeros(64, dtype=np.float32)
    if name == "call_station":
        v[:16] = 0.4
    elif name == "maniac":
        v[8:24] = 0.9
    else:
        v[16:24] = -0.5
        v[24:32] = 0.6
    return v


def _play_matchup(
    hero: Policy,
    villain: Policy,
    *,
    hands: int,
    seed: int,
    villain_uid: str,
    big_blind: int = 100,
    alternate_seats: bool = True,
) -> float:
    """AIVAT-adjusted BB/100 for hero vs villain (optional seat alternation)."""
    rng = random.Random(seed)
    hero_prof = PlayerProfile(profile_id="hero")
    vil_prof = PlayerProfile(profile_id=villain_uid)
    vil_style = _archetype_style(getattr(villain, "name", ""))
    zero = np.zeros(64, dtype=np.float32)

    adj_total = 0.0
    for i in range(hands):
        state = new_hu_hand(seed=seed + i)
        hero_seat = i % 2 if alternate_seats else 0
        if hero_seat == 0:
            policies = (hero, villain)
            profiles = (hero_prof, vil_prof)
            styles = ({villain_uid: vil_style}, {hero_prof.profile_id: zero})
        else:
            policies = (villain, hero)
            profiles = (vil_prof, hero_prof)
            styles = ({hero_prof.profile_id: zero}, {villain_uid: vil_style})
        result = play_hand(
            state,
            policies,
            profiles,
            rng,
            opponent_styles_by_seat=styles,
        )
        adj = _aivat_adjusted_delta(
            result.deltas[hero_seat],
            went_showdown=result.went_showdown,
            winner_seat=result.winner_seat,
            seat=hero_seat,
            big_blind=big_blind,
        )
        adj_total += adj
    return adj_total / max(1, hands) / max(1, big_blind) * 100.0


def evaluate_exploit_vs_gto(
    gto: Policy | None = None,
    *,
    hands_per_opponent: int = 300,
    seed: int = 42,
    use_best_baseline: bool = True,
    deviation_strength: float = 0.28,
    alternate_seats: bool = True,
) -> list[ExploitEvalResult]:
    """Compare GTO baseline vs ExploitPolicy vs TAG / station / maniac."""
    baseline = gto or load_gto_baseline(use_best=use_best_baseline)
    villains: list[tuple[str, Policy]] = [
        ("tag", HeuristicPolicy()),
        ("call_station", CallStationPolicy()),
        ("maniac", ManiacPolicy()),
    ]
    out: list[ExploitEvalResult] = []
    for label, vil in villains:
        uid = f"villain_{label}"
        hints = {uid: _villain_hints(getattr(vil, "name", label))}
        exploit = ExploitPolicy(
            baseline=baseline,
            classical_hints=hints,
            deviation_strength=deviation_strength,
        )
        gto_bb = _play_matchup(
            baseline,
            vil,
            hands=hands_per_opponent,
            seed=seed,
            villain_uid=uid,
            alternate_seats=alternate_seats,
        )
        exp_bb = _play_matchup(
            exploit,
            vil,
            hands=hands_per_opponent,
            seed=seed,
            villain_uid=uid,
            alternate_seats=alternate_seats,
        )
        out.append(
            ExploitEvalResult(
                opponent=label,
                hands=hands_per_opponent,
                gto_aivat_bb100=gto_bb,
                exploit_aivat_bb100=exp_bb,
                delta_bb100=exp_bb - gto_bb,
                baseline_name=baseline.name,
            )
        )
    return out
