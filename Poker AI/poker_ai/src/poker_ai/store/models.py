"""SQLAlchemy ORM models for the canonical hand-history store (Phase 1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all store tables."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


class Game(Base):
    """One row per hand — table metadata and stakes."""

    __tablename__ = "games"

    hand_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingest_source: Mapped[str] = mapped_column(String(32), nullable=False)
    external_ref: Mapped[str] = mapped_column(Text, nullable=False)
    stakes: Mapped[str] = mapped_column(String(32), nullable=False)
    game_type: Mapped[str] = mapped_column(String(16), nullable=False)
    num_players: Mapped[int] = mapped_column(Integer, nullable=False)
    small_blind: Mapped[float] = mapped_column(Float, nullable=False)
    big_blind: Mapped[float] = mapped_column(Float, nullable=False)
    # Posted antes (same currency as blinds). Populated from ParsedHand.antes on ingest.
    uses_antes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_ante_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    )

    players: Mapped[list[Player]] = relationship(
        back_populates="game",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    hand_row: Mapped[Hand | None] = relationship(
        back_populates="game",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )


class Player(Base):
    """Seat snapshot for one player in one hand."""

    __tablename__ = "players"

    hand_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("games.hand_id", ondelete="CASCADE"),
        primary_key=True,
    )
    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position: Mapped[str] = mapped_column(String(32), nullable=False)
    stack_size: Mapped[float] = mapped_column(Float, nullable=False)
    bb_size: Mapped[float] = mapped_column(Float, nullable=False)
    is_hero: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    player_uid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    screen_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    game: Mapped[Game] = relationship(back_populates="players")


class Hand(Base):
    """Board, pots, and hero hole cards for one hand."""

    __tablename__ = "hands"

    hand_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("games.hand_id", ondelete="CASCADE"),
        primary_key=True,
    )
    hero_position: Mapped[str | None] = mapped_column(String(32), nullable=True)
    hero_cards: Mapped[str | None] = mapped_column(String(16), nullable=True)
    board_cards: Mapped[str | None] = mapped_column(Text, nullable=True)
    pot_preflop: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pot_flop: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pot_turn: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pot_river: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    game: Mapped[Game] = relationship(back_populates="hand_row")
    actions: Mapped[list[Action]] = relationship(
        back_populates="hand",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Action.id",
    )
    results: Mapped[list[Result]] = relationship(
        back_populates="hand",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Action(Base):
    """One parsed betting line."""

    __tablename__ = "actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hand_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("hands.hand_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    player_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    position: Mapped[str] = mapped_column(String(32), nullable=False)
    street: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_all_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    effective_stack: Mapped[float] = mapped_column(Float, nullable=False)
    pot_before: Mapped[float] = mapped_column(Float, nullable=False)
    pot_after: Mapped[float] = mapped_column(Float, nullable=False)
    bet_to_pot_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    hand: Mapped[Hand] = relationship(back_populates="actions")


class Result(Base):
    """Showdown / accounting outcome per seat (equity columns reserved; backfill TBD)."""

    __tablename__ = "results"

    hand_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("hands.hand_id", ondelete="CASCADE"),
        primary_key=True,
    )
    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position: Mapped[str] = mapped_column(String(32), nullable=False)
    cards: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    net_result: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    won_pot: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    showdown: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    final_equity: Mapped[float | None] = mapped_column(Float, nullable=True)
    preflop_equity: Mapped[float | None] = mapped_column(Float, nullable=True)
    flop_equity: Mapped[float | None] = mapped_column(Float, nullable=True)
    turn_equity: Mapped[float | None] = mapped_column(Float, nullable=True)
    river_equity: Mapped[float | None] = mapped_column(Float, nullable=True)

    hand: Mapped[Hand] = relationship(back_populates="results")
