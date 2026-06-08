"""Canonical NLH seat labels (BTN, SB, BB, UTG, …) for store rows."""

from __future__ import annotations

import re

# Clockwise from the button for each table size (PHH / OHH-style inference).
POSITION_RING: dict[int, tuple[str, ...]] = {
    2: ("BTN", "BB"),
    3: ("BTN", "SB", "BB"),
    4: ("BTN", "SB", "BB", "UTG"),
    5: ("BTN", "SB", "BB", "UTG", "CO"),
    6: ("BTN", "SB", "BB", "UTG", "MP", "CO"),
    7: ("BTN", "SB", "BB", "UTG", "MP", "HJ", "CO"),
    8: ("BTN", "SB", "BB", "UTG", "UTG1", "MP", "HJ", "CO"),
    9: ("BTN", "SB", "BB", "UTG", "UTG1", "MP", "LJ", "HJ", "CO"),
    10: ("BTN", "SB", "BB", "UTG", "UTG1", "MP", "MP1", "LJ", "HJ", "CO"),
}

# Imported HH often labels seats differently (e.g. 4-max ``CO`` instead of ``UTG``).
_RING_SLOT_ALIASES: dict[int, dict[str, tuple[str, ...]]] = {
    4: {"UTG": ("UTG", "CO")},
    5: {"UTG": ("UTG", "MP", "UTG1")},
    6: {"UTG": ("UTG", "MP"), "MP": ("MP", "UTG", "HJ")},
}


def ring_slot_candidates(canonical: str, n: int) -> tuple[str, ...]:
    """Labels to try when mapping stored positions onto ``POSITION_RING[n]``."""
    per_table = _RING_SLOT_ALIASES.get(n, {})
    if canonical in per_table:
        return per_table[canonical]
    return (canonical,)


def physical_clockwise_pids(seat_to_pid: dict[int, int], n: int) -> list[int]:
    """Physical seat numbers increase clockwise; return ``player_id``s in that order."""
    if not seat_to_pid or len(seat_to_pid) != n:
        return list(range(1, n + 1))
    seats_sorted = sorted(seat_to_pid.keys())
    return [seat_to_pid[s] for s in seats_sorted]


def infer_sb_bb_pids(blinds: list[float], n: int) -> tuple[int, int] | None:
    """First two consecutive positive blinds in ``players`` list order → SB, BB ``player_id``."""
    for i in range(max(0, n - 1)):
        b0, b1 = float(blinds[i] or 0.0), float(blinds[i + 1] or 0.0)
        if b0 > 0 and b1 > 0 and b0 < b1:
            return i + 1, i + 2
    return None


def infer_button_pid(phys_order: list[int], sb_pid: int, n: int) -> int | None:
    """Button is immediately before SB clockwise; HU uses BTN = SB seat."""
    if n == 2:
        return sb_pid
    if sb_pid not in phys_order:
        return None
    i = phys_order.index(sb_pid)
    return phys_order[(i - 1) % len(phys_order)]


def ring_starting_button(phys_order: list[int], btn_pid: int) -> list[int]:
    """Clockwise ``player_id`` ring with the button first."""
    if btn_pid not in phys_order:
        return phys_order[:]
    k = phys_order.index(btn_pid)
    return phys_order[k:] + phys_order[:k]


def phh_position_label(
    *,
    n: int,
    player_id: int,
    blinds: list[float],
    seat_to_pid: dict[int, int],
) -> str:
    """Map PHH ``player_id`` to ``BTN`` / ``SB`` / … using blinds + seat layout."""
    if n < 2 or n > 10:
        return f"S{player_id}"
    ring_names = POSITION_RING.get(n)
    if ring_names is None:
        return f"S{player_id}"
    pair = infer_sb_bb_pids(blinds, n)
    if pair is None:
        return f"S{player_id}"
    sb_pid, _bb_pid = pair
    phys = physical_clockwise_pids(seat_to_pid, n)
    btn = infer_button_pid(phys, sb_pid, n)
    if btn is None:
        return f"S{player_id}"
    order = ring_starting_button(phys, btn)
    try:
        idx = order.index(player_id)
    except ValueError:
        return f"S{player_id}"
    if idx >= len(ring_names):
        return f"S{player_id}"
    return ring_names[idx]


def ohh_position_label(
    *,
    n: int,
    seat_num: int,
    phys_order: list[int],
    sb_seat: int | None,
    bb_seat: int | None,
) -> str:
    """Map OHH seat index (1..n in sorted-seat order) to canonical label."""
    if n < 2 or n > 10 or sb_seat is None or bb_seat is None:
        return f"S{seat_num}"
    ring_names = POSITION_RING.get(n)
    if ring_names is None or sb_seat not in phys_order:
        return f"S{seat_num}"
    btn = infer_button_pid(phys_order, sb_seat, n)
    if btn is None:
        return f"S{seat_num}"
    order = ring_starting_button(phys_order, btn)
    try:
        idx = order.index(seat_num)
    except ValueError:
        return f"S{seat_num}"
    if idx >= len(ring_names):
        return f"S{seat_num}"
    return ring_names[idx]


_HERO_BTN = re.compile(r"hero\s*\(\s*([^)]*)\s*\)", re.IGNORECASE)


def normalize_text_position(label: str) -> str:
    """Normalize normalized-text / PokerStars-style labels to a short token."""
    s = label.strip()
    if not s:
        return s
    m = _HERO_BTN.match(s)
    if m:
        inner = m.group(1).strip().upper()
        return inner if inner else "BTN"
    s_up = s.upper().replace(" ", "")
    return s_up.replace("UTG+1", "UTG1").replace("UTG+2", "UTG2")
