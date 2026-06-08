"""Games: record ingest time for incremental feature builds."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_games_ingested_at"
down_revision = "0004_games_ante_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite rejects ``ADD COLUMN ... NOT NULL`` with ``DEFAULT CURRENT_TIMESTAMP`` (non-constant default).
    # Add nullable, backfill, then enforce NOT NULL via table rebuild (batch).
    op.add_column(
        "games",
        sa.Column("ingested_at", sa.DateTime(), nullable=True),
    )
    op.execute(sa.text("UPDATE games SET ingested_at = datetime('now') WHERE ingested_at IS NULL"))
    with op.batch_alter_table("games") as batch_op:
        batch_op.alter_column(
            "ingested_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )
    op.create_index("ix_games_ingested_at", "games", ["ingested_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_games_ingested_at", table_name="games")
    op.drop_column("games", "ingested_at")
