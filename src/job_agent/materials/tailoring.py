from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from job_agent.providers.structured_llm import StructuredLlm


class TailoredClaimProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    source_fact_ids: list[str] = Field(min_length=1)
    transformation_type: Literal["verbatim", "wording_adaptation", "aggregation"]


class TailoringProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    professional_summary: list[TailoredClaimProposal]
    ordered_skill_names: list[str]
    ordered_project_fact_ids: list[str]
    bullet_claims: list[TailoredClaimProposal]


class TailoringRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job_title: str
    job_requirements: list[str]
    base_resume_track: Literal["technical", "technical_business"]
    approved_facts: dict[str, str]
    approved_skills: list[str]
    requested_skills: list[str]
    immutable_metrics: dict[str, dict[str, int | float | str]]

    @classmethod
    def fixture(cls, **updates: object) -> "TailoringRequest":
        payload: dict[str, object] = {
            "job_title": "Junior Data Engineer",
            "job_requirements": ["Python", "SQL"],
            "base_resume_track": "technical",
            "approved_facts": {
                "fact_samples": "Processed 2,000 samples using Python"
            },
            "approved_skills": ["Python"],
            "requested_skills": ["Python", "SQL"],
            "immutable_metrics": {"fact_samples": {"sample_count": 2000}},
        }
        payload.update(updates)
        return cls.model_validate(payload)


def build_tailoring_prompt(request: TailoringRequest) -> str:
    instruction = (
        "Create a controlled resume-tailoring proposal. You may reorder approved "
        "facts and skills, and make limited wording adaptations. You must not "
        "claim unapproved skills, alter metrics, change dates, employers, "
        "institutions, titles, publication states, or work-authorisation facts."
    )
    return f"{instruction}\n{request.model_dump_json(indent=2)}"


class TailoringService:
    def __init__(self, llm: StructuredLlm) -> None:
        self._llm = llm

    def propose(self, request: TailoringRequest) -> TailoringProposal:
        return self._llm.complete(
            "Return only a fact-referenced tailoring proposal.",
            build_tailoring_prompt(request),
            TailoringProposal,
        )
