from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MaterialModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GeneratedClaim(MaterialModel):
    claim_id: str
    text: str
    source_fact_ids: list[str] = Field(min_length=1)
    transformation_type: Literal["verbatim", "wording_adaptation", "aggregation"]
    confidence: float = Field(ge=0, le=1)
    validation_status: Literal["verified", "needs_review", "unsupported", "conflicting"]
    reviewer_approved: bool


class ScreeningAnswer(MaterialModel):
    answer_id: str
    canonical_question: str
    displayed_question: str
    answer_text: str
    source_type: Literal[
        "fixed_config",
        "route_state",
        "fact_template",
        "generated_draft",
        "user_required",
    ]
    source_fact_ids: list[str] = Field(default_factory=list)
    requires_review: bool
    risk_level: Literal["standard", "sensitive", "legal"]


class ApplicationPackage(MaterialModel):
    package_id: str
    workspace_id: str
    candidate_id: str
    job_id: str
    job_version_id: str
    base_resume_id: str
    tailored_resume_version: int = Field(ge=1)
    screening_answers_version: int = Field(ge=1)
    cover_letter_version: int | None = Field(default=None, ge=1)
    generated_claims: list[GeneratedClaim]
    screening_answers: list[ScreeningAnswer] = Field(default_factory=list)
    fact_references: list[str] = Field(default_factory=list)
    validation_status: Literal["verified", "needs_review", "unsupported", "conflicting"]
    review_status: Literal[
        "draft",
        "awaiting_review",
        "approved",
        "rejected",
        "superseded",
    ]
    cover_letter_text: str | None = None
    created_at: datetime

    @model_validator(mode="after")
    def invalid_claim_blocks_verified_package(self) -> "ApplicationPackage":
        if self.validation_status == "verified" and any(
            claim.validation_status != "verified" for claim in self.generated_claims
        ):
            raise ValueError("verified package cannot contain invalid claims")
        return self


class Application(MaterialModel):
    application_id: str
    workspace_id: str
    candidate_id: str
    job_id: str
    package_id: str
    application_url: str
    current_state: str
    autofill_status: str = "not_started"
    submitted_at: datetime | None = None
    outcome: str | None = None
    created_at: datetime


class ApplicationEvent(MaterialModel):
    event_id: str
    application_id: str
    from_state: str
    to_state: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
