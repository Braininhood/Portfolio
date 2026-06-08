"""Widen games.external_ref — long PHH tree paths truncated at 128 broke UNIQUE."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_games_external_ref_text"
down_revision = "0002_games_ingest_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("games") as batch:
        batch.alter_column(
            "external_ref",
            existing_type=sa.String(length=128),
            type_=sa.Text(),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("games") as batch:
        batch.alter_column(
            "external_ref",
            existing_type=sa.Text(),
            type_=sa.String(length=128),
            existing_nullable=False,
        )
