import re

from job_agent.resume_ingestion.models import ExtractedFactCandidate, ResumeFact


def _normalise(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split())


def classify_candidate(
    candidate: ExtractedFactCandidate,
    approved_facts: list[ResumeFact],
) -> ExtractedFactCandidate:
    for fact in approved_facts:
        same_context = (
            candidate.category == fact.category
            and candidate.organisation == fact.organisation
            and candidate.role_or_project == fact.role_or_project
        )
        if not same_context:
            continue
        if candidate.start_date and fact.start_date and candidate.start_date != fact.start_date:
            return candidate.model_copy(
                update={"merge_classification": "date_conflict", "matched_fact_id": fact.fact_id}
            )
        if candidate.end_date and fact.end_date and candidate.end_date != fact.end_date:
            return candidate.model_copy(
                update={"merge_classification": "date_conflict", "matched_fact_id": fact.fact_id}
            )
        if candidate.claim_status and fact.claim_status and candidate.claim_status != fact.claim_status:
            return candidate.model_copy(
                update={"merge_classification": "status_conflict", "matched_fact_id": fact.fact_id}
            )
        shared_keys = candidate.metrics.keys() & fact.metrics.keys()
        if shared_keys and any(candidate.metrics[key] != fact.metrics[key] for key in shared_keys):
            return candidate.model_copy(
                update={"merge_classification": "metric_conflict", "matched_fact_id": fact.fact_id}
            )
        candidate_text = _normalise(candidate.raw_fact)
        fact_text = _normalise(fact.raw_fact)
        if candidate_text == fact_text:
            return candidate.model_copy(
                update={"merge_classification": "duplicate", "matched_fact_id": fact.fact_id}
            )
        if set(candidate_text.split()) == set(fact_text.split()):
            return candidate.model_copy(
                update={"merge_classification": "wording_variant", "matched_fact_id": fact.fact_id}
            )
    return candidate.model_copy(update={"merge_classification": "new_fact"})
