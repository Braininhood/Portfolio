"""Load hero decisions from ``play_hands`` for NN / student training (Phase W7)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Literal

from poker_ai.config.settings import get_settings

PlayStudyRoute = Literal["hu", "multiway"]

_POSTFLOP_STREETS = frozenset({"flop", "turn", "river"})


@dataclass(frozen=True, slots=True)
class PlayStudyDecision:
    """One hero decision point from an interactive play-vs-AI hand."""

    session_id: str
    hand_no: int
    street: str
    action: str
    label: str
    pot_bb: float
    is_all_in: bool
    hero_cards: str | None
    board: str | None
    result_bb: float
    went_showdown: bool
    bot_lineup: dict[str, str | None]
    table_config: dict[str, Any]
    n_active: int


def sqlite_db_path() -> Path:
    url = get_settings().database_url
    if "+aiosqlite" in url:
        raw = url.split("///", 1)[-1]
        return Path(raw)
    if url.startswith("sqlite:///"):
        return Path(url.removeprefix("sqlite:///"))
    msg = f"Unsupported database URL for play study loader: {url}"
    raise ValueError(msg)


def _parse_json(raw: Any) -> dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(str(raw))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def play_study_route(dec: PlayStudyDecision) -> PlayStudyRoute | None:
    """HU student when 2 active; multi-way student on postflop with 3+ active."""
    if dec.n_active == 2:
        return "hu"
    if dec.n_active >= 3 and dec.street.lower() in _POSTFLOP_STREETS:
        return "multiway"
    return None


def iter_play_study_decisions(
    db_path: Path | None = None,
    *,
    session_ids: tuple[str, ...] | None = None,
    route: PlayStudyRoute | None = None,
) -> Iterator[PlayStudyDecision]:
    """Stream hero decision rows from ``play_hands`` (source of truth in DB)."""
    path = db_path or sqlite_db_path()
    if not path.is_file():
        return

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        sql = (
            "SELECT ph.session_id, ph.hand_no, ph.result_bb, ph.went_showdown, "
            "ph.board, ph.hero_cards, ph.summary_json, ps.table_config_json "
            "FROM play_hands ph "
            "JOIN play_sessions ps ON ps.session_id = ph.session_id "
        )
        params: list[Any] = []
        if session_ids:
            placeholders = ",".join("?" for _ in session_ids)
            sql += f"WHERE ph.session_id IN ({placeholders}) "
            params.extend(session_ids)
        sql += "ORDER BY ph.session_id, ph.hand_no"

        for row in conn.execute(sql, params):
            summary = _parse_json(row["summary_json"])
            record = summary.get("hand_record") or summary
            table_config = _parse_json(row["table_config_json"])
            if summary.get("table_config"):
                table_config = {**table_config, **summary["table_config"]}
            hero_seat = int(table_config.get("user_seat") or 0)
            bot_lineup = record.get("bot_lineup") or {}
            if isinstance(bot_lineup, dict):
                lineup = {str(k): v for k, v in bot_lineup.items()}
            else:
                lineup = {}

            action_log = [e for e in (record.get("action_log") or []) if isinstance(e, dict)]
            seats_in_hand: set[int] = {hero_seat}
            for entry in action_log:
                seats_in_hand.add(int(entry.get("seat", -1)))
            for k in lineup:
                try:
                    seats_in_hand.add(int(k))
                except ValueError:
                    pass

            folded: set[int] = set()
            for entry in action_log:
                seat = int(entry.get("seat", -1))
                street = str(entry.get("street") or "preflop")
                n_active = max(2, len(seats_in_hand - folded))

                if seat == hero_seat:
                    dec = PlayStudyDecision(
                        session_id=str(row["session_id"]),
                        hand_no=int(row["hand_no"]),
                        street=street,
                        action=str(entry.get("action") or ""),
                        label=str(entry.get("label") or ""),
                        pot_bb=float(entry.get("pot_bb") or 0.0),
                        is_all_in=bool(entry.get("is_all_in")),
                        hero_cards=row["hero_cards"],
                        board=row["board"],
                        result_bb=float(row["result_bb"]),
                        went_showdown=bool(row["went_showdown"]),
                        bot_lineup=lineup,
                        table_config=table_config,
                        n_active=n_active,
                    )
                    r = play_study_route(dec)
                    if route is None:
                        yield dec
                    elif r == route:
                        yield dec

                if str(entry.get("action") or "").lower() == "fold":
                    folded.add(seat)
    finally:
        conn.close()


def collect_play_study_stats(
    db_path: Path | None = None,
    *,
    session_ids: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Aggregate counts for UI / training manifest."""
    path = db_path or sqlite_db_path()
    if not path.is_file():
        return {
            "database_path": str(path),
            "database_exists": False,
            "sessions": 0,
            "hands": 0,
            "hero_decisions": 0,
            "hero_decisions_hu": 0,
            "hero_decisions_multiway": 0,
            "hero_decisions_skipped": 0,
            "showdown_hands": 0,
        }

    conn = sqlite3.connect(path)
    try:
        session_filter = ""
        params: list[Any] = []
        if session_ids:
            placeholders = ",".join("?" for _ in session_ids)
            session_filter = f" AND session_id IN ({placeholders})"
            params = list(session_ids)

        hands = conn.execute(
            f"SELECT COUNT(*) FROM play_hands WHERE 1=1{session_filter}",
            params,
        ).fetchone()[0]
        showdowns = conn.execute(
            f"SELECT COUNT(*) FROM play_hands WHERE went_showdown = 1{session_filter}",
            params,
        ).fetchone()[0]
        if session_ids:
            sessions = len(session_ids)
        else:
            sessions = conn.execute("SELECT COUNT(DISTINCT session_id) FROM play_hands").fetchone()[0]
    finally:
        conn.close()

    hu = multiway = skipped = 0
    for dec in iter_play_study_decisions(path, session_ids=session_ids, route=None):
        r = play_study_route(dec)
        if r == "hu":
            hu += 1
        elif r == "multiway":
            multiway += 1
        else:
            skipped += 1

    return {
        "database_path": str(path.resolve()),
        "database_exists": True,
        "sessions": int(sessions),
        "hands": int(hands),
        "hero_decisions": hu + multiway + skipped,
        "hero_decisions_hu": hu,
        "hero_decisions_multiway": multiway,
        "hero_decisions_skipped": skipped,
        "showdown_hands": int(showdowns),
    }


