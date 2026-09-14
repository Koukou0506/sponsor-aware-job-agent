from typing import Any
from pydantic import BaseModel
class PackageCreateRequest(BaseModel):
    cover_letter: bool = False
    force: bool = False
class PackageView(BaseModel):
    package_id: str
    job_id: str | None = None
    job_title: str
    company: str
    base_resume_id: str | None = None
    validation_status: str
    review_status: str
    claims: list[dict[str, Any]]
    screening_answers: list[dict[str, Any]]
    cover_letter_text: str | None = None
class ApplicationView(BaseModel):
    application_id: str
    package_id: str | None = None
    job_id: str
    job_title: str
    company: str
    country: str
    current_state: str
    autofill_status: str | None = None
    submitted_at: str | None = None
    outcome: str | None = None
class TransitionRequest(BaseModel):
    new_state: str
    payload: dict[str, Any] | None = None
