from datetime import datetime

from bs4 import BeautifulSoup

from job_agent.connectors.base import RawJob
from job_agent.domain.enums import Region
from job_agent.domain.ids import new_id
from job_agent.domain.models import Job

_REGION_TERMS: tuple[tuple[str, Region], ...] = (
    ("hong kong", Region.HK),
    ("united kingdom", Region.UK),
    ("great britain", Region.UK),
    (" uk", Region.UK),
    (",uk", Region.UK),
    ("netherlands", Region.NL),
    ("holland", Region.NL),
    ("germany", Region.DE),
    ("deutschland", Region.DE),
    ("ireland", Region.IE),
)
_COUNTRY_CODES = {"gb": Region.UK, "uk": Region.UK, "nl": Region.NL, "de": Region.DE, "ie": Region.IE, "hk": Region.HK}


def _collapse(text: str) -> str:
    return " ".join(text.split())


def infer_region(location_text: str, region_hint: str | None = None) -> Region:
    combined = f"{location_text} {region_hint or ''}".strip().lower()
    padded = f" {combined.replace(',', ',')}"
    for term, region in _REGION_TERMS:
        if term in padded:
            return region
    for token in combined.replace(",", " ").split():
        if token in _COUNTRY_CODES:
            return _COUNTRY_CODES[token]
    raise ValueError(f"unsupported or unknown region: {location_text}")


def normalize_raw_job(
    raw: RawJob,
    company_id: str,
    now: datetime,
    *,
    workspace_id: str = "default",
    region_hint: str | None = None,
) -> Job:
    description = BeautifulSoup(raw.description_html, "lxml").get_text(" ", strip=True)
    title = _collapse(raw.title)
    return Job(
        job_id=new_id("job"),
        workspace_id=workspace_id,
        external_job_id=raw.external_job_id,
        source_platform=raw.platform,
        source_url=raw.application_url,
        company_id=company_id,
        title=title,
        normalized_title=title.casefold(),
        country=infer_region(raw.location_text, region_hint),
        city=raw.location_text.split(",", maxsplit=1)[0].strip() or None,
        description_raw=_collapse(description),
        description_normalized=_collapse(description).casefold(),
        published_at=raw.published_at,
        discovered_at=now,
    )
