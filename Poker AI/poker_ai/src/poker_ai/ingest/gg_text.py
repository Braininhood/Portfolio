"""GGPoker-style text — placeholder parser (doc/ROADMAP.md Phase 1)."""

from __future__ import annotations

from poker_ai.ingest.records import ParsedHand


def looks_like_gg_text(text: str) -> bool:
    """Cheap detector for future GG-specific rules."""
    head = text[:1200]
    return "GGPoker Hand #" in head or "PokerCraft" in head


def parse_gg_text(_text: str, *, _hand_id: int, _uid_secret: str) -> ParsedHand | None:
    """Reserved for full GGPoker text parsing; returns ``None`` today."""
    return None
