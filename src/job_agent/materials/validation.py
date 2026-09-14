import re
from typing import Any

from pydantic import BaseModel, ConfigDict

from job_agent.materials.tailoring import TailoringProposal


class ClaimValidation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    text: str
    status: str
    reasons: list[str]


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    claim_results: list[ClaimValidation]
    export_allowed: bool


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\b\d[\d,.%]*\b", text))


def validate_proposal(
    proposal: TailoringProposal,
    facts: dict[str, dict[str, Any]],
    approved_skills: set[str],
    requested_skills: set[str],
) -> ValidationReport:
    results: list[ClaimValidation] = []
    normalized_approved = {skill.casefold() for skill in approved_skills}
    normalized_requested = {skill.casefold(): skill for skill in requested_skills}
    all_claims = [*proposal.professional_summary, *proposal.bullet_claims]
    for claim in all_claims:
        reasons: list[str] = []
        sources = [facts.get(fact_id) for fact_id in claim.source_fact_ids]
        if any(source is None for source in sources):
            reasons.append("missing source fact")
        source_numbers: set[str] = set()
        for source in sources:
            if source:
                source_numbers.update(_numbers(str(source.get("raw_fact", ""))))
                for value in dict(source.get("metrics", {})).values():
                    source_numbers.update(_numbers(str(value)))
        if not _numbers(claim.text) <= source_numbers:
            reasons.append("claim introduces or changes a numeric value")
        mentioned = {
            canonical
            for normalized, canonical in normalized_requested.items()
            if normalized in claim.text.casefold()
        }
        if not {skill.casefold() for skill in mentioned} <= normalized_approved:
            reasons.append("claim introduces an unapproved skill")
        results.append(
            ClaimValidation(
                text=claim.text,
                status="verified" if not reasons else "conflicting",
                reasons=reasons,
            )
        )
    if not {skill.casefold() for skill in proposal.ordered_skill_names} <= normalized_approved:
        results.append(
            ClaimValidation(
                text="Ordered skills",
                status="conflicting",
                reasons=["ordered skills contain an unapproved skill"],
            )
        )
    return ValidationReport(
        claim_results=results,
        export_allowed=bool(results)
        and all(result.status == "verified" for result in results),
    )
