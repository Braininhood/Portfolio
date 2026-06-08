"""Bayesian preflop range inference with Dirichlet prior (Phase 13 / W10)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from poker_ai.core.cards import parse_card
from poker_ai.features.range import isomorphic_preflop_id
from poker_ai.ingest.records import ParsedHand

NUM_PREFLOP_CLASSES = 169
_DIRICHLET_ALPHA = 1.0

# Display tiers (wireframe buckets).
_PREMIUM: frozenset[int] = frozenset(list(range(0, 4)) + list(range(140, 169)))
_MEDIUM: frozenset[int] = frozenset(range(100, 140))
_TIER_LABELS = {
    "premium": "AA–JJ, AKs, AQs",
    "medium": "TT–88, AJs, KQs",
    "other": "Other",
}


@dataclass(frozen=True, slots=True)
class RangeBucket:
    tier: str
    label: str
    mass_pct: float


@dataclass(frozen=True, slots=True)
class RangeInferenceResult:
    player_uid: str
    observed_actions: int
    buckets: tuple[RangeBucket, ...]
    confidence_label: str
    confidence_pct: float
    last_updated_at: str | None
    last_hand_id: int | None
    note: str | None = None


def _class_label(class_id: int) -> str:
    """Best-effort human label for one isomorphic class (for debugging)."""
    ranks = "AKQJT98765432"
    if 0 <= class_id <= 12:
        r = ranks[class_id]
        return f"{r}{r}"
    return f"cls{class_id}"


def _tier_for_class(class_id: int) -> str:
    if class_id in _PREMIUM:
        return "premium"
    if class_id in _MEDIUM:
        return "medium"
    return "other"


def _parse_hole_cards(cards: str | None) -> tuple[int, int] | None:
    if not cards or not cards.strip():
        return None
    parts = cards.replace(",", " ").split()
    if len(parts) < 2:
        s = cards.strip().lower().replace(" ", "")
        if len(s) >= 4:
            parts = [s[:2], s[2:4]]
        else:
            return None
    try:
        c0 = parse_card(parts[0])
        c1 = parse_card(parts[1])
        return c0, c1
    except ValueError:
        return None


def _update_from_showdown(alpha: list[float], cards: str) -> None:
    hole = _parse_hole_cards(cards)
    if hole is None:
        return
    cid = isomorphic_preflop_id(hole[0], hole[1])
    if 0 <= cid < NUM_PREFLOP_CLASSES:
        alpha[cid] += 3.0


def _soft_update_tier(alpha: list[float], tier: str, strength: float) -> None:
    members = _PREMIUM if tier == "premium" else _MEDIUM if tier == "medium" else None
    if members is None:
        return
    n = len(members)
    if n <= 0:
        return
    bump = strength / n
    for cid in members:
        alpha[cid] += bump


def infer_range_from_hands(
    player_uid: str,
    hands: list[ParsedHand],
    *,
    player_id_lookup: dict[int, str] | None = None,
) -> RangeInferenceResult:
    """Dirichlet-prior belief over 169 preflop classes from observed play."""
    alpha = [_DIRICHLET_ALPHA] * NUM_PREFLOP_CLASSES
    observed = 0
    last_hand_id: int | None = None
    last_ts: str | None = None

    for hand in hands:
        pid_for_uid: int | None = None
        for p in hand.players:
            if p.player_uid == player_uid:
                pid_for_uid = p.player_id
                break
        if pid_for_uid is None:
            continue

        acted_preflop = False
        for act in hand.actions:
            if act.player_id != pid_for_uid:
                continue
            if act.street.upper() != "PREFLOP":
                continue
            at = act.action_type.lower()
            if at in ("fold", "check", "call", "bet", "raise", "all-in", "allin"):
                observed += 1
                acted_preflop = True
                if at in ("raise", "bet", "all-in", "allin"):
                    _soft_update_tier(alpha, "premium", 0.8)
                elif at == "call":
                    _soft_update_tier(alpha, "medium", 0.5)

        for res in hand.results:
            if res.player_id != pid_for_uid:
                continue
            if res.showdown and res.cards.strip():
                _update_from_showdown(alpha, res.cards)
                observed += 1
                last_hand_id = hand.hand_id

        if acted_preflop:
            last_hand_id = hand.hand_id

    total = sum(alpha)
    tier_mass = {"premium": 0.0, "medium": 0.0, "other": 0.0}
    for cid, a in enumerate(alpha):
        tier_mass[_tier_for_class(cid)] += a / total

    buckets = tuple(
        RangeBucket(tier=t, label=_TIER_LABELS[t], mass_pct=round(tier_mass[t] * 100, 1))
        for t in ("premium", "medium", "other")
    )

    if observed >= 200:
        conf_label, conf_pct = "High", min(95.0, 60.0 + observed / 20.0)
    elif observed >= 50:
        conf_label, conf_pct = "Medium", min(75.0, 30.0 + observed / 3.0)
    elif observed >= 10:
        conf_label, conf_pct = "Low", min(45.0, 10.0 + observed)
    else:
        conf_label, conf_pct = "Very low", max(5.0, float(observed * 3))

    if last_hand_id is not None:
        last_ts = datetime.now(UTC).strftime("%Y-%m-%d")

    note = None
    if observed < 10:
        note = "Few observations — import more hands or wait for more showdowns."

    return RangeInferenceResult(
        player_uid=player_uid,
        observed_actions=observed,
        buckets=buckets,
        confidence_label=conf_label,
        confidence_pct=round(conf_pct, 1),
        last_updated_at=last_ts,
        last_hand_id=last_hand_id,
        note=note,
    )
