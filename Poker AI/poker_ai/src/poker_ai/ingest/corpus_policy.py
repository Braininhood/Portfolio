"""PHH bulk-tree ingest policy — cash vs MTT, obfuscation, corpus excludes (Phase 1 ops)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from poker_ai.ingest.records import ParsedHand


@dataclass(frozen=True, slots=True)
class PhhCorpusPolicy:
    """Filter rules for ``hand/poker-hand-histories/`` style trees."""

    cash_only: bool = False
    exclude_obfuscated: bool = False
    exclude_paths: tuple[str, ...] = ()
    min_total_ante: float | None = None
    max_total_ante: float | None = None


def policy_from_env() -> PhhCorpusPolicy:
    """Read ``POKER_AI_PHH_*`` env vars (optional; defaults accept all NT hands)."""
    excl_raw = os.environ.get("POKER_AI_PHH_EXCLUDE_PATHS", "")
    excludes = tuple(p.strip() for p in excl_raw.split(",") if p.strip())
    min_a = os.environ.get("POKER_AI_PHH_MIN_TOTAL_ANTE")
    max_a = os.environ.get("POKER_AI_PHH_MAX_TOTAL_ANTE")
    return PhhCorpusPolicy(
        cash_only=os.environ.get("POKER_AI_PHH_CASH_ONLY", "").strip().lower() in ("1", "true", "yes"),
        exclude_obfuscated=os.environ.get("POKER_AI_PHH_NO_OBFU", "").strip().lower()
        in ("1", "true", "yes"),
        exclude_paths=excludes,
        min_total_ante=float(min_a) if min_a else None,
        max_total_ante=float(max_a) if max_a else None,
    )


def _path_hits_exclude(rel_posix: str, excludes: tuple[str, ...]) -> bool:
    rel = rel_posix.replace("\\", "/").lower()
    for frag in excludes:
        if frag.lower() in rel:
            return True
    return False


def is_mtt_like_path(rel_posix: str) -> bool:
    """Heuristic: WSOP / large-ante tournament trees."""
    rel = rel_posix.replace("\\", "/").lower()
    if "/wsop/" in rel or rel.startswith("wsop/"):
        return True
    if "tournament" in rel or "/mtt/" in rel:
        return True
    return False


def is_obfuscated_path(rel_posix: str) -> bool:
    rel = rel_posix.replace("\\", "/").lower()
    return "obfu" in rel or "/handhq/" in rel


def phh_hand_passes_policy(
    hand: ParsedHand,
    *,
    file_path: Path | None = None,
    policy: PhhCorpusPolicy | None = None,
) -> bool:
    """Return False to skip upsert for this PHH hand."""
    pol = policy or policy_from_env()
    rel = ""
    if file_path is not None:
        rel = file_path.as_posix()

    if pol.exclude_paths and rel and _path_hits_exclude(rel, pol.exclude_paths):
        return False
    if pol.cash_only and rel and is_mtt_like_path(rel):
        return False
    if pol.exclude_obfuscated and rel and is_obfuscated_path(rel):
        return False

    from poker_ai.ingest.records import total_ante_amount

    ante_total = total_ante_amount(hand)
    if pol.min_total_ante is not None and ante_total < pol.min_total_ante:
        return False
    if pol.max_total_ante is not None and ante_total > pol.max_total_ante:
        return False
    return True
