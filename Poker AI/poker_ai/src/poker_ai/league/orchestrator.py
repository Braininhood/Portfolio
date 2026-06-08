"""League match scheduler — HU + multi-way formats, promotion gates (Phase 9)."""

from __future__ import annotations

import json
import random
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from collections.abc import Callable
from typing import Any, TypedDict, cast

from poker_ai.runtime.progress import ProgressFn

from poker_ai.league.agents.registry import LeagueAgent, build_default_roster
from poker_ai.league.evaluator import (
    LeagueBoard,
    aivat_one_sample_pvalue,
    leaderboard_rows,
    league_chip_balance,
    promotion_significant,
    record_hand,
)
from poker_ai.league.formats import TableFormat, formats_from_seats
from poker_ai.league.matchup_worker import (
    MatchupSpec,
    _worker_init,
    merge_hand_records,
    run_matchup,
)
from poker_ai.league.sim import HandResult, new_table_hand, play_hand


class LeaderboardRow(TypedDict):
    agent_id: str
    elo: float
    hands: int
    bb_per_100: float
    aivat_bb_per_100: float


class LeagueReport(TypedDict, total=False):
    finished_at: str
    schedule: str
    hands_played: int
    matchups: int
    wall_sec: float
    target_wall_sec: float | None
    workers: int
    promoted: bool
    promotion_pvalue: float
    chip_balance: int
    big_blind_chips: int
    formats: list[str]
    brain_switches_total: int
    hu_decisions_total: int
    multiway_decisions_total: int
    leaderboard: list[LeaderboardRow]


@dataclass(frozen=True, slots=True)
class LeagueConfig:
    hands_per_matchup: int = 200
    max_wall_sec: float | None = None
    """Wall-clock cap. In round-robin mode, stop when done or cap hit."""

    run_until_wall: bool = False
    """If True, keep scheduling random matchups until ``max_wall_sec`` elapses."""

    until_multiway_only: bool = True
    """In until mode, only ring tables (≥3 seats) unless ``until_include_hu``."""

    until_include_hu: bool = False
    """In until mode, include HU when True (overrides ``until_multiway_only``)."""

    seed: int = 42
    stack_bb: float = 100.0
    report_path: Path = Path("reports/league_leaderboard.json")
    promote_elo_delta: float = 25.0
    min_hands_for_promotion: int = 1000
    promotion_alpha: float = 0.05
    table_sizes: tuple[int, ...] = (2, 6, 9)
    workers: int = 1
    use_style_vectors: bool = True


@dataclass
class LeagueRunResult:
    hands_played: int
    matchups: int
    wall_sec: float
    main_elo: float
    main_aivat_bb100: float
    main_aivat_pvalue: float
    promoted: bool
    report_path: Path
    brain_switches_total: int = 0
    formats_played: tuple[str, ...] = ()
    workers: int = 1


def _formats_for_schedule(
    formats: tuple[TableFormat, ...], *, cfg: LeagueConfig
) -> tuple[TableFormat, ...]:
    if not cfg.run_until_wall:
        return formats
    if cfg.until_include_hu:
        return formats
    if cfg.until_multiway_only:
        mw = tuple(f for f in formats if f.num_seats >= 3)
        if mw:
            return mw
    return formats


def _random_pair(agents: list[LeagueAgent], rng: random.Random) -> tuple[str, str]:
    i, j = rng.sample(range(len(agents)), 2)
    return agents[i].agent_id, agents[j].agent_id


def _random_matchup_spec(
    *,
    aid: str,
    bid: str,
    fmt: TableFormat,
    batch_hands: int,
    seed: int,
    stack_bb: float,
) -> MatchupSpec:
    return MatchupSpec(
        agent_a_id=aid,
        agent_b_id=bid,
        hands_per_format=(batch_hands,),
        format_seats=(fmt.num_seats,),
        format_ids=(fmt.format_id,),
        seed=seed,
        stack_bb=stack_bb,
    )


def _round_robin_pairs(agents: list[LeagueAgent]) -> list[tuple[str, str]]:
    ids = [a.agent_id for a in agents]
    pairs: list[tuple[str, str]] = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            pairs.append((ids[i], ids[j]))
    return pairs


def _hands_per_format(total: int, n_formats: int) -> list[int]:
    base = total // n_formats
    rem = total % n_formats
    return [base + (1 if i < rem else 0) for i in range(n_formats)]


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


