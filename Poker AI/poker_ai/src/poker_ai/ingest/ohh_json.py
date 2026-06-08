"""Open Hand History (OHH) JSON — https://hh-specs.handhistory.org/"""

from __future__ import annotations

import json
from typing import Any

from poker_ai.ingest.antes import build_antes_tuple, merge_ante_post
from poker_ai.ingest.canonical_id import INGEST_OHH_JSON, resolve_hand_id
from poker_ai.ingest.identity import player_uid_hmac
from poker_ai.ingest.positions import ohh_position_label
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer, ParsedResult


def parse_ohh_json_bytes(raw: bytes, *, uid_secret: str) -> ParsedHand | None:
    """Parse UTF-8 JSON bytes into :class:`ParsedHand`."""
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return parse_ohh_dict(data, uid_secret=uid_secret)


def parse_ohh_dict(data: dict[str, Any], *, uid_secret: str) -> ParsedHand | None:
    """Map OHH 1.x structure to the canonical :class:`ParsedHand`."""
    ohh = data.get("ohh", data)
    if not isinstance(ohh, dict):
        return None

    game_number = str(ohh.get("game_number") or "0")
    hand_id = resolve_hand_id(INGEST_OHH_JSON, game_number)

    sb = float(ohh.get("small_blind_amount") or 0.0)
    bb = float(ohh.get("big_blind_amount") or 0.0)
    stakes = f"{sb}/{bb}"
    bet_type = (ohh.get("bet_limit") or {}).get("bet_type") or "NL"
    if str(bet_type).upper() != "NL":
        return None
    game_type = "NLH"

    players_raw = list(ohh.get("players") or [])
    if not players_raw:
        return None

    sorted_players = sorted(players_raw, key=lambda p: int(p.get("seat") or 0))
    ohh_id_to_seat: dict[int, int] = {}
    for i, p in enumerate(sorted_players, start=1):
        ohh_id_to_seat[int(p["id"])] = i

    hero_ohh_id = ohh.get("hero_player_id")
    hero_seat_num: int | None = None
    if hero_ohh_id is not None:
        hero_seat_num = ohh_id_to_seat.get(int(hero_ohh_id))

    rounds = list(ohh.get("rounds") or [])
    sb_seat_found: int | None = None
    bb_seat_found: int | None = None
    for rnd in rounds:
        if str(rnd.get("street") or "").lower() != "preflop":
            continue
        for act in rnd.get("actions") or []:
            if not isinstance(act, dict):
                continue
            lab = str(act.get("action") or "").strip().lower()
            ohh_pid = act.get("player_id")
            if ohh_pid is None:
                continue
            seat_idx = ohh_id_to_seat.get(int(ohh_pid))
            if seat_idx is None:
                continue
            if lab == "post sb":
                sb_seat_found = seat_idx
            elif lab == "post bb":
                bb_seat_found = seat_idx
        break

    n_players = len(sorted_players)
    phys_order = list(range(1, n_players + 1))

    def _seat_pos(seat_num: int) -> str:
        return ohh_position_label(
            n=n_players,
            seat_num=seat_num,
            phys_order=phys_order,
            sb_seat=sb_seat_found,
            bb_seat=bb_seat_found,
        )

    players_out: list[ParsedPlayer] = []
    for p in sorted_players:
        seat_num = ohh_id_to_seat[int(p["id"])]
        name = str(p.get("name") or "")
        is_hero = hero_seat_num is not None and seat_num == hero_seat_num
        # Stack in big blinds (same convention as PHH): starting_stack / big_blind.
        bb_size = float(p.get("starting_stack") or 0.0) / bb if bb > 0 else 0.0
        uid = player_uid_hmac(uid_secret, nickname=name, hand_id=hand_id, seat_player_id=seat_num)
        players_out.append(
            ParsedPlayer(
                player_id=seat_num,
                position=_seat_pos(seat_num),
                stack_size=float(p.get("starting_stack") or 0.0),
                bb_size=bb_size,
                is_hero=is_hero,
                player_uid=uid,
                screen_name=name or None,
            )
        )

    board_parts: list[str] = []
    actions_out: list[ParsedAction] = []
    results_out: list[ParsedResult] = []

    pot = sb + bb
    last_commit_to = bb
    hero_cards: str | None = None
    prev_street: str | None = None

    for rnd in rounds:
        street = str(rnd.get("street") or "Preflop")
        if prev_street is not None and street != prev_street:
            last_commit_to = 0.0
        prev_street = street
        for c in rnd.get("cards") or []:
            if isinstance(c, str):
                board_parts.append(c.lower())

        for act in rnd.get("actions") or []:
            if not isinstance(act, dict):
                continue
            label = str(act.get("action") or "")
            ohh_pid = act.get("player_id")
            if ohh_pid is None and label.lower() != "dealt cards":
                continue
            act_seat = ohh_id_to_seat.get(int(ohh_pid)) if ohh_pid is not None else None

            if label.lower() == "dealt cards" and act.get("cards"):
                cs = [str(x).lower() for x in act["cards"]]
                if len(cs) == 2 and act_seat == hero_seat_num:
                    hero_cards = " ".join(cs)
                continue
            if label.lower().startswith("post "):
                continue
            if label.lower() in ("shows cards", "mucks cards"):
                if act.get("cards") and act_seat is not None:
                    cs = [str(x).lower() for x in act["cards"]]
                    results_out.append(
                        ParsedResult(
                            player_id=act_seat,
                            position=_seat_pos(act_seat),
                            cards=" ".join(cs),
                            net_result=0.0,
                            won_pot=0.0,
                            showdown=True,
                        )
                    )
                continue

            mapped = _map_ohh_action(label)
            if mapped is None or act_seat is None:
                continue

            amt = float(act.get("amount") or 0.0)
            is_all_in = bool(act.get("is_allin") or act.get("is_all_in"))
            pos = _seat_pos(act_seat)
            stack = next(pl.stack_size for pl in players_out if pl.player_id == act_seat)

            pot_before = pot
            if mapped == "Raise":
                pot += max(0.0, amt - last_commit_to)
                last_commit_to = amt
            elif mapped == "Bet":
                pot += amt
                last_commit_to = amt
            elif mapped == "Call":
                pot += amt
            pot_after = pot

            actions_out.append(
                ParsedAction(
                    player_id=act_seat,
                    position=pos,
                    street=street,
                    action_type=mapped,
                    amount=amt,
                    is_all_in=is_all_in,
                    effective_stack=stack,
                    pot_before=pot_before,
                    pot_after=pot_after,
                    bet_to_pot_ratio=None,
                )
            )

    for pot_info in ohh.get("pots") or []:
        for w in pot_info.get("player_wins") or []:
            sid = int(w["player_id"])
            win_seat = ohh_id_to_seat.get(sid)
            if win_seat is None:
                continue
            win_amt = float(w.get("win_amount") or 0.0)
            # merge into results_out if showdown row exists
            updated = False
            for i, r in enumerate(results_out):
                if r.player_id == win_seat:
                    results_out[i] = ParsedResult(
                        player_id=r.player_id,
                        position=r.position,
                        cards=r.cards,
                        net_result=win_amt,
                        won_pot=win_amt,
                        showdown=r.showdown,
                    )
                    updated = True
                    break
            if not updated:
                results_out.append(
                    ParsedResult(
                        player_id=win_seat,
                        position=_seat_pos(win_seat),
                        cards="",
                        net_result=win_amt,
                        won_pot=win_amt,
                        showdown=True,
                    )
                )

    board_joined = " ".join(board_parts) if board_parts else None

    antes_by_pid: dict[int, float] = {}
    antes_raw = ohh.get("antes")
    if isinstance(antes_raw, list):
        for i, p in enumerate(sorted_players):
            if i >= len(antes_raw):
                break
            pid = ohh_id_to_seat.get(int(p["id"]))
            if pid is not None:
                merge_ante_post(antes_by_pid, pid, float(antes_raw[i] or 0.0))
    if not antes_by_pid:
        for rnd in rounds:
            if str(rnd.get("street") or "").lower() != "preflop":
                continue
            for act in rnd.get("actions") or []:
                if not isinstance(act, dict):
                    continue
                lab = str(act.get("action") or "").strip().lower()
                if "ante" not in lab or not lab.startswith("post"):
                    continue
                ohh_pid = act.get("player_id")
                if ohh_pid is None:
                    continue
                seat_idx = ohh_id_to_seat.get(int(ohh_pid))
                if seat_idx is None:
                    continue
                merge_ante_post(antes_by_pid, seat_idx, float(act.get("amount") or 0.0))
            break

    players_tpl = tuple(players_out)
    antes_tpl = build_antes_tuple(players_tpl, antes_by_pid)

    return ParsedHand(
        hand_id=hand_id,
        stakes=stakes,
        game_type=game_type,
        num_players=len(players_out),
        small_blind=sb,
        big_blind=bb,
        hero_position=_seat_pos(hero_seat_num) if hero_seat_num else None,
        hero_cards=hero_cards,
        board_cards=board_joined,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        antes=antes_tpl,
        players=players_tpl,
        actions=tuple(actions_out),
        results=tuple(results_out),
        ingest_source=INGEST_OHH_JSON,
        external_ref=game_number,
    )


def _map_ohh_action(label: str) -> str | None:
    key = label.strip().lower()
    if key == "fold":
        return "Fold"
    if key == "call":
        return "Call"
    if key == "raise":
        return "Raise"
    if key == "check":
        return "Check"
    if key == "bet":
        return "Bet"
    return None
