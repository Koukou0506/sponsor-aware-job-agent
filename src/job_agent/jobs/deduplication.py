from hashlib import sha256
from typing import Literal

from job_agent.domain.models import Job

JobChange = Literal["new", "duplicate", "revision"]


def primary_job_key(job: Job) -> str:
    return f"{job.source_platform}:{job.company_id}:{job.external_job_id}"


def fallback_fingerprint(job: Job, company_domain: str | None = None) -> str:
    payload = "|".join(
        [
            company_domain or job.company_id,
            job.normalized_title,
            job.city or "",
            job.description_normalized,
        ]
    )
    return sha256(payload.encode()).hexdigest()


def content_hash(job: Job) -> str:
    payload = "|".join([job.title, job.description_normalized, job.city or ""])
    return sha256(payload.encode()).hexdigest()


def classify_job_change(existing: Job | None, incoming: Job) -> JobChange:
    if existing is None:
        return "new"
    if (
        existing.description_normalized == incoming.description_normalized
        and existing.title == incoming.title
        and existing.city == incoming.city
    ):
        return "duplicate"
    return "revision"
