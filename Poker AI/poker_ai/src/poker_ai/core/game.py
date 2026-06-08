"""NLH game state and action vocabulary (Phase 2)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Street(StrEnum):
    PREFLOP = "Preflop"
    FLOP = "Flop"
    TURN = "Turn"
    RIVER = "River"
    SHOWDOWN = "Showdown"


class EngineActionKind(StrEnum):
    FOLD = "Fold"
    CHECK = "Check"
    CALL = "Call"
    BET = "Bet"
    RAISE = "Raise"


@dataclass(frozen=True, slots=True)
class EngineAction:
    """A single engine step (amount semantics match the canonical ingest store).

    * ``Raise`` — new **total** chips committed on the current street (raise-to).
    * ``Bet`` — chips **added** on the current street (first aggression postflop).
    * ``Call`` — chips **added** on the current street (delta toward the current max).
    * ``Fold`` / ``Check`` — ``amount_chips`` must be ``0``.
    """

    seat: int
    kind: EngineActionKind
    amount_chips: int = 0


@dataclass(slots=True)
class GameState:
    """Mutable NLH table state; :func:`poker_ai.core.engine.step` returns a deep copy."""

    num_seats: int
    stacks: list[int]
    folded: list[bool]
    street: Street
    board: list[int]
    full_board: tuple[int, ...]
    pot: int
    button_seat: int
    sb_seat: int
    bb_seat: int
    seat_pid: list[int]
    street_commit: list[int]
    current_max: int
    big_blind: int
    small_blind: int
    acting_seat: int | None
    hand_over: bool
    winner_seat: int | None
    seed: int
    last_aggressor_seat: int | None
    bb_checked_preflop: bool
    raise_count_street: int
    action_log: list[EngineAction]
    acted_this_round: list[bool]
    seat_holes: list[tuple[int, int] | None] | None = None
    hand_id: str | None = None

    def clone(self) -> GameState:
        return GameState(
            num_seats=self.num_seats,
            stacks=list(self.stacks),
            folded=list(self.folded),
            street=self.street,
            board=list(self.board),
            full_board=tuple(self.full_board),
            pot=self.pot,
            button_seat=self.button_seat,
            sb_seat=self.sb_seat,
            bb_seat=self.bb_seat,
            seat_pid=list(self.seat_pid),
            street_commit=list(self.street_commit),
            current_max=self.current_max,
            big_blind=self.big_blind,
            small_blind=self.small_blind,
            acting_seat=self.acting_seat,
            hand_over=self.hand_over,
            winner_seat=self.winner_seat,
            seed=self.seed,
            last_aggressor_seat=self.last_aggressor_seat,
            bb_checked_preflop=self.bb_checked_preflop,
            raise_count_street=self.raise_count_street,
            action_log=list(self.action_log),
            acted_this_round=list(self.acted_this_round),
            seat_holes=(list(self.seat_holes) if self.seat_holes is not None else None),
            hand_id=self.hand_id,
        )
