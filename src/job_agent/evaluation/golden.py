from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class GoldenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class BinaryMetrics(GoldenModel):
    false_rejection_rate: float
    miss_rate: float
    accuracy: float


class GoldenCase(GoldenModel):
    case_id: str
    country: str
    legal_entity: str
    route_conclusion: str
    evidence_levels: list[str]
    role_track: str
    reviewed_apply: bool
    predicted_apply: bool
    explicit_no_sponsorship: bool = False
    predicted_no_sponsorship: bool = False
    entity_match_correct: bool
    duplicate_expected: bool = False
    duplicate_blocked: bool = False
    fact_traceability: bool = True
    standard_fields_total: int = Field(default=0, ge=0)
    standard_fields_filled: int = Field(default=0, ge=0)
    unapproved_submission_count: int = Field(default=0, ge=0)
    work_authorization_factual_errors: int = Field(default=0, ge=0)
    resume_track: str
    matches: list[str]
    gaps: list[str]
    reviewer: str
    reviewed_at: str

    @model_validator(mode="after")
    def filled_fields_do_not_exceed_total(self) -> "GoldenCase":
        if self.standard_fields_filled > self.standard_fields_total:
            raise ValueError("standard_fields_filled cannot exceed standard_fields_total")
        return self


class MetricResult(GoldenModel):
    value: float
    target: str
    passed: bool


class EvaluationReport(GoldenModel):
    case_count: int
    viable_job_false_rejection_rate: MetricResult
    explicit_no_sponsorship_miss_rate: MetricResult
    entity_matching_accuracy: MetricResult
    duplicate_blocking_rate: MetricResult
    fact_traceability_rate: MetricResult
    autofill_coverage_rate: MetricResult
    unapproved_submissions: MetricResult
    work_authorization_factual_errors: MetricResult

    @property
    def passed(self) -> bool:
        return all(
            result.passed
            for name, result in self
            if name != "case_count"
        )


def _percent(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else round(numerator / denominator * 100, 2)


def evaluate_binary_cases(
    labels: list[bool],
    predictions: list[bool],
) -> BinaryMetrics:
    if len(labels) != len(predictions):
        raise ValueError("labels and predictions must have equal length")
    positives = sum(labels)
    negatives = len(labels) - positives
    false_rejections = sum(
        label and not prediction
        for label, prediction in zip(labels, predictions, strict=True)
    )
    misses = sum(
        not label and prediction
        for label, prediction in zip(labels, predictions, strict=True)
    )
    correct = sum(
        label == prediction
        for label, prediction in zip(labels, predictions, strict=True)
    )
    return BinaryMetrics(
        false_rejection_rate=_percent(false_rejections, positives),
        miss_rate=_percent(misses, negatives),
        accuracy=_percent(correct, len(labels)),
    )


def load_golden_cases(path: Path) -> list[GoldenCase]:
    files = [path] if path.is_file() else sorted(path.glob("*.yaml"))
    if not files:
        raise ValueError(f"no golden YAML cases found at: {path}")
    cases: list[GoldenCase] = []
    seen: set[str] = set()
    for file_path in files:
        payload: Any = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        case = GoldenCase.model_validate(payload)
        if case.case_id in seen:
            raise ValueError(f"duplicate golden case_id: {case.case_id}")
        seen.add(case.case_id)
        cases.append(case)
    return cases


def evaluate_golden_cases(cases: list[GoldenCase]) -> EvaluationReport:
    if not cases:
        raise ValueError("at least one reviewed case is required")
    apply_metrics = evaluate_binary_cases(
        [case.reviewed_apply for case in cases],
        [case.predicted_apply for case in cases],
    )
    no_sponsor_cases = [case for case in cases if case.explicit_no_sponsorship]
    no_sponsor_misses = sum(
        not case.predicted_no_sponsorship for case in no_sponsor_cases
    )
    entity_accuracy = _percent(
        sum(case.entity_match_correct for case in cases),
        len(cases),
    )
    duplicate_cases = [case for case in cases if case.duplicate_expected]
    duplicate_rate = _percent(
        sum(case.duplicate_blocked for case in duplicate_cases),
        len(duplicate_cases),
    )
    traceability = _percent(
        sum(case.fact_traceability for case in cases),
        len(cases),
    )
    standard_total = sum(case.standard_fields_total for case in cases)
    standard_filled = sum(case.standard_fields_filled for case in cases)
    autofill_coverage = _percent(standard_filled, standard_total)
    unapproved_submissions = sum(case.unapproved_submission_count for case in cases)
    work_auth_errors = sum(case.work_authorization_factual_errors for case in cases)

    return EvaluationReport(
        case_count=len(cases),
        viable_job_false_rejection_rate=MetricResult(
            value=apply_metrics.false_rejection_rate,
            target="<3%",
            passed=apply_metrics.false_rejection_rate < 3.0,
        ),
        explicit_no_sponsorship_miss_rate=MetricResult(
            value=_percent(no_sponsor_misses, len(no_sponsor_cases)),
            target="<5%",
            passed=_percent(no_sponsor_misses, len(no_sponsor_cases)) < 5.0,
        ),
        entity_matching_accuracy=MetricResult(
            value=entity_accuracy,
            target=">95%",
            passed=entity_accuracy > 95.0,
        ),
        duplicate_blocking_rate=MetricResult(
            value=duplicate_rate,
            target=">98%",
            passed=not duplicate_cases or duplicate_rate > 98.0,
        ),
        fact_traceability_rate=MetricResult(
            value=traceability,
            target="100%",
            passed=traceability == 100.0,
        ),
        autofill_coverage_rate=MetricResult(
            value=autofill_coverage,
            target=">80%",
            passed=standard_total == 0 or autofill_coverage > 80.0,
        ),
        unapproved_submissions=MetricResult(
            value=float(unapproved_submissions),
            target="0",
            passed=unapproved_submissions == 0,
        ),
        work_authorization_factual_errors=MetricResult(
            value=float(work_auth_errors),
            target="0",
            passed=work_auth_errors == 0,
        ),
    )


def report_rows(report: EvaluationReport) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name, result in report:
        if name == "case_count":
            continue
        rows.append(
            {
                "metric": name,
                "value": result.value,
                "target": result.target,
                "passed": result.passed,
            }
        )
    return rows
