"""Add live state snapshot column for play session resume (W7 Day 28)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_play_session_snapshot"
down_revision = "0007_play_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("play_sessions") as batch_op:
        batch_op.add_column(sa.Column("state_snapshot_json", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("play_sessions") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("state_snapshot_json")
