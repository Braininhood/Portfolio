"""Decision drill helpers — hero spots, action labels, policy comparison."""

from __future__ import annotations

from typing import Any

from poker_ai.core.engine import IllegalActionError, legal_actions
from poker_ai.core.game import GameState
from poker_ai.core.profiles import PlayerProfile
from poker_ai.core.replay import state_after_actions
from poker_ai.equity.backfill import hero_street_equity_from_hand
from poker_ai.equity.live import hero_equity_from_state
from poker_ai.explain.engine import explain_decision
from poker_ai.ingest.records import ParsedAction, ParsedHand
from poker_ai.policy.base import ActionDist, Policy

from services.policy_service import get_policy, propose_with_timing
from state_codec import action_dist_to_probs


def hero_player_id(hand: ParsedHand) -> int | None:
    return next((p.player_id for p in hand.players if p.is_hero), None)


def quick_hero_action_count(hand: ParsedHand) -> int:
    """Fast count of hero actions (full validation on /drill/{id}/steps and /spot)."""
    hero_pid = hero_player_id(hand)
    if hero_pid is None:
        return 0
    return sum(1 for pa in hand.actions if pa.player_id == hero_pid)


def hero_decision_indices(hand: ParsedHand) -> list[int]:
    """Action indices where hero is to act and /decide can run."""
    hero_pid = hero_player_id(hand)
    if hero_pid is None:
        return []
    out: list[int] = []
    for idx, pa in enumerate(hand.actions):
        if pa.player_id != hero_pid:
            continue
        try:
            state = state_after_actions(hand, idx, lenient=True)
            if not state.hand_over and legal_actions(state):
                out.append(idx)
        except (IllegalActionError, ValueError):
            continue
    return out


def hand_has_decision_point(hand: ParsedHand) -> bool:
    return bool(hero_decision_indices(hand))


def _pot_fraction_label(amount_chips: int, pot: int) -> str | None:
    if pot <= 0 or amount_chips <= 0:
        return None
    frac = amount_chips / pot
    if 0.25 <= frac <= 0.40:
        return "1/3 pot"
    if 0.52 <= frac <= 0.72:
        return "2/3 pot"
    if 0.85 <= frac <= 1.15:
        return "pot"
    if frac >= 1.5:
        return "overbet"
    return None


def format_action_label(
    kind: str,
    amount_chips: int,
    *,
    pot: int,
    bb: float,
) -> str:
    k = kind.strip().lower()
    if k == "fold":
        return "Fold"
    if k == "check":
        return "Check"
    if k == "call":
        if amount_chips > 0 and bb > 0:
            return f"Call {round(amount_chips / bb, 1)} BB"
        return "Call"
    if k in ("bet", "raise"):
        sizing = _pot_fraction_label(amount_chips, pot)
        verb = "Bet" if k == "bet" else "Raise"
        if sizing:
            return f"{verb} {sizing}"
        if amount_chips > 0 and bb > 0:
            return f"{verb} {round(amount_chips / bb, 1)} BB"
        return verb
    return kind.capitalize()


def _action_kind_bucket(kind: str) -> str:
    k = kind.strip().lower()
    if k == "fold":
        return "fold"
    if k in ("check", "call"):
        return "passive"
    if k in ("bet", "raise"):
        return "aggressive"
    return k


def _top_from_probs(actions: list[dict[str, float | int | str]]) -> tuple[str, int, float]:
    if not actions:
        return ("unknown", 0, 0.0)
    top = max(actions, key=lambda a: float(a["prob"]))
    return (str(top["kind"]), int(top["amount_chips"]), float(top["prob"]))


def _top_action(dist: ActionDist) -> tuple[str, int, float]:
    if not dist.actions:
        return ("unknown", 0, 0.0)
    top_i = max(range(len(dist.probs)), key=lambda i: dist.probs[i])
    kind, amount, _seat = dist.actions[top_i]
    return (str(kind), int(amount), float(dist.probs[top_i]))


