"""Games: persist ante summary for training / dataset splits."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_games_ante_columns"
down_revision = "0003_games_external_ref_text"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "games",
        sa.Column(
            "uses_antes",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "games",
        sa.Column(
            "total_ante_amount",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
    )
    op.create_index("ix_games_uses_antes", "games", ["uses_antes"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_games_uses_antes", table_name="games")
    op.drop_column("games", "total_ante_amount")
    op.drop_column("games", "uses_antes")
