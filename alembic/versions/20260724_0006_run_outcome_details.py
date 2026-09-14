"""Add distinct duplicate and hard-fail run counters.

Revision ID: 20260724_0006
Revises: 20260724_0005
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0006"
down_revision: str | None = "20260724_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("run_records") as batch:
        batch.add_column(
            sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0")
        )
        batch.add_column(
            sa.Column("hard_failed_count", sa.Integer(), nullable=False, server_default="0")
        )


def downgrade() -> None:
    with op.batch_alter_table("run_records") as batch:
        batch.drop_column("hard_failed_count")
        batch.drop_column("duplicate_count")
