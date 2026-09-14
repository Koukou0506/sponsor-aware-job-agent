"""Create application package and tracker tables.

Revision ID: 20260724_0004
Revises: 20260724_0003
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0004"
down_revision: str | None = "20260724_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "application_packages",
        sa.Column("package_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("job_version_id", sa.String(), nullable=False),
        sa.Column("base_resume_id", sa.String(), nullable=False),
        sa.Column("active_key", sa.String(), nullable=True),
        sa.Column("tailored_resume_version", sa.Integer(), nullable=False),
        sa.Column("screening_answers_version", sa.Integer(), nullable=False),
        sa.Column("cover_letter_version", sa.Integer(), nullable=True),
        sa.Column("fact_references", sa.JSON(), nullable=False),
        sa.Column("validation_status", sa.String(), nullable=False),
        sa.Column("review_status", sa.String(), nullable=False),
        sa.Column("cover_letter_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("active_key", name="uq_application_packages_active_key"),
    )
    for column in (
        "workspace_id",
        "candidate_id",
        "job_id",
        "job_version_id",
        "validation_status",
        "review_status",
    ):
        op.create_index(f"ix_application_packages_{column}", "application_packages", [column])

    op.create_table(
        "generated_claims",
        sa.Column("claim_id", sa.String(), primary_key=True),
        sa.Column("package_id", sa.String(), sa.ForeignKey("application_packages.package_id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source_fact_ids", sa.JSON(), nullable=False),
        sa.Column("transformation_type", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("validation_status", sa.String(), nullable=False),
        sa.Column("reviewer_approved", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_generated_claims_package_id", "generated_claims", ["package_id"])
    op.create_index("ix_generated_claims_validation_status", "generated_claims", ["validation_status"])

    op.create_table(
        "screening_answers",
        sa.Column("answer_id", sa.String(), primary_key=True),
        sa.Column("package_id", sa.String(), sa.ForeignKey("application_packages.package_id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("canonical_question", sa.String(), nullable=False),
        sa.Column("displayed_question", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_fact_ids", sa.JSON(), nullable=False),
        sa.Column("requires_review", sa.Boolean(), nullable=False),
        sa.Column("risk_level", sa.String(), nullable=False),
    )
    op.create_index("ix_screening_answers_package_id", "screening_answers", ["package_id"])
    op.create_index("ix_screening_answers_canonical_question", "screening_answers", ["canonical_question"])

    op.create_table(
        "applications",
        sa.Column("application_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("package_id", sa.String(), sa.ForeignKey("application_packages.package_id"), nullable=False),
        sa.Column("application_url", sa.Text(), nullable=False),
        sa.Column("current_state", sa.String(), nullable=False),
        sa.Column("autofill_status", sa.String(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("workspace_id", "candidate_id", "job_id", "package_id", "current_state", "autofill_status"):
        op.create_index(f"ix_applications_{column}", "applications", [column])

    op.create_table(
        "application_events",
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("application_id", sa.String(), sa.ForeignKey("applications.application_id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_state", sa.String(), nullable=False),
        sa.Column("to_state", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_application_events_application_id", "application_events", ["application_id"])
    op.create_index("ix_application_events_to_state", "application_events", ["to_state"])


def downgrade() -> None:
    op.drop_index("ix_application_events_to_state", table_name="application_events")
    op.drop_index("ix_application_events_application_id", table_name="application_events")
    op.drop_table("application_events")
    for column in reversed(("workspace_id", "candidate_id", "job_id", "package_id", "current_state", "autofill_status")):
        op.drop_index(f"ix_applications_{column}", table_name="applications")
    op.drop_table("applications")
    op.drop_index("ix_screening_answers_canonical_question", table_name="screening_answers")
    op.drop_index("ix_screening_answers_package_id", table_name="screening_answers")
    op.drop_table("screening_answers")
    op.drop_index("ix_generated_claims_validation_status", table_name="generated_claims")
    op.drop_index("ix_generated_claims_package_id", table_name="generated_claims")
    op.drop_table("generated_claims")
    for column in reversed(("workspace_id", "candidate_id", "job_id", "job_version_id", "validation_status", "review_status")):
        op.drop_index(f"ix_application_packages_{column}", table_name="application_packages")
    op.drop_table("application_packages")
