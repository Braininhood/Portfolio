"""Extensive-form game protocol for tabular CFR (Phase 6)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ExtensiveGame(Protocol):
    """Two-player zero-sum extensive game with perfect recall info sets."""

    num_players: int

    def initial_chance_outcomes(self) -> tuple[tuple[float, object], ...]:
        """Root chance outcomes ``(probability, child_state)``."""
        ...

    def current_player(self, state: object) -> int | None:
        """Acting player index, ``None`` for chance, ``-1`` for terminal."""
        ...

    def legal_actions(self, state: object) -> tuple[int, ...]:
        """Integer action ids (stable per state shape)."""
        ...

    def next_state(self, state: object, action: int) -> object:
        """Deterministic child after a player action."""
        ...

    def chance_outcomes(self, state: object) -> tuple[tuple[float, object], ...]:
        """Chance branches at ``state`` (empty if not chance)."""
        ...

    def terminal_utility(self, state: object, player: int) -> float:
        """Payoff for ``player`` at a terminal node (zero-sum)."""
        ...

    def information_set_key(self, state: object, player: int) -> str:
        """Perfect-recall info-set id for ``player``."""
        ...
