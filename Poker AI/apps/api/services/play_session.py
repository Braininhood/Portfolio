"""Interactive play-vs-AI session manager (Phase W7)."""

from __future__ import annotations

import asyncio
import random
import uuid
from dataclasses import dataclass, field
from typing import Any

from poker_ai.core.cards import card_from_int
from poker_ai.core.engine import apply_action, legal_actions
from poker_ai.core.game import EngineAction, EngineActionKind, GameState, Street
from poker_ai.core.profiles import PlayerProfile
from poker_ai.league.agents.registry import build_default_roster
from poker_ai.league.sim import _pick_action, finalize_hand
from poker_ai.policy.base import Policy
from services.play_hand_eval import best_hand_description, hero_hand_payload

DEFAULT_TIMEOUT_MS = 10_000
DISCONNECT_GRACE_SEC = 5
ABANDON_TIMEOUT_SEC = 30 * 60

BOT_LABELS: dict[str, str] = {
    "main_agent": "Main AI",
    "distilled_gto": "GTO Bot",
    "main_exploiter": "Maniac",
    "cfr_stacked": "CFR Stacked",
    "tag": "TAG Bot",
    "lag": "LAG Bot",
    "nit": "Nit",
    "rock": "Rock",
    "fish": "Calling Fish",
    "call_station": "Calling Station",
    "passive_reg": "Passive Reg",
    "random": "Random Bot",
    "league_exploiter": "League Exploiter",
}

BOT_DIFFICULTY: dict[str, str] = {
    "fish": "Easiest",
    "call_station": "Easiest",
    "random": "Easy",
    "passive_reg": "Medium",
    "nit": "Medium",
    "rock": "Medium",
    "tag": "Hard",
    "lag": "Hard",
    "main_exploiter": "Hard",
    "distilled_gto": "Expert",
    "main_agent": "Expert",
    "cfr_stacked": "Expert",
}


@dataclass
class PlaySessionConfig:
    seats: int = 6
    user_seat: int = 0
    bots: list[str] = field(default_factory=list)
    buy_in_bb: int = 100
    small_blind_bb: float = 0.5
    big_blind_bb: float = 1.0
    ante_bb: float = 0.0
    timeout_ms: int = DEFAULT_TIMEOUT_MS

    def validate(self) -> None:
        if not (2 <= self.seats <= 9):
            msg = f"seats must be 2–9, got {self.seats}"
            raise ValueError(msg)
        if not (0 <= self.user_seat < self.seats):
            msg = f"user_seat out of range: {self.user_seat}"
            raise ValueError(msg)
        expected_bots = self.seats - 1
        if len(self.bots) != expected_bots:
            msg = f"expected {expected_bots} bot ids, got {len(self.bots)}"
            raise ValueError(msg)


def list_play_bots() -> list[dict[str, str]]:
    roster = build_default_roster()
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for agent in roster:
        if agent.agent_id in seen:
            continue
        seen.add(agent.agent_id)
        out.append(
            {
                "id": agent.agent_id,
                "name": BOT_LABELS.get(agent.agent_id, agent.agent_id.replace("_", " ").title()),
                "difficulty": BOT_DIFFICULTY.get(agent.agent_id, "Medium"),
            }
        )
    return out


def _policy_roster() -> dict[str, Policy]:
    return {a.agent_id: a.policy for a in build_default_roster()}


def _card_str(c: int) -> str:
    r, s = card_from_int(c)
    return f"{r}{s}"


def _hole_str(hole: tuple[int, int] | None) -> list[str] | None:
    if hole is None:
        return None
    lo, hi = hole
    return [_card_str(lo), _card_str(hi)]


def _board_str(state: GameState) -> str:
    if state.board:
        return " ".join(_card_str(c) for c in state.board)
    return ""


def _seat_bot_id(config: PlaySessionConfig, seat: int) -> str | None:
    if seat == config.user_seat:
        return None
    bot_idx = seat if seat < config.user_seat else seat - 1
    if bot_idx < 0 or bot_idx >= len(config.bots):
        return "random"
    return config.bots[bot_idx]


def _bot_display_name(bot_id: str) -> str:
    return BOT_LABELS.get(bot_id, bot_id.replace("_", " ").title())


def _bb_from_chips(chips: int, state: GameState) -> float:
    bb = max(state.big_blind, 1)
    return round(chips / bb, 1)


def _chips_from_bb(amount_bb: float, state: GameState) -> int:
    return max(0, round(amount_bb * state.big_blind))


