"""Multi-way postflop policy: n-way equity + tighter lines (Phase 7b)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from poker_ai.core.context import count_active_players
from poker_ai.core.engine import legal_actions
from poker_ai.core.game import EngineAction, EngineActionKind, GameState, Street
from poker_ai.core.profiles import PlayerProfile
from poker_ai.equity.multiway import hero_equity_vs_n_uniform
from poker_ai.policy.base import ActionDist
from poker_ai.policy.distilled_policy import _map_student_to_legal
from poker_ai.policy.heuristic import HeuristicPolicy
from poker_ai.solver.bridge.monker import MonkerTeacherCache, MultiwaySpotSpec, monker_lookup_key
from poker_ai.solver.bridge.schemas import STUDENT_ACTIONS


class MultiwayPostflopPolicy:
    """Postflop decisions when ``n_active >= 3`` — never calls the HU distilled student."""

    name: str = "multiway_postflop"
    version: str = "1.0.0"

    def __init__(
        self,
        *,
        student_dir: Path | None = None,
        hhformer_dir: Path | None = None,
        monker_export_dir: Path | None = None,
        monker_blend: float = 0.15,
        device: str = "cpu",
    ) -> None:
        self._fallback = HeuristicPolicy()
        self._student_dir = student_dir or Path("artifacts/student/multiway_v1")
        self._hhformer_dir = hhformer_dir or Path("artifacts/hhformer/v1")
        self._device = device
        self._monker_blend = max(0.0, min(1.0, monker_blend))
        self._monker: MonkerTeacherCache | None = None
        if monker_export_dir is not None and monker_export_dir.is_dir():
            cache = MonkerTeacherCache(monker_export_dir)
            if len(cache) > 0:
                self._monker = cache
        self._hhformer: object | None = None
        self._student: object | None = None
        self._load_multiway_student()

    def _load_multiway_student(self) -> None:
        weights = self._student_dir / "student.safetensors"
        if not weights.is_file():
            return
        from safetensors.torch import load_file

        from poker_ai.learn._ml_deps import require_torch
        from poker_ai.learn.hhformer_inference import load_hhformer
        from poker_ai.models.multiway_student import MultiwayStudentConfig, MultiwayStudentHead

        torch = require_torch()
        hhformer, _, _ = load_hhformer(self._hhformer_dir, device=self._device)
        mod = MultiwayStudentHead(MultiwayStudentConfig()).module
        mod.load_state_dict(load_file(str(weights)))
        mod.eval()
        mod.to(torch.device(self._device))
        self._hhformer = hhformer
        self._student = mod

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> ActionDist:
        _ = profile, opponent_styles, thinking_ms
        if state.hand_over or state.street == Street.PREFLOP:
            return self._fallback.propose(state, profile)

        legal = legal_actions(state)
        if not legal or state.acting_seat is None:
            return ActionDist((), ())

        n_active = count_active_players(state)
        if n_active < 3:
            return ActionDist((), ())

        if self._student is not None and self._hhformer is not None:
            dist = self._student_propose(state, legal, n_active=n_active)
            if dist.actions:
                return dist

        return self._equity_propose(state, legal, n_active=n_active, profile=profile)

    def _equity_propose(
        self,
        state: GameState,
        legal: tuple[EngineAction, ...],
        *,
        n_active: int,
        profile: PlayerProfile,
    ) -> ActionDist:
        hero = state.acting_seat
        holes = state.seat_holes
        if holes is None or hero is None or hero >= len(holes) or holes[hero] is None:
            return self._fallback.propose(state, profile)

        lo, hi = holes[hero]
        n_opp = n_active - 1
        eq = hero_equity_vs_n_uniform(
            (lo, hi), tuple(state.board), n_opp, n_samples=25_000, seed=state.seed
        )
        return _dist_from_multiway_equity(eq, legal, n_active=n_active)

    def _student_propose(
        self,
        state: GameState,
        legal: tuple[EngineAction, ...],
        *,
        n_active: int,
    ) -> ActionDist:
        from poker_ai.features.board_texture import texture_int16
        from poker_ai.features.hhformer_tokens import encode_hand_sequence
        from poker_ai.learn._ml_deps import require_torch
        from poker_ai.models.multiway_student import encode_multiway_extras
        from poker_ai.policy.distilled_policy import _state_to_parsed_hand

        hhformer = self._hhformer
        student = self._student
        if hhformer is None or student is None:
            return ActionDist((), ())

        torch = require_torch()
        hand = _state_to_parsed_hand(state)
        seq = encode_hand_sequence(hand)
        dev = torch.device(self._device)
        ids = torch.tensor([list(seq.token_ids)], dtype=torch.long, device=dev)
        mask = torch.zeros((1, ids.shape[1]), dtype=torch.bool, device=dev)
        if seq.length < ids.shape[1]:
            mask[0, seq.length :] = True
        tex = texture_int16(tuple(state.board))
        hero_seat = state.acting_seat or 0
        extras = encode_multiway_extras(
            hero_is_ip=hero_seat == state.bb_seat,
            effective_stack=max(state.stacks),
            pot_chips=max(1, state.pot),
            board_texture=tex,
            n_active=n_active,
            num_seats=state.num_seats,
        )
        ex_t = torch.tensor([list(extras)], dtype=torch.float32, device=dev)
        with torch.no_grad():
            cls = hhformer(ids, key_padding_mask=mask)["cls"]
            probs = student(cls, ex_t)[0].cpu().numpy()

        if self._monker is not None and self._monker_blend > 0:
            spec = _state_to_multiway_spec(state, n_active=n_active)
            key = monker_lookup_key(spec)
            teacher = self._monker.get(key)
            if teacher is not None and len(teacher) == len(probs):
                blend = (1.0 - self._monker_blend) * probs + self._monker_blend * np.asarray(
                    teacher, dtype=np.float64
                )
                probs = blend / blend.sum()

        return _map_student_to_legal(probs, legal)

    def explain(self, state: GameState, decision: ActionDist) -> str:
        n = count_active_players(state)
        top = max(zip(decision.actions, decision.probs, strict=True), key=lambda x: x[1])
        src = "multiway_student" if self._student is not None else "multiway_equity"
        return f"brain=multiway n_active={n} src={src} top={top[0][0]} p={top[1]:.2f}"


def _state_to_multiway_spec(state: GameState, *, n_active: int) -> MultiwaySpotSpec:
    from poker_ai.policy.distilled_policy import _format_card

    board = ",".join(_format_card(c) for c in state.board)
    return MultiwaySpotSpec(
        board=board,
        pot_chips=max(1, state.pot),
        effective_stack=max(1, max(state.stacks)),
        n_active=n_active,
        num_seats=state.num_seats,
        sizing_tree_id="runtime_multiway",
    )


def _dist_from_multiway_equity(
    eq: float,
    legal: tuple[EngineAction, ...],
    *,
    n_active: int,
) -> ActionDist:
    """Tighter than HU: more folding / less bluffing as field size grows."""
    _ = STUDENT_ACTIONS
    pressure = min(1.0, (n_active - 2) / 6.0)
    fold_p, call_p, raise_p = 0.12 + 0.18 * pressure, 0.48, 0.40 - 0.22 * pressure
    if eq < 0.28 + 0.05 * pressure:
        fold_p, call_p, raise_p = 0.62 + 0.08 * pressure, 0.32, 0.06
    elif eq < 0.48:
        fold_p, call_p, raise_p = 0.28 + 0.10 * pressure, 0.58, 0.14
    keys = [(a.kind.value, a.amount_chips, a.seat) for a in legal]
    mass = [0.0] * len(legal)
    for i, a in enumerate(legal):
        if a.kind == EngineActionKind.FOLD:
            mass[i] = fold_p
        elif a.kind in (EngineActionKind.CALL, EngineActionKind.CHECK):
            mass[i] = call_p
        else:
            mass[i] = raise_p
    s = sum(mass)
    if s <= 0:
        mass = [1.0 / len(legal)] * len(legal)
    else:
        mass = [m / s for m in mass]
    return ActionDist(tuple(keys), tuple(mass))
