from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from job_agent.storage.orm import Base, UTCDateTime


class ApplicationPackageRow(Base):
    __tablename__ = "application_packages"
    __table_args__ = (UniqueConstraint("active_key", name="uq_application_packages_active_key"),)

    package_id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    candidate_id: Mapped[str] = mapped_column(String, index=True)
    job_id: Mapped[str] = mapped_column(String, index=True)
    job_version_id: Mapped[str] = mapped_column(String, index=True)
    base_resume_id: Mapped[str] = mapped_column(String)
    active_key: Mapped[str | None] = mapped_column(String, nullable=True)
    tailored_resume_version: Mapped[int] = mapped_column(Integer)
    screening_answers_version: Mapped[int] = mapped_column(Integer)
    cover_letter_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fact_references: Mapped[list[str]] = mapped_column(JSON, default=list)
    validation_status: Mapped[str] = mapped_column(String, index=True)
    review_status: Mapped[str] = mapped_column(String, index=True)
    cover_letter_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime())


class GeneratedClaimRow(Base):
    __tablename__ = "generated_claims"

    claim_id: Mapped[str] = mapped_column(String, primary_key=True)
    package_id: Mapped[str] = mapped_column(
        ForeignKey("application_packages.package_id", ondelete="CASCADE"),
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    source_fact_ids: Mapped[list[str]] = mapped_column(JSON)
    transformation_type: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column()
    validation_status: Mapped[str] = mapped_column(String, index=True)
    reviewer_approved: Mapped[bool] = mapped_column(Boolean)


class ScreeningAnswerRow(Base):
    __tablename__ = "screening_answers"

    answer_id: Mapped[str] = mapped_column(String, primary_key=True)
    package_id: Mapped[str] = mapped_column(
        ForeignKey("application_packages.package_id", ondelete="CASCADE"),
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer)
    canonical_question: Mapped[str] = mapped_column(String, index=True)
    displayed_question: Mapped[str] = mapped_column(Text)
    answer_text: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String)
    source_fact_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    requires_review: Mapped[bool] = mapped_column(Boolean)
    risk_level: Mapped[str] = mapped_column(String)


class ApplicationRow(Base):
    __tablename__ = "applications"

    application_id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    candidate_id: Mapped[str] = mapped_column(String, index=True)
    job_id: Mapped[str] = mapped_column(String, index=True)
    package_id: Mapped[str] = mapped_column(
        ForeignKey("application_packages.package_id"),
        index=True,
    )
    application_url: Mapped[str] = mapped_column(Text)
    current_state: Mapped[str] = mapped_column(String, index=True)
    autofill_status: Mapped[str] = mapped_column(String, index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime())


class ApplicationEventRow(Base):
    __tablename__ = "application_events"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    application_id: Mapped[str] = mapped_column(
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        index=True,
    )
    from_state: Mapped[str] = mapped_column(String)
    to_state: Mapped[str] = mapped_column(String, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime())