def _deal_with_stacks(
    *,
    config: PlaySessionConfig,
    stacks: list[int],
    button_seat: int,
    seed: int,
) -> GameState:
    """Deal a new hand using existing stacks and a rotated button."""
    from poker_ai.core.engine import money_to_chips

    n = config.seats
    rng = random.Random(seed)
    deck = list(range(52))
    rng.shuffle(deck)
    holes: list[tuple[int, int] | None] = [(deck.pop(), deck.pop()) for _ in range(n)]
    full_board = (deck.pop(), deck.pop(), deck.pop(), deck.pop(), deck.pop())

    bb = money_to_chips(config.big_blind_bb)
    sb = money_to_chips(config.small_blind_bb)
    ante = money_to_chips(config.ante_bb)
    working_stacks = list(stacks)
    street_commit = [0] * n
    folded = [working_stacks[s] <= 0 for s in range(n)]
    pot = 0

    if ante > 0:
        for s in range(n):
            if folded[s]:
                continue
            post = min(ante, working_stacks[s])
            working_stacks[s] -= post
            pot += post
            if working_stacks[s] == 0:
                folded[s] = False

    if n == 2:
        sb_s = button_seat
        bb_s = (button_seat + 1) % n
    else:
        sb_s = (button_seat + 1) % n
        bb_s = (button_seat + 2) % n

    for blind_seat, amount in ((sb_s, sb), (bb_s, bb)):
        if folded[blind_seat]:
            continue
        post = min(amount, working_stacks[blind_seat])
        working_stacks[blind_seat] -= post
        street_commit[blind_seat] += post
        if working_stacks[blind_seat] == 0 and street_commit[blind_seat] > 0:
            folded[blind_seat] = False

    pot += sum(street_commit)
    current_max = max(street_commit) if pot else bb

    if n == 2:
        acting = button_seat
    else:
        acting = (bb_s + 1) % n
    for _ in range(n):
        if not folded[acting] and (working_stacks[acting] > 0 or street_commit[acting] < current_max):
            break
        acting = (acting + 1) % n

    return GameState(
        num_seats=n,
        stacks=working_stacks,
        folded=folded,
        street=Street.PREFLOP,
        board=[],
        full_board=full_board,
        pot=pot,
        button_seat=button_seat,
        sb_seat=sb_s,
        bb_seat=bb_s,
        seat_pid=list(range(1, n + 1)),
        street_commit=street_commit,
        current_max=current_max,
        big_blind=bb,
        small_blind=sb,
        acting_seat=acting if not folded[acting] else None,
        hand_over=False,
        winner_seat=None,
        seed=seed,
        last_aggressor_seat=None,
        bb_checked_preflop=False,
        raise_count_street=0,
        action_log=[],
        acted_this_round=[False] * n,
        seat_holes=holes,
        hand_id=str(seed),
    )


