"""PHH / PHHS — ACPC / HandHQ / Pluribus-style key=value hand blocks (``variant = 'NT'``)."""

from __future__ import annotations

import ast
import re
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from poker_ai.ingest.canonical_id import INGEST_PHH, resolve_hand_id
from poker_ai.ingest.identity import player_uid_hmac
from poker_ai.ingest.positions import phh_position_label
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer, ParsedResult

_BLOCK_HEADER = re.compile(r"^\s*\[\d+\]\s*$")
_CARD_PAIR = re.compile(r"([2-9TJQKA])([shdc])", re.IGNORECASE)


def looks_like_phh_text(text: str) -> bool:
    """True when the buffer looks like PHH (``variant =`` … ``'NT'`` or ``\"NT\"``)."""
    head = text[:8000]
    if "variant" not in head or "actions" not in head:
        return False
    return bool(re.search(r"variant\s*=\s*['\"]NT['\"]", head, re.IGNORECASE))


def split_phh_blocks(text: str) -> list[str]:
    """Split ``.phhs`` concatenated ``[n]`` hands; a bare ``.phh`` yields a single block."""
    lines = text.splitlines()
    blocks: list[list[str]] = []
    cur: list[str] = []
    saw_bracket = False
    for line in lines:
        if _BLOCK_HEADER.match(line):
            saw_bracket = True
            if cur:
                blocks.append(cur)
            cur = []
            continue
        cur.append(line)
    if cur:
        blocks.append(cur)
    if not saw_bracket:
        return [text.strip()]
    return ["\n".join(b).strip() for b in blocks if any(x.strip() for x in b)]


