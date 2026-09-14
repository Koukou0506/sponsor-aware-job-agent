from typing import Any
from pydantic import BaseModel, Field
class WorkAuthorisationView(BaseModel):
    status: str
    fit: float | None = None
    route: str | None = None
    confidence: float | None = None
    evidence: list[Any] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)
    ruleset_version: str | None = None
class JobSummary(BaseModel):
    job_id: str
    review_id: str | None = None
    company: str
    title: str
    country: str
    city: str | None = None
    role_track: str
    work_authorisation: WorkAuthorisationView
    total_score: float
    language: str | None = None
    ats: str | None = None
    published_at: str | None = None
    review_status: str | None = None
class JobDetail(JobSummary):
    requirements: list[str] = Field(default_factory=list)
    fit: dict[str, Any] = Field(default_factory=dict)
class JobsPage(BaseModel):
    items: list[JobSummary]
    page: int
    page_size: int
    total: int
class ReviewStatusRequest(BaseModel):
    status: str
