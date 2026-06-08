"""Stable per-player identifiers (doc/ROADMAP.md Phase 1)."""

from __future__ import annotations

import hashlib
import hmac


def player_uid_hmac(secret: str, *, nickname: str | None, hand_id: int, seat_player_id: int) -> str:
    """Return hex digest of HMAC-SHA256.

    When ``nickname`` is known (e.g. OHH / raw PokerStars), the UID is stable across hands.
    Otherwise we derive a deterministic **per-hand** UID from ``(hand_id, seat_player_id)`` so
    re-ingest stays idempotent without merging anonymous seats into one global player.
    """
    key = secret.encode("utf-8")
    if nickname is not None and nickname.strip() != "":
        msg = nickname.strip().casefold().encode("utf-8")
    else:
        msg = f"ephemeral:{hand_id}:{seat_player_id}".encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()