class PlaySession:
    """Manages a single interactive game session."""

    def __init__(self, config: PlaySessionConfig, session_id: str | None = None) -> None:
        config.validate()
        self.session_id = session_id or uuid.uuid4().hex
        self.config = config
        self.engine_state: GameState | None = None
        self.policies: dict[int, Policy] = {}
        self.profiles: dict[int, PlayerProfile] = {}
        self.hand_no = 0
        self.rng = random.Random()
        self.button_seat = 0
        self.stacks: list[int] = []
        self._timer_task: asyncio.Task[None] | None = None
        self._outbound: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._action_queue: asyncio.Queue[tuple[str, float | None]] = asyncio.Queue()
        self._loop_task: asyncio.Task[None] | None = None
        self._connected = False
        self._ws_connected = False
        self._session_alive = True
        self._grace_task: asyncio.Task[None] | None = None
        self._abandon_task: asyncio.Task[None] | None = None
        self._auto_hero_after_disconnect = False
        self._hand_action_log: list[dict[str, Any]] = []
        self.seat_bot_ids: dict[int, str] = {}
        self.completed_hands: list[dict[str, Any]] = []
        self._await_next_hand = False
        self._resume_mid_hand = False

        self.hands_played = 0
        self.net_bb = 0.0
        self.vpip_count = 0
        self.pfr_count = 0
        self.total_decisions = 0
        self._hero_voluntary_preflop = False
        self._hero_raised_preflop = False

        roster = _policy_roster()
        from poker_ai.core.engine import money_to_chips

        start_stack = money_to_chips(float(config.buy_in_bb))
        self.stacks = [start_stack] * config.seats
        for seat in range(config.seats):
            if seat == config.user_seat:
                self.profiles[seat] = PlayerProfile(profile_id="hero")
                continue
            bot_id = _seat_bot_id(config, seat) or "random"
            self.seat_bot_ids[seat] = bot_id
            self.policies[seat] = roster.get(bot_id) or roster["random"]
            self.profiles[seat] = PlayerProfile(profile_id=f"bot_{seat}")

    def _seat_name(self, seat: int) -> str:
        if seat == self.config.user_seat:
            return "You"
        bot_id = self.seat_bot_ids.get(seat, "random")
        return f"{_bot_display_name(bot_id)} (S{seat + 1})"

    async def _replace_busted_bots(self) -> None:
        """Seat a fresh random bot when a villain busts (stack < 1 BB)."""
        from poker_ai.core.engine import money_to_chips

        state = self.engine_state
        bb = state.big_blind if state else money_to_chips(self.config.big_blind_bb)
        buy_in = money_to_chips(float(self.config.buy_in_bb))
        roster = _policy_roster()
        roster_ids = list(roster.keys())
        replacements: list[dict[str, Any]] = []

        for seat in range(self.config.seats):
            if seat == self.config.user_seat:
                continue
            if self.stacks[seat] >= bb:
                continue
            old_id = self.seat_bot_ids.get(seat, "random")
            pool = [bid for bid in roster_ids if bid != old_id] or roster_ids
            new_id = self.rng.choice(pool)
            self.seat_bot_ids[seat] = new_id
            self.policies[seat] = roster.get(new_id) or roster["random"]
            self.profiles[seat] = PlayerProfile(profile_id=f"bot_{seat}_{new_id}")
            self.stacks[seat] = buy_in
            replacements.append(
                {
                    "seat": seat,
                    "old_bot_id": old_id,
                    "old_name": _bot_display_name(old_id),
                    "new_bot_id": new_id,
                    "new_name": _bot_display_name(new_id),
                    "buy_in_bb": float(self.config.buy_in_bb),
                }
            )

        if replacements:
            await self._emit({"type": "bot_replaced", "replacements": replacements})
            await self._emit_table_update()

    def session_stats(self) -> dict[str, float | int]:
        vpip_pct = round(100.0 * self.vpip_count / max(self.total_decisions, 1), 1)
        pfr_pct = round(100.0 * self.pfr_count / max(self.total_decisions, 1), 1)
        return {
            "hands": self.hands_played,
            "net_bb": round(self.net_bb, 1),
            "vpip_pct": vpip_pct,
            "pfr_pct": pfr_pct,
        }

    async def get_hint(self) -> dict[str, Any] | None:
        """AI hint for hero's current decision (W7 Day 27 — uses POST /decide logic)."""
        state = self.engine_state
        if state is None or state.hand_over or state.acting_seat != self.config.user_seat:
            return None
        from services.decide_service import run_decide_for_state
        from services.play_session_snapshot import game_state_to_dict

        try:
            result = await asyncio.to_thread(
                run_decide_for_state,
                state,
                profile_id="hero",
                policy_name="best",
            )
        except ValueError:
            return None
        actions = result.get("actions") or []
        if not actions:
            return None
        best = max(actions, key=lambda a: float(a.get("prob") or 0))
        prob = round(float(best.get("prob") or 0) * 100, 1)
        label = str(best.get("label") or best.get("kind") or "check")
        explanation = str(result.get("explanation") or "").split("\n")[0].strip()
        detail = f"Recommended: {label} ({prob}%)"
        if explanation:
            detail = f"{detail} — {explanation}"
        return {"label": label, "prob_pct": prob, "detail": detail, "game_state": game_state_to_dict(state)}

    def _cancel_abandon_timer(self) -> None:
        if self._abandon_task and not self._abandon_task.done():
            self._abandon_task.cancel()
        self._abandon_task = None

    def _start_abandon_timer(self) -> None:
        if self._abandon_task and not self._abandon_task.done():
            return
        self._abandon_task = asyncio.create_task(self._abandon_after_timeout())

    async def _abandon_after_timeout(self) -> None:
        await asyncio.sleep(ABANDON_TIMEOUT_SEC)
        if self._ws_connected:
            return
        await self._mark_session_abandoned()

    async def _mark_session_abandoned(self) -> None:
        from poker_ai.store.db import session_scope
        from poker_ai.store.play_sessions_store import update_play_session_stats, utc_now

        try:
            async with session_scope() as db:
                await update_play_session_stats(
                    db,
                    self.session_id,
                    status="abandoned",
                    finished_at=utc_now(),
                )
                await db.commit()
        except Exception:
            pass
        self.end_session()
        async with _registry_lock:
            _sessions.pop(self.session_id, None)

    async def _disconnect_grace(self) -> None:
        await asyncio.sleep(DISCONNECT_GRACE_SEC)
        if self._ws_connected:
            return
        self._auto_hero_after_disconnect = True
        state = self.engine_state
        hero = self.config.user_seat
        if state and not state.hand_over and state.acting_seat == hero:
            fallback = self._timeout_action(state)
            await self._action_queue.put((fallback, None))
        await self.persist_to_db()
        self._start_abandon_timer()

    def mark_ws_disconnected(self) -> None:
        self._ws_connected = False
        self._cancel_timer()
        if self._grace_task and not self._grace_task.done():
            self._grace_task.cancel()
        self._grace_task = asyncio.create_task(self._disconnect_grace())
        asyncio.create_task(self.persist_to_db())

    def mark_ws_connected(self) -> None:
        self._ws_connected = True
        self._auto_hero_after_disconnect = False
        if self._grace_task and not self._grace_task.done():
            self._grace_task.cancel()
        self._grace_task = None
        self._cancel_abandon_timer()

    async def persist_to_db(self) -> None:
        """Write live snapshot + stats for resume after API restart."""
        from poker_ai.store.db import session_scope
        from poker_ai.store.play_sessions_store import save_session_snapshot
        from services.play_session_snapshot import session_snapshot_dict

        snap = session_snapshot_dict(self)
        try:
            async with session_scope() as db:
                await save_session_snapshot(
                    db,
                    self.session_id,
                    snapshot=snap,
                    hands_played=self.hands_played,
                    net_bb=self.net_bb,
                    vpip_count=self.vpip_count,
                    pfr_count=self.pfr_count,
                    total_decisions=self.total_decisions,
                )
                await db.commit()
        except Exception:
            pass

    async def _emit_session_sync(self) -> None:
        """Push full table state after reconnect or DB restore."""
        state = self.engine_state
        hero = self.config.user_seat
        phase = "idle"
        if self._await_next_hand:
            phase = "await_next_hand"
        elif state is not None and not state.hand_over:
            phase = "in_hand"

        payload: dict[str, Any] = {
            "type": "session_sync",
            "hand_no": self.hand_no,
            "phase": phase,
            "session_stats": self.session_stats(),
            "study_hands": list(self.completed_hands),
            "await_next": self._await_next_hand,
        }

        if state is not None:
            payload.update(
                {
                    "street": state.street.value.lower(),
                    "board": _board_str(state),
                    "pot_bb": _bb_from_chips(state.pot, state),
                    "button_seat": state.button_seat,
                    "acting_seat": state.acting_seat,
                    "seats": self._seats_payload(state),
                    "await_next": self._await_next_hand,
                }
            )
            if state.seat_holes and state.seat_holes[hero]:
                payload["your_cards"] = _hole_str(state.seat_holes[hero]) or []
                payload["hero_hand"] = hero_hand_payload(state, hero)
        await self._emit(payload)

    async def outbound_messages(self) -> asyncio.Queue[dict[str, Any]]:
        return self._outbound

    async def _emit(self, msg: dict[str, Any]) -> None:
        await self._outbound.put(msg)

    def _seats_payload(self, state: GameState) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        hero = self.config.user_seat
        for seat in range(state.num_seats):
            behind = state.stacks[seat]
            commit = state.street_commit[seat]
            rows.append(
                {
                    "seat": seat,
                    "name": self._seat_name(seat),
                    "bot_id": self.seat_bot_ids.get(seat),
                    "stack_bb": _bb_from_chips(behind, state),
                    "bet_bb": _bb_from_chips(commit, state),
                    "total_bb": _bb_from_chips(behind + commit, state),
                    "folded": state.folded[seat],
                    "is_hero": seat == hero,
                    "is_button": seat == state.button_seat,
                    "is_sb": seat == state.sb_seat,
                    "is_bb": seat == state.bb_seat,
                    "all_in": behind == 0 and commit > 0 and not state.folded[seat],
                }
            )
        return rows

    async def _emit_table_update(self, *, acting_seat: int | None = None) -> None:
        state = self.engine_state
        if state is None:
            return
        hero = self.config.user_seat
        payload: dict[str, Any] = {
            "type": "table_update",
            "hand_no": self.hand_no,
            "street": state.street.value.lower(),
            "board": _board_str(state),
            "pot_bb": _bb_from_chips(state.pot, state),
            "button_seat": state.button_seat,
            "acting_seat": acting_seat if acting_seat is not None else state.acting_seat,
            "seats": self._seats_payload(state),
        }
        if state.seat_holes and state.seat_holes[hero]:
            payload["hero_hand"] = hero_hand_payload(state, hero)
        await self._emit(payload)

    def _legal_actions_payload(self, state: GameState) -> list[dict[str, Any]]:
        seat = state.acting_seat
        if seat is None:
            return []

        stack_behind = state.stacks[seat]
        total_chips = stack_behind + state.street_commit[seat]
        stack_bb = _bb_from_chips(stack_behind, state)
        total_bb = _bb_from_chips(total_chips, state)
        pot_bb = _bb_from_chips(state.pot, state)

        out: list[dict[str, Any]] = []
        raise_opts: list[EngineAction] = []
        bet_opts: list[EngineAction] = []
        has_all_in = False

        for action in legal_actions(state):
            if action.kind == EngineActionKind.FOLD:
                out.append({"kind": "fold"})
            elif action.kind == EngineActionKind.CHECK:
                out.append({"kind": "check"})
            elif action.kind == EngineActionKind.CALL:
                out.append({"kind": "call", "amount_bb": _bb_from_chips(action.amount_chips, state)})
            elif action.kind == EngineActionKind.BET:
                bet_opts.append(action)
            elif action.kind == EngineActionKind.RAISE:
                raise_opts.append(action)

        for action in bet_opts:
            min_bet = min(b.amount_chips for b in bet_opts)
            min_bb = _bb_from_chips(min_bet, state)
            suggested = [
                s
                for s in (
                    round(pot_bb / 3, 1),
                    round(pot_bb / 2, 1),
                    round(pot_bb * 2 / 3, 1),
                    round(pot_bb, 1),
                )
                if min_bb <= s <= stack_bb
            ]
            out.append(
                {
                    "kind": "bet",
                    "min_bb": min_bb,
                    "max_bb": stack_bb,
                    "suggested_bb": suggested[:4],
                }
            )
            if stack_behind > 0 and stack_behind <= min(b.amount_chips for b in bet_opts):
                has_all_in = True
            break

        if raise_opts:
            min_raise = min(raise_opts, key=lambda a: a.amount_chips)
            max_raise = max(raise_opts, key=lambda a: a.amount_chips)
            is_all_in = max_raise.amount_chips >= total_chips
            if is_all_in:
                has_all_in = True
            out.append(
                {
                    "kind": "raise",
                    "min_bb": _bb_from_chips(min_raise.amount_chips, state),
                    "max_bb": total_bb,
                    "raise_to_bb": _bb_from_chips(max_raise.amount_chips, state),
                    "is_all_in": is_all_in,
                }
            )

        if has_all_in and not any(x.get("kind") == "all_in" for x in out):
            out.append({"kind": "all_in", "amount_bb": total_bb})

        return out

    def _timeout_action(self, state: GameState) -> str:
        legal = legal_actions(state)
        kinds = {a.kind for a in legal}
        if EngineActionKind.CHECK in kinds:
            return "check"
        return "fold"

    async def _send_your_turn(self) -> None:
        state = self.engine_state
        if state is None or state.acting_seat != self.config.user_seat:
            return
        hero = self.config.user_seat
        holes = state.seat_holes[hero] if state.seat_holes else None
        timeout_action = self._timeout_action(state)
        from services.play_session_snapshot import game_state_to_dict

        await self._emit_table_update(acting_seat=hero)
        await self._emit(
            {
                "type": "your_turn",
                "hand_no": self.hand_no,
                "street": state.street.value.lower(),
                "board": _board_str(state),
                "pot_bb": _bb_from_chips(state.pot, state),
                "your_cards": _hole_str(holes) or [],
                "hero_hand": hero_hand_payload(state, hero),
                "legal_actions": self._legal_actions_payload(state),
                "timeout_ms": self.config.timeout_ms,
                "timeout_action": timeout_action,
                "seats": self._seats_payload(state),
                "button_seat": state.button_seat,
                "game_state": game_state_to_dict(state),
            }
        )
        if not (self._auto_hero_after_disconnect and not self._ws_connected):
            self._start_timeout(timeout_action)

    def _start_timeout(self, fallback: str) -> None:
        self._cancel_timer()
        timeout_ms = self.config.timeout_ms

        async def _timer() -> None:
            await asyncio.sleep(timeout_ms / 1000.0)
            await self._action_queue.put((fallback, None))

        self._timer_task = asyncio.create_task(_timer())

    def _cancel_timer(self) -> None:
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
        self._timer_task = None

    async def apply_user_action(self, action: str, amount: float | None) -> None:
        await self._action_queue.put((action.lower(), amount))

    async def request_next_hand(self) -> None:
        await self._action_queue.put(("__next_hand__", None))

    def _pick_engine_action(
        self,
        state: GameState,
        action: str,
        amount_bb: float | None,
    ) -> EngineAction:
        legal = legal_actions(state)
        seat = state.acting_seat
        if seat is None:
            msg = "no acting seat"
            raise ValueError(msg)

        if action == "fold":
            return next(a for a in legal if a.kind == EngineActionKind.FOLD)
        if action == "check":
            return next(a for a in legal if a.kind == EngineActionKind.CHECK)
        if action == "call":
            return next(a for a in legal if a.kind == EngineActionKind.CALL)
        if action == "all_in":
            raises = [a for a in legal if a.kind == EngineActionKind.RAISE]
            if raises:
                return max(raises, key=lambda a: a.amount_chips)
            bets = [a for a in legal if a.kind == EngineActionKind.BET]
            if bets:
                return max(bets, key=lambda a: a.amount_chips)
            return next(a for a in legal if a.kind == EngineActionKind.CALL)

        if action == "bet":
            bets = [a for a in legal if a.kind == EngineActionKind.BET]
            if not bets:
                msg = "bet not legal"
                raise ValueError(msg)
            target = _chips_from_bb(amount_bb or 0.0, state)
            return min(bets, key=lambda a: abs(a.amount_chips - target))

        if action == "raise":
            raises = [a for a in legal if a.kind == EngineActionKind.RAISE]
            if not raises:
                msg = "raise not legal"
                raise ValueError(msg)
            target = _chips_from_bb(amount_bb or 0.0, state)
            return min(raises, key=lambda a: abs(a.amount_chips - target))

        msg = f"unknown action {action!r}"
        raise ValueError(msg)

    def _action_log_entry(
        self,
        *,
        state: GameState,
        seat: int,
        action: EngineAction,
        before_commit: int,
    ) -> dict[str, Any]:
        kind = action.kind.value.lower()
        bb = state.big_blind
        total_chips = state.stacks[seat] + state.street_commit[seat]
        is_all_in = state.stacks[seat] == 0 and state.street_commit[seat] > 0

        entry: dict[str, Any] = {
            "hand_no": self.hand_no,
            "street": state.street.value.lower(),
            "seat": seat,
            "name": self._seat_name(seat),
            "action": kind,
            "pot_bb": _bb_from_chips(state.pot, state),
            "is_all_in": is_all_in,
        }

        if kind == "fold":
            entry["label"] = f"{entry['name']} folds"
        elif kind == "check":
            entry["label"] = f"{entry['name']} checks"
        elif kind == "call":
            add_bb = _bb_from_chips(action.amount_chips, state)
            entry["amount_bb"] = add_bb
            entry["label"] = f"{entry['name']} calls {add_bb:g} BB" + (" (all-in)" if is_all_in else "")
        elif kind == "bet":
            add_bb = _bb_from_chips(action.amount_chips, state)
            entry["amount_bb"] = add_bb
            entry["label"] = f"{entry['name']} bets {add_bb:g} BB" + (" (all-in)" if is_all_in else "")
        elif kind == "raise":
            raise_to_bb = _bb_from_chips(state.street_commit[seat], state)
            add_bb = _bb_from_chips(state.street_commit[seat] - before_commit, state)
            entry["amount_bb"] = add_bb
            entry["raise_to_bb"] = raise_to_bb
            entry["label"] = f"{entry['name']} raises to {raise_to_bb:g} BB" + (" (all-in)" if is_all_in else "")

        return entry

    async def _emit_action(self, entry: dict[str, Any], *, opponent: bool) -> None:
        self._hand_action_log.append(entry)
        if opponent:
            state = self.engine_state
            await self._emit(
                {
                    "type": "opponent_action",
                    "entry": entry,
                    "seats": self._seats_payload(state) if state else [],
                    "pot_bb": _bb_from_chips(state.pot, state) if state else 0.0,
                }
            )
        else:
            await self._emit({"type": "action_log", "entry": entry})
        asyncio.create_task(self.persist_to_db())

    def _track_hero_preflop(self, action: EngineAction) -> None:
        if self.engine_state is None or self.engine_state.street != Street.PREFLOP:
            return
        if action.kind in (EngineActionKind.CALL, EngineActionKind.BET, EngineActionKind.RAISE):
            self._hero_voluntary_preflop = True
        if action.kind in (EngineActionKind.BET, EngineActionKind.RAISE):
            self._hero_raised_preflop = True

    async def _run_bot_action(self, seat: int) -> EngineAction:
        state = self.engine_state
        if state is None:
            msg = "no engine state"
            raise RuntimeError(msg)
        policy = self.policies[seat]
        legal = legal_actions(state)
        dist = await asyncio.to_thread(
            policy.propose,
            state,
            self.profiles[seat],
        )
        action = _pick_action(dist, legal, self.rng)
        return action

    async def _maybe_street_change(self, prev_street: Street) -> None:
        state = self.engine_state
        if state is None or state.street == prev_street:
            return
        await self._emit(
            {
                "type": "street_change",
                "street": state.street.value.lower(),
                "board": _board_str(state),
                "seats": self._seats_payload(state),
                "pot_bb": _bb_from_chips(state.pot, state),
                "hero_hand": hero_hand_payload(state, self.config.user_seat),
            }
        )

    def _showdown_rows(self, *, start_totals: list[int] | None = None) -> list[dict[str, Any]]:
        from services.play_hand_eval import rank_for_hole_board

        state = self.engine_state
        if state is None:
            return []
        board = list(state.full_board) if state.full_board else list(state.board)
        bb = max(state.big_blind, 1)
        hero = self.config.user_seat

        deltas_bb: list[float] = []
        if start_totals:
            for seat in range(state.num_seats):
                end_total = state.stacks[seat] + state.street_commit[seat]
                deltas_bb.append(round((end_total - start_totals[seat]) / bb, 1))
        max_win = max(deltas_bb) if deltas_bb else 0.0

        rows: list[dict[str, Any]] = []
        for seat in range(state.num_seats):
            holes = state.seat_holes[seat] if state.seat_holes else None
            at_showdown = not state.folded[seat]
            is_hero = seat == hero
            if not at_showdown and not is_hero:
                continue
            if not at_showdown and is_hero and (not start_totals or deltas_bb[seat] <= 0):
                continue

            hand_info = best_hand_description(hole=holes, board=board)
            rank_val = rank_for_hole_board(hole=holes, board=board) if len(board) >= 5 else 10**9
            chips_bb = deltas_bb[seat] if start_totals and seat < len(deltas_bb) else 0.0
            if start_totals:
                won = chips_bb > 0.01 and chips_bb >= max_win - 0.01
            else:
                won = seat == state.winner_seat

            rows.append(
                {
                    "seat": seat,
                    "name": self._seat_name(seat),
                    "bot_id": self.seat_bot_ids.get(seat),
                    "cards": _hole_str(holes) or [],
                    "hand_rank": hand_info["name"],
                    "hand_category": hand_info["category"],
                    "rank_value": rank_val,
                    "won": won,
                    "chips_won_bb": chips_bb,
                    "folded": state.folded[seat],
                }
            )

        rows.sort(key=lambda r: (r["rank_value"], -r["chips_won_bb"]))
        return rows

    def _pot_bb_from_totals(self, start_totals: list[int] | None) -> float:
        state = self.engine_state
        if state is None or not start_totals:
            return 0.0
        bb = max(state.big_blind, 1)
        end_totals = [state.stacks[s] + state.street_commit[s] for s in range(state.num_seats)]
        won = sum(max(0, end_totals[s] - start_totals[s]) for s in range(state.num_seats))
        return round(won / bb, 1)

    async def _send_showdown(
        self,
        *,
        hero_result_bb: float,
        pot_bb: float,
        start_totals: list[int] | None = None,
    ) -> None:
        if pot_bb <= 0 and start_totals:
            pot_bb = self._pot_bb_from_totals(start_totals)
        rows = self._showdown_rows(start_totals=start_totals)
        winners = [r for r in rows if r["won"]]
        if not winners and rows:
            best_rank = min(r["rank_value"] for r in rows if not r["folded"])
            winners = [r for r in rows if not r["folded"] and r["rank_value"] == best_rank]
        winner = winners[0] if len(winners) == 1 else None
        await self._emit(
            {
                "type": "showdown",
                "seats": rows,
                "winners": winners,
                "hero_result_bb": hero_result_bb,
                "winner": winner,
                "pot_bb": pot_bb,
                "board": _board_str(self.engine_state) if self.engine_state else "",
            }
        )

    async def start_hand(self) -> None:
        self.hand_no += 1
        self._hero_voluntary_preflop = False
        self._hero_raised_preflop = False
        self._hand_action_log = []
        seed = self.rng.randint(0, 2**31 - 1)
        if self.hand_no > 1:
            self.button_seat = (self.button_seat + 1) % self.config.seats
        self.engine_state = _deal_with_stacks(
            config=self.config,
            stacks=self.stacks,
            button_seat=self.button_seat,
            seed=seed,
        )

        await self._emit(
            {
                "type": "hand_started",
                "hand_no": self.hand_no,
                "button_seat": self.engine_state.button_seat,
                "seats": self._seats_payload(self.engine_state),
                "ante_bb": self.config.ante_bb,
            }
        )
        await self._emit_table_update()

    async def _finish_hand(self, *, went_showdown: bool, hero_result_bb: float) -> dict[str, Any]:
        state = self.engine_state
        if state is None:
            return {}
        self.stacks = list(state.stacks)
        self.hands_played += 1
        self.net_bb += hero_result_bb
        if self._hero_voluntary_preflop:
            self.vpip_count += 1
        if self._hero_raised_preflop:
            self.pfr_count += 1

        hero = self.config.user_seat
        holes = state.seat_holes[hero] if state.seat_holes else None
        board = list(state.full_board) if state.full_board else list(state.board)
        all_in_count = sum(1 for e in self._hand_action_log if e.get("is_all_in"))
        start_totals = getattr(self, "_hand_start_totals", None)
        showdown_rows = self._showdown_rows(start_totals=start_totals) if went_showdown else []
        winners = [r for r in showdown_rows if r.get("won")]
        winner = winners[0] if len(winners) == 1 else None

        opponent_bb: dict[str, float] = {}
        if start_totals:
            bb = max(state.big_blind, 1)
            for seat, bot_id in self.seat_bot_ids.items():
                if seat == hero or not bot_id:
                    continue
                end_total = state.stacks[seat]
                villain_delta_bb = (end_total - start_totals[seat]) / bb
                opponent_bb[str(bot_id)] = round(-villain_delta_bb, 1)

        hand_record = {
            "hand_no": self.hand_no,
            "result_bb": hero_result_bb,
            "went_showdown": went_showdown,
            "board": " ".join(_card_str(c) for c in board[:5]) if board else "",
            "hero_cards": " ".join(_hole_str(holes) or []),
            "hero_hand": best_hand_description(hole=holes, board=board[:5]),
            "action_log": list(self._hand_action_log),
            "showdown": showdown_rows,
            "winners": winners,
            "winner": winner,
            "all_in_count": all_in_count,
            "ending_street": state.street.value.lower(),
            "bot_lineup": {str(s): self.seat_bot_ids.get(s) for s in self.seat_bot_ids},
            "opponent_bb": opponent_bb,
        }
        self.completed_hands.append(hand_record)
        self._auto_hero_after_disconnect = False

        await self._emit(
            {
                "type": "hand_complete",
                "hand_no": self.hand_no,
                "result_bb": hero_result_bb,
                "went_showdown": went_showdown,
                "session_stats": self.session_stats(),
                "action_log": list(self._hand_action_log),
                "hand_record": hand_record,
                "all_in_count": all_in_count,
            }
        )
        await self.persist_to_db()
        await self._replace_busted_bots()
        return hand_record

    async def _play_hand_loop(self) -> None:
        state = self.engine_state
        if state is None:
            return
        hero = self.config.user_seat
        start_totals = [
            state.stacks[s] + state.street_commit[s] for s in range(state.num_seats)
        ]
        self._hand_start_totals = start_totals
        start_total = start_totals[hero]
        went_showdown = False
        pot_at_showdown = 0.0

        while state and not state.hand_over:
            seat = state.acting_seat
            if seat is None:
                break
            prev_street = state.street
            before_commit = state.street_commit[seat]

            if seat == hero:
                auto_disconnect = self._auto_hero_after_disconnect and not self._ws_connected
                if auto_disconnect:
                    action_str = self._timeout_action(state)
                    amount_bb = None
                    await self._emit(
                        {
                            "type": "timeout",
                            "action": action_str,
                            "message": f"Disconnected — auto-{action_str}{'ed' if action_str.endswith('e') else 'd'}",
                        }
                    )
                else:
                    await self._send_your_turn()
                    action_str, amount_bb = await self._action_queue.get()
                    self._cancel_timer()
                if action_str == "__next_hand__":
                    return
                try:
                    engine_action = self._pick_engine_action(state, action_str, amount_bb)
                except (StopIteration, ValueError):
                    fallback = self._timeout_action(state)
                    engine_action = self._pick_engine_action(state, fallback, None)
                    await self._emit(
                        {
                            "type": "timeout",
                            "action": fallback,
                            "message": f"Time expired — auto-{fallback}{'ed' if fallback.endswith('e') else 'd'}",
                        }
                    )
                self.total_decisions += 1
                self._track_hero_preflop(engine_action)
                state = apply_action(state, engine_action)
                self.engine_state = state
                entry = self._action_log_entry(
                    state=state, seat=seat, action=engine_action, before_commit=before_commit
                )
                await self._emit_action(entry, opponent=False)
            else:
                await asyncio.sleep(0.4)
                engine_action = await self._run_bot_action(seat)
                state = apply_action(state, engine_action)
                self.engine_state = state
                entry = self._action_log_entry(
                    state=state, seat=seat, action=engine_action, before_commit=before_commit
                )
                await self._emit_action(entry, opponent=True)

            await self._maybe_street_change(prev_street)
            await self._emit_table_update()
            if state.street == Street.SHOWDOWN and not state.hand_over:
                went_showdown = True
                pot_at_showdown = _bb_from_chips(state.pot, state)
                from poker_ai.core.showdown import resolve_showdown

                resolve_showdown(state, start_totals=start_totals)
                self.engine_state = state

        if finalize_hand(state, start_totals=start_totals):
            went_showdown = True
            if pot_at_showdown <= 0:
                pot_at_showdown = _bb_from_chips(state.pot, state)
        self.engine_state = state

        end_total = state.stacks[hero] + state.street_commit[hero]
        bb = max(state.big_blind, 1)
        hero_result_bb = round((end_total - start_total) / bb, 1)
        if went_showdown or state.street == Street.SHOWDOWN:
            await self._send_showdown(
                hero_result_bb=hero_result_bb,
                pot_bb=pot_at_showdown,
                start_totals=start_totals,
            )
        await self._finish_hand(went_showdown=went_showdown, hero_result_bb=hero_result_bb)

    async def run_session_loop(self) -> None:
        try:
            while self._session_alive:
                if self._await_next_hand:
                    await self._emit_session_sync()
                    await self._emit({"type": "await_next_hand", "hand_no": self.hand_no})
                else:
                    if self._resume_mid_hand:
                        self._resume_mid_hand = False
                        await self._emit_session_sync()
                    else:
                        await self.start_hand()
                    await self._play_hand_loop()
                    self._await_next_hand = True
                    await self.persist_to_db()
                    await self._emit({"type": "await_next_hand", "hand_no": self.hand_no})

                cmd, payload = await self._action_queue.get()
                if cmd == "__end_session__":
                    break
                if cmd != "__next_hand__":
                    await self._action_queue.put((cmd, payload))
                self._await_next_hand = False
        except asyncio.CancelledError:
            raise

    def connect(self) -> None:
        self._connected = True
        self.mark_ws_connected()

    def disconnect(self) -> None:
        """WebSocket closed — keep session alive for reconnect (W7 Day 28)."""
        self.mark_ws_disconnected()

    def end_session(self) -> None:
        self._session_alive = False
        self._cancel_timer()
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()

    async def ensure_loop(self) -> None:
        if self._loop_task is None or self._loop_task.done():
            self.connect()
            self._loop_task = asyncio.create_task(self.run_session_loop())


