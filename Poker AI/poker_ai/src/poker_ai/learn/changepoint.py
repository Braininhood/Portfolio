"""BOCPD-style opponent regime changepoints (Phase 11 / W8)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ChangepointAlert:
    player_uid: str
    display_name: str
    detected_at: str
    description: str
    confidence: float


def _alerts_path() -> Path:
    return Path("data/drift/changepoints.json")


def detect_changepoints(*, player_uid: str | None = None) -> list[ChangepointAlert]:
    """Load persisted alerts, optionally filtered by player."""
    p = _alerts_path()
    if not p.is_file():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        alerts = [
            ChangepointAlert(
                player_uid=str(a["player_uid"]),
                display_name=str(a.get("display_name", a["player_uid"][:8])),
                detected_at=str(a["detected_at"]),
                description=str(a["description"]),
                confidence=float(a.get("confidence", 0.5)),
            )
            for a in raw.get("alerts", [])
        ]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []
    if player_uid:
        alerts = [a for a in alerts if a.player_uid == player_uid]
    return alerts


def changepoint_for_player(player_uid: str) -> ChangepointAlert | None:
    """Most recent alert for a player, if any."""
    alerts = detect_changepoints(player_uid=player_uid)
    if not alerts:
        return None
    return max(alerts, key=lambda a: a.detected_at)


def save_changepoints(alerts: list[ChangepointAlert]) -> None:
    p = _alerts_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(tz=UTC).isoformat(),
        "alerts": [
            {
                "player_uid": a.player_uid,
                "display_name": a.display_name,
                "detected_at": a.detected_at,
                "description": a.description,
                "confidence": a.confidence,
            }
            for a in alerts
        ],
    }
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def scan_play_sessions_for_changepoints() -> list[ChangepointAlert]:
    """Heuristic: flag bots whose aggression shifted between first/second half of play hands."""
    from poker_ai.learn.play_study_loader import collect_play_opponent_stats

    alerts: list[ChangepointAlert] = []
    for opp in collect_play_opponent_stats():
        af_early = float(opp.get("af_early") or 0)
        af_late = float(opp.get("af_late") or 0)
        if opp.get("decisions", 0) < 20:
            continue
        if abs(af_late - af_early) >= 1.0:
            alerts.append(
                ChangepointAlert(
                    player_uid=str(opp["player_uid"]),
                    display_name=str(opp.get("display_name", "Bot")),
                    detected_at=datetime.now(tz=UTC).strftime("%Y-%m-%d"),
                    description=f"Aggression factor shifted {af_early:.1f} -> {af_late:.1f} (play vs AI)",
                    confidence=min(0.95, 0.5 + abs(af_late - af_early) * 0.2),
                )
            )
    save_changepoints(alerts)
    return alerts
