from pydantic import BaseModel, ConfigDict, Field

from job_agent.providers.structured_llm import StructuredLlm


class CoverLetterDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    source_fact_ids: list[str] = Field(min_length=2)
    company_evidence_id: str
    company_evidence_url: str


def should_recommend_cover_letter(
    *,
    required: bool,
    total_score: float,
    high_priority: bool,
) -> bool:
    return required or total_score >= 85 or high_priority


def validate_cover_letter_input(
    *,
    education_fact_ids: list[str],
    project_fact_ids: list[str],
    motivation: str,
    company_evidence_id: str,
    company_evidence_url: str,
) -> None:
    if not education_fact_ids:
        raise ValueError("cover letter requires an education or technical fact")
    if not project_fact_ids:
        raise ValueError("cover letter requires a project or work fact")
    if not motivation.strip():
        raise ValueError("cover letter requires a job motivation")
    if not company_evidence_id.strip() or not company_evidence_url.strip():
        raise ValueError("cover letter requires source-backed company evidence")


class CoverLetterService:
    def __init__(self, llm: StructuredLlm) -> None:
        self._llm = llm

    def generate(
        self,
        *,
        education_fact_ids: list[str],
        project_fact_ids: list[str],
        motivation: str,
        company_evidence_id: str,
        company_evidence_url: str,
        fact_context: str,
    ) -> CoverLetterDraft:
        validate_cover_letter_input(
            education_fact_ids=education_fact_ids,
            project_fact_ids=project_fact_ids,
            motivation=motivation,
            company_evidence_id=company_evidence_id,
            company_evidence_url=company_evidence_url,
        )
        prompt = (
            f"Facts: {fact_context}\nMotivation: {motivation}\n"
            f"Company evidence: {company_evidence_id} {company_evidence_url}"
        )
        return self._llm.complete(
            "Write a source-backed cover letter. Do not add unsupported claims.",
            prompt,
            CoverLetterDraft,
        )