_sessions: dict[str, PlaySession] = {}
_registry_lock = asyncio.Lock()


async def create_session(config: PlaySessionConfig) -> PlaySession:
    async with _registry_lock:
        session = PlaySession(config)
        _sessions[session.session_id] = session
        return session


async def get_session(session_id: str) -> PlaySession | None:
    async with _registry_lock:
        return _sessions.get(session_id)


def _config_from_table_json(raw: dict[str, Any]) -> PlaySessionConfig:
    return PlaySessionConfig(
        seats=int(raw.get("seats") or 6),
        user_seat=int(raw.get("user_seat") or 0),
        bots=list(raw.get("bots") or []),
        buy_in_bb=int(raw.get("buy_in_bb") or 100),
        small_blind_bb=float(raw.get("small_blind_bb") or 0.5),
        big_blind_bb=float(raw.get("big_blind_bb") or 1.0),
        ante_bb=float(raw.get("ante_bb") or 0.0),
        timeout_ms=int(raw.get("timeout_ms") or DEFAULT_TIMEOUT_MS),
    )


def _hand_record_from_db_row(h: dict[str, Any]) -> dict[str, Any] | None:
    import json

    raw = h.get("summary_json")
    if not raw:
        return None
    try:
        summary = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except json.JSONDecodeError:
        return None
    return summary.get("hand_record") or summary


