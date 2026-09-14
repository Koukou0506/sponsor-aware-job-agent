from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from job_agent.domain.enums import RoleTrack
from job_agent.domain.ids import new_id
from job_agent.domain.models import MatchAssessment


class ScoreInputs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    work_authorization_fit: float = Field(ge=0, le=1)
    skill_fit: float = Field(ge=0, le=1)
    experience_fit: float = Field(ge=0, le=1)
    role_transition_fit: float = Field(ge=0, le=1)
    language_fit: float = Field(ge=0, le=1)
    company_signal: float = Field(ge=0, le=1)
    recency: float = Field(ge=0, le=1)

    @computed_field
    @property
    def material_generation_allowed(self) -> bool:
        return self.work_authorization_fit >= 0.5


_WEIGHTS = {
    "technical": {"work_authorization_fit": 0.30, "skill_fit": 0.25, "experience_fit": 0.15, "role_transition_fit": 0.10, "language_fit": 0.08, "company_signal": 0.07, "recency": 0.05},
    "technical_business": {"work_authorization_fit": 0.30, "skill_fit": 0.12, "experience_fit": 0.20, "role_transition_fit": 0.18, "language_fit": 0.08, "company_signal": 0.07, "recency": 0.05},
}


def calculate_track_score(track: Literal["technical", "technical_business"], inputs: ScoreInputs) -> float:
    score = sum(getattr(inputs, name) * weight for name, weight in _WEIGHTS[track].items())
    return round(score * 100, 1)


def build_match_assessment(job_id: str, workspace_id: str, candidate_id: str, track: RoleTrack, inputs: ScoreInputs, *, evidence: list[str] | None = None, missing: list[str] | None = None, disqualifiers: list[str] | None = None, model_version: str = "deterministic-v1") -> MatchAssessment:
    selected = RoleTrack.TECHNICAL if track is RoleTrack.MIXED else track
    if selected not in {RoleTrack.TECHNICAL, RoleTrack.TECHNICAL_BUSINESS}:
        selected = RoleTrack.TECHNICAL_BUSINESS
    key: Literal["technical", "technical_business"] = "technical" if selected is RoleTrack.TECHNICAL else "technical_business"
    return MatchAssessment(assessment_id=new_id("match"), workspace_id=workspace_id, candidate_id=candidate_id, job_id=job_id, selected_resume_track=selected, visa_fit=inputs.work_authorization_fit, skill_fit=inputs.skill_fit, experience_fit=inputs.experience_fit, language_fit=inputs.language_fit, role_transition_fit=inputs.role_transition_fit, company_signal=inputs.company_signal, recency_score=inputs.recency, total_score=calculate_track_score(key, inputs), matching_evidence=evidence or [], missing_requirements=missing or [], disqualifiers=disqualifiers or [], model_version=model_version, assessed_at=datetime.now(UTC))
