"""Elo + AIVAT-style EV tracking and promotion gates (Phase 9)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from poker_ai.league.sim import HandResult


@dataclass
class MatchStats:
    agent_a: str
    agent_b: str
    format_id: str = "hu"
    hands: int = 0
    chips_a: int = 0
    chips_b: int = 0
    aivat_chips_a: float = 0.0
    aivat_chips_b: float = 0.0
    showdowns: int = 0
    brain_switches: int = 0
    hu_decisions: int = 0
    multiway_decisions: int = 0


@dataclass
class AgentRecord:
    agent_id: str
    elo: float = 1500.0
    hands: int = 0
    chips_won: int = 0
    aivat_bb_per_100: float = 0.0
    aivat_adj_sum: float = 0.0
    aivat_adj_sum_sq: float = 0.0
    brain_switches: int = 0
    hu_decisions: int = 0
    multiway_decisions: int = 0
    by_format: dict[str, dict[str, float]] = field(default_factory=dict)


@dataclass
class LeagueBoard:
    """In-memory leaderboard."""

    agents: dict[str, AgentRecord] = field(default_factory=dict)
    matches: list[MatchStats] = field(default_factory=list)

    def ensure(self, agent_id: str) -> AgentRecord:
        if agent_id not in self.agents:
            self.agents[agent_id] = AgentRecord(agent_id=agent_id)
        return self.agents[agent_id]

    def update_elo(self, winner_id: str, loser_id: str, *, k: float = 32.0) -> None:
        a = self.ensure(winner_id)
        b = self.ensure(loser_id)
        ea = 1.0 / (1.0 + 10 ** ((b.elo - a.elo) / 400.0))
        eb = 1.0 - ea
        a.elo += k * (1.0 - ea)
        b.elo += k * (0.0 - eb)


def _aivat_adjusted_delta(
    delta_chips: int,
    *,
    went_showdown: bool,
    winner_seat: int | None,
    seat: int,
    big_blind: int,
) -> float:
    """AIVAT-adjusted chips — full corrections when ``POKER_AI_AIVAT_FULL=1``."""
    from poker_ai.eval.aivat import aivat_adjust_delta

    return aivat_adjust_delta(
        delta_chips,
        went_showdown=went_showdown,
        winner_seat=winner_seat,
        seat=seat,
        big_blind=big_blind,
    )


def _update_format_bucket(rec: AgentRecord, format_id: str, adj_bb: float) -> None:
    bucket = rec.by_format.setdefault(
        format_id,
        {"hands": 0.0, "aivat_bb_sum": 0.0},
    )
    bucket["hands"] += 1.0
    bucket["aivat_bb_sum"] += adj_bb


def record_hand(
    board: LeagueBoard,
    agent_a: str,
    agent_b: str,
    result: HandResult,
    *,
    big_blind: int,
    format_id: str = "hu",
    seat_agent_ids: tuple[str, ...] | None = None,
) -> None:
    """Record one hand; optional ``seat_agent_ids`` maps seat index → agent id (N-way)."""
    n = len(result.deltas)
    if seat_agent_ids is not None and len(seat_agent_ids) != n:
        msg = "seat_agent_ids length must match deltas"
        raise ValueError(msg)

    if seat_agent_ids is None:
        da, db = result.deltas[0], result.deltas[1]
        agents_seats = [(agent_a, 0, da), (agent_b, 1, db)]
    else:
        agents_seats = [(seat_agent_ids[s], s, result.deltas[s]) for s in range(n)]

    winner = result.winner_seat
    for aid, seat, delta in agents_seats:
        rec = board.ensure(aid)
        rec.hands += 1
        rec.chips_won += delta
        adj = _aivat_adjusted_delta(
            delta,
            went_showdown=result.went_showdown,
            winner_seat=winner,
            seat=seat,
            big_blind=big_blind,
        )
        adj_bb = adj / max(1, big_blind) * 100.0
        n_h = max(1, rec.hands)
        rec.aivat_bb_per_100 = (rec.aivat_bb_per_100 * (n_h - 1) + adj_bb) / n_h
        rec.aivat_adj_sum += adj_bb
        rec.aivat_adj_sum_sq += adj_bb * adj_bb
        rec.brain_switches += result.brain_switches
        rec.hu_decisions += result.hu_decisions
        rec.multiway_decisions += result.multiway_decisions
        _update_format_bucket(rec, format_id, adj_bb)

    if n == 2 and seat_agent_ids is None:
        da, db = result.deltas[0], result.deltas[1]
        if da > db:
            board.update_elo(agent_a, agent_b)
        elif db > da:
            board.update_elo(agent_b, agent_a)
    elif winner is not None and seat_agent_ids is not None:
        win_id = seat_agent_ids[winner]
        for aid, _, delta in agents_seats:
            if aid != win_id and delta < 0:
                board.update_elo(win_id, aid)


def bb_per_100(chips_won: int, hands: int, big_blind_chips: int) -> float:
    """Net win rate in big blinds per 100 hands (integer chip units)."""
    if hands <= 0 or big_blind_chips <= 0:
        return 0.0
    return float(chips_won) / float(big_blind_chips) / float(hands) * 100.0


def league_chip_balance(board: LeagueBoard) -> int:
    """Sum of all agents' ``chips_won`` (zero in a closed zero-sum league)."""
    return sum(rec.chips_won for rec in board.agents.values())


def aivat_one_sample_pvalue(rec: AgentRecord) -> float:
    """Two-sided p-value for mean AIVAT-adjusted BB/100 > 0 (normal approx)."""
    n = rec.hands
    if n < 2:
        return 1.0
    mean = rec.aivat_adj_sum / n
    var = max(1e-9, (rec.aivat_adj_sum_sq / n) - mean * mean)
    if var <= 0:
        return 1.0 if mean <= 0 else 0.0
    se = math.sqrt(var / n)
    if se <= 0:
        return 1.0 if mean <= 0 else 0.0
    z = mean / se
    return float(math.erfc(abs(z) / math.sqrt(2.0)))


def promotion_significant(
    rec: AgentRecord,
    *,
    min_hands: int = 1000,
    alpha: float = 0.05,
) -> bool:
    """ROADMAP gate: AIVAT-adjusted win rate significant at ``alpha`` over ``min_hands``."""
    if rec.hands < min_hands:
        return False
    return aivat_one_sample_pvalue(rec) < alpha and rec.aivat_bb_per_100 > 0


def leaderboard_rows(board: LeagueBoard, *, big_blind: int = 100) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rec in sorted(board.agents.values(), key=lambda r: r.elo, reverse=True):
        rows.append(
            {
                "agent_id": rec.agent_id,
                "elo": round(rec.elo, 1),
                "hands": rec.hands,
                "bb_per_100": round(bb_per_100(rec.chips_won, rec.hands, big_blind), 2),
                "aivat_bb_per_100": round(rec.aivat_bb_per_100, 2),
                "aivat_pvalue": round(aivat_one_sample_pvalue(rec), 4),
                "brain_switches": rec.brain_switches,
                "hu_decisions": rec.hu_decisions,
                "multiway_decisions": rec.multiway_decisions,
                "formats": {
                    fid: {
                        "hands": int(b["hands"]),
                        "aivat_bb_per_100": round(b["aivat_bb_sum"] / max(1.0, b["hands"]), 2),
                    }
                    for fid, b in rec.by_format.items()
                },
            }
        )
    return rows