def _play_one_hand(
    *,
    fmt: TableFormat,
    a: LeagueAgent,
    b: LeagueAgent,
    rng: random.Random,
    stack_bb: float,
    use_styles: bool = True,
) -> tuple[HandResult, int, int]:
    if fmt.num_seats == 2:
        seat_plan = [(0, a), (1, b)]
    else:
        seat_plan = _seat_plan_multiway(fmt, a, b)
    seed = rng.randint(0, 2**31 - 1)
    state = new_table_hand(num_seats=fmt.num_seats, seed=seed, stack_bb=stack_bb)
    bb = state.big_blind
    policies = [ag.policy for _, ag in seat_plan]
    profiles = [ag.profile for _, ag in seat_plan]
    opp_by_seat = None
    if use_styles:
        from poker_ai.league.style_bridge import load_persisted_style_map, styles_by_seat

        style_map = load_persisted_style_map()
        if style_map:
            seat_ids = [ag.agent_id for _, ag in seat_plan]
            opp_by_seat = styles_by_seat(fmt.num_seats, seat_ids, style_map)
    result = play_hand(state, policies, profiles, rng, opponent_styles_by_seat=opp_by_seat)
    win = result.winner_seat if result.winner_seat in (0, 1) else None
    scored = HandResult(
        deltas=(result.deltas[0], result.deltas[1]),
        went_showdown=result.went_showdown,
        winner_seat=win,
        starting_stacks=result.starting_stacks[:2],
        num_seats=2,
        hu_decisions=result.hu_decisions,
        multiway_decisions=result.multiway_decisions,
        brain_switches=result.brain_switches,
        max_active_seen=result.max_active_seen,
    )
    field_delta = sum(result.deltas[s] for s in range(2, fmt.num_seats)) if fmt.num_seats > 2 else 0
    return scored, bb, field_delta


def _league_emit(
    *,
    progress: ProgressFn,
    cfg: LeagueConfig,
    t0: float,
    hands_played: int,
    matchups: int,
    msg: str,
) -> None:
    if not progress:
        return
    pct = 0
    if cfg.max_wall_sec is not None and cfg.max_wall_sec > 0:
        pct = min(99, int(100 * (time.perf_counter() - t0) / cfg.max_wall_sec))
    elif cfg.hands_per_matchup > 0:
        pct = min(99, int(100 * hands_played / max(cfg.hands_per_matchup * 4, 1)))
    progress(
        {
            "pct": pct,
            "msg": msg,
            "detail": {
                "hands_played": hands_played,
                "matchups": matchups,
                "elapsed_sec": round(time.perf_counter() - t0, 1),
            },
        }
    )


def _run_serial(
    agents: list[LeagueAgent],
    *,
    cfg: LeagueConfig,
    formats: tuple[TableFormat, ...],
    per_fmt_hands: list[int],
    board: LeagueBoard,
    t0: float,
    progress: ProgressFn = None,
    cancel_check: Callable[[], bool] | None = None,
) -> tuple[int, int, int, int, int, int]:
    agent_by_id = {a.agent_id: a for a in agents}
    pairs = _round_robin_pairs(agents)
    rng = random.Random(cfg.seed)
    hands_played = 0
    matchups = 0
    bb = 100
    brain_switches_total = 0
    hu_decisions_total = 0
    multiway_decisions_total = 0

    for aid, bid in pairs:
        if cancel_check and cancel_check():
            break
        if cfg.max_wall_sec is not None and (time.perf_counter() - t0) >= cfg.max_wall_sec:
            break
        matchups += 1
        a, b = agent_by_id[aid], agent_by_id[bid]
        for fmt, n_hands in zip(formats, per_fmt_hands, strict=True):
            if n_hands <= 0:
                continue
            for _ in range(n_hands):
                if cancel_check and cancel_check():
                    break
                if cfg.max_wall_sec is not None and (time.perf_counter() - t0) >= cfg.max_wall_sec:
                    break
                scored, bb, field_delta = _play_one_hand(
                    fmt=fmt,
                    a=a,
                    b=b,
                    rng=rng,
                    stack_bb=cfg.stack_bb,
                    use_styles=cfg.use_style_vectors,
                )
                record_hand(
                    board,
                    a.agent_id,
                    b.agent_id,
                    scored,
                    big_blind=bb,
                    format_id=fmt.format_id,
                )
                if field_delta != 0:
                    field_rec = board.ensure("_field")
                    field_rec.hands += 1
                    field_rec.chips_won += field_delta
                hands_played += 1
                brain_switches_total += scored.brain_switches
                hu_decisions_total += scored.hu_decisions
                multiway_decisions_total += scored.multiway_decisions
                if progress and hands_played % 250 == 0:
                    _league_emit(
                        progress=progress,
                        cfg=cfg,
                        t0=t0,
                        hands_played=hands_played,
                        matchups=matchups,
                        msg=f"League: {hands_played} hands ({aid} vs {bid})",
                    )

    return (
        hands_played,
        matchups,
        brain_switches_total,
        hu_decisions_total,
        multiway_decisions_total,
        bb,
    )


