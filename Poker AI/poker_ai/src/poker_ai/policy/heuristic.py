"""Chart-style open / 3-bet heuristic policy (Phase 6 fallback)."""

from __future__ import annotations

import numpy as np

from poker_ai.core.engine import legal_actions
from poker_ai.core.game import EngineAction, EngineActionKind, GameState, Street
from poker_ai.core.profiles import PlayerProfile
from poker_ai.features.range import isomorphic_preflop_id
from poker_ai.ingest.positions import POSITION_RING
from poker_ai.policy.base import ActionDist

# Isomorphic preflop class ids 0..168 (see features.range). Ranges are inclusive lower bounds.
_OPEN_UTG: frozenset[int] = frozenset(range(120, 169))  # ~top 30 %
_OPEN_BTN: frozenset[int] = frozenset(range(60, 169))
_OPEN_CO: frozenset[int] = frozenset(range(90, 169))
_3BET_VALUE: frozenset[int] = frozenset(range(140, 169))
_3BET_BLUFF: frozenset[int] = frozenset({45, 67, 88, 102})


def _seat_position(state: GameState, seat: int) -> int:
    n = state.num_seats
    if n == 2:
        return 0 if seat == state.button_seat else 1
    order = (state.bb_seat + 1) % n
    return (seat - order) % n


def _preflop_class_from_state(state: GameState, seat: int) -> int:
    # Without hole cards in GameState, use seat + seed proxy for deterministic tests.
    pid = state.seat_pid[seat] if seat < len(state.seat_pid) else seat
    return (pid * 17 + state.seed) % 169


def _open_range_for_pos(pos_idx: int, num_players: int) -> frozenset[int]:
    ring = POSITION_RING.get(num_players, POSITION_RING[6])
    label = ring[pos_idx % len(ring)] if ring else "UTG"
    _ = label
    if num_players <= 3:
        return _OPEN_BTN
    if pos_idx <= 1:
        return _OPEN_UTG
    if pos_idx >= num_players - 2:
        return _OPEN_BTN
    return _OPEN_CO


class HeuristicPolicy:
    """Position-based open / defend heuristics over legal engine actions."""

    name: str = "heuristic"
    version: str = "0.1.0"

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> ActionDist:
        _ = profile, opponent_styles, thinking_ms
        seat = state.acting_seat
        if seat is None or state.hand_over:
            return ActionDist((), ())

        legal = legal_actions(state)
        if not legal:
            return ActionDist((), ())

        keys = [(a.kind.value, a.amount_chips, a.seat) for a in legal]
        mass = [0.0] * len(keys)

        if state.street != Street.PREFLOP:
            return self._postflop_dist(keys, legal)

        hand_cls = _preflop_class_from_state(state, seat)
        pos = _seat_position(state, seat)
        facing_raise = state.raise_count_street > 0

        if facing_raise:
            if hand_cls in _3BET_VALUE:
                self._weight(keys, mass, legal, EngineActionKind.RAISE, 0.55)
                self._weight(keys, mass, legal, EngineActionKind.CALL, 0.35)
                self._weight(keys, mass, legal, EngineActionKind.FOLD, 0.10)
            elif hand_cls in _3BET_BLUFF:
                self._weight(keys, mass, legal, EngineActionKind.RAISE, 0.18)
                self._weight(keys, mass, legal, EngineActionKind.FOLD, 0.72)
                self._weight(keys, mass, legal, EngineActionKind.CALL, 0.10)
            else:
                self._weight(keys, mass, legal, EngineActionKind.FOLD, 0.70)
                self._weight(keys, mass, legal, EngineActionKind.CALL, 0.30)
        else:
            open_set = _open_range_for_pos(pos, state.num_seats)
            if hand_cls in open_set:
                self._weight(keys, mass, legal, EngineActionKind.RAISE, 0.72)
                self._weight(keys, mass, legal, EngineActionKind.CALL, 0.18)
                self._weight(keys, mass, legal, EngineActionKind.FOLD, 0.10)
            else:
                self._weight(keys, mass, legal, EngineActionKind.FOLD, 0.55)
                self._weight(keys, mass, legal, EngineActionKind.CALL, 0.40)
                self._weight(keys, mass, legal, EngineActionKind.RAISE, 0.05)

        if not mass:
            n = len(keys)
            return ActionDist(tuple(keys), tuple(1.0 / n for _ in range(n)))
        return ActionDist(tuple(keys), tuple(mass)).normalized()

    def explain(self, state: GameState, decision: ActionDist) -> str:
        seat = state.acting_seat
        top = max(zip(decision.actions, decision.probs, strict=True), key=lambda x: x[1])
        return f"heuristic seat={seat} top={top[0][0]} p={top[1]:.2f}"

    @staticmethod
    def _weight(
        keys: list[tuple[str, int, int]],
        mass: list[float],
        legal: tuple[EngineAction, ...],
        kind: EngineActionKind,
        p: float,
    ) -> None:
        for a in legal:
            if a.kind == kind:
                k = (a.kind.value, a.amount_chips, a.seat)
                if k in keys:
                    mass[keys.index(k)] += p

    @staticmethod
    def _postflop_dist(
        keys: list[tuple[str, int, int]],
        legal: tuple[EngineAction, ...],
    ) -> ActionDist:
        mass = [0.0] * len(keys)
        for i, a in enumerate(legal):
            if a.kind == EngineActionKind.CHECK:
                mass[i] = 0.45
            elif a.kind == EngineActionKind.CALL:
                mass[i] = 0.40
            elif a.kind in (EngineActionKind.BET, EngineActionKind.RAISE):
                mass[i] = 0.12
            elif a.kind == EngineActionKind.FOLD:
                mass[i] = 0.03
        return ActionDist(tuple(keys), tuple(mass)).normalized()


def hero_preflop_class(card_a: int, card_b: int) -> int:
    """Map hole cards to isomorphic class for range charts."""
    return isomorphic_preflop_id(card_a, card_b)
