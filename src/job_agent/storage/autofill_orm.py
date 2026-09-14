from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from job_agent.storage.orm import Base, UTCDateTime


class AutofillSessionRow(Base):
    __tablename__ = "autofill_sessions"
    __table_args__ = (
        UniqueConstraint("active_key", name="uq_autofill_sessions_active_key"),
    )

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    candidate_id: Mapped[str] = mapped_column(String, index=True)
    application_id: Mapped[str] = mapped_column(
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        index=True,
    )
    active_key: Mapped[str | None] = mapped_column(String, nullable=True)
    ats_platform: Mapped[str] = mapped_column(String, index=True)
    application_url: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String, index=True)
    stop_reasons: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    manual_submission_confirmed_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime(),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime())


class AutofillFieldMappingRow(Base):
    __tablename__ = "autofill_field_mappings"

    mapping_id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("autofill_sessions.session_id", ondelete="CASCADE"),
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer)
    canonical_field: Mapped[str] = mapped_column(String, index=True)
    page_label: Mapped[str] = mapped_column(Text)
    selector: Mapped[str] = mapped_column(Text)
    value: Mapped[str | bool | list[str]] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    requires_review: Mapped[bool] = mapped_column(Boolean)
    risk_level: Mapped[str] = mapped_column(String, index=True)
