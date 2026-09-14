from pathlib import Path

import yaml

from job_agent.domain.ids import new_id
from job_agent.materials.models import ScreeningAnswer
from job_agent.providers.structured_llm import StructuredLlm

_HIGH_RISK = {
    "criminal_record",
    "health_or_disability",
    "equal_opportunity",
    "export_control",
    "nationality_restriction",
    "conflict_of_interest",
    "legal_declaration",
}
_SENSITIVE = {
    "currently_authorized",
    "requires_employer_sponsorship",
    "salary_expectation",
}


class FixedAnswerResolver:
    def __init__(self, route_answers: dict[str, dict[str, dict[str, str]]]) -> None:
        self._route_answers = route_answers

    def resolve(
        self,
        canonical_question: str,
        country: str,
        route_state: str,
    ) -> ScreeningAnswer:
        if canonical_question in _HIGH_RISK:
            return ScreeningAnswer(
                answer_id=new_id("answer"),
                canonical_question=canonical_question,
                displayed_question=canonical_question,
                answer_text="",
                source_type="user_required",
                requires_review=True,
                risk_level="legal",
            )
        answer = (
            self._route_answers
            .get(country, {})
            .get(route_state, {})
            .get(canonical_question)
        )
        if answer is None:
            return ScreeningAnswer(
                answer_id=new_id("answer"),
                canonical_question=canonical_question,
                displayed_question=canonical_question,
                answer_text="",
                source_type="user_required",
                requires_review=True,
                risk_level=(
                    "sensitive" if canonical_question in _SENSITIVE else "standard"
                ),
            )
        return ScreeningAnswer(
            answer_id=new_id("answer"),
            canonical_question=canonical_question,
            displayed_question=canonical_question,
            answer_text=answer,
            source_type="route_state",
            requires_review=True,
            risk_level=(
                "sensitive" if canonical_question in _SENSITIVE else "standard"
            ),
        )


class ScreeningDraftService:
    def __init__(self, llm: StructuredLlm) -> None:
        self._llm = llm

    def draft(
        self,
        displayed_question: str,
        fact_context: str,
    ) -> ScreeningAnswer:
        class Draft(ScreeningAnswer):
            pass

        return self._llm.complete(
            "Draft a concise answer using only the supplied facts.",
            f"Question: {displayed_question}\nFacts: {fact_context}",
            Draft,
        )


def load_fixed_answer_resolver(path: Path) -> FixedAnswerResolver:
    if not path.exists():
        return FixedAnswerResolver({})
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    answers = payload.get("answers", {})
    if not isinstance(answers, dict):
        raise ValueError("screening answers configuration must contain an answers mapping")
    normalized: dict[str, dict[str, dict[str, str]]] = {}
    for country, states in answers.items():
        if not isinstance(country, str) or not isinstance(states, dict):
            raise ValueError("screening answer countries and states must be mappings")
        normalized[country] = {}
        for state, values in states.items():
            if not isinstance(state, str) or not isinstance(values, dict):
                raise ValueError("screening answer route states must be mappings")
            valid_answers = all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in values.items()
            )
            if not valid_answers:
                raise ValueError("screening answers must map string questions to string answers")
            normalized[country][state] = dict(values)
    return FixedAnswerResolver(normalized)
