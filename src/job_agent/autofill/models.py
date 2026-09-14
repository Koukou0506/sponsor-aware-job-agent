from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

CanonicalFieldName = Literal[
    "full_name",
    "first_name",
    "last_name",
    "email",
    "phone",
    "location",
    "linkedin_url",
    "github_url",
    "resume_upload",
    "cover_letter_upload",
    "currently_authorized",
    "sponsorship_required",
    "relocation_willingness",
    "notice_period",
    "salary_expectation",
    "open_question",
    "legal_declaration",
]

AutofillState = Literal[
    "not_started",
    "page_loaded",
    "form_detected",
    "fields_mapped",
    "autofilled",
    "needs_review",
    "ready_to_submit",
    "submitted_manually",
    "failed",
]

_TERMINAL_STATES = {"submitted_manually", "failed"}
_SENSITIVE_FIELDS = {
    "currently_authorized",
    "sponsorship_required",
    "relocation_willingness",
    "notice_period",
    "salary_expectation",
    "legal_declaration",
}


class AutofillModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DetectedField(AutofillModel):
    selector: str
    tag: str
    input_type: str | None = None
    ats_field_id: str | None = None
    label: str = ""
    name: str = ""
    placeholder: str = ""
    nearby_text: str = ""
    required: bool = False
    max_length: int | None = Field(default=None, ge=1)
    options: list[str] = Field(default_factory=list)


class FieldMapping(AutofillModel):
    mapping_id: str
    canonical_field: CanonicalFieldName
    page_label: str
    selector: str
    value: str | bool | list[str]
    source: str
    confidence: float = Field(ge=0, le=1)
    requires_review: bool
    risk_level: Literal["standard", "sensitive", "legal"]

    @model_validator(mode="after")
    def sensitive_fields_require_review(self) -> "FieldMapping":
        if self.canonical_field in _SENSITIVE_FIELDS and not self.requires_review:
            raise ValueError("sensitive application field must require review")
        return self


class StopReason(AutofillModel):
    code: Literal[
        "captcha",
        "authentication",
        "duplicate_application",
        "closed_job",
        "job_identity_mismatch",
        "work_authorization_conflict",
        "file_upload_failed",
        "character_limit_overflow",
        "legal_declaration",
        "unknown_page_structure",
    ]
    detail: str
    selector: str | None = None


class AutofillApplicationContext(AutofillModel):
    application_id: str
    workspace_id: str
    candidate_id: str
    package_id: str
    current_state: str
    ats_platform: str
    application_url: HttpUrl
    job_title: str
    answer_catalog: dict[str, Any] = Field(default_factory=dict)
    file_catalog: dict[str, str] = Field(default_factory=dict)
    requires_sponsorship: bool = False


class AutofillSession(AutofillModel):
    session_id: str
    workspace_id: str
    candidate_id: str
    application_id: str
    ats_platform: str
    application_url: HttpUrl
    state: AutofillState
    field_mappings: list[FieldMapping] = Field(default_factory=list)
    stop_reasons: list[StopReason] = Field(default_factory=list)
    manual_submission_confirmed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @property
    def is_terminal(self) -> bool:
        return self.state in _TERMINAL_STATES
