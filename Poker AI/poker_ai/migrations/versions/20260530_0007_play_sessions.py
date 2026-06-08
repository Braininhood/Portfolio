"""Interactive play-vs-AI sessions (Phase W7)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_play_sessions"
down_revision = "0006_jobs_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "play_sessions",
        sa.Column("session_id", sa.Text(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(datetime('now'))")),
        sa.Column("status", sa.Text(), nullable=False, server_default="in_progress"),
        sa.Column("table_config_json", sa.Text(), nullable=True),
        sa.Column("hands_played", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("net_bb", sa.Float(), nullable=False, server_default="0"),
        sa.Column("vpip_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pfr_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_decisions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "play_hands",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Text(), sa.ForeignKey("play_sessions.session_id"), nullable=False),
        sa.Column("hand_no", sa.Integer(), nullable=False),
        sa.Column("result_bb", sa.Float(), nullable=False),
        sa.Column("went_showdown", sa.Boolean(), nullable=False),
        sa.Column("board", sa.Text(), nullable=True),
        sa.Column("hero_cards", sa.Text(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=True),
    )
    op.create_index("ix_play_hands_session_id", "play_hands", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_play_hands_session_id", table_name="play_hands")
    op.drop_table("play_hands")
    op.drop_table("play_sessions")
