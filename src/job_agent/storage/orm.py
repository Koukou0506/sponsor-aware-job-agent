from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """Persist UTC and always return timezone-aware UTC datetimes."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        del dialect
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        del dialect
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class Base(DeclarativeBase):
    pass


class CompanyRow(Base):
    __tablename__ = "companies"
    company_id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    canonical_name: Mapped[str] = mapped_column(String, index=True)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    domain: Mapped[str | None] = mapped_column(String, nullable=True)


class JobRow(Base):
    __tablename__ = "jobs"
    job_id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    external_job_id: Mapped[str] = mapped_column(String, index=True)
    source_platform: Mapped[str] = mapped_column(String, index=True)
    source_url: Mapped[str] = mapped_column(Text)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.company_id"), index=True)
    title: Mapped[str] = mapped_column(String)
    normalized_title: Mapped[str] = mapped_column(String, index=True)
    country: Mapped[str] = mapped_column(String, index=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    role_track: Mapped[str] = mapped_column(String, index=True)
    description_raw: Mapped[str] = mapped_column(Text)
    description_normalized: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(UTCDateTime())
    status: Mapped[str] = mapped_column(String, index=True)


class JobVersionRow(Base):
    __tablename__ = "job_versions"
    job_version_id: Mapped[str] = mapped_column(String, primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), index=True)
    content_hash: Mapped[str] = mapped_column(String, index=True)
    source_payload_hash: Mapped[str] = mapped_column(String, index=True)
    description_snapshot: Mapped[str] = mapped_column(Text)
    changed_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    captured_at: Mapped[datetime] = mapped_column(UTCDateTime())


class WorkAuthorizationAssessmentRow(Base):
    __tablename__ = "work_authorization_assessments"
    assessment_id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    candidate_id: Mapped[str] = mapped_column(String, index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), index=True)
    country: Mapped[str] = mapped_column(String, index=True)
    route_type: Mapped[str] = mapped_column(String)
    route_ownership: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, index=True)
    work_authorization_fit: Mapped[float] = mapped_column(Float)
    hard_fail: Mapped[bool] = mapped_column(Boolean)
    hard_fail_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    unresolved_items: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float)
    ruleset_version: Mapped[str] = mapped_column(String)
    assessed_at: Mapped[datetime] = mapped_column(UTCDateTime())


class MatchAssessmentRow(Base):
    __tablename__ = "match_assessments"
    assessment_id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    candidate_id: Mapped[str] = mapped_column(String, index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), index=True)
    selected_resume_track: Mapped[str] = mapped_column(String)
    component_scores: Mapped[dict[str, float]] = mapped_column(JSON)
    total_score: Mapped[float] = mapped_column(Float, index=True)
    matching_evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    disqualifiers: Mapped[list[str]] = mapped_column(JSON, default=list)
    model_version: Mapped[str] = mapped_column(String)
    assessed_at: Mapped[datetime] = mapped_column(UTCDateTime())


class RunRecordRow(Base):
    __tablename__ = "run_records"
    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    run_type: Mapped[str] = mapped_column(String, index=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime())
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    hard_failed_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    token_usage: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    error_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ReviewQueueRow(Base):
    __tablename__ = "review_queue"
    review_id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    candidate_id: Mapped[str] = mapped_column(String, index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), index=True)
    work_authorization_assessment_id: Mapped[str] = mapped_column(
        ForeignKey("work_authorization_assessments.assessment_id"), index=True
    )
    match_assessment_id: Mapped[str] = mapped_column(
        ForeignKey("match_assessments.assessment_id"), index=True
    )
    status: Mapped[str] = mapped_column(String, index=True, default="pending")
    materials_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime())


class ConnectorHealthRow(Base):
    __tablename__ = "connector_health"
    connector_key: Mapped[str] = mapped_column(String, primary_key=True)
    platform: Mapped[str] = mapped_column(String, index=True)
    board_token: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    last_error_type: Mapped[str | None] = mapped_column(String, nullable=True)
    last_error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(UTCDateTime())
