"""Neural student policy with optional TexasSolver teacher fallback (Phase 7)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.core.cards import card_from_int
from poker_ai.core.context import is_multiway_context
from poker_ai.core.engine import legal_actions
from poker_ai.core.game import EngineAction, EngineActionKind, GameState, Street
from poker_ai.core.profiles import PlayerProfile
from poker_ai.features.board_texture import texture_int16
from poker_ai.features.hhformer_tokens import encode_hand_sequence
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer
from poker_ai.learn.hhformer_inference import load_hhformer
from poker_ai.models.student import StudentConfig, StudentHead, encode_state_extras
from poker_ai.policy.base import ActionDist, Policy
from poker_ai.policy.heuristic import HeuristicPolicy
from poker_ai.policy.postflop_equity import PostflopEquityPolicy
from poker_ai.solver.bridge.cache import SolverCache, cache_key
from poker_ai.solver.bridge.schemas import STUDENT_ACTIONS, SpotSpec
from poker_ai.solver.bridge.texas import solve_spot


def _format_card(c: int) -> str:
    r, s = card_from_int(c)
    return f"{r}{s}"


class DistilledPolicy:
    """Fast student net at runtime; teacher only when ``offline_teacher=True`` and cache miss."""

    name: str = "distilled"
    version: str = "1.0.0"

    def __init__(
        self,
        *,
        student_dir: Path | None = None,
        hhformer_dir: Path | None = None,
        cache_dir: Path | None = None,
        offline_teacher: bool = False,
        device: str = "cpu",
    ) -> None:
        self._student_dir = student_dir or Path("artifacts/student/v1")
        self._hhformer_dir = hhformer_dir or Path("artifacts/hhformer/v1")
        self._cache = SolverCache(cache_dir or Path("artifacts/solver_cache"))
        self._offline_teacher = offline_teacher
        self._device = device
        self._fallback = HeuristicPolicy()
        self._equity_fallback = PostflopEquityPolicy()
        self._multiway: Policy | None = None
        self._hhformer: Any | None = None
        self._student: Any | None = None
        self._cls_cache: dict[tuple[object, ...], Any] = {}
        self._cls_cache_max = 64
        self._load_models()

    def _load_models(self) -> None:
        weights = self._student_dir / "student.safetensors"
        if not weights.is_file():
            return
        from safetensors.torch import load_file

        from poker_ai.learn._ml_deps import require_torch

        torch = require_torch()
        hhformer, _, _ = load_hhformer(self._hhformer_dir, device=self._device)
        student_module = StudentHead(StudentConfig()).module
        student_module.load_state_dict(load_file(str(weights)))
        student_module.eval()
        student_module.to(torch.device(self._device))
        self._hhformer = hhformer
        self._student = student_module
        self._warmup_inference()

    def _warmup_inference(self) -> None:
        if self._hhformer is None or self._student is None:
            return
        from poker_ai.learn._ml_deps import require_torch

        torch = require_torch()
        dev = torch.device(self._device)
        ids = torch.zeros((1, 8), dtype=torch.long, device=dev)
        mask = torch.ones((1, 8), dtype=torch.bool, device=dev)
        ex = torch.zeros((1, 28), dtype=torch.float32, device=dev)
        with torch.inference_mode():
            for _ in range(5):
                cls = self._hhformer(ids, key_padding_mask=mask)["cls"]
                _ = self._student(cls, ex)

    def _cls_cache_key(self, state: GameState, hand: ParsedHand, seq_len: int) -> tuple[object, ...]:
        return (
            hand.hand_id,
            seq_len,
            state.street.value,
            tuple(state.board),
            len(state.action_log),
            state.acting_seat,
        )

    def _multiway_brain(self) -> Policy:
        if self._multiway is None:
            from poker_ai.policy.multiway_stack import MultiwayStackPolicy

            self._multiway = MultiwayStackPolicy()
        return self._multiway

    @classmethod
    def from_artifacts(
        cls,
        *,
        student_dir: Path = Path("artifacts/student/v1"),
        hhformer_dir: Path = Path("artifacts/hhformer/v1"),
        cache_dir: Path = Path("artifacts/solver_cache"),
        offline_teacher: bool = False,
    ) -> DistilledPolicy:
        return cls(
            student_dir=student_dir,
            hhformer_dir=hhformer_dir,
            cache_dir=cache_dir,
            offline_teacher=offline_teacher,
        )

    def propose(
        self,
        state: GameState,
        profile: PlayerProfile,
        *,
        opponent_styles: dict[str, np.ndarray] | None = None,
        thinking_ms: int = 0,
    ) -> ActionDist:
        if state.hand_over:
            return ActionDist((), ())
        if is_multiway_context(state):
            return self._multiway_brain().propose(
                state,
                profile,
                opponent_styles=opponent_styles,
                thinking_ms=thinking_ms,
            )
        legal = legal_actions(state)
        if not legal:
            return ActionDist((), ())

        if state.street == Street.PREFLOP:
            return self._fallback.propose(state, profile)

        if self._student is None or self._hhformer is None:
            return self._equity_fallback.propose(state, profile)

        dist = self._student_propose(state, legal)
        if dist.actions:
            return dist
        return self._equity_fallback.propose(state, profile)

    def _student_propose(
        self,
        state: GameState,
        legal: tuple[EngineAction, ...],
    ) -> ActionDist:
        from poker_ai.learn._ml_deps import require_torch

        hhformer = self._hhformer
        student = self._student
        if hhformer is None or student is None:
            return ActionDist((), ())

        torch = require_torch()
        spec = _state_to_spot_spec(state)
        teacher_freqs: tuple[float, ...] | None = None
        if self._offline_teacher:
            key = cache_key(spec)
            cached = self._cache.get(key)
            if cached is not None:
                teacher_freqs = cached.frequencies
            else:
                spot = solve_spot(spec, backend="auto")
                self._cache.put(spot)
                teacher_freqs = spot.frequencies

        hand = _state_to_parsed_hand(state)
        seq = encode_hand_sequence(hand)
        ck = self._cls_cache_key(state, hand, seq.length)
        cls = self._cls_cache.get(ck)
        dev = torch.device(self._device)
        if cls is None:
            ids = torch.tensor([list(seq.token_ids)], dtype=torch.long, device=dev)
            mask = torch.zeros((1, ids.shape[1]), dtype=torch.bool, device=dev)
            if seq.length < ids.shape[1]:
                mask[0, seq.length :] = True
            with torch.inference_mode():
                cls = hhformer(ids, key_padding_mask=mask)["cls"]
            if len(self._cls_cache) >= self._cls_cache_max:
                self._cls_cache.clear()
            self._cls_cache[ck] = cls
        tex = texture_int16(tuple(state.board))
        hero_seat = state.acting_seat or 0
        hero_ip = hero_seat == state.bb_seat
        extras = encode_state_extras(
            hero_is_ip=hero_ip,
            effective_stack=max(state.stacks),
            pot_chips=max(1, state.pot),
            board_texture=tex,
            sizing_tree_id=spec.sizing_tree_id,
        )
        ex_t = torch.tensor([list(extras)], dtype=torch.float32, device=dev)
        with torch.inference_mode():
            probs = student(cls, ex_t)[0].cpu().numpy()

        if teacher_freqs is not None and len(teacher_freqs) == len(probs):
            blend = 0.9 * probs + 0.1 * np.asarray(teacher_freqs, dtype=np.float64)
            probs = blend / blend.sum()

        return _map_student_to_legal(probs, legal)

    def explain(self, state: GameState, decision: ActionDist) -> str:
        top = max(zip(decision.actions, decision.probs, strict=True), key=lambda x: x[1])
        return f"distilled_student top={top[0][0]} p={top[1]:.2f}"


def _state_to_spot_spec(state: GameState) -> SpotSpec:
    board = ",".join(_format_card(c) for c in state.board)
    return SpotSpec(
        board=board,
        pot_chips=max(1, state.pot),
        effective_stack=max(1, max(state.stacks)),
        range_oop="",
        range_ip="",
        sizing_tree_id="runtime_v1",
    )


def _state_to_parsed_hand(state: GameState) -> ParsedHand:
    board = " ".join(_format_card(c) for c in state.board)
    hero_seat = state.acting_seat or 0
    ring = ("BTN", "SB", "BB", "UTG", "MP", "CO")
    players = tuple(
        ParsedPlayer(
            i + 1,
            ring[min(i, len(ring) - 1)],
            float(state.stacks[i]),
            float(state.stacks[i]),
            i == hero_seat,
            f"p{i}",
            None,
        )
        for i in range(state.num_seats)
    )
    actions: list[ParsedAction] = []
    for ea in state.action_log[-16:]:
        pos = ring[min(ea.seat, len(ring) - 1)]
        actions.append(
            ParsedAction(
                player_id=ea.seat + 1,
                position=pos,
                street=state.street.value,
                action_type=ea.kind.value,
                amount=float(ea.amount_chips),
                is_all_in=False,
                effective_stack=float(state.stacks[ea.seat]),
                pot_before=float(state.pot),
                pot_after=float(state.pot),
                bet_to_pot_ratio=None,
            )
        )
    hero_cards = None
    holes = state.seat_holes
    if holes is not None and hero_seat < len(holes):
        hole_cards = holes[hero_seat]
        if hole_cards is not None:
            lo, hi = hole_cards
            hero_cards = f"{_format_card(lo)} {_format_card(hi)}"
    hid = abs(hash(str(state.hand_id or state.seed))) % (2**31 - 1)
    return ParsedHand(
        hand_id=hid,
        stakes="0.05/0.10",
        game_type="NLH",
        num_players=state.num_seats,
        small_blind=float(state.small_blind),
        big_blind=float(state.big_blind),
        hero_position=ring[min(hero_seat, len(ring) - 1)],
        hero_cards=hero_cards,
        board_cards=board or None,
        pot_preflop=float(state.pot),
        pot_flop=float(state.pot),
        pot_turn=0.0,
        pot_river=0.0,
        players=players,
        actions=tuple(actions),
    )


def _map_student_to_legal(
    student_probs: np.ndarray,
    legal: tuple[EngineAction, ...],
) -> ActionDist:
    labels = STUDENT_ACTIONS
    mass = {labels[i]: float(student_probs[i]) for i in range(min(len(labels), len(student_probs)))}
    keys: list[tuple[str, int, int]] = []
    probs: list[float] = []
    for a in legal:
        keys.append((a.kind.value, a.amount_chips, a.seat))
        if a.kind == EngineActionKind.FOLD:
            probs.append(mass.get("fold", 0.0))
        elif a.kind in (EngineActionKind.CHECK, EngineActionKind.CALL):
            probs.append(mass.get("check_call", 0.0))
        elif a.kind in (EngineActionKind.BET, EngineActionKind.RAISE):
            probs.append(mass.get("bet_33", 0.0) + mass.get("bet_66", 0.0) + mass.get("allin", 0.0))
        else:
            probs.append(0.0)
    s = sum(probs)
    if s <= 0:
        probs = [1.0 / len(legal)] * len(legal)
    else:
        probs = [p / s for p in probs]
    return ActionDist(tuple(keys), tuple(probs)).normalized()


def load_best_policy() -> Policy:
    """Router policy (HU vs multi-way) — automatic brain by active player count."""
    from poker_ai.config.settings import get_settings
    from poker_ai.policy.router_policy import RouterPolicy
    from poker_ai.policy.router_sources import resolve_router_student_dir

    s = get_settings()
    return RouterPolicy.from_artifacts(
        hu_student_dir=resolve_router_student_dir("hu"),
        multiway_student_dir=resolve_router_student_dir("multiway"),
        monker_export_dir=s.monker_export_dir,
        monker_blend=s.monker_teacher_blend,
    )
