"""Terminal payoffs for abstract preflop (bucket or real combo strength)."""

from __future__ import annotations

from poker_ai.features.range import combo_at_index
from poker_ai.solver.abstraction import bucket_midpoint


def showdown_payoffs(
    *,
    num_players: int,
    active: list[bool],
    bets: list[int],
    pot: int,
    buckets: tuple[int, ...],
    combos: tuple[int, ...] | None,
    use_combos: bool,
) -> tuple[float, ...]:
    live = [i for i, a in enumerate(active) if a]
    if len(live) == 1:
        return _award_pot(num_players, bets, pot, winner=live[0])
    if use_combos and combos is not None and len(live) == 2:
        return _hu_combo_showdown(num_players, live[0], live[1], bets, pot, combos)
    return _bucket_showdown(num_players, live, bets, pot, buckets)


def _award_pot(num_players: int, bets: list[int], pot: int, *, winner: int) -> tuple[float, ...]:
    out = [-float(bets[i]) for i in range(num_players)]
    out[winner] += float(pot) - float(bets[winner])
    return tuple(out)


def _bucket_showdown(
    num_players: int,
    live: list[int],
    bets: list[int],
    pot: int,
    buckets: tuple[int, ...],
) -> tuple[float, ...]:
    strengths = [bucket_midpoint(buckets[i]) for i in live]
    best = max(strengths)
    winners = [i for i in live if bucket_midpoint(buckets[i]) >= best - 1e-9]
    share = float(pot) / float(len(winners))
    out = [-float(bets[i]) for i in range(num_players)]
    for w in winners:
        out[w] += share
    return tuple(out)


def _hu_combo_showdown(
    num_players: int,
    seat_a: int,
    seat_b: int,
    bets: list[int],
    pot: int,
    combos: tuple[int, ...],
) -> tuple[float, ...]:
    from poker_ai.equity.mc import mc_equity_hands

    lo_a, hi_a = combo_at_index(combos[seat_a])
    lo_b, hi_b = combo_at_index(combos[seat_b])
    seed = (combos[seat_a] * 1327 + combos[seat_b]) % (2**31 - 1)
    eq_a = float(
        mc_equity_hands(
            (lo_a, hi_a),
            (lo_b, hi_b),
            (),
            n_samples=400,
            seed=seed,
        )
    )
    out = [-float(bets[i]) for i in range(num_players)]
    out[seat_a] += eq_a * float(pot)
    out[seat_b] += (1.0 - eq_a) * float(pot)
    return tuple(out)