def policy_vs_human(actual_kind: str, ai_kind: str, ai_prob: float) -> str:
    if _action_kind_bucket(actual_kind) == _action_kind_bucket(ai_kind):
        if actual_kind.lower() == ai_kind.lower():
            return "Same"
        return "Similar line"
    return "Different — see recommendations"


def build_action_comparison(
    actual: ParsedAction,
    dist: ActionDist,
    *,
    pot: int,
    bb: float,
    action_probs: list[dict[str, float | int | str]] | None = None,
) -> str:
    actual_label = format_action_label(
        actual.action_type,
        int(actual.amount) if actual.amount else 0,
        pot=pot,
        bb=bb,
    )
    if dist.actions:
        ai_kind, ai_amount, ai_prob = _top_action(dist)
    elif action_probs:
        ai_kind, ai_amount, ai_prob = _top_from_probs(action_probs)
    else:
        ai_kind, ai_amount, ai_prob = ("unknown", 0, 0.0)
    ai_label = format_action_label(ai_kind, ai_amount, pot=pot, bb=bb)
    pct = f"{ai_prob * 100:.0f}%"
    return f"You {actual_label.lower()} · AI says {ai_label.lower()} ({pct})"


def spot_context(hand: ParsedHand, state: GameState, step_index: int) -> dict[str, Any]:
    bb = float(hand.big_blind) if hand.big_blind > 0 else 1.0
    pot_bb = round(state.pot / bb, 1) if bb > 0 else None
    hero_seat = state.acting_seat
    stack_bb = None
    spr = None
    if hero_seat is not None and hero_seat < len(state.stacks):
        stack_bb = round(state.stacks[hero_seat] / bb, 1)
        spr = round(state.stacks[hero_seat] / max(1, state.pot), 1)
    pa = hand.actions[step_index]
    return {
        "hero_cards": hand.hero_cards,
        "board": hand.board_cards,
        "street": state.street.value,
        "position": pa.position,
        "pot_bb": pot_bb,
        "stack_bb": stack_bb,
        "spr": spr,
    }


def run_decide(
    hand: ParsedHand,
    step_index: int,
    *,
    policy_name: str,
    thinking_ms: int = 0,
    deep_search: bool = False,
) -> tuple[ActionDist, float, str, GameState, Policy]:
    profile = PlayerProfile(profile_id="hero", display_name="hero")
    policy = get_policy(policy_name)
    state = state_after_actions(hand, step_index, lenient=True)
    if state.hand_over:
        msg = "hand is over at this step"
        raise ValueError(msg)
    if not legal_actions(state):
        msg = "no legal actions at this node"
        raise ValueError(msg)

    dist, latency_ms = propose_with_timing(
        policy,
        state,
        profile,
        thinking_ms=thinking_ms,
        deep_search=deep_search,
    )
    if not dist.actions:
        policy = get_policy("heuristic")
        dist, latency_ms = propose_with_timing(
            policy,
            state,
            profile,
            thinking_ms=thinking_ms,
            deep_search=deep_search,
        )
    explanation = explain_decision(state, dist, policy_name=policy.name)
    try:
        policy_explain = policy.explain(state, dist)
        if policy_explain and policy_explain not in explanation:
            explanation = f"{explanation}\n{policy_explain}"
    except Exception:
        pass
    return dist, latency_ms, explanation, state, policy


def dist_to_action_probs(
    dist: ActionDist,
    *,
    pot: int = 0,
    bb: float = 1.0,
) -> list[dict[str, float | int | str]]:
    raw = action_dist_to_probs(dist.actions, dist.probs)
    return [
        {
            "kind": str(r["kind"]),
            "amount_chips": int(r["amount_chips"]),
            "seat": int(r["seat"]),
            "prob": float(r["prob"]),
            "label": format_action_label(str(r["kind"]), int(r["amount_chips"]), pot=pot, bb=bb),
        }
        for r in raw
    ]


