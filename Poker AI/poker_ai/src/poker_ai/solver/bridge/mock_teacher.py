"""Mock GTO teacher using Phase 4 equity (no TexasSolver binary required)."""

from __future__ import annotations

from poker_ai.core.cards import parse_card
from poker_ai.equity.mc import mc_equity_range_vs_range
from poker_ai.features.range import one_hot_range, uniform_range
from poker_ai.solver.abstraction import BET_FRACTIONS
from poker_ai.solver.bridge.cache import cache_key
from poker_ai.solver.bridge.schemas import STUDENT_ACTIONS, SolvedSpot, SpotSpec


def _board_ints(board: str) -> tuple[int, ...]:
    norm = board.replace(",", " ").strip()
    parts = [p.strip() for p in norm.split() if p.strip()]
    return tuple(parse_card(p) for p in parts)


def _representative_equity(spec: SpotSpec) -> float:
    """Hero (IP) equity vs OOP uniform-ish range on the flop board."""
    board = _board_ints(spec.normalized_board())
    if len(board) < 3:
        return 0.5
    # Use a strong IP combo proxy when ranges are textual — median over a few combos.
    samples = ("As", "Ah"), ("Kd", "Kc"), ("Qh", "Qs"), ("Jc", "Td"), ("9s", "8s")
    vals: list[float] = []
    opp = uniform_range()
    for a, b in samples:
        try:
            hero = one_hot_range(parse_card(a), parse_card(b))
        except ValueError:
            continue
        if len(board) >= 5:
            from poker_ai.equity import equity_range_vs_range

            vals.append(float(equity_range_vs_range(hero, opp, board)))
        else:
            vals.append(
                float(
                    mc_equity_range_vs_range(
                        hero,
                        opp,
                        board,
                        n_samples=400,
                        seed=hash(spec.normalized_board()) & 0xFFFF,
                    )
                )
            )
    return sum(vals) / len(vals) if vals else 0.5


def mock_strategy(spec: SpotSpec) -> tuple[tuple[str, ...], tuple[float, ...]]:
    """Map equity + SPR to abstract action frequencies (teacher labels)."""
    eq = _representative_equity(spec)
    spr = spec.effective_stack / max(1, spec.pot_chips)
    labels = STUDENT_ACTIONS
    fold_p, check_p, b33, b66, allin_p = 0.04, 0.36, 0.28, 0.22, 0.10
    if eq < 0.38:
        fold_p, check_p, b33, b66, allin_p = 0.42, 0.38, 0.12, 0.06, 0.02
    elif eq < 0.52:
        fold_p, check_p, b33, b66, allin_p = 0.12, 0.48, 0.22, 0.14, 0.04
    elif eq > 0.68:
        fold_p, check_p, b33, b66, allin_p = 0.02, 0.18, 0.30, 0.28, 0.22
    if spr < 3:
        allin_p = min(0.45, allin_p + 0.12)
        check_p = max(0.05, check_p - 0.08)
    mass = [fold_p, check_p, b33, b66, allin_p]
    s = sum(mass)
    freqs = tuple(m / s for m in mass)
    _ = BET_FRACTIONS  # aligned abstraction reference
    return labels, freqs


def solve_mock(spec: SpotSpec) -> SolvedSpot:
    from poker_ai.solver.bridge.cache import ranges_hash

    labels, freqs = mock_strategy(spec)
    key = cache_key(spec)
    return SolvedSpot(
        cache_key=key,
        board=spec.normalized_board(),
        sizing_tree_id=spec.sizing_tree_id,
        ranges_hash=ranges_hash(spec.range_oop, spec.range_ip),
        action_labels=labels,
        frequencies=freqs,
        backend="mock",
        meta={
            "equity_proxy": _representative_equity(spec),
            "spr": spec.effective_stack / max(1, spec.pot_chips),
        },
    )
