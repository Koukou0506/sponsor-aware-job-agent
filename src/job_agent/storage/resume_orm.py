from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, ForeignKey, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from job_agent.storage.orm import Base, UTCDateTime


class ResumeSourceRow(Base):
    __tablename__ = "resume_sources"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "candidate_id",
            "file_hash",
            name="uq_resume_sources_candidate_hash",
        ),
    )

    source_id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    candidate_id: Mapped[str] = mapped_column(String, index=True)
    filename: Mapped[str] = mapped_column(String)
    file_hash: Mapped[str] = mapped_column(String, index=True)
    uploaded_at: Mapped[datetime] = mapped_column(UTCDateTime())
    language: Mapped[str] = mapped_column(String)
    resume_track: Mapped[str] = mapped_column(String)
    extraction_method: Mapped[str] = mapped_column(String)
    local_path: Mapped[str] = mapped_column(Text)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)


class ResumeFactRow(Base):
    __tablename__ = "resume_facts"

    fact_id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    candidate_id: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    organisation: Mapped[str | None] = mapped_column(String, nullable=True)
    role_or_project: Mapped[str | None] = mapped_column(String, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    raw_fact: Mapped[str] = mapped_column(Text)
    claim_status: Mapped[str | None] = mapped_column(String, nullable=True)
    metrics: Mapped[dict[str, int | float | str]] = mapped_column(JSON, default=dict)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    allowed_claims: Mapped[list[str]] = mapped_column(JSON, default=list)
    verification_status: Mapped[str] = mapped_column(String, index=True)
    provenance: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)


class ResumeImportSessionRow(Base):
    __tablename__ = "resume_import_sessions"

    import_id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    candidate_id: Mapped[str] = mapped_column(String, index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("resume_sources.source_id"), index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime())
    extracted_facts: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)


Index("ix_resume_facts_context", ResumeFactRow.category, ResumeFactRow.organisation, ResumeFactRow.role_or_project)
