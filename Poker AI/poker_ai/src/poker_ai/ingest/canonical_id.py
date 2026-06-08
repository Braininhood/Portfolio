"""Stable hand primary keys and external refs across ingest sources."""

from __future__ import annotations

import hashlib

# Short labels stored on ``games.ingest_source`` (extend when adding parsers).
INGEST_NORMALIZED_TXT = "normalized_txt"
INGEST_OHH_JSON = "ohh_json"
INGEST_POKERSTARS_RAW_MINIMAL = "pokerstars_raw_minimal"
INGEST_GG_NETWORK = "gg_network"
INGEST_PHH = "phh"


def stable_hand_int(ingest_source: str, external_ref: str) -> int:
    """Deterministic positive int for ``(ingest_source, external_ref)``.

    Capped at **JavaScript Number.MAX_SAFE_INTEGER** (2^53 - 1) so JSON / browser /
    spreadsheet tooling does not round ``hand_id`` and break joins to ``actions`` /
    ``players``. SQLite still stores 64-bit integers.
    """
    key = f"{ingest_source}\0{external_ref}".encode()
    digest = hashlib.blake2b(key, digest_size=8).digest()
    # Same order of magnitude as JS Number.MAX_SAFE_INTEGER (2**53 - 1).
    max_safe = (1 << 53) - 1
    h = int.from_bytes(digest, "big") & max_safe
    if h == 0:
        h = 1
    return h


def resolve_hand_id(ingest_source: str, external_ref: str) -> int:
    """Return ``games.hand_id`` — numeric IDs only for normalized converter corpus."""
    ref = external_ref.strip()
    if ingest_source == INGEST_NORMALIZED_TXT and ref.isdigit():
        return int(ref)
    return stable_hand_int(ingest_source, ref)
