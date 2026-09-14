from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RegionCode = Literal["UK", "NL", "DE", "IE", "HK"]
RoleTrackName = Literal["technical", "technical_business"]


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CandidateProfileConfig(FrozenModel):
    workspace_id: str = "default"
    candidate_id: str = "default"
    full_name: str = Field(min_length=1)


class PreferencesConfig(FrozenModel):
    regions: list[RegionCode]
    role_tracks: list[RoleTrackName]


class RouteAnswer(FrozenModel):
    route_type: str
    application_status: str


class VisaAnswersConfig(FrozenModel):
    routes: dict[RegionCode, RouteAnswer]


class ScoreWeights(FrozenModel):
    work_authorization_fit: float = Field(ge=0, le=1)
    skill_fit: float = Field(ge=0, le=1)
    experience_fit: float = Field(ge=0, le=1)
    role_transition_fit: float = Field(ge=0, le=1)
    language_fit: float = Field(ge=0, le=1)
    company_signal: float = Field(ge=0, le=1)
    recency: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "ScoreWeights":
        if abs(sum(self.model_dump().values()) - 1.0) > 1e-9:
            raise ValueError("score weights must sum to 1.0")
        return self


class ScoringRulesConfig(FrozenModel):
    technical: ScoreWeights
    technical_business: ScoreWeights
