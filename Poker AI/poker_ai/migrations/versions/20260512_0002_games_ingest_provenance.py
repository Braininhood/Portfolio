"""Add ingest provenance for multi-room / multi-format hands."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_games_ingest_provenance"
down_revision = "0001_phase1_store"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "games",
        sa.Column(
            "ingest_source",
            sa.String(length=32),
            nullable=False,
            server_default="normalized_txt",
        ),
    )
    op.add_column(
        "games",
        sa.Column(
            "external_ref",
            sa.String(length=128),
            nullable=False,
            server_default="__pending__",
        ),
    )
    op.execute("UPDATE games SET external_ref = CAST(hand_id AS TEXT)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_games_ingest_external "
        "ON games (ingest_source, external_ref) "
        "WHERE length(trim(external_ref)) > 0"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_games_ingest_external")
    op.drop_column("games", "external_ref")
    op.drop_column("games", "ingest_source")