def run_decide_parity(
    hand: ParsedHand,
    step_index: int,
    *,
    policy_name: str,
    thinking_ms: int = 0,
    lenient: bool = False,
) -> tuple[list[dict[str, float | int | str]], str, str]:
    """Same core logic as ``POST /decide`` (no drill fallback or comparison fields)."""
    profile = PlayerProfile(profile_id="hero", display_name="hero")
    policy = get_policy(policy_name)
    if step_index > len(hand.actions):
        msg = "step_index exceeds action count"
        raise ValueError(msg)
    state = state_after_actions(hand, step_index, lenient=lenient)
    if state.hand_over:
        msg = "hand is over at this step"
        raise ValueError(msg)
    if not legal_actions(state):
        msg = "no legal actions at this node"
        raise ValueError(msg)

    dist, _latency_ms = propose_with_timing(
        policy,
        state,
        profile,
        thinking_ms=thinking_ms,
    )
    bb = float(hand.big_blind) if hand.big_blind > 0 else 1.0
    return (
        dist_to_action_probs(dist, pot=state.pot, bb=bb),
        policy.name,
        state.street.value,
    )


def compare_action_lists(
    decide_actions: list[dict[str, float | int | str]],
    drill_actions: list[dict[str, float | int | str]],
    *,
    prob_tol: float = 0.001,
) -> tuple[bool, list[str]]:
    """Return (ok, messages) comparing /decide vs /drill/spot action frequencies."""

    def key(a: dict[str, float | int | str]) -> tuple[str, int]:
        return (str(a["kind"]).lower(), int(a["amount_chips"]))

    a_map = {key(a): float(a["prob"]) for a in decide_actions}
    b_map = {key(a): float(a["prob"]) for a in drill_actions}

    issues: list[str] = []
    all_keys = sorted(set(a_map) | set(b_map), key=lambda k: (k[0], k[1]))
    for k in all_keys:
        pa = a_map.get(k)
        pb = b_map.get(k)
        if pa is None:
            issues.append(f"only in drill: {k[0]} amount={k[1]} p={pb:.4f}")
        elif pb is None:
            issues.append(f"only in decide: {k[0]} amount={k[1]} p={pa:.4f}")
        elif abs(pa - pb) > prob_tol:
            issues.append(f"prob mismatch {k[0]} amount={k[1]}: decide={pa:.4f} drill={pb:.4f}")

    return (not issues, issues)


def build_drill_spot(
    hand: ParsedHand,
    step_index: int,
    *,
    policy_name: str,
    thinking_ms: int = 0,
    deep_search: bool = False,
    include_equity: bool = True,
) -> dict[str, Any]:
    hero_pid = hero_player_id(hand)
    if hero_pid is None:
        msg = "hand has no hero seat"
        raise ValueError(msg)
    if step_index < 0 or step_index >= len(hand.actions):
        msg = "step_index out of range"
        raise ValueError(msg)
    actual = hand.actions[step_index]
    if actual.player_id != hero_pid:
        msg = "step_index is not a hero decision point"
        raise ValueError(msg)

    dist, latency_ms, explanation, state, policy = run_decide(
        hand,
        step_index,
        policy_name=policy_name,
        thinking_ms=thinking_ms,
        deep_search=deep_search,
    )
    bb = float(hand.big_blind) if hand.big_blind > 0 else 1.0
    ctx = spot_context(hand, state, step_index)
    actual_amount_bb = round(actual.amount / bb, 1) if actual.amount and bb > 0 else None
    action_probs = dist_to_action_probs(dist, pot=state.pot, bb=bb)
    ai_kind, ai_amount, ai_prob = _top_from_probs(action_probs)
    hero_eq: float | None = None
    if include_equity:
        hero_eq = hero_street_equity_from_hand(hand, street=state.street.value)
        if hero_eq is None:
            hero_eq = hero_equity_from_state(state)

    return {
        "policy_name": policy.name,
        "policy_version": policy.version,
        "latency_ms": latency_ms,
        "actions": action_probs,
        "explanation": explanation,
        "street": state.street.value,
        "acting_seat": state.acting_seat,
        "step_index": step_index,
        "actual_action": actual.action_type,
        "actual_amount": actual_amount_bb,
        "hero_cards": ctx["hero_cards"],
        "board": ctx["board"],
        "position": ctx["position"],
        "pot_bb": ctx["pot_bb"],
        "stack_bb": ctx["stack_bb"],
        "spr": ctx["spr"],
        "action_comparison": build_action_comparison(
            actual,
            dist,
            pot=state.pot,
            bb=bb,
            action_probs=action_probs,
        ),
        "policy_vs_human": policy_vs_human(
            actual.action_type,
            ai_kind,
            ai_prob,
        ),
        "ai_top_action": format_action_label(ai_kind, ai_amount, pot=state.pot, bb=bb),
        "ai_top_prob": ai_prob,
        "hero_equity": round(hero_eq, 4) if hero_eq is not None else None,
    }


