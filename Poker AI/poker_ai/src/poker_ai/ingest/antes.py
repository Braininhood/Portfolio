"""Shared helpers for ``ParsedHand.antes`` (parallel to ``players`` tuple order)."""

from __future__ import annotations

import re

from poker_ai.ingest.records import ParsedPlayer

_POST_ANTE_RE = re.compile(
    r"^(.+?):\s*posts?\s+(?:the\s+)?ante\s+\$?(\d+(?:\.\d+)?)\s*$",
    re.IGNORECASE,
)


def build_antes_tuple(
    players: tuple[ParsedPlayer, ...],
    amounts_by_pid: dict[int, float],
) -> tuple[float, ...]:
    """Map ``player_id`` → amount into a tuple aligned with ``players``."""
    if not players:
        return ()
    return tuple(float(amounts_by_pid.get(p.player_id, 0.0) or 0.0) for p in players)


def merge_ante_post(amounts: dict[int, float], player_id: int, amount: float) -> None:
    """Accumulate ante for a seat (supports multiple posts in malformed exports)."""
    if amount <= 0:
        return
    amounts[player_id] = float(amounts.get(player_id, 0.0) + amount)


def scan_text_ante_posts(
    lines: list[str],
    *,
    player_id_map: dict[str, int],
    hero_position: str | None,
    stop_at_street: str = "Flop",
) -> dict[int, float]:
    """Parse PokerStars-style ``posts the ante $X`` lines in normalized / raw text."""
    from poker_ai.ingest.positions import normalize_text_position

    amounts: dict[int, float] = {}
    for line in lines:
        stripped = line.strip()
        if re.match(rf"^{stop_at_street}\b", stripped, re.IGNORECASE):
            break
        m = _POST_ANTE_RE.match(stripped)
        if not m:
            continue
        pos_raw = m.group(1).strip()
        if pos_raw.lower().startswith("hero"):
            hm = re.match(r"Hero\s*\((\w+)\)", pos_raw, re.IGNORECASE)
            if hm is not None:
                pos = normalize_text_position(hm.group(1))
            elif hero_position is not None:
                pos = hero_position
            else:
                continue
        else:
            pos = normalize_text_position(pos_raw)
        pid = player_id_map.get(pos)
        if pid is None:
            continue
        merge_ante_post(amounts, pid, float(m.group(2)))
    return amounts