def _run_parallel(
    agents: list[LeagueAgent],
    *,
    cfg: LeagueConfig,
    formats: tuple[TableFormat, ...],
    per_fmt_hands: list[int],
    board: LeagueBoard,
    t0: float,
    progress: ProgressFn = None,
    cancel_check: Callable[[], bool] | None = None,
) -> tuple[int, int, int, int, int, int]:
    pairs = _round_robin_pairs(agents)
    fmt_seats = tuple(f.num_seats for f in formats)
    fmt_ids = tuple(f.format_id for f in formats)
    hands_tuple = tuple(per_fmt_hands)
    specs: list[MatchupSpec] = []
    rng = random.Random(cfg.seed)
    for i, (aid, bid) in enumerate(pairs):
        specs.append(
            MatchupSpec(
                agent_a_id=aid,
                agent_b_id=bid,
                hands_per_format=hands_tuple,
                format_seats=fmt_seats,
                format_ids=fmt_ids,
                seed=rng.randint(0, 2**31 - 1) + i,
                stack_bb=cfg.stack_bb,
            )
        )

    hands_played = 0
    matchups = 0
    brain_switches_total = 0
    hu_decisions_total = 0
    multiway_decisions_total = 0
    bb = 100
    nw = max(1, cfg.workers)

    with ProcessPoolExecutor(max_workers=nw, initializer=_worker_init) as pool:
        futures = {pool.submit(run_matchup, spec): spec for spec in specs}
        while futures:
            if cancel_check and cancel_check():
                for fut in list(futures):
                    fut.cancel()
                break
            if cfg.max_wall_sec is not None and (time.perf_counter() - t0) >= cfg.max_wall_sec:
                for fut in list(futures):
                    fut.cancel()
                break
            done, _ = wait(futures, timeout=0.2, return_when=FIRST_COMPLETED)
            if not done and cfg.max_wall_sec is None:
                done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for fut in done:
                futures.pop(fut, None)
                result = fut.result()
                bs, hu, mw, n = merge_hand_records(board, result.records)
                hands_played += n
                brain_switches_total += bs
                hu_decisions_total += hu
                multiway_decisions_total += mw
                matchups += 1
                if result.records:
                    bb = result.records[-1].big_blind
                if progress and hands_played % 500 == 0:
                    _league_emit(
                        progress=progress,
                        cfg=cfg,
                        t0=t0,
                        hands_played=hands_played,
                        matchups=matchups,
                        msg=f"League parallel: {hands_played} hands",
                    )

    return (
        hands_played,
        matchups,
        brain_switches_total,
        hu_decisions_total,
        multiway_decisions_total,
        bb,
    )


def _run_until_wall_serial(
    agents: list[LeagueAgent],
    *,
    cfg: LeagueConfig,
    formats: tuple[TableFormat, ...],
    board: LeagueBoard,
    t0: float,
    progress: ProgressFn = None,
    cancel_check: Callable[[], bool] | None = None,
) -> tuple[int, int, int, int, int, int]:
    agent_by_id = {a.agent_id: a for a in agents}
    rng = random.Random(cfg.seed)
    hands_played = 0
    matchups = 0
    bb = 100
    brain_switches_total = 0
    hu_decisions_total = 0
    multiway_decisions_total = 0
    batch = max(1, cfg.hands_per_matchup)
    assert cfg.max_wall_sec is not None

    while (time.perf_counter() - t0) < cfg.max_wall_sec:
        if cancel_check and cancel_check():
            break
        aid, bid = _random_pair(agents, rng)
        a, b = agent_by_id[aid], agent_by_id[bid]
        fmt = rng.choice(formats)
        matchups += 1
        for _ in range(batch):
            if cancel_check and cancel_check():
                break
            if (time.perf_counter() - t0) >= cfg.max_wall_sec:
                break
            scored, bb, field_delta = _play_one_hand(
                fmt=fmt,
                a=a,
                b=b,
                rng=rng,
                stack_bb=cfg.stack_bb,
                use_styles=cfg.use_style_vectors,
            )
            record_hand(
                board,
                a.agent_id,
                b.agent_id,
                scored,
                big_blind=bb,
                format_id=fmt.format_id,
            )
            if field_delta != 0:
                field_rec = board.ensure("_field")
                field_rec.hands += 1
                field_rec.chips_won += field_delta
            hands_played += 1
            brain_switches_total += scored.brain_switches
            hu_decisions_total += scored.hu_decisions
            multiway_decisions_total += scored.multiway_decisions
            if progress and hands_played % 250 == 0:
                _league_emit(
                    progress=progress,
                    cfg=cfg,
                    t0=t0,
                    hands_played=hands_played,
                    matchups=matchups,
                    msg=f"League until-wall: {hands_played} hands",
                )

    return (
        hands_played,
        matchups,
        brain_switches_total,
        hu_decisions_total,
        multiway_decisions_total,
        bb,
    )