POLICY_DISPLAY: dict[str, str] = {
    "distilled": "Distilled",
    "heuristic": "Heuristic",
    "best": "Main AI",
}


def compare_policies(
    hand: ParsedHand,
    step_index: int,
    *,
    policies: tuple[str, ...] = ("distilled", "heuristic", "best"),
    thinking_ms: int = 0,
    deep_search: bool = False,
) -> dict[str, Any]:
    columns: list[dict[str, Any]] = []
    top_buckets: list[str] = []

    state = state_after_actions(hand, step_index, lenient=True)
    bb = float(hand.big_blind) if hand.big_blind > 0 else 1.0
    pot = state.pot
    ctx = spot_context(hand, state, step_index)
    actual = hand.actions[step_index]
    actual_amount_bb = round(actual.amount / bb, 1) if actual.amount and bb > 0 else None

    for key in policies:
        dist, latency_ms, _explanation, _state, policy = run_decide(
            hand,
            step_index,
            policy_name=key,
            thinking_ms=thinking_ms,
            deep_search=deep_search,
        )
        rows = []
        for ap in dist_to_action_probs(dist, pot=pot, bb=bb):
            label = str(ap["label"])
            rows.append({"label": label, "prob": float(ap["prob"])})
        rows.sort(key=lambda r: r["prob"], reverse=True)
        top_kind, _, _ = _top_action(dist)
        top_buckets.append(_action_kind_bucket(top_kind))
        columns.append(
            {
                "policy_key": key,
                "policy_label": POLICY_DISPLAY.get(key, policy.name),
                "policy_name": policy.name,
                "latency_ms": latency_ms,
                "actions": rows[:5],
            }
        )

    consensus = _consensus_label(top_buckets)
    return {
        "policies": columns,
        "consensus": consensus,
        "actual_action": actual.action_type,
        "actual_amount": actual_amount_bb,
        "hero_cards": ctx["hero_cards"],
        "board": ctx["board"],
        "street": ctx["street"],
        "position": ctx["position"],
        "pot_bb": ctx["pot_bb"],
        "stack_bb": ctx["stack_bb"],
        "spr": ctx["spr"],
    }


def _consensus_label(buckets: list[str]) -> str:
    if not buckets:
        return "No data"
    if len(set(buckets)) == 1:
        b = buckets[0]
        if b == "aggressive":
            return "All recommend betting — STRONG BET"
        if b == "passive":
            return "All recommend check/call — PASSIVE"
        if b == "fold":
            return "All recommend folding — FOLD"
        return f"Unanimous — {b.upper()}"
    if all(b in ("aggressive", "passive") for b in buckets):
        return "Mixed passive/aggressive — no clear consensus"
    return "Policies disagree — review each column"
