"""Template-based explanations — no LLM (see doc/NOVEL_TECHNIQUES.md §7)."""

from __future__ import annotations

import json
from pathlib import Path

from poker_ai.core.game import GameState
from poker_ai.features.board_texture import texture_int16
from poker_ai.policy.base import ActionDist

_TEMPLATES_PATH = Path(__file__).resolve().parent / "templates.json"


def _spr_bucket(state: GameState) -> str:
    hero = state.acting_seat or 0
    eff = float(state.stacks[hero]) if hero < len(state.stacks) else 0.0
    pot = max(1, state.pot)
    spr = eff / pot
    if spr >= 8.0:
        return "deep"
    if spr >= 3.0:
        return "medium"
    return "shallow"


def _board_texture_label(state: GameState) -> str:
    if not state.board:
        return "none"
    tex = texture_int16(tuple(state.board))
    if len(tex) >= 3 and tex[0] > 200:
        return "paired"
    if len(tex) >= 2 and tex[1] > 200:
        return "monotone"
    if len(tex) >= 4 and tex[3] > 180:
        return "connected"
    return "dry"


def _action_bucket(dist: ActionDist) -> str:
    if not dist.actions:
        return "unknown"
    top_idx = max(range(len(dist.probs)), key=lambda i: dist.probs[i])
    kind, amount, _seat = dist.actions[top_idx]
    k = kind.lower()
    if k == "fold":
        return "fold"
    if k in ("check", "call"):
        return "check_call"
    if k in ("bet", "raise"):
        pot = max(1, 1)  # placeholder; sizing bucket uses amount only
        _ = pot
        if amount <= 0:
            return "bet_small"
        return "bet_aggressive"
    return k


def _hero_position(state: GameState) -> str:
    hero = state.acting_seat or 0
    ring = ("BTN", "SB", "BB", "UTG", "MP", "CO")
    return ring[min(hero, len(ring) - 1)]


def _load_templates() -> list[dict[str, object]]:
    if not _TEMPLATES_PATH.is_file():
        return []
    raw = json.loads(_TEMPLATES_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []
    return [t for t in raw if isinstance(t, dict)]


def _match_template(
    *,
    position: str,
    street: str,
    spr_bucket: str,
    board_texture: str,
    action_bucket: str,
) -> str | None:
    for row in _load_templates():
        match = row.get("match")
        if not isinstance(match, dict):
            continue
        if match.get("position") and match["position"] != position:
            continue
        street_match = match.get("street")
        if street_match and str(street_match).lower() != street.lower():
            continue
        if match.get("spr_bucket") and match["spr_bucket"] != spr_bucket:
            continue
        if match.get("board_texture") and match["board_texture"] != board_texture:
            continue
        if match.get("action_bucket") and match["action_bucket"] != action_bucket:
            continue
        tpl = row.get("template")
        return tpl if isinstance(tpl, str) else None
    return None


def explain_decision(
    state: GameState,
    decision: ActionDist,
    *,
    policy_name: str = "policy",
) -> str:
    """Return a human-readable rationale for ``decision`` at ``state``."""
    if not decision.actions:
        return f"{policy_name}: no legal decision at this node."

    top_idx = max(range(len(decision.probs)), key=lambda i: decision.probs[i])
    kind, amount, seat = decision.actions[top_idx]
    freq = decision.probs[top_idx]
    position = _hero_position(state)
    spr_bucket = _spr_bucket(state)
    board_texture = _board_texture_label(state)
    action_bucket = _action_bucket(decision)
    street_key = state.street.value.lower()

    tpl = _match_template(
        position=position,
        street=street_key,
        spr_bucket=spr_bucket,
        board_texture=board_texture,
        action_bucket=action_bucket,
    )
    hero = state.acting_seat or 0
    spr = float(state.stacks[hero]) / max(1, state.pot) if hero < len(state.stacks) else 0.0
    recommendation = f"{kind} {amount} chips" if amount else kind

    if tpl:
        return tpl.format(
            position=position,
            street=state.street.value,
            spr=spr,
            spr_bucket=spr_bucket,
            board_texture=board_texture,
            action_bucket=action_bucket,
            freq=freq,
            recommendation=recommendation,
            policy=policy_name,
            seat=seat,
        )

    return (
        f"{policy_name}: {position} on {state.street.value} (SPR {spr:.1f}, {spr_bucket}) "
        f"recommends {recommendation} at {freq:.0%} — board texture {board_texture}."
    )
