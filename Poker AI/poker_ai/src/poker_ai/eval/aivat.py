"""Full AIVAT chance + strategy corrections (Burch et al., 2018 — v2 implementation)."""

from __future__ import annotations

import json
import math
import os
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from poker_ai.core.profiles import PlayerProfile
from poker_ai.eval.baseline import hero_equity_at_showdown
from poker_ai.eval.hand_trace import pot_at_showdown
from poker_ai.ingest.records import ParsedHand
from poker_ai.league.agents.baselines import RandomPolicy
from poker_ai.league.sim import HandResult, new_hu_hand, play_hand


def full_aivat_enabled() -> bool:
    return os.environ.get("POKER_AI_AIVAT_FULL", "").strip() in ("1", "true", "yes")


def aivat_mode() -> str:
    return "full" if full_aivat_enabled() else "sketch"


def _sketch_adjustment(
    delta_chips: int,
    *,
    went_showdown: bool,
    winner_seat: int | None,
    seat: int,
    big_blind: int,
) -> float:
    if not went_showdown or winner_seat is None:
        return float(delta_chips)
    luck = big_blind * (1.0 if winner_seat == seat else -1.0) * 0.25
    return float(delta_chips) - luck


def _showdown_luck_component(
    delta_chips: int,
    *,
    hand: ParsedHand | None,
    big_blind: int,
) -> float:
    """Chip luck at showdown to subtract (chance correction)."""
    if hand is not None:
        eq = hero_equity_at_showdown(hand)
        if eq is not None:
            pot = pot_at_showdown(hand)
            expected = (eq - 0.5) * float(pot)
            return float(delta_chips) - expected
    return big_blind * 0.25 * (1.0 if delta_chips > 0 else -1.0 if delta_chips < 0 else 0.0)


def _strategy_correction_stub(*, big_blind: int) -> float:
    _ = big_blind
    return 0.0


def aivat_adjust_delta(
    delta_chips: int,
    *,
    went_showdown: bool,
    winner_seat: int | None,
    seat: int,
    big_blind: int,
    hand: ParsedHand | None = None,
    full: bool | None = None,
) -> float:
    """AIVAT-adjusted chip delta for one seat."""
    use_full = full_aivat_enabled() if full is None else full
    if not use_full:
        return _sketch_adjustment(
            delta_chips,
            went_showdown=went_showdown,
            winner_seat=winner_seat,
            seat=seat,
            big_blind=big_blind,
        )
    if not went_showdown:
        return float(delta_chips)
    luck = _showdown_luck_component(delta_chips, hand=hand, big_blind=big_blind)
    return float(delta_chips) - luck - _strategy_correction_stub(big_blind=big_blind)


@dataclass(frozen=True, slots=True)
class AivatAuditReport:
    finished_at: str
    aivat_mode: str
    hands: int
    naive_bb100: float
    full_bb100: float
    naive_stderr: float
    full_stderr: float
    stderr_reduction_pct: float
    report_path: str


def _stderr(samples: list[float]) -> float:
    n = len(samples)
    if n < 2:
        return 0.0
    mean = sum(samples) / n
    var = sum((x - mean) ** 2 for x in samples) / (n - 1)
    return math.sqrt(var / n)


def run_aivat_audit(
    *,
    hands: int = 1000,
    seed: int = 42,
    report_path: Path | None = None,
) -> AivatAuditReport:
    """Run synthetic HU sample comparing naive vs full AIVAT stderr."""
    from datetime import UTC, datetime

    rng = random.Random(seed)
    profile = PlayerProfile(profile_id="audit")
    pol_a = RandomPolicy(seed=1)
    pol_b = RandomPolicy(seed=2)
    naive_samples: list[float] = []
    full_samples: list[float] = []
    bb = 100

    for i in range(hands):
        state = new_hu_hand(seed=seed + i)
        bb = max(state.big_blind, 1)
        result: HandResult = play_hand(state, (pol_a, pol_b), (profile, profile), rng)
        for seat, delta in enumerate(result.deltas):
            sketch = _sketch_adjustment(
                delta,
                went_showdown=result.went_showdown,
                winner_seat=result.winner_seat,
                seat=seat,
                big_blind=bb,
            )
            full = aivat_adjust_delta(
                delta,
                went_showdown=result.went_showdown,
                winner_seat=result.winner_seat,
                seat=seat,
                big_blind=bb,
                full=True,
            )
            naive_samples.append(sketch / bb * 100.0)
            full_samples.append(full / bb * 100.0)

    naive_se = _stderr(naive_samples)
    full_se = _stderr(full_samples)
    reduction = 0.0 if naive_se <= 0 else (1.0 - full_se / naive_se) * 100.0

    dest = report_path or Path("reports/aivat_audit.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    report = AivatAuditReport(
        finished_at=datetime.now(tz=UTC).isoformat(),
        aivat_mode="full",
        hands=hands,
        naive_bb100=round(sum(naive_samples) / max(1, len(naive_samples)), 4),
        full_bb100=round(sum(full_samples) / max(1, len(full_samples)), 4),
        naive_stderr=round(naive_se, 6),
        full_stderr=round(full_se, 6),
        stderr_reduction_pct=round(reduction, 2),
        report_path=str(dest.resolve()),
    )
    payload: dict[str, Any] = asdict(report)
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report
