"""Fill ``hero_position`` / ``hero_cards`` when parsers leave them unset (e.g. PHH)."""

from __future__ import annotations

from dataclasses import replace

from poker_ai.ingest.records import ParsedHand, ParsedPlayer


def ensure_hero_viewpoint(hand: ParsedHand) -> ParsedHand:
    """Pick a single decision seat and align ``is_hero`` flags.

    * If ``hero_position`` is already set, resolve it to a ``player_id`` when possible.
    * Otherwise prefer the **lowest** ``player_id`` that has non-empty known hole cards
      in ``results`` (stable, replay-friendly).
    * If no hole cards are known, use **player_id** ``1`` when present, else the lowest
      seat id present.
    * ``hero_cards`` is taken from ``results`` when missing on the hand row.
    """
    if not hand.players:
        return hand

    valid_ids = {p.player_id for p in hand.players}
    pos_by_pid = {p.player_id: p.position for p in hand.players}
    pid_by_pos = {p.position: p.player_id for p in hand.players}

    cards_by_pid: dict[int, str] = {}
    for r in hand.results:
        c = (r.cards or "").strip().lower()
        if c and "?" not in c:
            cards_by_pid[r.player_id] = c

    hero_pid: int | None = None
    if hand.hero_position:
        cand = pid_by_pos.get(hand.hero_position.strip())
        if cand in valid_ids:
            hero_pid = cand

    if hero_pid is None:
        with_cards = sorted(pid for pid in cards_by_pid if pid in valid_ids)
        if with_cards:
            hero_pid = with_cards[0]
        else:
            hero_pid = min(valid_ids)

    hero_pos = pos_by_pid[hero_pid]

    hero_cs = (hand.hero_cards or "").strip().lower() if hand.hero_cards else ""
    if not hero_cs:
        hero_cs = cards_by_pid.get(hero_pid, "")
    hero_cards_out: str | None = hero_cs if hero_cs else None

    new_players: tuple[ParsedPlayer, ...] = tuple(
        replace(p, is_hero=(p.player_id == hero_pid)) for p in hand.players
    )

    return replace(
        hand,
        hero_position=hero_pos,
        hero_cards=hero_cards_out,
        players=new_players,
    )