def write_play_study_manifest(
    out_dir: Path,
    *,
    db_path: Path | None = None,
    session_ids: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Write ``manifest.json`` pointing at DB rows (no duplicate hand dump required)."""
    stats = collect_play_study_stats(db_path, session_ids=session_ids)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": 2,
        "source": "play_hands",
        "storage": "sqlite",
        "loader_module": "poker_ai.learn.play_study_loader",
        "loader_fn": "iter_play_study_decisions",
        "routing": {
            "hu": "train_student → artifacts/student/play_study_hu_v1",
            "multiway": "train_multiway_student → artifacts/student/play_study_multiway_v1",
        },
        **stats,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"manifest_path": str(manifest_path.resolve()), **manifest}


def _hero_action_to_target_freqs(dec: PlayStudyDecision) -> tuple[float, ...]:
    """Map hero action to STUDENT_ACTIONS one-hot (behavioral clone from play sessions)."""
    from poker_ai.solver.bridge.schemas import STUDENT_ACTIONS

    n = len(STUDENT_ACTIONS)
    freqs = [0.0] * n
    action = dec.action.lower()
    label = dec.label.lower()
    if action == "fold":
        freqs[0] = 1.0
    elif action in ("check", "call"):
        freqs[1] = 1.0
    elif action == "all_in" or "all-in" in label or "all in" in label:
        freqs[4] = 1.0
    elif action in ("bet", "raise"):
        if "1/3" in label:
            freqs[2] = 1.0
        elif "2/3" in label or "pot" in label:
            freqs[3] = 1.0
        elif dec.pot_bb <= 4:
            freqs[2] = 1.0
        else:
            freqs[3] = 1.0
    else:
        freqs[1] = 1.0
    return tuple(freqs)


def _decision_to_student_row(dec: PlayStudyDecision) -> Any | None:
    """Convert one play-vs-AI hero decision to a StudentRow for train_student (HU)."""
    from poker_ai.core.cards import parse_card
    from poker_ai.features.board_texture import texture_int16
    from poker_ai.features.hhformer_tokens import encode_hand_sequence
    from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer
    from poker_ai.learn.student_dataset import StudentRow
    from poker_ai.models.student import encode_state_extras

    if not dec.hero_cards or play_study_route(dec) != "hu":
        return None

    board_parts = [p.strip() for p in (dec.board or "").split() if p.strip()]
    street_key = dec.street.lower()
    street_name = {"preflop": "Preflop", "flop": "Flop", "turn": "Turn", "river": "River"}.get(
        street_key,
        "Preflop",
    )
    act_map = {
        "fold": "Fold",
        "check": "Check",
        "call": "Call",
        "bet": "Bet",
        "raise": "Raise",
        "all_in": "All-in",
    }
    hero_act = act_map.get(dec.action.lower(), "Call")
    amount = max(dec.pot_bb * 2.0, 2.0)

    actions: list[ParsedAction] = [
        ParsedAction(
            player_id=1,
            position="BTN",
            street="Preflop",
            action_type="Raise",
            amount=20.0,
            is_all_in=False,
            effective_stack=100.0,
            pot_before=10.0,
            pot_after=20.0,
            bet_to_pot_ratio=2.0,
        ),
        ParsedAction(
            player_id=2,
            position="BB",
            street="Preflop",
            action_type="Call",
            amount=20.0,
            is_all_in=False,
            effective_stack=100.0,
            pot_before=20.0,
            pot_after=40.0,
            bet_to_pot_ratio=None,
        ),
    ]
    if len(board_parts) >= 3 and street_key != "preflop":
        actions.append(
            ParsedAction(
                player_id=2,
                position="BB",
                street="Flop",
                action_type="Check",
                amount=0.0,
                is_all_in=False,
                effective_stack=90.0,
                pot_before=40.0,
                pot_after=40.0,
                bet_to_pot_ratio=None,
            )
        )
    actions.append(
        ParsedAction(
            player_id=1,
            position="BTN",
            street=street_name,
            action_type=hero_act,
            amount=amount,
            is_all_in=dec.is_all_in,
            effective_stack=90.0,
            pot_before=max(dec.pot_bb * 10.0, 10.0),
            pot_after=max(dec.pot_bb * 10.0, 10.0),
            bet_to_pot_ratio=amount / max(dec.pot_bb * 10.0, 10.0) if amount > 0 else None,
        )
    )

    players = (
        ParsedPlayer(1, "BTN", 100.0, 100.0, True, "hero", dec.hero_cards),
        ParsedPlayer(2, "BB", 100.0, 100.0, False, "villain", None),
    )
    hid = abs(hash(f"{dec.session_id}:{dec.hand_no}:{dec.street}:{dec.action}")) % (2**31 - 1)
    hand = ParsedHand(
        hand_id=hid,
        stakes="0.5/1.0",
        game_type="NLH",
        num_players=2,
        small_blind=5.0,
        big_blind=10.0,
        hero_position="BTN",
        hero_cards=dec.hero_cards,
        board_cards=" ".join(board_parts) if board_parts else None,
        pot_preflop=20.0,
        pot_flop=40.0 if len(board_parts) >= 3 else 0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=players,
        actions=tuple(actions),
    )
    tokens = encode_hand_sequence(hand).token_ids
    board_ints = tuple(parse_card(p) for p in board_parts) if board_parts else ()
    tex = texture_int16(board_ints)
    pot_chips = int(max(dec.pot_bb * 10, 10))
    extras = encode_state_extras(
        hero_is_ip=True,
        effective_stack=95,
        pot_chips=pot_chips,
        board_texture=tex,
        sizing_tree_id="play_study",
    )
    cache_key = f"play:{dec.session_id}:{dec.hand_no}:{street_key}:{dec.action}"
    return StudentRow(
        token_ids=tuple(tokens),
        state_extras=extras,
        target_freqs=_hero_action_to_target_freqs(dec),
        cache_key=cache_key,
    )


def _decision_to_multiway_row(dec: PlayStudyDecision) -> Any | None:
    """Convert one play decision to MultiwayRow (3+ active, postflop)."""
    from poker_ai.core.cards import parse_card
    from poker_ai.features.board_texture import texture_int16
    from poker_ai.features.hhformer_tokens import encode_hand_sequence
    from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer
    from poker_ai.learn.multiway_dataset import MultiwayRow, _action_to_target_freq
    from poker_ai.models.multiway_student import encode_multiway_extras

    if not dec.hero_cards or play_study_route(dec) != "multiway":
        return None

    board_parts = [p.strip() for p in (dec.board or "").split() if p.strip()]
    if len(board_parts) < 3:
        return None

    street_key = dec.street.lower()
    street_name = {"flop": "Flop", "turn": "Turn", "river": "River"}.get(street_key, "Flop")
    act_map = {
        "fold": "Fold",
        "check": "Check",
        "call": "Call",
        "bet": "Bet",
        "raise": "Raise",
        "all_in": "All-in",
    }
    hero_act = act_map.get(dec.action.lower(), "Call")
    amount = max(dec.pot_bb * 2.0, 2.0)
    num_seats = int(dec.table_config.get("seats") or max(dec.n_active, 2))

    players: list[ParsedPlayer] = [
        ParsedPlayer(1, "BTN", 100.0, 100.0, True, "hero", dec.hero_cards),
    ]
    for i in range(2, dec.n_active + 1):
        bot_name = dec.bot_lineup.get(str(i - 1)) or dec.bot_lineup.get(str(i)) or f"bot_{i}"
        players.append(
            ParsedPlayer(i, f"S{i}", 100.0, 100.0, False, str(bot_name), None),
        )
    while len(players) < dec.n_active:
        players.append(
            ParsedPlayer(len(players) + 1, f"S{len(players)+1}", 100.0, 100.0, False, "villain", None),
        )

    pa = ParsedAction(
        player_id=1,
        position="BTN",
        street=street_name,
        action_type=hero_act,
        amount=amount,
        is_all_in=dec.is_all_in,
        effective_stack=90.0,
        pot_before=max(dec.pot_bb * 10.0, 10.0),
        pot_after=max(dec.pot_bb * 10.0, 10.0),
        bet_to_pot_ratio=amount / max(dec.pot_bb * 10.0, 10.0) if amount > 0 else None,
    )
    hid = abs(hash(f"mw:{dec.session_id}:{dec.hand_no}:{dec.street}:{dec.action}")) % (2**31 - 1)
    hand = ParsedHand(
        hand_id=hid,
        stakes="0.5/1.0",
        game_type="NLH",
        num_players=max(dec.n_active, num_seats),
        small_blind=5.0,
        big_blind=10.0,
        hero_position="BTN",
        hero_cards=dec.hero_cards,
        board_cards=" ".join(board_parts),
        pot_preflop=20.0,
        pot_flop=40.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=tuple(players[: dec.n_active]),
        actions=(pa,),
    )
    seq = encode_hand_sequence(hand)
    board_ints = tuple(parse_card(p) for p in board_parts)
    tex = texture_int16(board_ints)
    pot_chips = int(max(dec.pot_bb * 10, 10))
    extras = encode_multiway_extras(
        hero_is_ip=False,
        effective_stack=90,
        pot_chips=pot_chips,
        board_texture=tex,
        n_active=dec.n_active,
        num_seats=num_seats,
    )
    return MultiwayRow(
        token_ids=tuple(seq.token_ids),
        state_extras=extras,
        target_freqs=_action_to_target_freq(pa),
        hand_id=hid,
        n_active=dec.n_active,
    )


def load_play_study_student_rows(
    *,
    db_path: Path | None = None,
    manifest_path: Path | None = None,
    session_ids: tuple[str, ...] | None = None,
) -> list[Any]:
    """Load HU StudentRow list from play_hands (``n_active == 2``)."""
    path = db_path
    if manifest_path and manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not path:
            path = Path(str(manifest.get("database_path", "")))
        if session_ids is None and manifest.get("session_ids"):
            session_ids = tuple(str(x) for x in manifest["session_ids"])

    rows: list[Any] = []
    for dec in iter_play_study_decisions(path, session_ids=session_ids, route="hu"):
        row = _decision_to_student_row(dec)
        if row is not None:
            rows.append(row)
    return rows


def collect_play_opponent_stats(
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Aggregate villain/bot action stats from play_hands for profiles + BOCPD."""
    path = db_path or sqlite_db_path()
    if not path.is_file():
        return []

    by_bot: dict[str, dict[str, Any]] = {}

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        for row in conn.execute(
            "SELECT ph.summary_json, ps.table_config_json FROM play_hands ph "
            "JOIN play_sessions ps ON ps.session_id = ph.session_id"
        ):
            summary = _parse_json(row["summary_json"])
            record = summary.get("hand_record") or summary
            table_config = _parse_json(row["table_config_json"])
            hero_seat = int(table_config.get("user_seat") or 0)
            lineup = record.get("bot_lineup") or {}
            if not isinstance(lineup, dict):
                lineup = {}

            half = 0
            log = record.get("action_log") or []
            mid = len(log) // 2

            for i, entry in enumerate(log):
                if not isinstance(entry, dict):
                    continue
                seat = int(entry.get("seat", -1))
                if seat == hero_seat:
                    continue
                bot_key = str(lineup.get(str(seat)) or lineup.get(seat) or f"seat_{seat}")
                uid = f"play_bot:{bot_key}"
                st = by_bot.setdefault(
                    uid,
                    {
                        "player_uid": uid,
                        "display_name": bot_key.replace("_", " ").title(),
                        "source": "play",
                        "decisions": 0,
                        "bets_raises": 0,
                        "calls_checks": 0,
                        "early_bets": 0,
                        "early_calls": 0,
                        "late_bets": 0,
                        "late_calls": 0,
                    },
                )
                st["decisions"] += 1
                act = str(entry.get("action") or "").lower()
                is_agg = act in ("bet", "raise", "all_in")
                is_pass = act in ("call", "check")
                if is_agg:
                    st["bets_raises"] += 1
                if is_pass:
                    st["calls_checks"] += 1
                if i < mid:
                    if is_agg:
                        st["early_bets"] += 1
                    if is_pass:
                        st["early_calls"] += 1
                else:
                    if is_agg:
                        st["late_bets"] += 1
                    if is_pass:
                        st["late_calls"] += 1
    finally:
        conn.close()

    out: list[dict[str, Any]] = []
    for st in by_bot.values():
        d = max(int(st["decisions"]), 1)
        st["vpip_pct"] = round(100.0 * (st["bets_raises"] + st["calls_checks"]) / d, 1)
        st["pfr_pct"] = round(100.0 * st["bets_raises"] / d, 1)
        ec = max(st["early_calls"], 1)
        lc = max(st["late_calls"], 1)
        st["af_early"] = round(st["early_bets"] / ec, 2)
        st["af_late"] = round(st["late_bets"] / lc, 2)
        st["aggression_factor"] = round(st["bets_raises"] / max(st["calls_checks"], 1), 2)
        out.append(st)
    return sorted(out, key=lambda x: -int(x["decisions"]))


def load_play_study_multiway_rows(
    *,
    db_path: Path | None = None,
    manifest_path: Path | None = None,
    session_ids: tuple[str, ...] | None = None,
) -> list[Any]:
    """Load MultiwayRow list from play_hands (``n_active >= 3``, postflop)."""
    path = db_path
    if manifest_path and manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not path:
            path = Path(str(manifest.get("database_path", "")))
        if session_ids is None and manifest.get("session_ids"):
            session_ids = tuple(str(x) for x in manifest["session_ids"])

    rows: list[Any] = []
    for dec in iter_play_study_decisions(path, session_ids=session_ids, route="multiway"):
        row = _decision_to_multiway_row(dec)
        if row is not None:
            rows.append(row)
    return rows
