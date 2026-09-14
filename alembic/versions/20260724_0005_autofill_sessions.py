"""Create autofill session and mapping tables.

Revision ID: 20260724_0005
Revises: 20260724_0004
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0005"
down_revision: str | None = "20260724_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "autofill_sessions",
        sa.Column("session_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column(
            "application_id",
            sa.String(),
            sa.ForeignKey("applications.application_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("active_key", sa.String(), nullable=True),
        sa.Column("ats_platform", sa.String(), nullable=False),
        sa.Column("application_url", sa.Text(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("stop_reasons", sa.JSON(), nullable=False),
        sa.Column(
            "manual_submission_confirmed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("active_key", name="uq_autofill_sessions_active_key"),
    )
    for column in (
        "workspace_id",
        "candidate_id",
        "application_id",
        "ats_platform",
        "state",
    ):
        op.create_index(f"ix_autofill_sessions_{column}", "autofill_sessions", [column])

    op.create_table(
        "autofill_field_mappings",
        sa.Column("mapping_id", sa.String(), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(),
            sa.ForeignKey("autofill_sessions.session_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("canonical_field", sa.String(), nullable=False),
        sa.Column("page_label", sa.Text(), nullable=False),
        sa.Column("selector", sa.Text(), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("requires_review", sa.Boolean(), nullable=False),
        sa.Column("risk_level", sa.String(), nullable=False),
    )
    op.create_index(
        "ix_autofill_field_mappings_session_id",
        "autofill_field_mappings",
        ["session_id"],
    )
    op.create_index(
        "ix_autofill_field_mappings_canonical_field",
        "autofill_field_mappings",
        ["canonical_field"],
    )
    op.create_index(
        "ix_autofill_field_mappings_risk_level",
        "autofill_field_mappings",
        ["risk_level"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_autofill_field_mappings_risk_level",
        table_name="autofill_field_mappings",
    )
    op.drop_index(
        "ix_autofill_field_mappings_canonical_field",
        table_name="autofill_field_mappings",
    )
    op.drop_index(
        "ix_autofill_field_mappings_session_id",
        table_name="autofill_field_mappings",
    )
    op.drop_table("autofill_field_mappings")
    for column in reversed(
        ("workspace_id", "candidate_id", "application_id", "ats_platform", "state")
    ):
        op.drop_index(f"ix_autofill_sessions_{column}", table_name="autofill_sessions")
    op.drop_table("autofill_sessions")
