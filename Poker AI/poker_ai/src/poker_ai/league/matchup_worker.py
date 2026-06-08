"""Process-pool workers for parallel league matchups (Phase 9)."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from poker_ai.league.agents.registry import LeagueAgent, build_default_roster
from poker_ai.league.formats import TableFormat, formats_from_seats
from poker_ai.league.sim import HandResult, new_table_hand, play_hand

_worker_agents: dict[str, LeagueAgent] | None = None
_worker_use_styles: bool = True


def _worker_init() -> None:
    global _worker_agents
    roster = build_default_roster()
    _worker_agents = {a.agent_id: a for a in roster}


@dataclass(frozen=True, slots=True)
class MatchupSpec:
    """Picklable unit of work: one agent pair, fixed hand budget."""

    agent_a_id: str
    agent_b_id: str
    hands_per_format: tuple[int, ...]
    format_seats: tuple[int, ...]
    format_ids: tuple[str, ...]
    seed: int
    stack_bb: float


@dataclass(frozen=True, slots=True)
class HandRecord:
    agent_a_id: str
    agent_b_id: str
    delta_a: int
    delta_b: int
    went_showdown: bool
    winner_seat: int | None
    format_id: str
    big_blind: int
    field_delta: int
    brain_switches: int
    hu_decisions: int
    multiway_decisions: int


@dataclass(frozen=True, slots=True)
class MatchupWorkResult:
    records: tuple[HandRecord, ...]
    hands_played: int


def _seat_plan_multiway(
    fmt: TableFormat, a: LeagueAgent, b: LeagueAgent
) -> list[tuple[int, LeagueAgent]]:
    from poker_ai.league.agents.baselines import CallStationPolicy
    from poker_ai.league.agents.registry import LeagueAgent as LA

    n = fmt.num_seats
    ghost = LA("_ghost", "ghost", CallStationPolicy(), a.profile)
    plan: list[tuple[int, LeagueAgent]] = [(0, a), (1, b)]
    for seat in range(2, n):
        plan.append((seat, ghost))
    return plan


def run_matchup(spec: MatchupSpec) -> MatchupWorkResult:
    """Play one round-robin matchup (all formats); policies loaded once per process."""
    if _worker_agents is None:
        _worker_init()
    assert _worker_agents is not None
    a = _worker_agents[spec.agent_a_id]
    b = _worker_agents[spec.agent_b_id]
    formats = formats_from_seats(spec.format_seats)
    fmt_ids = spec.format_ids
    rng = random.Random(spec.seed)
    records: list[HandRecord] = []
    hands = 0

    for fmt, n_hands, fid in zip(formats, spec.hands_per_format, fmt_ids, strict=True):
        if n_hands <= 0:
            continue
        for _ in range(n_hands):
            if fmt.num_seats == 2:
                seat_plan = [(0, a), (1, b)]
            else:
                seat_plan = _seat_plan_multiway(fmt, a, b)
            seed = rng.randint(0, 2**31 - 1)
            state = new_table_hand(
                num_seats=fmt.num_seats,
                seed=seed,
                stack_bb=spec.stack_bb,
            )
            bb = state.big_blind
            policies = [ag.policy for _, ag in seat_plan]
            profiles = [ag.profile for _, ag in seat_plan]
            opp_by_seat = None
            if _worker_use_styles:
                from poker_ai.league.style_bridge import load_persisted_style_map, styles_by_seat

                style_map = load_persisted_style_map()
                if style_map:
                    seat_ids = [ag.agent_id for _, ag in seat_plan]
                    opp_by_seat = styles_by_seat(fmt.num_seats, seat_ids, style_map)
            result = play_hand(
                state, policies, profiles, rng, opponent_styles_by_seat=opp_by_seat
            )
            win = result.winner_seat if result.winner_seat in (0, 1) else None
            field_delta = (
                sum(result.deltas[s] for s in range(2, fmt.num_seats)) if fmt.num_seats > 2 else 0
            )
            records.append(
                HandRecord(
                    agent_a_id=a.agent_id,
                    agent_b_id=b.agent_id,
                    delta_a=result.deltas[0],
                    delta_b=result.deltas[1],
                    went_showdown=result.went_showdown,
                    winner_seat=win,
                    format_id=fid,
                    big_blind=bb,
                    field_delta=field_delta,
                    brain_switches=result.brain_switches,
                    hu_decisions=result.hu_decisions,
                    multiway_decisions=result.multiway_decisions,
                )
            )
            hands += 1

    return MatchupWorkResult(records=tuple(records), hands_played=hands)


def merge_hand_records(
    board: Any,
    records: tuple[HandRecord, ...],
) -> tuple[int, int, int, int]:
    """Apply worker results to ``LeagueBoard``; return aggregate counters."""
    from poker_ai.league.evaluator import record_hand

    brain_sw = 0
    hu_dec = 0
    mw_dec = 0
    for rec in records:
        scored = HandResult(
            deltas=(rec.delta_a, rec.delta_b),
            went_showdown=rec.went_showdown,
            winner_seat=rec.winner_seat,
            num_seats=2,
            brain_switches=rec.brain_switches,
            hu_decisions=rec.hu_decisions,
            multiway_decisions=rec.multiway_decisions,
        )
        record_hand(
            board,
            rec.agent_a_id,
            rec.agent_b_id,
            scored,
            big_blind=rec.big_blind,
            format_id=rec.format_id,
        )
        if rec.field_delta != 0:
            field_rec = board.ensure("_field")
            field_rec.hands += 1
            field_rec.chips_won += rec.field_delta
        brain_sw += rec.brain_switches
        hu_dec += rec.hu_decisions
        mw_dec += rec.multiway_decisions
    return brain_sw, hu_dec, mw_dec, len(records)
