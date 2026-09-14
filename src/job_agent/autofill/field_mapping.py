from collections.abc import Callable
from typing import Any, cast

from job_agent.autofill.models import (
    CanonicalFieldName,
    DetectedField,
    FieldMapping,
)
from job_agent.domain.ids import new_id

SemanticResolver = Callable[[DetectedField], CanonicalFieldName | None]

_ATS_IDS: dict[str, CanonicalFieldName] = {
    "job_application_email": "email",
    "job_application_name": "full_name",
    "job_application_phone": "phone",
    "job_application_first_name": "first_name",
    "job_application_last_name": "last_name",
    "resume": "resume_upload",
    "resume_upload": "resume_upload",
    "cover_letter": "cover_letter_upload",
    "cover_letter_upload": "cover_letter_upload",
    "currently_authorized": "currently_authorized",
    "sponsorship_required": "sponsorship_required",
    "relocation_willingness": "relocation_willingness",
    "notice_period": "notice_period",
    "salary_expectation": "salary_expectation",
}

_LABEL_RULES: tuple[tuple[str, CanonicalFieldName], ...] = (
    ("first name", "first_name"),
    ("last name", "last_name"),
    ("full name", "full_name"),
    ("email", "email"),
    ("e-mail", "email"),
    ("phone", "phone"),
    ("telephone", "phone"),
    ("location", "location"),
    ("linkedin", "linkedin_url"),
    ("github", "github_url"),
    ("cover letter", "cover_letter_upload"),
    ("resume", "resume_upload"),
    ("cv", "resume_upload"),
    ("require sponsorship", "sponsorship_required"),
    ("visa sponsorship", "sponsorship_required"),
    ("authorized to work", "currently_authorized"),
    ("authorised to work", "currently_authorized"),
    ("right to work", "currently_authorized"),
    ("notice period", "notice_period"),
    ("salary", "salary_expectation"),
    ("compensation", "salary_expectation"),
    ("relocate", "relocation_willingness"),
    ("relocation", "relocation_willingness"),
)

_LEGAL_TERMS = (
    "certify",
    "declaration",
    "privacy consent",
    "information is true",
    "terms and conditions",
)

_SENSITIVE_FIELDS = {
    "currently_authorized",
    "sponsorship_required",
    "relocation_willingness",
    "notice_period",
    "salary_expectation",
}


def _match_text(text: str) -> CanonicalFieldName | None:
    lowered = " ".join(text.casefold().split())
    if any(term in lowered for term in _LEGAL_TERMS):
        return "legal_declaration"
    return next(
        (canonical for term, canonical in _LABEL_RULES if term in lowered),
        None,
    )


def _answer_value(
    canonical: CanonicalFieldName,
    answers: dict[str, object],
) -> tuple[str | bool | list[str], str]:
    raw = answers.get(canonical)
    if isinstance(raw, dict):
        value = raw.get("value", "")
        source = raw.get("source", "answer_catalog")
        if not isinstance(source, str):
            source = "answer_catalog"
        if isinstance(value, str | bool | list):
            return cast(str | bool | list[str], value), source
    if isinstance(raw, str | bool | list):
        return cast(str | bool | list[str], raw), "answer_catalog"
    if canonical == "legal_declaration":
        return False, "user_required"
    return "", "unresolved"


class FieldMapper:
    def __init__(self, semantic_resolver: SemanticResolver | None = None) -> None:
        self._semantic_resolver = semantic_resolver

    def map_one(
        self,
        field: DetectedField,
        answers: dict[str, object],
    ) -> FieldMapping:
        canonical = _ATS_IDS.get((field.ats_field_id or "").casefold())
        confidence = 1.0 if canonical else 0.0

        if canonical is None:
            canonical = _match_text(field.label)
            confidence = 0.95 if canonical else 0.0
        if canonical is None:
            canonical = _match_text(f"{field.name} {field.placeholder}")
            confidence = 0.9 if canonical else 0.0
        if canonical is None:
            canonical = _match_text(field.nearby_text)
            confidence = 0.8 if canonical else 0.0
        if canonical is None and self._semantic_resolver is not None:
            canonical = self._semantic_resolver(field)
            confidence = 0.65 if canonical else 0.0
        if canonical is None:
            canonical = "open_question"
            confidence = 0.4

        if canonical == "legal_declaration":
            risk_level = "legal"
        elif canonical in _SENSITIVE_FIELDS:
            risk_level = "sensitive"
        else:
            risk_level = "standard"
        value, source = _answer_value(canonical, answers)
        requires_review = risk_level != "standard" or confidence < 0.9 or source == "unresolved"
        return FieldMapping(
            mapping_id=new_id("mapping"),
            canonical_field=canonical,
            page_label=field.label or field.nearby_text or field.name,
            selector=field.selector,
            value=value,
            source=source,
            confidence=confidence,
            requires_review=requires_review,
            risk_level=risk_level,
        )

    def map_all(
        self,
        fields: list[DetectedField],
        answers: dict[str, object],
    ) -> list[FieldMapping]:
        return [self.map_one(field, answers) for field in fields]
