import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RequirementState(StrEnum):
    VERIFIED = "verified"
    ADJACENT = "adjacent"
    LEARNABLE = "learnable"
    MISSING = "missing"
    UNKNOWN = "unknown"


class JobRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mandatory_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    minimum_years: int | None = None
    responsibilities: list[str] = Field(default_factory=list)
    work_authorization_text: list[str] = Field(default_factory=list)


_SKILLS = ("python", "sql", "docker", "kubernetes", "aws", "azure", "gcp", "api", "linux", "playwright", "selenium", "project management", "stakeholder management", "implementation", "integration")


def extract_requirements(text: str) -> JobRequirements:
    lowered = text.casefold()
    mandatory: list[str] = []
    preferred: list[str] = []
    for skill in _SKILLS:
        if skill not in lowered:
            continue
        window_start = max(0, lowered.find(skill) - 60)
        context = lowered[window_start: lowered.find(skill) + len(skill) + 60]
        if any(term in context for term in ("preferred", "nice to have", "bonus")):
            preferred.append(skill)
        else:
            mandatory.append(skill)
    languages = [language for language in ("english", "german", "dutch", "cantonese", "mandarin") if language in lowered]
    years_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", lowered)
    work_auth = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if any(term in sentence.casefold() for term in ("sponsor", "visa", "work author", "right to work", "citizen"))]
    return JobRequirements(mandatory_skills=sorted(set(mandatory)), preferred_skills=sorted(set(preferred)), languages=languages, minimum_years=int(years_match.group(1)) if years_match else None, work_authorization_text=work_auth)
