"""Create core storage schema.

Revision ID: 20260724_0001
Revises:
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("company_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("canonical_name", sa.String(), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("domain", sa.String(), nullable=True),
    )
    op.create_index("ix_companies_workspace_id", "companies", ["workspace_id"])
    op.create_index("ix_companies_canonical_name", "companies", ["canonical_name"])

    op.create_table(
        "jobs",
        sa.Column("job_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("external_job_id", sa.String(), nullable=False),
        sa.Column("source_platform", sa.String(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.company_id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("normalized_title", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("role_track", sa.String(), nullable=False),
        sa.Column("description_raw", sa.Text(), nullable=False),
        sa.Column("description_normalized", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
    )
    for column in (
        "workspace_id",
        "external_job_id",
        "source_platform",
        "company_id",
        "normalized_title",
        "country",
        "role_track",
        "status",
    ):
        op.create_index(f"ix_jobs_{column}", "jobs", [column])

    op.create_table(
        "job_versions",
        sa.Column("job_version_id", sa.String(), primary_key=True),
        sa.Column("job_id", sa.String(), sa.ForeignKey("jobs.job_id"), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("description_snapshot", sa.Text(), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_job_versions_job_id", "job_versions", ["job_id"])
    op.create_index("ix_job_versions_content_hash", "job_versions", ["content_hash"])

    op.create_table(
        "work_authorization_assessments",
        sa.Column("assessment_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), sa.ForeignKey("jobs.job_id"), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("route_type", sa.String(), nullable=False),
        sa.Column("route_ownership", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("work_authorization_fit", sa.Float(), nullable=False),
        sa.Column("hard_fail", sa.Boolean(), nullable=False),
        sa.Column("hard_fail_reasons", sa.JSON(), nullable=False),
        sa.Column("unresolved_items", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("ruleset_version", sa.String(), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("workspace_id", "candidate_id", "job_id", "country", "status"):
        op.create_index(
            f"ix_work_authorization_assessments_{column}",
            "work_authorization_assessments",
            [column],
        )

    op.create_table(
        "match_assessments",
        sa.Column("assessment_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), sa.ForeignKey("jobs.job_id"), nullable=False),
        sa.Column("selected_resume_track", sa.String(), nullable=False),
        sa.Column("component_scores", sa.JSON(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("matching_evidence", sa.JSON(), nullable=False),
        sa.Column("missing_requirements", sa.JSON(), nullable=False),
        sa.Column("disqualifiers", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("workspace_id", "candidate_id", "job_id", "total_score"):
        op.create_index(f"ix_match_assessments_{column}", "match_assessments", [column])

    op.create_table(
        "run_records",
        sa.Column("run_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("run_type", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("token_usage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.JSON(), nullable=False),
    )
    op.create_index("ix_run_records_workspace_id", "run_records", ["workspace_id"])
    op.create_index("ix_run_records_run_type", "run_records", ["run_type"])


def downgrade() -> None:
    op.drop_index("ix_run_records_run_type", table_name="run_records")
    op.drop_index("ix_run_records_workspace_id", table_name="run_records")
    op.drop_table("run_records")

    for column in reversed(("workspace_id", "candidate_id", "job_id", "total_score")):
        op.drop_index(f"ix_match_assessments_{column}", table_name="match_assessments")
    op.drop_table("match_assessments")

    for column in reversed(("workspace_id", "candidate_id", "job_id", "country", "status")):
        op.drop_index(
            f"ix_work_authorization_assessments_{column}",
            table_name="work_authorization_assessments",
        )
    op.drop_table("work_authorization_assessments")

    op.drop_index("ix_job_versions_content_hash", table_name="job_versions")
    op.drop_index("ix_job_versions_job_id", table_name="job_versions")
    op.drop_table("job_versions")

    for column in reversed(
        (
            "workspace_id",
            "external_job_id",
            "source_platform",
            "company_id",
            "normalized_title",
            "country",
            "role_track",
            "status",
        )
    ):
        op.drop_index(f"ix_jobs_{column}", table_name="jobs")
    op.drop_table("jobs")

    op.drop_index("ix_companies_canonical_name", table_name="companies")
    op.drop_index("ix_companies_workspace_id", table_name="companies")
    op.drop_table("companies")