def _run_until_wall_parallel(
    agents: list[LeagueAgent],
    *,
    cfg: LeagueConfig,
    formats: tuple[TableFormat, ...],
    board: LeagueBoard,
    t0: float,
    progress: ProgressFn = None,
    cancel_check: Callable[[], bool] | None = None,
) -> tuple[int, int, int, int, int, int]:
    assert cfg.max_wall_sec is not None
    rng = random.Random(cfg.seed)
    batch = max(1, cfg.hands_per_matchup)
    nw = max(1, cfg.workers)
    max_inflight = nw * 2
    spec_seq = 0

    hands_played = 0
    matchups = 0
    brain_switches_total = 0
    hu_decisions_total = 0
    multiway_decisions_total = 0
    bb = 100

    def _next_spec() -> MatchupSpec:
        nonlocal spec_seq
        aid, bid = _random_pair(agents, rng)
        fmt = rng.choice(formats)
        spec = _random_matchup_spec(
            aid=aid,
            bid=bid,
            fmt=fmt,
            batch_hands=batch,
            seed=rng.randint(0, 2**31 - 1) + spec_seq,
            stack_bb=cfg.stack_bb,
        )
        spec_seq += 1
        return spec

    def _consume_done(done_set: set[Any]) -> None:
        nonlocal hands_played, matchups, brain_switches_total, hu_decisions_total
        nonlocal multiway_decisions_total, bb
        for fut in done_set:
            futures.pop(fut, None)
            result = fut.result()
            bs, hu, mw, n = merge_hand_records(board, result.records)
            hands_played += n
            brain_switches_total += bs
            hu_decisions_total += hu
            multiway_decisions_total += mw
            matchups += 1
            if result.records:
                bb = result.records[-1].big_blind

    with ProcessPoolExecutor(max_workers=nw, initializer=_worker_init) as pool:
        futures: dict[Any, None] = {}
        while True:
            if cancel_check and cancel_check():
                for fut in list(futures):
                    fut.cancel()
                break
            elapsed = time.perf_counter() - t0
            submit_more = elapsed < cfg.max_wall_sec
            while submit_more and len(futures) < max_inflight:
                futures[pool.submit(run_matchup, _next_spec())] = None
                elapsed = time.perf_counter() - t0
            if not futures:
                break
            done, _ = wait(futures, timeout=0.2, return_when=FIRST_COMPLETED)
            if done:
                _consume_done(done)
            if not submit_more and not futures:
                break

    return (
        hands_played,
        matchups,
        brain_switches_total,
        hu_decisions_total,
        multiway_decisions_total,
        bb,
    )