async def restore_session_from_row(
    row: dict[str, Any],
    *,
    hand_rows: list[dict[str, Any]] | None = None,
) -> PlaySession | None:
    """Rebuild in-memory session from DB row + optional persisted hands."""
    import json

    from services.play_session_snapshot import apply_snapshot_to_session

    session_id = str(row["session_id"])
    async with _registry_lock:
        if session_id in _sessions:
            return _sessions[session_id]

        config_raw = row.get("table_config_json")
        config_dict: dict[str, Any] = {}
        if config_raw:
            try:
                config_dict = json.loads(config_raw) if isinstance(config_raw, str) else dict(config_raw)
            except json.JSONDecodeError:
                config_dict = {}
        config = _config_from_table_json(config_dict)
        try:
            config.validate()
        except ValueError:
            return None

        ps = PlaySession(config, session_id=session_id)
        ps.hands_played = int(row.get("hands_played") or 0)
        ps.net_bb = float(row.get("net_bb") or 0.0)
        ps.vpip_count = int(row.get("vpip_count") or 0)
        ps.pfr_count = int(row.get("pfr_count") or 0)
        ps.total_decisions = int(row.get("total_decisions") or 0)

        snap_raw = row.get("state_snapshot_json")
        if snap_raw:
            try:
                snap = json.loads(snap_raw) if isinstance(snap_raw, str) else dict(snap_raw)
                apply_snapshot_to_session(ps, snap)
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

        if hand_rows:
            ps.completed_hands = []
            for h in sorted(hand_rows, key=lambda x: int(x["hand_no"])):
                rec = _hand_record_from_db_row(h)
                if rec:
                    ps.completed_hands.append(rec)

        _sessions[session_id] = ps
        return ps


async def get_or_restore_session(
    session_id: str,
    *,
    row: dict[str, Any] | None = None,
    hand_rows: list[dict[str, Any]] | None = None,
) -> PlaySession | None:
    live = await get_session(session_id)
    if live is not None:
        return live
    if row is None:
        return None
    if str(row.get("status") or "") != "in_progress":
        return None
    return await restore_session_from_row(row, hand_rows=hand_rows)


async def remove_session(session_id: str) -> None:
    async with _registry_lock:
        sess = _sessions.pop(session_id, None)
        if sess:
            sess.end_session()
