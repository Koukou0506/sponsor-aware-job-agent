from typing import Any
from pydantic import BaseModel, Field
class CountItem(BaseModel):
    key: str
    count: int
class DashboardCounts(BaseModel):
    new_jobs: int = 0
    work_authorisation_eligible: int = 0
    high_fit: int = 0
    awaiting_review: int = 0
    ready_to_submit: int = 0
    interviews: int = 0
class DashboardResponse(BaseModel):
    counts: DashboardCounts
    country_distribution: list[CountItem] = Field(default_factory=list)
    track_distribution: list[CountItem] = Field(default_factory=list)
    application_funnel: list[CountItem] = Field(default_factory=list)
    recent_high_fit_jobs: list[dict[str, Any]] = Field(default_factory=list)
    alerts: list[dict[str, Any]] = Field(default_factory=list)
