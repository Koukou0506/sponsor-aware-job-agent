from pydantic import BaseModel, ConfigDict, Field

from job_agent.domain.enums import RoleTrack
from job_agent.matcher.requirements import JobRequirements

_TECHNICAL = ("data engineer", "analytics engineer", "backend", "python developer", "software engineer", "qa automation", "sdet", "ai engineer", "cloud support", "technical support")
_TECHNICAL_BUSINESS = ("implementation consultant", "implementation specialist", "technical project", "project coordinator", "tpm", "pmo", "product operations", "technical operations", "integration specialist")
_MIXED = ("solutions engineer", "solution engineer", "integration engineer")


class RoleClassification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    primary_track: RoleTrack
    technical_probability: float = Field(ge=0, le=1)
    technical_business_probability: float = Field(ge=0, le=1)
    evidence: tuple[str, ...] = ()


def classify_role(title: str, requirements: JobRequirements) -> RoleClassification:
    lowered = title.casefold()
    technical_hits = [term for term in _TECHNICAL if term in lowered]
    business_hits = [term for term in _TECHNICAL_BUSINESS if term in lowered]
    mixed_hits = [term for term in _MIXED if term in lowered]
    engineering_skills = {"python", "sql", "docker", "kubernetes", "api", "linux", "playwright", "selenium"}.intersection(requirements.mandatory_skills)
    if mixed_hits:
        return RoleClassification(primary_track=RoleTrack.MIXED, technical_probability=0.7 if engineering_skills else 0.55, technical_business_probability=0.7, evidence=tuple(mixed_hits))
    if technical_hits and business_hits:
        return RoleClassification(primary_track=RoleTrack.MIXED, technical_probability=0.75, technical_business_probability=0.75, evidence=tuple(technical_hits + business_hits))
    if technical_hits:
        return RoleClassification(primary_track=RoleTrack.TECHNICAL, technical_probability=0.9, technical_business_probability=0.2, evidence=tuple(technical_hits))
    if business_hits:
        return RoleClassification(primary_track=RoleTrack.TECHNICAL_BUSINESS, technical_probability=0.25, technical_business_probability=0.9, evidence=tuple(business_hits))
    return RoleClassification(primary_track=RoleTrack.IRRELEVANT, technical_probability=0.1, technical_business_probability=0.1, evidence=())
