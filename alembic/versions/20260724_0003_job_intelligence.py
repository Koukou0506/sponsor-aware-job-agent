"""Add source payload hashes and review queue.

Revision ID: 20260724_0003
Revises: 20260724_0002
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0003"
down_revision: str | None = "20260724_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("job_versions") as batch:
        batch.add_column(sa.Column("source_payload_hash", sa.String(), nullable=True))
        batch.create_index("ix_job_versions_source_payload_hash", ["source_payload_hash"])

    op.create_table(
        "review_queue",
        sa.Column("review_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), sa.ForeignKey("jobs.job_id"), nullable=False),
        sa.Column("work_authorization_assessment_id", sa.String(), sa.ForeignKey("work_authorization_assessments.assessment_id"), nullable=False),
        sa.Column("match_assessment_id", sa.String(), sa.ForeignKey("match_assessments.assessment_id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("materials_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("workspace_id", "candidate_id", "job_id", "work_authorization_assessment_id", "match_assessment_id", "status"):
        op.create_index(f"ix_review_queue_{column}", "review_queue", [column])

    op.create_table(
        "connector_health",
        sa.Column("connector_key", sa.String(), primary_key=True),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("board_token", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("last_error_type", sa.String(), nullable=True),
        sa.Column("last_error_detail", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("platform", "board_token", "status"):
        op.create_index(f"ix_connector_health_{column}", "connector_health", [column])


def downgrade() -> None:
    for column in reversed(("platform", "board_token", "status")):
        op.drop_index(f"ix_connector_health_{column}", table_name="connector_health")
    op.drop_table("connector_health")
    for column in reversed(("workspace_id", "candidate_id", "job_id", "work_authorization_assessment_id", "match_assessment_id", "status")):
        op.drop_index(f"ix_review_queue_{column}", table_name="review_queue")
    op.drop_table("review_queue")
    with op.batch_alter_table("job_versions") as batch:
        batch.drop_index("ix_job_versions_source_payload_hash")
        batch.drop_column("source_payload_hash")
