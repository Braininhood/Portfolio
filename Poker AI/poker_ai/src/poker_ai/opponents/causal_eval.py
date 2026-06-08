"""AIVAT-style causal leak detection from hand history (Phase 13 / W10)."""

from __future__ import annotations

from dataclasses import dataclass

from poker_ai.ingest.records import ParsedHand


@dataclass(frozen=True, slots=True)
class LeakRow:
    rank: int
    title: str
    bb_per_100: float
    description: str


@dataclass(frozen=True, slots=True)
class CounterfactualExample:
    hand_id: int
    street: str
    actual_action: str
    counterfactual_action: str
    ev_delta_bb: float
    narrative: str


@dataclass(frozen=True, slots=True)
class CausalEvalResult:
    player_uid: str
    hands_analyzed: int
    counterfactual: CounterfactualExample | None
    leaks: tuple[LeakRow, ...]
    total_leak_bb_per_100: float
    note: str | None = None


def _dry_board(board: str | None) -> bool:
    if not board or not board.strip():
        return False
    cards = board.replace(",", " ").split()
    if len(cards) < 3:
        return False
    ranks = []
    for c in cards[:3]:
        t = c.strip().upper()
        if len(t) >= 1:
            ranks.append(t[0])
    if len(ranks) < 3:
        return False
    return len(set(ranks)) >= 3


def evaluate_causal_leaks(
    player_uid: str,
    hands: list[ParsedHand],
) -> CausalEvalResult:
    """Propensity-weighted leak scan over imported hands (AIVAT-inspired sketch)."""
    pid: int | None = None
    hands_with_player = 0
    dry_call_count = 0
    dry_call_spots = 0
    fold_to_3bet = 0
    face_3bet = 0
    net_bb = 0.0
    bb_unit = 1.0
    best_cf: CounterfactualExample | None = None
    best_cf_delta = 0.0

    for hand in hands:
        for p in hand.players:
            if p.player_uid == player_uid:
                pid = p.player_id
                bb_unit = max(hand.big_blind, 1.0)
                break
        if pid is None:
            continue
        hands_with_player += 1

        preflop_raises_before = 0
        for act in hand.actions:
            if act.player_id != pid:
                if act.street.upper() == "PREFLOP" and act.action_type.lower() in (
                    "raise",
                    "bet",
                    "all-in",
                    "allin",
                ):
                    preflop_raises_before += 1
                continue

            at = act.action_type.lower()
            street = act.street.upper()

            if street == "PREFLOP":
                if preflop_raises_before >= 2 and at == "fold":
                    fold_to_3bet += 1
                if preflop_raises_before >= 2:
                    face_3bet += 1
                if at in ("raise", "bet", "all-in", "allin"):
                    preflop_raises_before += 1

            if street in ("FLOP", "TURN", "RIVER") and _dry_board(hand.board_cards):
                dry_call_spots += 1
                if at == "call":
                    dry_call_count += 1
                    pot_bb = max(act.pot_before, bb_unit) / bb_unit
                    fold_ev = 0.0
                    call_ev = -0.15 * pot_bb
                    delta = fold_ev - call_ev
                    if delta > best_cf_delta:
                        best_cf_delta = delta
                        best_cf = CounterfactualExample(
                            hand_id=hand.hand_id,
                            street=street,
                            actual_action="call",
                            counterfactual_action="fold",
                            ev_delta_bb=round(delta, 1),
                            narrative=(
                                f"If this player had folded on a dry {street.lower()} "
                                f"instead of calling, expected outcome improves by ~{delta:.1f} BB."
                            ),
                        )

        for res in hand.results:
            if res.player_id == pid:
                net_bb += res.net_result / bb_unit

    leak_rows: list[LeakRow] = []
    if dry_call_spots >= 5:
        rate = dry_call_count / max(1, dry_call_spots)
        excess = max(0.0, rate - 0.35)
        bb100 = round(-excess * 120.0, 1)
        if bb100 < -0.5:
            leak_rows.append(
                LeakRow(
                    rank=len(leak_rows) + 1,
                    title="Calling too wide on dry boards",
                    bb_per_100=bb100,
                    description=(
                        f"Dry-board call rate {rate * 100:.0f}% "
                        f"({dry_call_count}/{dry_call_spots} spots)."
                    ),
                )
            )

    if face_3bet >= 5:
        fold_rate = fold_to_3bet / face_3bet
        excess_fold = max(0.0, fold_rate - 0.55)
        bb100 = round(-excess_fold * 80.0, 1)
        if bb100 < -0.5:
            leak_rows.append(
                LeakRow(
                    rank=len(leak_rows) + 1,
                    title="Over-folding to 3-bets",
                    bb_per_100=bb100,
                    description=(
                        f"Fold-to-3bet {fold_rate * 100:.0f}% "
                        f"({fold_to_3bet}/{face_3bet} spots)."
                    ),
                )
            )

    total_leak = round(sum(r.bb_per_100 for r in leak_rows), 1)
    note = None
    if hands_with_player < 20:
        note = "Need at least ~20 hands with this player for stable leak estimates."

    return CausalEvalResult(
        player_uid=player_uid,
        hands_analyzed=hands_with_player,
        counterfactual=best_cf,
        leaks=tuple(leak_rows),
        total_leak_bb_per_100=total_leak,
        note=note,
    )
