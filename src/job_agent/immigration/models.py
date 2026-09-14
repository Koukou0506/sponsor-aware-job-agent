from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CountryCode = Literal["UK", "NL", "DE", "IE", "HK"]


class ImmigrationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RegistryRecord(ImmigrationModel):
    registry_record_id: str
    country: CountryCode
    legal_name: str
    canonical_domain: str | None
    registry_identifier: str
    status: str
    source: str
    ruleset_version: str
    effective_date: date | None = None
    retrieved_at: datetime | None = None
    aliases: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompanyEntityMatch(ImmigrationModel):
    registry_record_id: str | None
    match_type: Literal["exact", "exact_normalized", "domain", "verified_alias", "fuzzy", "none"]
    confidence: float = Field(ge=0, le=1)
    verified: bool
    requires_review: bool


class ImmigrationRuleset(ImmigrationModel):
    country: CountryCode
    version: str
    source: str
    effective_date: date
    salary_thresholds: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
