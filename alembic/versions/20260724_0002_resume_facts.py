"""Create resume source and fact tables.

Revision ID: 20260724_0002
Revises: 20260724_0001
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0002"
down_revision: str | None = "20260724_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resume_sources",
        sa.Column("source_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("file_hash", sa.String(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("resume_track", sa.String(), nullable=False),
        sa.Column("extraction_method", sa.String(), nullable=False),
        sa.Column("local_path", sa.Text(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "workspace_id",
            "candidate_id",
            "file_hash",
            name="uq_resume_sources_candidate_hash",
        ),
    )
    for column in ("workspace_id", "candidate_id", "file_hash"):
        op.create_index(f"ix_resume_sources_{column}", "resume_sources", [column])

    op.create_table(
        "resume_facts",
        sa.Column("fact_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("organisation", sa.String(), nullable=True),
        sa.Column("role_or_project", sa.String(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("raw_fact", sa.Text(), nullable=False),
        sa.Column("claim_status", sa.String(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("allowed_claims", sa.JSON(), nullable=False),
        sa.Column("verification_status", sa.String(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
    )
    for column in ("workspace_id", "candidate_id", "category", "verification_status"):
        op.create_index(f"ix_resume_facts_{column}", "resume_facts", [column])
    op.create_index(
        "ix_resume_facts_context",
        "resume_facts",
        ["category", "organisation", "role_or_project"],
    )

    op.create_table(
        "resume_import_sessions",
        sa.Column("import_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), sa.ForeignKey("resume_sources.source_id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("extracted_facts", sa.JSON(), nullable=False),
    )
    for column in ("workspace_id", "candidate_id", "source_id", "status"):
        op.create_index(f"ix_resume_import_sessions_{column}", "resume_import_sessions", [column])


def downgrade() -> None:
    for column in reversed(("workspace_id", "candidate_id", "source_id", "status")):
        op.drop_index(f"ix_resume_import_sessions_{column}", table_name="resume_import_sessions")
    op.drop_table("resume_import_sessions")
    op.drop_index("ix_resume_facts_context", table_name="resume_facts")
    for column in reversed(("workspace_id", "candidate_id", "category", "verification_status")):
        op.drop_index(f"ix_resume_facts_{column}", table_name="resume_facts")
    op.drop_table("resume_facts")
    for column in reversed(("workspace_id", "candidate_id", "file_hash")):
        op.drop_index(f"ix_resume_sources_{column}", table_name="resume_sources")
    op.drop_table("resume_sources")