def _parse_kv_block(block: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        try:
            out[key] = ast.literal_eval(val)
        except (ValueError, SyntaxError, MemoryError):
            out[key] = val.strip().strip("'\"")
    return out


def _card_tokens_from_phh_chunk(chunk: str) -> list[str]:
    return [f"{r}{s}".lower() for r, s in _CARD_PAIR.findall(chunk)]


def _phh_seat_to_player_id(n: int, seats: list[Any] | None) -> dict[int, int]:
    """Map PHH seat number (``pN`` in actions) → 1-based player index in ``players`` order."""
    if seats and len(seats) == n:
        out: dict[int, int] = {}
        for i in range(n):
            try:
                seat = int(seats[i])
            except (TypeError, ValueError):
                return {j: j for j in range(1, n + 1)}
            out[seat] = i + 1
        return out
    return {j: j for j in range(1, n + 1)}


def _hole_cards_from_deal_actions(
    actions: Sequence[Any],
    *,
    seat_to_pid: dict[int, int],
) -> dict[int, str]:
    """Known hole cards from ``d dh pN …`` (skip ``????`` obfuscation)."""
    out: dict[int, str] = {}
    for raw in actions:
        if not isinstance(raw, str):
            continue
        tok = raw.split()
        if len(tok) < 4 or tok[0] != "d" or tok[1] != "dh":
            continue
        if not tok[2].startswith("p"):
            continue
        try:
            seat = int(tok[2][1:])
        except ValueError:
            continue
        pid = seat_to_pid.get(seat)
        if pid is None:
            continue
        chunk = "".join(tok[3:])
        if "?" in chunk:
            continue
        cards = " ".join(_card_tokens_from_phh_chunk(chunk))
        if cards:
            out[pid] = cards
    return out


def _parse_actions_phh(
    actions: Sequence[Any],
    *,
    n_players: int,
    starting_stacks: list[float],
    blinds_or_straddles: list[float],
    antes: list[float],
    seat_to_pid: dict[int, int],
    position_for: Callable[[int], str] | None = None,
) -> tuple[
    list[ParsedAction],
    str | None,
    list[ParsedResult],
    tuple[float, float, float, float],
]:
    """Walk PHH ``actions`` tokens → ParsedAction rows; board from ``d db``; ``sm`` → results.

    Returns ``(actions, board, sm_results, (pot_preflop, pot_flop, pot_turn, pot_river))``.
    """
    pl = position_for or (lambda p: f"S{p}")
    street_commit: dict[int, float] = {i: 0.0 for i in range(1, n_players + 1)}
    max_on_street = 0.0
    pot = 0.0
    current_street = "Preflop"
    db_count = 0
    board_parts: list[str] = []
    actions_out: list[ParsedAction] = []
    sm_cards: dict[int, str] = {}
    pots_at_board: list[float] = []

    blinds = list(blinds_or_straddles[:n_players])
    while len(blinds) < n_players:
        blinds.append(0.0)
    blinds = [float(x or 0.0) for x in blinds]

    ante_list = list(antes[:n_players])
    while len(ante_list) < n_players:
        ante_list.append(0.0)
    ante_list = [float(x or 0.0) for x in ante_list]

    for i, blind in enumerate(blinds):
        blind_pid = i + 1
        b = float(blind or 0.0)
        if b > 0:
            street_commit[blind_pid] += b
            pot += b
            max_on_street = max(max_on_street, street_commit[blind_pid])

    for ante in ante_list:
        if ante > 0:
            pot += ante

    def eff_stack(pid: int) -> float:
        return float(starting_stacks[pid - 1])

    for raw in actions:
        if not isinstance(raw, str):
            continue
        tok = raw.split()
        if not tok:
            continue
        if tok[0] == "d" and len(tok) >= 2 and tok[1] == "dh":
            continue
        if tok[0] == "d" and len(tok) >= 2 and tok[1] == "db" and len(tok) >= 3:
            pots_at_board.append(pot)
            cards_part = "".join(tok[2:])
            board_parts.extend(_card_tokens_from_phh_chunk(cards_part))
            db_count += 1
            if db_count == 1:
                current_street = "Flop"
            elif db_count == 2:
                current_street = "Turn"
            else:
                current_street = "River"
            street_commit = {i: 0.0 for i in range(1, n_players + 1)}
            max_on_street = 0.0
            continue

        if not tok[0].startswith("p"):
            continue
        try:
            seat = int(tok[0][1:])
        except ValueError:
            continue
        pid = seat_to_pid.get(seat)
        if pid is None or pid < 1 or pid > n_players:
            continue

        verb = tok[1].lower()
        pos = pl(pid)

        if verb == "f":
            actions_out.append(
                ParsedAction(
                    player_id=pid,
                    position=pos,
                    street=current_street,
                    action_type="Fold",
                    amount=0.0,
                    is_all_in=False,
                    effective_stack=eff_stack(pid),
                    pot_before=pot,
                    pot_after=pot,
                    bet_to_pot_ratio=None,
                )
            )
            continue

        if verb == "cc":
            need = max_on_street - street_commit[pid]
            if need <= 1e-9:
                mapped, amt = "Check", 0.0
                pot_before = pot
                pot_after = pot
            else:
                mapped, amt = "Call", need
                pot_before = pot
                pot += need
                street_commit[pid] += need
                pot_after = pot
            actions_out.append(
                ParsedAction(
                    player_id=pid,
                    position=pos,
                    street=current_street,
                    action_type=mapped,
                    amount=amt,
                    is_all_in=False,
                    effective_stack=eff_stack(pid),
                    pot_before=pot_before,
                    pot_after=pot_after,
                    bet_to_pot_ratio=None,
                )
            )
            continue

        if verb == "cbr" and len(tok) >= 3:
            try:
                target = float(tok[2])
            except ValueError:
                continue
            prev_c = street_commit[pid]
            inc = max(0.0, target - prev_c)
            pot_before = pot
            prior_max = max_on_street
            pot += inc
            street_commit[pid] = target
            max_on_street = max(max_on_street, street_commit[pid])
            pot_after = pot
            if current_street == "Preflop":
                mapped = "Raise"
            else:
                mapped = "Bet" if prior_max < 1e-9 else "Raise"
            bet_to_pot = round(inc / pot_before, 4) if pot_before > 0 else None
            is_ai = "all" in raw.lower() and "in" in raw.lower()
            actions_out.append(
                ParsedAction(
                    player_id=pid,
                    position=pos,
                    street=current_street,
                    action_type=mapped,
                    amount=target,
                    is_all_in=is_ai,
                    effective_stack=eff_stack(pid),
                    pot_before=pot_before,
                    pot_after=pot_after,
                    bet_to_pot_ratio=bet_to_pot,
                )
            )
            continue

        if verb == "sm":
            if len(tok) >= 3:
                cards = " ".join(_card_tokens_from_phh_chunk("".join(tok[2:])))
            else:
                cards = ""
            sm_cards[pid] = cards
            continue

    pot_preflop = pot_flop = pot_turn = pot_river = 0.0
    if not pots_at_board:
        pot_preflop = pot
    else:
        pot_preflop = pots_at_board[0]
        if len(pots_at_board) >= 2:
            pot_flop = pots_at_board[1]
        if len(pots_at_board) >= 3:
            pot_turn = pots_at_board[2]
    pot_river = pot

    results: list[ParsedResult] = []
    for pid, cs in sm_cards.items():
        results.append(
            ParsedResult(
                player_id=pid,
                position=pl(pid),
                cards=cs,
                net_result=0.0,
                won_pot=0.0,
                showdown=True,
            )
        )

    board_joined = " ".join(board_parts) if board_parts else None
    return actions_out, board_joined, results, (pot_preflop, pot_flop, pot_turn, pot_river)


def _merge_finishing_results(
    players: list[str],
    starting: list[float],
    finishing: list[float] | None,
    base: list[ParsedResult],
    *,
    hole_by_pid: dict[int, str] | None = None,
    position_for: Callable[[int], str] | None = None,
) -> tuple[ParsedResult, ...]:
    pl = position_for or (lambda p: f"S{p}")
    sm_by = {r.player_id: r.cards for r in base}
    hole_by_pid = hole_by_pid or {}
    if not finishing or len(finishing) != len(players):
        # No stack deltas: still emit one row per seat with known hole cards from deal.
        if not base and hole_by_pid:
            return tuple(
                ParsedResult(
                    player_id=i + 1,
                    position=pl(i + 1),
                    cards=hole_by_pid.get(i + 1, ""),
                    net_result=0.0,
                    won_pot=0.0,
                    showdown=bool(hole_by_pid.get(i + 1)),
                )
                for i in range(len(players))
            )
        return tuple(base)
    out: list[ParsedResult] = []
    for i, _name in enumerate(players):
        pid = i + 1
        net = float(finishing[i]) - float(starting[i])
        cards = sm_by.get(pid, "") or hole_by_pid.get(pid, "")
        show = bool(cards) or abs(net) > 1e-6
        out.append(
            ParsedResult(
                player_id=pid,
                position=pl(pid),
                cards=cards,
                net_result=net,
                won_pot=max(0.0, net),
                showdown=show,
            )
        )
    return tuple(out)


def _coerce_float_list_n(val: Any, n: int) -> list[float] | None:
    if not isinstance(val, list) or len(val) != n:
        return None
    try:
        return [float(x) for x in val]
    except (TypeError, ValueError):
        return None


def _build_phh_results(
    *,
    n: int,
    players: list[str],
    stacks: list[float],
    data: dict[str, Any],
    sm_results: list[ParsedResult],
    hole_by: dict[int, str],
    position_for: Callable[[int], str] | None = None,
) -> tuple[ParsedResult, ...]:
    fin = _coerce_float_list_n(data.get("finishing_stacks"), n)
    if fin is not None:
        return _merge_finishing_results(
            players, stacks, fin, sm_results, hole_by_pid=hole_by, position_for=position_for
        )

    pay = _coerce_float_list_n(data.get("winnings"), n)
    if pay is None:
        pay = _coerce_float_list_n(data.get("_results"), n)
    if pay is not None:
        pl = position_for or (lambda p: f"S{p}")
        sm_cards = {r.player_id: r.cards for r in sm_results}
        return tuple(
            ParsedResult(
                player_id=i + 1,
                position=pl(i + 1),
                cards=sm_cards.get(i + 1, "") or hole_by.get(i + 1, ""),
                net_result=float(pay[i]),
                won_pot=max(0.0, float(pay[i])),
                showdown=bool(
                    sm_cards.get(i + 1) or hole_by.get(i + 1) or abs(float(pay[i])) > 1e-6
                ),
            )
            for i in range(n)
        )

    return _merge_finishing_results(
        players, stacks, None, sm_results, hole_by_pid=hole_by, position_for=position_for
    )


def parse_phh_block_dict(
    data: dict[str, Any],
    *,
    external_ref: str,
    uid_secret: str,
) -> ParsedHand | None:
    """One PHH hand from a parsed key-value dict."""
    variant = str(data.get("variant") or "").strip().upper()
    if variant != "NT":
        return None

    players = list(data.get("players") or [])
    if not players:
        return None

    n = int(data.get("seat_count") or len(players))
    n = min(n, len(players))
    players = players[:n]

    stacks = [float(x) for x in (data.get("starting_stacks") or [])][:n]
    if len(stacks) != n:
        return None

    seats_raw = data.get("seats")
    seats_list: list[Any] | None = list(seats_raw) if isinstance(seats_raw, list) else None
    seat_to_pid = _phh_seat_to_player_id(n, seats_list)

    blinds = list(data.get("blinds_or_straddles") or [])
    while len(blinds) < n:
        blinds.append(0.0)
    blinds = [float(x or 0.0) for x in blinds[:n]]
    sb = float(blinds[0]) if blinds else 0.0
    bb = float(blinds[1]) if len(blinds) > 1 else 0.0
    try:
        min_bet = float(data.get("min_bet") or 0.0)
    except (TypeError, ValueError):
        min_bet = 0.0
    if bb <= 0 and min_bet > 0:
        bb = min_bet
    if sb <= 0 < bb:
        sb = bb * 0.5
    if len(blinds) >= 2:
        blinds[0], blinds[1] = sb, bb

    def _position_for(pid: int) -> str:
        return phh_position_label(n=n, player_id=pid, blinds=blinds, seat_to_pid=seat_to_pid)

    antes_raw = data.get("antes")
    if isinstance(antes_raw, list):
        antes = [float(x or 0.0) for x in antes_raw[:n]]
    else:
        antes = [0.0] * n
    while len(antes) < n:
        antes.append(0.0)

    actions_raw = data.get("actions")
    if not isinstance(actions_raw, list):
        return None

    action_strs = [str(x) for x in actions_raw]
    hole_by = _hole_cards_from_deal_actions(action_strs, seat_to_pid=seat_to_pid)

    actions_list, board, sm_results, pots = _parse_actions_phh(
        action_strs,
        n_players=n,
        starting_stacks=stacks,
        blinds_or_straddles=blinds,
        antes=antes,
        seat_to_pid=seat_to_pid,
        position_for=_position_for,
    )

    results = _build_phh_results(
        n=n,
        players=players,
        stacks=stacks,
        data=data,
        sm_results=sm_results,
        hole_by=hole_by,
        position_for=_position_for,
    )

    hand_id = resolve_hand_id(INGEST_PHH, external_ref)

    players_out: list[ParsedPlayer] = []
    for i, name in enumerate(players):
        pid = i + 1
        stack = stacks[i]
        bb_size = stack / bb if bb > 0 else 0.0
        uid = player_uid_hmac(uid_secret, nickname=str(name), hand_id=hand_id, seat_player_id=pid)
        players_out.append(
            ParsedPlayer(
                player_id=pid,
                position=_position_for(pid),
                stack_size=stack,
                bb_size=bb_size,
                is_hero=False,
                player_uid=uid,
                screen_name=str(name) if name else None,
            )
        )

    antes_tpl = tuple(float(antes[i] or 0.0) for i in range(n))

    return ParsedHand(
        hand_id=hand_id,
        stakes=f"{sb}/{bb}",
        game_type="NLH",
        num_players=n,
        small_blind=sb,
        big_blind=bb,
        hero_position=None,
        hero_cards=None,
        board_cards=board,
        pot_preflop=pots[0],
        pot_flop=pots[1],
        pot_turn=pots[2],
        pot_river=pots[3],
        antes=antes_tpl,
        players=tuple(players_out),
        actions=tuple(actions_list),
        results=results,
        ingest_source=INGEST_PHH,
        external_ref=external_ref,
    )


def parse_phh_bytes(
    raw: bytes,
    *,
    path: Path,
    uid_secret: str,
) -> list[ParsedHand]:
    """Parse ``.phh`` / ``.phhs`` bytes into zero or more :class:`ParsedHand` rows."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return []
    if not looks_like_phh_text(text):
        return []

    rel_name = path.name
    out: list[ParsedHand] = []
    for bi, block in enumerate(split_phh_blocks(text)):
        data = _parse_kv_block(block)
        if not data:
            continue
        hand_key = data.get("hand")
        suffix = f"{hand_key}" if hand_key is not None else str(bi)
        external_ref = f"{rel_name}#{suffix}"
        ph = parse_phh_block_dict(data, external_ref=external_ref, uid_secret=uid_secret)
        if ph is not None:
            out.append(ph)
    return out


def parse_phh_path(path: Path, raw: bytes, *, uid_secret: str) -> list[ParsedHand]:
    """Convenience wrapper used by :mod:`poker_ai.ingest.service`."""
    return parse_phh_bytes(raw, path=path, uid_secret=uid_secret)
