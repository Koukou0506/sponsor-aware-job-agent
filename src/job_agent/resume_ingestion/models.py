from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResumeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def datetimes_are_timezone_aware(self) -> "ResumeModel":
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if isinstance(value, datetime) and value.tzinfo is None:
                raise ValueError(f"{field_name} must be timezone-aware")
        return self


class ResumeSource(ResumeModel):
    source_id: str
    workspace_id: str
    candidate_id: str
    filename: str
    file_hash: str
    uploaded_at: datetime
    language: Literal["en", "zh", "mixed", "unknown"]
    resume_track: Literal["technical", "technical_business", "historical", "unknown"]
    extraction_method: str
    local_path: str
    revoked_at: datetime | None = None


class Provenance(ResumeModel):
    source_id: str
    page_number: int | None = Field(default=None, ge=1)
    section: str
    original_text: str
    extraction_method: str
    extraction_confidence: float = Field(ge=0, le=1)


class ResumeFact(ResumeModel):
    fact_id: str
    workspace_id: str
    candidate_id: str
    category: str
    organisation: str | None = None
    role_or_project: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    raw_fact: str
    claim_status: str | None = None
    metrics: dict[str, int | float | str] = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=list)
    allowed_claims: list[str] = Field(default_factory=list)
    verification_status: Literal["pending", "approved", "rejected", "revoked"]
    provenance: list[Provenance]


class ExtractedFactCandidate(ResumeModel):
    candidate_fact_id: str
    raw_fact: str
    category: str
    organisation: str | None = None
    role_or_project: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    claim_status: str | None = None
    metrics: dict[str, int | float | str] = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=list)
    provenance: Provenance
    merge_classification: Literal[
        "new_fact",
        "duplicate",
        "wording_variant",
        "metric_conflict",
        "date_conflict",
        "status_conflict",
        "unsupported_claim",
    ] = "new_fact"
    matched_fact_id: str | None = None


class ImportSession(ResumeModel):
    import_id: str
    workspace_id: str
    candidate_id: str
    source_id: str
    status: Literal["parsed", "extracted", "awaiting_review", "approved", "rejected"]
    created_at: datetime
    extracted_facts: list[ExtractedFactCandidate] = Field(default_factory=list)
