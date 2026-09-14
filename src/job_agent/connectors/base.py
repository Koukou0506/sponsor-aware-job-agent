from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BoardRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    platform: str
    company_name: str
    board_token: str
    region_hint: str | None = None
    base_url: HttpUrl | None = None


class RawJob(BaseModel):
    model_config = ConfigDict(extra="forbid")
    platform: str
    board_token: str
    external_job_id: str
    company_name: str
    title: str
    location_text: str
    description_html: str
    application_url: HttpUrl
    published_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_payload: dict[str, Any]


class JobConnector(Protocol):
    async def list_jobs(self, board: BoardRef) -> list[RawJob]: ...

    async def fetch_job(self, board: BoardRef, external_job_id: str) -> RawJob: ...

    async def health_check(self, board: BoardRef) -> bool: ...
