"""NLH header and 52-card sanity checks for normalized text hands."""

from __future__ import annotations

import re
from collections import Counter

_CARD_RE = re.compile(r"\b([2-9TJQKA])([cdhs])\b", re.IGNORECASE)


def is_normalized_nlh_header(head_line: str) -> bool:
    """True for converter ``NLH`` lines and ``No Limit Hold'em``-style exports (e.g. WPN)."""
    u = head_line.upper().replace("POT-LIMIT", "POT LIMIT")
    if "OMAHA" in u or re.search(r"\bPLO\b", u) or "POT LIMIT" in u:
        return False
    if "NLH" in u:
        return True
    if "NO LIMIT" in u and ("HOLD" in u or "HOLD'EM" in u or "HOLD EM" in u):
        return True
    return False


def _all_card_tokens(text: str) -> list[str]:
    """Collect card tokens, skipping ``Final Board:`` lines (they repeat street cards)."""
    out: list[str] = []
    for line in text.splitlines():
        ls = line.strip()
        if ls.lower().startswith("final board:"):
            continue
        out.extend(f"{r}{s}".lower() for r, s in _CARD_RE.findall(ls))
    return out


def normalized_nlh_card_integrity_ok(text: str) -> bool:
    """At most one physical copy of each card; hero preflop line has exactly two hole cards.

    Summaries often repeat hero hole cards on ``Hero showed X Y``; when ``X Y`` matches the
    preflop hero cards, that single repeat is ignored for duplicate detection.
    """
    hero_preflop: tuple[str, str] | None = None
    for line in text.splitlines():
        ls = line.strip()
        lu = ls.lower()
        if lu.startswith("preflop:") and "hero" in lu:
            ht = [f"{r}{s}".lower() for r, s in _CARD_RE.findall(ls)]
            if len(ht) != 2:
                return False
            hero_preflop = (ht[0], ht[1])
            break

    hero_show_repeats_preflop = False
    if hero_preflop is not None:
        want = sorted(hero_preflop)
        for line in text.splitlines():
            lu = line.strip().lower()
            if "hero" not in lu or "showed" not in lu:
                continue
            got = sorted([f"{r}{s}".lower() for r, s in _CARD_RE.findall(line)])
            if got == want:
                hero_show_repeats_preflop = True
                break

    toks = _all_card_tokens(text)
    cnt: Counter[str] = Counter(toks)
    if hero_preflop is not None and hero_show_repeats_preflop:
        a, b = hero_preflop
        if cnt[a] < 2 or cnt[b] < 2:  # pragma: no cover — inconsistent with matched showdown line
            return False
        cnt[a] -= 1
        cnt[b] -= 1

    if sum(cnt.values()) > 52:  # pragma: no cover — max 52 physical cards
        return False
    if any(v > 1 for v in cnt.values()):
        return False
    return True
