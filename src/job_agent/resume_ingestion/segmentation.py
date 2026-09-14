import re
from collections.abc import Callable

from job_agent.domain.ids import new_id
from job_agent.resume_ingestion.extraction import ExtractedBullet
from job_agent.resume_ingestion.models import ExtractedFactCandidate, Provenance

MetricValue = int | float | str

_KNOWN_SKILLS = (
    "Python",
    "SQL",
    "Linux",
    "Docker",
    "FastAPI",
    "PostgreSQL",
    "Git",
    "scikit-learn",
    "project management",
    "implementation",
)


def _skills_in_text(text: str) -> list[str]:
    lowered = text.casefold()
    return [
        skill
        for skill in _KNOWN_SKILLS
        if re.search(
            rf"(?<!\w){re.escape(skill.casefold())}(?!\w)",
            lowered,
        )
    ]


def _sample_phrase(value: MetricValue) -> str:
    if isinstance(value, (int, float)):
        return f"Processed {value:,} samples"
    return f"Processed {value} samples"


def _parameter_phrase(value: MetricValue) -> str:
    return f"Analysed {value} parameters"


_METRIC_PHRASES: dict[str, Callable[[MetricValue], str]] = {
    "sample_count": _sample_phrase,
    "parameter_count": _parameter_phrase,
}


def _compose_action(action: str, object_name: str) -> str:
    action_words = action.split()
    object_words = object_name.split()
    if action_words and object_words and action_words[-1].casefold() == object_words[-1].casefold():
        return " ".join([*action_words[:-1], *object_words])
    return f"{action} {object_name}"


def segment_bullet(bullet: ExtractedBullet) -> list[ExtractedFactCandidate]:
    provenance = Provenance(
        source_id=bullet.source_id,
        page_number=bullet.page_number,
        section=bullet.section,
        original_text=bullet.original_text,
        extraction_method="structured_extraction",
        extraction_confidence=bullet.confidence,
    )
    facts: list[ExtractedFactCandidate] = []
    inferred_skills = list(
        dict.fromkeys(
            [*(_skills_in_text(bullet.original_text)), *([bullet.method] if bullet.method else [])]
        )
    )
    if bullet.action and bullet.object:
        method_suffix = f" using {bullet.method}" if bullet.method else ""
        facts.append(
            ExtractedFactCandidate(
                candidate_fact_id=new_id("candidate"),
                raw_fact=f"{_compose_action(bullet.action, bullet.object)}{method_suffix}",
                category=bullet.category,
                organisation=bullet.organisation,
                role_or_project=bullet.role_or_project,
                skills=inferred_skills,
                provenance=provenance,
            )
        )
    for metric_name, metric_value in bullet.metrics.items():
        formatter = _METRIC_PHRASES.get(metric_name)
        if formatter is None:
            continue
        facts.append(
            ExtractedFactCandidate(
                candidate_fact_id=new_id("candidate"),
                raw_fact=formatter(metric_value),
                category=bullet.category,
                organisation=bullet.organisation,
                role_or_project=bullet.role_or_project,
                metrics={metric_name: metric_value},
                skills=inferred_skills,
                provenance=provenance,
            )
        )
    if bullet.outcome:
        facts.append(
            ExtractedFactCandidate(
                candidate_fact_id=new_id("candidate"),
                raw_fact=bullet.outcome,
                category=bullet.category,
                organisation=bullet.organisation,
                role_or_project=bullet.role_or_project,
                skills=inferred_skills,
                provenance=provenance,
            )
        )
    return facts
