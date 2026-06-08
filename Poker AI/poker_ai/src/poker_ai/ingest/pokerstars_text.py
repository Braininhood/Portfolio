"""PokerStars-style and post-converter normalized text hands (see doc/HAND_HISTORY_FORMATS.md)."""

from __future__ import annotations

import re
from pathlib import Path

from poker_ai.ingest.antes import build_antes_tuple, scan_text_ante_posts
from poker_ai.ingest.canonical_id import (
    INGEST_NORMALIZED_TXT,
    INGEST_POKERSTARS_RAW_MINIMAL,
    resolve_hand_id,
)
from poker_ai.ingest.identity import player_uid_hmac
from poker_ai.ingest.nlh_validate import is_normalized_nlh_header, normalized_nlh_card_integrity_ok
from poker_ai.ingest.positions import normalize_text_position
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer, ParsedResult


def hand_id_from_path(path: Path) -> int | None:
    """Parse ``hand_<id>.txt`` filenames used by ``convert/`` output."""
    m = re.search(r"hand_(\d+)\.txt", path.name, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _convert_amount(amount_str: str | None) -> float:
    if not amount_str:
        return 0.0
    cleaned = amount_str.replace("$", "").replace(",", "").strip()
    return float(cleaned)


def _bb_float(bb_raw: str) -> float:
    return float(bb_raw.replace(",", ""))


_ACTION_VERB_RE = re.compile(
    r"\b(folds?|checks?|calls|bets|raises\s+to)\b",
    re.IGNORECASE,
)

# Amount after verb is optional so ``UTG folds`` / ``BB checks`` match (no trailing ``$``).
_NORMALIZED_SINGLE_ACTION_RE = re.compile(
    r"^(.+?)\s+(raises to|calls|bets|folds?|checks?)(?:\s+\$?(\d+(?:\.\d+)?))?",
    re.IGNORECASE,
)

_ACTION_VERB_TO_CANONICAL = {
    "bets": "Bet",
    "calls": "Call",
    "raises to": "Raise",
    "fold": "Fold",
    "folds": "Fold",
    "check": "Check",
    "checks": "Check",
}


def _comma_separated_action_fragments(line: str, *, is_seat_line: bool) -> list[str]:
    """Split ``A calls $x, B folds, …`` (WPN / CardRunners); else return one chunk."""
    s = line.strip()
    if not s or is_seat_line:
        return [s]
    if re.match(r"^(Flop|Turn|River|Final Board|Results)\b", s, re.IGNORECASE):
        return [s]
    if "," not in s or not _ACTION_VERB_RE.search(s):
        return [s]
    return [p.strip() for p in s.split(",") if p.strip()]


def looks_like_normalized_converter_text(first_line: str) -> bool:
    """Detect ``$SB/$BB, NLH`` or WPN / converter first lines."""
    return bool(re.match(r"^\s*(\$\d|WPN,)", first_line))


def looks_like_pokerstars_raw(text: str) -> bool:
    """Detect classic PokerStars export header."""
    return "PokerStars Hand #" in text[:800]


def parse_text(
    text: str,
    *,
    hand_id: int,
    uid_secret: str,
    default_screen_names: dict[str, str] | None = None,
    enforce_card_integrity: bool | None = None,
) -> ParsedHand | None:
    """Parse normalized block text (primary corpus) or minimal raw PS fragments.

    ``default_screen_names`` maps seat position label (e.g. ``\"BTN\"``) to a screen name when
    the text does not carry per-hand nicknames (legacy normalized files).
    """
    from poker_ai.config.settings import get_settings

    strict_cards = (
        enforce_card_integrity
        if enforce_card_integrity is not None
        else get_settings().strict_nlh_card_integrity
    )
    if looks_like_pokerstars_raw(text):
        return _parse_raw_pokerstars_minimal(text, hand_id=hand_id, uid_secret=uid_secret)
    return _parse_normalized_block(
        text,
        hand_id=hand_id,
        uid_secret=uid_secret,
        aliases=default_screen_names,
        enforce_card_integrity=strict_cards,
    )


def _parse_normalized_block(
    text: str,
    *,
    hand_id: int,
    uid_secret: str,
    aliases: dict[str, str] | None,
    enforce_card_integrity: bool,
) -> ParsedHand | None:
    lines = text.splitlines()
    if not lines:
        return None

    stakes_match = re.search(r"\$(\d+(?:\.\d+)?)/\$(\d+(?:\.\d+)?)", lines[0])
    if not stakes_match:
        return None

    head = lines[0]
    if not is_normalized_nlh_header(head):
        return None

    small_blind = _convert_amount(stakes_match.group(1))
    big_blind = _convert_amount(stakes_match.group(2))
    game_type = "NLH"
    players_match = re.search(r"(\d+)\s+Players", lines[0])
    num_players = int(players_match.group(1)) if players_match else 0
    stakes = f"{small_blind}/{big_blind}"

    player_id_map: dict[str, int] = {}
    player_id_counter = 1
    seat_rows: list[tuple[int, str, float, float, bool, str | None]] = []
    hero_position: str | None = None

    seat_re = re.compile(
        r"^Hero\s*\((\w+)\):\s*\$(\d+(?:\.\d+)?)\s*\((\d+[,.]?\d*) bb\)|"
        r"^(\w+):\s*\$(\d+(?:\.\d+)?)\s*\((\d+[,.]?\d*) bb\)"
    )
    for line in lines:
        player_match = seat_re.match(line.strip())
        if not player_match:
            continue
        if player_match.group(1):
            is_hero = True
            position = normalize_text_position(player_match.group(1))
            stack_size = _convert_amount(player_match.group(2))
            bb_size = _bb_float(player_match.group(3))
            hero_position = position
        else:
            is_hero = False
            position = normalize_text_position(player_match.group(4))
            stack_size = _convert_amount(player_match.group(5))
            bb_size = _bb_float(player_match.group(6))

        if position not in player_id_map:
            player_id_map[position] = player_id_counter
            player_id_counter += 1

        pid = player_id_map[position]
        screen = None
        if aliases and position in aliases:
            screen = aliases[position]
        seat_rows.append((pid, position, stack_size, bb_size, is_hero, screen))

    hero_cards: str | None = None
    for line in lines:
        if "Preflop" in line and "Hero" in line:
            hero_cards_match = re.search(
                r"Hero\s+([2-9TJQKA][cdhs])\s+([2-9TJQKA][cdhs])", line, re.IGNORECASE
            )
            if hero_cards_match:
                c1, c2 = hero_cards_match.group(1), hero_cards_match.group(2)
                hero_cards = f"{c1} {c2}".lower()
            else:
                alt = re.search(
                    r"with\s+([2-9TJQKA][cdhs])\s+([2-9TJQKA][cdhs])", line, re.IGNORECASE
                )
                if alt:
                    hero_cards = f"{alt.group(1)} {alt.group(2)}".lower()

    board_cards_dict: dict[str, str | None] = {"Flop": None, "Turn": None, "River": None}
    pot_sizes = {"Preflop": 0.0, "Flop": 0.0, "Turn": 0.0, "River": 0.0}

    for line in lines:
        flop_match = re.search(
            r"Flop:\s+\(\$?(\d+(?:\.\d+)?)\)\s+"
            r"([2-9TJQKA][cdhs]\s+[2-9TJQKA][cdhs]\s+[2-9TJQKA][cdhs])",
            line,
            re.IGNORECASE,
        )
        if flop_match and not board_cards_dict["Flop"]:
            pot_sizes["Flop"] = _convert_amount(flop_match.group(1))
            board_cards_dict["Flop"] = flop_match.group(2).lower()

        turn_match = re.search(
            r"Turn:\s+\(\$?(\d+(?:\.\d+)?)\)\s+([2-9TJQKA][cdhs])", line, re.IGNORECASE
        )
        if turn_match and not board_cards_dict["Turn"]:
            pot_sizes["Turn"] = _convert_amount(turn_match.group(1))
            board_cards_dict["Turn"] = turn_match.group(2).lower()

        river_match = re.search(
            r"River:\s+\(\$?(\d+(?:\.\d+)?)\)\s+([2-9TJQKA][cdhs])", line, re.IGNORECASE
        )
        if river_match and not board_cards_dict["River"]:
            pot_sizes["River"] = _convert_amount(river_match.group(1))
            board_cards_dict["River"] = river_match.group(2).lower()

    board_joined = " ".join(x for x in board_cards_dict.values() if x)

    actions: list[ParsedAction] = []
    pot_size = small_blind + big_blind
    acted_players: set[str] = set()
    last_bet_amount = 0.0
    current_street = "Preflop"

    stack_by_pid = {row[0]: row[2] for row in seat_rows}

    for line in lines:
        if "Preflop:" in line:
            current_street = "Preflop"
            last_bet_amount = 0.0
        elif "Flop:" in line:
            current_street = "Flop"
            last_bet_amount = 0.0
        elif "Turn:" in line:
            current_street = "Turn"
            last_bet_amount = 0.0
        elif "River:" in line:
            current_street = "River"
            last_bet_amount = 0.0

        is_seat_line = bool(seat_re.match(line.strip()))
        for frag in _comma_separated_action_fragments(line, is_seat_line=is_seat_line):
            f = frag.strip()
            if not f:
                continue

            fold_match = re.match(r"(\d+)\s+folds", f, re.IGNORECASE)
            if fold_match:
                num_folds = int(fold_match.group(1))
                for _pid, pos, _s, _bb, is_h, _sn in seat_rows:
                    if pos in acted_players:
                        continue
                    if is_h:
                        continue
                    pid = _pid
                    actions.append(
                        ParsedAction(
                            player_id=pid,
                            position=pos,
                            street=current_street,
                            action_type="Fold",
                            amount=0.0,
                            is_all_in=False,
                            effective_stack=stack_by_pid[pid],
                            pot_before=pot_size,
                            pot_after=pot_size,
                            bet_to_pot_ratio=None,
                        )
                    )
                    acted_players.add(pos)
                    num_folds -= 1
                    if num_folds == 0:
                        break
                continue

            if f.lower() == "all fold":
                for _pid, pos, _s, _bb, is_h, _sn in seat_rows:
                    if pos in acted_players or is_h:
                        continue
                    pid = _pid
                    actions.append(
                        ParsedAction(
                            player_id=pid,
                            position=pos,
                            street=current_street,
                            action_type="Fold",
                            amount=0.0,
                            is_all_in=False,
                            effective_stack=stack_by_pid[pid],
                            pot_before=pot_size,
                            pot_after=pot_size,
                            bet_to_pot_ratio=None,
                        )
                    )
                    acted_players.add(pos)
                continue

            action_match = _NORMALIZED_SINGLE_ACTION_RE.match(f)
            if not action_match:
                continue
            position_raw, action_raw, amount_raw = action_match.groups()
            position = position_raw.strip()
            if position == "Hero" and hero_position:
                position = hero_position
            else:
                position = normalize_text_position(position)
            verb_key = action_raw.strip().lower()
            mapped = _ACTION_VERB_TO_CANONICAL[verb_key]
            amount = _convert_amount(amount_raw) if amount_raw else 0.0

            if position.isdigit():
                position = "Unknown"

            if position not in player_id_map:
                continue

            pid = player_id_map[position]
            is_all_in = "all-in" in f.lower()

            pot_before = pot_size
            if mapped in ("Bet", "Raise", "Call"):
                if mapped == "Raise":
                    pot_size += amount - last_bet_amount
                elif mapped == "Bet":
                    pot_size += amount
                elif mapped == "Call":
                    pot_size += amount
            pot_after = pot_size

            bet_to_pot: float | None = None
            if mapped in ("Bet", "Raise"):
                if mapped == "Bet":
                    bet_to_pot = round(amount / pot_before, 4) if pot_before > 0 else None
                    last_bet_amount = amount
                else:
                    inc = amount - last_bet_amount
                    bet_to_pot = round(inc / pot_before, 4) if pot_before > 0 else None
                    last_bet_amount = amount
            else:
                bet_to_pot = None

            actions.append(
                ParsedAction(
                    player_id=pid,
                    position=position,
                    street=current_street,
                    action_type=mapped,
                    amount=amount,
                    is_all_in=is_all_in,
                    effective_stack=stack_by_pid[pid],
                    pot_before=pot_before,
                    pot_after=pot_after,
                    bet_to_pot_ratio=bet_to_pot,
                )
            )
            acted_players.add(position)

    results: list[ParsedResult] = []
    result_pattern = re.compile(
        r"(\w+)\s+"
        r"(showed|mucked)\s*"
        r"([2-9TJQKA][cdhs]\s+[2-9TJQKA][cdhs])?\s*"
        r"and\s+(won|lost)\s+"
        r"(?:\$?(\d+(?:\.\d+)?))?\s*"
        r"(?:\((-?\$?\d+(?:\.\d+)?)\s+net\))?",
        re.IGNORECASE,
    )
    for line in lines:
        result_match = result_pattern.search(line)
        if not result_match:
            continue
        pos = result_match.group(1)
        if pos == "Hero" and hero_position:
            pos = hero_position
        else:
            pos = normalize_text_position(pos)
        cards = (result_match.group(3) or "").strip().lower()
        outcome = result_match.group(4)
        won_amount = _convert_amount(result_match.group(5)) if result_match.group(5) else 0.0
        net_result = _convert_amount(result_match.group(6)) if result_match.group(6) else 0.0
        showdown = outcome.lower() == "won"

        if pos.isdigit():
            pos = "Unknown"
        if pos not in player_id_map:
            continue

        pid = player_id_map[pos]
        results.append(
            ParsedResult(
                player_id=pid,
                position=pos,
                cards=cards,
                net_result=net_result,
                won_pot=won_amount,
                showdown=showdown,
            )
        )

    # ``bb_size`` is the value from the normalized seat line, e.g. ``(97.5 bb)`` — not
    # recomputed as ``stack_size / big_blind`` (PHH and OHH use that ratio instead).
    players_out = tuple(
        ParsedPlayer(
            player_id=pid,
            position=pos,
            stack_size=stack,
            bb_size=bb,
            is_hero=is_h,
            player_uid=player_uid_hmac(
                uid_secret, nickname=screen, hand_id=hand_id, seat_player_id=pid
            ),
            screen_name=screen,
        )
        for pid, pos, stack, bb, is_h, screen in seat_rows
    )

    if enforce_card_integrity and not normalized_nlh_card_integrity_ok(text):
        return None

    antes_by_pid = scan_text_ante_posts(
        lines,
        player_id_map=player_id_map,
        hero_position=hero_position,
    )
    antes_tpl = build_antes_tuple(players_out, antes_by_pid)

    return ParsedHand(
        hand_id=hand_id,
        stakes=stakes,
        game_type=game_type,
        num_players=num_players,
        small_blind=small_blind,
        big_blind=big_blind,
        hero_position=hero_position,
        hero_cards=hero_cards,
        board_cards=board_joined or None,
        pot_preflop=pot_sizes["Preflop"],
        pot_flop=pot_sizes["Flop"],
        pot_turn=pot_sizes["Turn"],
        pot_river=pot_sizes["River"],
        antes=antes_tpl,
        players=players_out,
        actions=tuple(actions),
        results=tuple(results),
        ingest_source=INGEST_NORMALIZED_TXT,
        external_ref=str(hand_id),
    )


def _parse_raw_pokerstars_minimal(
    text: str,
    *,
    hand_id: int,
    uid_secret: str,
) -> ParsedHand | None:
    """Placeholder path for full PokerStars HH — only extracts blinds + table size if present."""
    head_u = text[:1200].upper()
    if "OMAHA" in head_u or "PLO" in head_u or "POT-LIMIT" in head_u.replace(" ", ""):
        return None
    if "NO LIMIT" not in head_u:
        return None
    m_stakes = re.search(
        r"\(\$?(\d+(?:\.\d+)?)/\$?(\d+(?:\.\d+)?)\s*(?:USD|EUR)?\)\s*-\s*",
        text[:1200],
    )
    m_seat = re.search(r"Seat #(\d+) is the button", text)
    if not m_stakes:
        return None
    sb = float(m_stakes.group(1))
    bb = float(m_stakes.group(2))
    _ = m_seat  # reserved for seat maps in a later iteration
    m_ps = re.search(r"PokerStars Hand #(\d+)", text[:1200], re.IGNORECASE)
    external_ref = f"ps:{m_ps.group(1)}" if m_ps else f"ps:adhoc_{hand_id}"
    hid = resolve_hand_id(INGEST_POKERSTARS_RAW_MINIMAL, external_ref)
    return ParsedHand(
        hand_id=hid,
        stakes=f"{sb}/{bb}",
        game_type="NLH",
        num_players=0,
        small_blind=sb,
        big_blind=bb,
        hero_position=None,
        hero_cards=None,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(),
        actions=(),
        results=(),
        ingest_source=INGEST_POKERSTARS_RAW_MINIMAL,
        external_ref=external_ref,
    )
