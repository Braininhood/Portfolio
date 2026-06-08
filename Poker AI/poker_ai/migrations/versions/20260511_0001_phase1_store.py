"""Phase 1 canonical store tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_phase1_store"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "games",
        sa.Column("hand_id", sa.Integer(), nullable=False),
        sa.Column("stakes", sa.String(length=32), nullable=False),
        sa.Column("game_type", sa.String(length=16), nullable=False),
        sa.Column("num_players", sa.Integer(), nullable=False),
        sa.Column("small_blind", sa.Float(), nullable=False),
        sa.Column("big_blind", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("hand_id"),
    )
    op.create_table(
        "players",
        sa.Column("hand_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(length=32), nullable=False),
        sa.Column("stack_size", sa.Float(), nullable=False),
        sa.Column("bb_size", sa.Float(), nullable=False),
        sa.Column("is_hero", sa.Boolean(), nullable=False),
        sa.Column("player_uid", sa.String(length=64), nullable=False),
        sa.Column("screen_name", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["hand_id"], ["games.hand_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("hand_id", "player_id"),
    )
    op.create_index("ix_players_player_uid", "players", ["player_uid"], unique=False)
    op.create_index("ix_players_is_hero", "players", ["is_hero"], unique=False)

    op.create_table(
        "hands",
        sa.Column("hand_id", sa.Integer(), nullable=False),
        sa.Column("hero_position", sa.String(length=32), nullable=True),
        sa.Column("hero_cards", sa.String(length=16), nullable=True),
        sa.Column("board_cards", sa.Text(), nullable=True),
        sa.Column("pot_preflop", sa.Float(), nullable=False),
        sa.Column("pot_flop", sa.Float(), nullable=False),
        sa.Column("pot_turn", sa.Float(), nullable=False),
        sa.Column("pot_river", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["hand_id"], ["games.hand_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("hand_id"),
    )

    op.create_table(
        "actions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hand_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(length=32), nullable=False),
        sa.Column("street", sa.String(length=16), nullable=False),
        sa.Column("action_type", sa.String(length=16), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("is_all_in", sa.Boolean(), nullable=False),
        sa.Column("effective_stack", sa.Float(), nullable=False),
        sa.Column("pot_before", sa.Float(), nullable=False),
        sa.Column("pot_after", sa.Float(), nullable=False),
        sa.Column("bet_to_pot_ratio", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["hand_id"], ["hands.hand_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_actions_hand_id", "actions", ["hand_id"], unique=False)
    op.create_index("ix_actions_hand_street", "actions", ["hand_id", "street"], unique=False)
    op.create_index("ix_actions_player_id", "actions", ["player_id"], unique=False)
    op.create_index("ix_actions_street", "actions", ["street"], unique=False)

    op.create_table(
        "results",
        sa.Column("hand_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(length=32), nullable=False),
        sa.Column("cards", sa.String(length=32), nullable=False),
        sa.Column("net_result", sa.Float(), nullable=False),
        sa.Column("won_pot", sa.Float(), nullable=False),
        sa.Column("showdown", sa.Boolean(), nullable=False),
        sa.Column("final_equity", sa.Float(), nullable=True),
        sa.Column("preflop_equity", sa.Float(), nullable=True),
        sa.Column("flop_equity", sa.Float(), nullable=True),
        sa.Column("turn_equity", sa.Float(), nullable=True),
        sa.Column("river_equity", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["hand_id"], ["hands.hand_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("hand_id", "player_id"),
    )
    op.create_index("ix_results_hand_id", "results", ["hand_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_results_hand_id", table_name="results")
    op.drop_table("results")
    op.drop_index("ix_actions_street", table_name="actions")
    op.drop_index("ix_actions_player_id", table_name="actions")
    op.drop_index("ix_actions_hand_street", table_name="actions")
    op.drop_index("ix_actions_hand_id", table_name="actions")
    op.drop_table("actions")
    op.drop_table("hands")
    op.drop_index("ix_players_is_hero", table_name="players")
    op.drop_index("ix_players_player_uid", table_name="players")
    op.drop_table("players")
    op.drop_table("games")
