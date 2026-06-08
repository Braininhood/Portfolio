"""Training rows from DB hands at multi-way decision points (Phase 7b V2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from poker_ai.core.cards import parse_card
from poker_ai.features.board_texture import texture_int16
from poker_ai.features.hhformer_tokens import encode_hand_sequence
from poker_ai.ingest.records import ParsedAction, ParsedHand
from poker_ai.models.multiway_student import encode_multiway_extras
from poker_ai.solver.bridge.schemas import STUDENT_ACTIONS


@dataclass(frozen=True, slots=True)
class MultiwayRow:
    token_ids: tuple[int, ...]
    state_extras: tuple[float, ...]
    target_freqs: tuple[float, ...]
    hand_id: int
    n_active: int


_POSTFLOP = frozenset({"Flop", "Turn", "River"})


def _action_to_target_freq(pa: ParsedAction) -> tuple[float, ...]:
    """One-hot-ish target over :data:`STUDENT_ACTIONS`."""
    mass = {k: 0.0 for k in STUDENT_ACTIONS}
    t = pa.action_type
    if t == "Fold":
        mass["fold"] = 1.0
    elif t in ("Check", "Call"):
        mass["check_call"] = 1.0
    elif t in ("Bet", "Raise"):
        bpr = pa.bet_to_pot_ratio
        if bpr is not None and bpr >= 0.55:
            mass["bet_66"] = 0.7
            mass["allin"] = 0.3
        elif bpr is not None and bpr >= 0.25:
            mass["bet_33"] = 0.6
            mass["bet_66"] = 0.4
        else:
            mass["bet_33"] = 1.0
    else:
        mass["check_call"] = 1.0
    return tuple(mass[k] for k in STUDENT_ACTIONS)


def _count_active_before_action(hand: ParsedHand, action_index: int) -> int:
    folded: set[int] = set()
    player_ids = {p.player_id for p in hand.players}
    for pa in hand.actions[:action_index]:
        if pa.action_type == "Fold" and pa.player_id in player_ids:
            folded.add(pa.player_id)
    return hand.num_players - len(folded)


def _hero_player_id(hand: ParsedHand) -> int | None:
    for p in hand.players:
        if p.is_hero:
            return p.player_id
    if hand.hero_position:
        for p in hand.players:
            if p.position == hand.hero_position:
                return p.player_id
    return hand.players[0].player_id if hand.players else None


def rows_from_hand(hand: ParsedHand) -> list[MultiwayRow]:
    """Extract hero decision rows where ``n_active >= 3`` on postflop streets."""
    hero_pid = _hero_player_id(hand)
    if hero_pid is None or not hand.hero_cards:
        return []

    board_ints: tuple[int, ...] = ()
    if hand.board_cards:
        try:
            board_ints = tuple(parse_card(p) for p in hand.board_cards.split())
        except ValueError:
            board_ints = ()

    out: list[MultiwayRow] = []
    for i, pa in enumerate(hand.actions):
        if pa.street not in _POSTFLOP:
            continue
        n_active = _count_active_before_action(hand, i)
        if n_active < 3 or pa.player_id != hero_pid:
            continue
        prefix = hand.actions[: i + 1]
        sub = ParsedHand(
            hand_id=hand.hand_id,
            stakes=hand.stakes,
            game_type=hand.game_type,
            num_players=hand.num_players,
            small_blind=hand.small_blind,
            big_blind=hand.big_blind,
            hero_position=hand.hero_position,
            hero_cards=hand.hero_cards,
            board_cards=hand.board_cards,
            pot_preflop=hand.pot_preflop,
            pot_flop=hand.pot_flop,
            pot_turn=hand.pot_turn,
            pot_river=hand.pot_river,
            antes=hand.antes,
            players=hand.players,
            actions=prefix,
            results=hand.results,
            ingest_source=hand.ingest_source,
            external_ref=hand.external_ref,
        )
        seq = encode_hand_sequence(sub)
        tex = texture_int16(board_ints)
        pot = max(1, int(pa.pot_after * 100))
        extras = encode_multiway_extras(
            hero_is_ip=False,
            effective_stack=max(1, int(pa.effective_stack * 100)),
            pot_chips=pot,
            board_texture=tex,
            n_active=n_active,
            num_seats=hand.num_players,
        )
        out.append(
            MultiwayRow(
                token_ids=tuple(seq.token_ids),
                state_extras=extras,
                target_freqs=_action_to_target_freq(pa),
                hand_id=hand.hand_id,
                n_active=n_active,
            )
        )
    return out


async def load_multiway_rows(
    session_factory: Any,
    *,
    limit: int | None = None,
    min_rows: int = 100,
) -> list[MultiwayRow]:
    from poker_ai.store.loader import iter_parsed_hands_since

    rows: list[MultiwayRow] = []
    async with session_factory() as session:
        async for hand in iter_parsed_hands_since(session, since=None):
            rows.extend(rows_from_hand(hand))
            if limit is not None and len(rows) >= limit:
                break
    if len(rows) < min_rows and limit is None:
        return rows
    return rows[:limit] if limit is not None else rows


def collate_multiway_batch(batch: list[MultiwayRow]) -> dict[str, Any]:
    max_len = max(len(r.token_ids) for r in batch)
    token_ids = []
    targets = []
    extras = []
    for r in batch:
        pad = list(r.token_ids) + [0] * (max_len - len(r.token_ids))
        token_ids.append(pad)
        targets.append(list(r.target_freqs))
        extras.append(list(r.state_extras))
    return {
        "token_ids": token_ids,
        "state_extras": extras,
        "targets": targets,
    }