def run_league(
    roster: list[LeagueAgent] | None = None,
    *,
    cfg: LeagueConfig | None = None,
    progress: ProgressFn = None,
    cancel_check: Callable[[], bool] | None = None,
) -> LeagueRunResult:
    """Round-robin or until-wall random matchups; optional parallel workers."""
    cfg = cfg or LeagueConfig()
    agents = roster if roster is not None else build_default_roster()
    if cfg.use_style_vectors:
        from poker_ai.league.style_bridge import persist_league_style_map

        persist_league_style_map(agents)
    formats = _formats_for_schedule(formats_from_seats(cfg.table_sizes), cfg=cfg)
    if not formats:
        msg = "no table formats selected for league run"
        raise ValueError(msg)
    board = LeagueBoard()
    for ag in agents:
        rec = board.ensure(ag.agent_id)
        rec.elo = ag.elo

    per_fmt_hands = _hands_per_format(cfg.hands_per_matchup, len(formats))
    t0 = time.perf_counter()
    nw = max(1, cfg.workers)
    schedule = "until_wall" if cfg.run_until_wall else "round_robin"

    if cfg.run_until_wall:
        if cfg.max_wall_sec is None:
            msg = "run_until_wall requires max_wall_sec"
            raise ValueError(msg)
        if nw <= 1 or len(agents) < 2:
            (
                hands_played,
                matchups,
                brain_switches_total,
                hu_decisions_total,
                multiway_decisions_total,
                bb,
            ) = _run_until_wall_serial(
                agents,
                cfg=cfg,
                formats=formats,
                board=board,
                t0=t0,
                progress=progress,
                cancel_check=cancel_check,
            )
        else:
            (
                hands_played,
                matchups,
                brain_switches_total,
                hu_decisions_total,
                multiway_decisions_total,
                bb,
            ) = _run_until_wall_parallel(
                agents,
                cfg=cfg,
                formats=formats,
                board=board,
                t0=t0,
                progress=progress,
                cancel_check=cancel_check,
            )
    elif nw <= 1 or len(agents) < 2:
        (
            hands_played,
            matchups,
            brain_switches_total,
            hu_decisions_total,
            multiway_decisions_total,
            bb,
        ) = _run_serial(
            agents,
            cfg=cfg,
            formats=formats,
            per_fmt_hands=per_fmt_hands,
            board=board,
            t0=t0,
            progress=progress,
            cancel_check=cancel_check,
        )
    else:
        (
            hands_played,
            matchups,
            brain_switches_total,
            hu_decisions_total,
            multiway_decisions_total,
            bb,
        ) = _run_parallel(
            agents,
            cfg=cfg,
            formats=formats,
            per_fmt_hands=per_fmt_hands,
            board=board,
            t0=t0,
            progress=progress,
            cancel_check=cancel_check,
        )

    main = board.ensure("main_agent")
    start_elo = 1500.0
    aivat_ok = promotion_significant(
        main,
        min_hands=cfg.min_hands_for_promotion,
        alpha=cfg.promotion_alpha,
    )
    promoted = (
        main.hands >= cfg.min_hands_for_promotion
        and main.elo >= start_elo + cfg.promote_elo_delta
        and aivat_ok
        and all(
            board.ensure(b.agent_id).elo < main.elo
            for b in agents
            if b.role == "frozen" and b.agent_id != "main_agent"
        )
    )

    balance = league_chip_balance(board)
    wall_sec = time.perf_counter() - t0
    report: LeagueReport = {
        "finished_at": datetime.now(tz=UTC).isoformat(),
        "schedule": schedule,
        "hands_played": hands_played,
        "matchups": matchups,
        "wall_sec": wall_sec,
        "target_wall_sec": cfg.max_wall_sec,
        "workers": nw,
        "promoted": promoted,
        "promotion_pvalue": round(aivat_one_sample_pvalue(main), 4),
        "chip_balance": balance,
        "big_blind_chips": bb,
        "formats": [f.format_id for f in formats],
        "brain_switches_total": brain_switches_total,
        "hu_decisions_total": hu_decisions_total,
        "multiway_decisions_total": multiway_decisions_total,
        "leaderboard": cast(list[LeaderboardRow], leaderboard_rows(board, big_blind=bb)),
    }
    cfg.report_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if promoted:
        from poker_ai.league.checkpoint_registry import register_checkpoint

        register_checkpoint(
            main_elo=main.elo,
            hands=main.hands,
            promoted=True,
            student_hu=Path("artifacts/student/v1"),
            student_multiway=Path("artifacts/student/multiway_v1"),
            note=f"league {schedule} hands={hands_played}",
        )

    return LeagueRunResult(
        hands_played=hands_played,
        matchups=matchups,
        wall_sec=wall_sec,
        main_elo=main.elo,
        main_aivat_bb100=main.aivat_bb_per_100,
        main_aivat_pvalue=aivat_one_sample_pvalue(main),
        promoted=promoted,
        report_path=cfg.report_path,
        brain_switches_total=brain_switches_total,
        formats_played=tuple(f.format_id for f in formats),
        workers=nw,
    )


def load_leaderboard(path: Path) -> LeagueReport:
    if not path.is_file():
        return {"leaderboard": []}
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {"leaderboard": []}
    rows = raw.get("leaderboard", [])
    if not isinstance(rows, list):
        return {"leaderboard": []}
    return cast(LeagueReport, raw)
