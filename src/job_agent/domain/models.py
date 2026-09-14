from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from job_agent.domain.enums import (
    EvidenceLevel,
    JobStatus,
    Region,
    RoleTrack,
    RouteOwnership,
    WorkAuthorizationStatus,
)


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def persistent_datetimes_are_timezone_aware(self) -> "DomainModel":
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if isinstance(value, datetime) and value.tzinfo is None:
                raise ValueError(f"{field_name} must be timezone-aware")
        return self


class Evidence(DomainModel):
    level: EvidenceLevel
    kind: str
    source: str
    detail: str
    source_url: HttpUrl | None = None
    retrieved_at: datetime | None = None


class Company(DomainModel):
    company_id: str
    workspace_id: str
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)
    domain: str | None = None


class Job(DomainModel):
    job_id: str
    workspace_id: str
    external_job_id: str
    source_platform: str
    source_url: HttpUrl
    company_id: str
    title: str
    normalized_title: str
    country: Region
    city: str | None = None
    role_track: RoleTrack = RoleTrack.IRRELEVANT
    description_raw: str
    description_normalized: str
    published_at: datetime | None = None
    discovered_at: datetime
    status: JobStatus = JobStatus.DISCOVERED


class WorkAuthorizationAssessment(DomainModel):
    assessment_id: str
    workspace_id: str
    candidate_id: str
    job_id: str
    country: Region
    route_type: str
    route_ownership: RouteOwnership
    status: WorkAuthorizationStatus
    work_authorization_fit: float = Field(ge=0, le=1)
    hard_fail: bool
    hard_fail_reasons: list[str] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    evidence: list[Evidence]
    confidence: float = Field(ge=0, le=1)
    ruleset_version: str
    assessed_at: datetime

    @model_validator(mode="after")
    def hard_fail_has_reason(self) -> "WorkAuthorizationAssessment":
        if self.hard_fail and not self.hard_fail_reasons:
            raise ValueError("hard-failed assessment requires at least one reason")
        return self


class MatchAssessment(DomainModel):
    assessment_id: str
    workspace_id: str
    candidate_id: str
    job_id: str
    selected_resume_track: RoleTrack
    visa_fit: float = Field(ge=0, le=1)
    skill_fit: float = Field(ge=0, le=1)
    experience_fit: float = Field(ge=0, le=1)
    language_fit: float = Field(ge=0, le=1)
    role_transition_fit: float = Field(ge=0, le=1)
    company_signal: float = Field(ge=0, le=1)
    recency_score: float = Field(ge=0, le=1)
    total_score: float = Field(ge=0, le=100)
    matching_evidence: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    disqualifiers: list[str] = Field(default_factory=list)
    model_version: str
    assessed_at: datetime


class RunRecord(DomainModel):
    run_id: str
    workspace_id: str
    run_type: str
    started_at: datetime
    completed_at: datetime | None = None
    processed_count: int = 0
    success_count: int = 0
    skipped_count: int = 0
    duplicate_count: int = 0
    hard_failed_count: int = 0
    failed_count: int = 0
    token_usage: int = 0
    estimated_cost: float = 0.0
    error_summary: dict[str, Any] = Field(default_factory=dict)
