"""Tabular CFR+ policy over abstracted preflop info sets (Phase 6)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import numpy as np

from poker_ai.core.engine import legal_actions
from poker_ai.core.game import EngineAction, EngineActionKind, GameState, Street
from poker_ai.core.profiles import PlayerProfile
from poker_ai.features.info_set import UNKNOWN_PREFLOP, parts_from_hand
from poker_ai.features.range import combo_index
from poker_ai.ingest.records import ParsedHand
from poker_ai.policy.base import ActionDist
from poker_ai.policy.heuristic import HeuristicPolicy
from poker_ai.solver.abstraction import equity_bucket
from poker_ai.solver.preflop import ALLIN, CALL, FOLD, RAISE
from poker_ai.solver.preflop_equity import EquityMode, bucket_for_combo

TabularStrategy = dict[str, tuple[float, ...]]


@dataclass(frozen=True, slots=True)
class CFRPolicy:
    """Tabular CFR strategy with heuristic fallback."""

    strategy: TabularStrategy
    name: str = "cfr_preflop"
    version: str = "0.1.0"
    equity_mode: EquityMode = "random"
    equity_mc_samples: int = 2000
    _fallback: HeuristicPolicy = field(default_factory=HeuristicPolicy)

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
        if seat is None or state.hand_over or state.street != Street.PREFLOP:
            return self._fallback.propose(state, profile)

        legal = legal_actions(state)
        if not legal:
            return ActionDist((), ())

        bucket = _bucket_from_state(
            state,
            seat,
            equity_mode=self.equity_mode,
            equity_mc_samples=self.equity_mc_samples,
        )
        hist = _abstract_history(state)
        key = f"n{state.num_seats}|p{seat}|b{bucket}|h{hist}"
        sigma = self.strategy.get(key)
        if sigma is None:
            return self._fallback.propose(state, profile)

        keys = [(a.kind.value, a.amount_chips, a.seat) for a in legal]
        probs = _map_abstract_to_legal(sigma, legal)
        return ActionDist(tuple(keys), tuple(probs)).normalized()

    def explain(self, state: GameState, decision: ActionDist) -> str:
        top = max(zip(decision.actions, decision.probs, strict=True), key=lambda x: x[1])
        return f"cfr_preflop top={top[0][0]} p={top[1]:.2f}"

    @classmethod
    def load_json(cls, path: Path) -> CFRPolicy:
        raw = json.loads(path.read_text(encoding="utf-8"))
        strategy = {k: tuple(float(x) for x in v) for k, v in raw["strategy"].items()}
        version = str(raw.get("version", "0.1.0"))
        mode = str(raw.get("equity_mode", "random"))
        if mode not in ("random", "real"):
            mode = "random"
        mc = int(raw.get("equity_mc_samples", 2000))
        return cls(
            strategy=strategy,
            version=version,
            equity_mode=cast(EquityMode, mode),
            equity_mc_samples=mc,
        )

    def save_json(
        self,
        path: Path,
        *,
        iterations: int,
        exploitability_mbb: float,
        equity_mode: EquityMode | None = None,
        equity_mc_samples: int | None = None,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": self.version,
            "iterations": iterations,
            "exploitability_mbb": exploitability_mbb,
            "equity_mode": equity_mode if equity_mode is not None else self.equity_mode,
            "equity_mc_samples": (
                equity_mc_samples if equity_mc_samples is not None else self.equity_mc_samples
            ),
            "strategy": {k: list(v) for k, v in self.strategy.items()},
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _bucket_from_state(
    state: GameState,
    seat: int,
    *,
    equity_mode: EquityMode,
    equity_mc_samples: int,
) -> int:
    holes = getattr(state, "seat_holes", None)
    if equity_mode == "real" and holes is not None and seat < len(holes):
        cards = holes[seat]
        if cards is not None:
            lo, hi = (cards[0], cards[1]) if cards[0] < cards[1] else (cards[1], cards[0])
            return bucket_for_combo(combo_index(lo, hi), mc_samples=equity_mc_samples)
    pid = state.seat_pid[seat] if seat < len(state.seat_pid) else seat
    proxy_eq = ((pid * 31) % 169) / 168.0
    return equity_bucket(proxy_eq)


def _abstract_history(state: GameState) -> str:
    codes: list[int] = []
    for a in state.action_log:
        if a.seat is None:
            continue
        act = _engine_to_abstract(a.kind)
        codes.append(a.seat * 4 + act)
    return ",".join(str(c) for c in codes)


def _engine_to_abstract(kind: EngineActionKind) -> int:
    if kind == EngineActionKind.FOLD:
        return FOLD
    if kind in (EngineActionKind.CALL, EngineActionKind.CHECK):
        return CALL
    if kind in (EngineActionKind.BET, EngineActionKind.RAISE):
        return RAISE
    return CALL


def _map_abstract_to_legal(
    sigma: tuple[float, ...],
    legal: tuple[EngineAction, ...],
) -> list[float]:
    """Map 4-action abstract vector [fold,call,raise,allin] onto legal engine actions."""

    def _p(idx: int) -> float:
        return sigma[idx] if len(sigma) > idx else 0.0

    mass = [0.0] * len(legal)
    for i, a in enumerate(legal):
        if a.kind == EngineActionKind.FOLD:
            mass[i] = _p(FOLD)
        elif a.kind in (EngineActionKind.CALL, EngineActionKind.CHECK):
            mass[i] = _p(CALL)
        elif a.kind == EngineActionKind.RAISE:
            stack_cap = a.amount_chips >= a.seat  # all-in raise-to heuristic
            mass[i] = _p(ALLIN) if stack_cap else _p(RAISE)
        elif a.kind == EngineActionKind.BET:
            mass[i] = _p(RAISE)
    s = sum(mass)
    if s <= 0.0:
        return [1.0 / len(legal)] * len(legal)
    return [m / s for m in mass]


def info_set_key_from_hand(hand: ParsedHand) -> str:
    """Stable key aligned with solver info sets (for corpus lookup)."""
    parts = parts_from_hand(hand)
    bucket = parts.preflop_id if parts.preflop_id != UNKNOWN_PREFLOP else 25
    hp = parts.hero_pos
    hist = ",".join(str(t) for t in parts.action_tokens if t != 0)
    return f"n{hand.num_players}|p{hp}|b{bucket}|h{hist}"
