from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict

from job_agent.domain.enums import Region, RouteOwnership, WorkAuthorizationStatus
from job_agent.domain.ids import new_id
from job_agent.domain.models import Evidence, WorkAuthorizationAssessment


class WorkAuthorizationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: str = "default"
    candidate_id: str = "default"
    job_id: str
    country: Region
    entity_verified: bool
    entity_status: str | None = None
    entity_match_uncertain: bool = False
    explicit_positive: bool = False
    explicit_negative: bool = False
    requires_permanent_rights: bool = False
    salary_eligible: bool | None = None
    role_eligible: bool | None = None
    contract_eligible: bool | None = None
    degree_aligned: bool | None = None
    blue_card_eligible: bool | None = None
    skilled_worker_eligible: bool | None = None
    critical_skills_eligible: bool | None = None
    general_permit_eligible: bool | None = None
    occupation_ineligible: bool = False
    candidate_route_status: str | None = None
    ruleset_version: str

    @classmethod
    def fixture(cls, country: str, **updates: object) -> "WorkAuthorizationInput":
        payload: dict[str, object] = {
            "job_id": "job_fixture",
            "country": Region(country),
            "ruleset_version": f"{country.casefold()}-fixture",
            "entity_verified": False,
        }
        payload.update(updates)
        return cls.model_validate(payload)


class CountryRule(Protocol):
    def evaluate(self, input: WorkAuthorizationInput) -> WorkAuthorizationAssessment: ...


def build_assessment(
    input: WorkAuthorizationInput,
    *,
    route_type: str,
    ownership: RouteOwnership,
    status: WorkAuthorizationStatus,
    fit: float,
    hard_fail_reasons: list[str],
    unresolved: list[str],
    evidence: list[Evidence],
    confidence: float,
) -> WorkAuthorizationAssessment:
    return WorkAuthorizationAssessment(
        assessment_id=new_id("wa"),
        workspace_id=input.workspace_id,
        candidate_id=input.candidate_id,
        job_id=input.job_id,
        country=input.country,
        route_type=route_type,
        route_ownership=ownership,
        status=status,
        work_authorization_fit=fit,
        hard_fail=bool(hard_fail_reasons),
        hard_fail_reasons=hard_fail_reasons,
        unresolved_items=unresolved,
        evidence=evidence,
        confidence=confidence,
        ruleset_version=input.ruleset_version,
        assessed_at=datetime.now(UTC),
    )


class ImmigrationEngine:
    def __init__(self, rules: dict[Region, CountryRule] | None = None) -> None:
        if rules is None:
            from job_agent.immigration.rules.germany import GermanyWorkRouteRule
            from job_agent.immigration.rules.hong_kong import HongKongTtpsRule
            from job_agent.immigration.rules.ireland import IrelandEmploymentPermitRule
            from job_agent.immigration.rules.netherlands import NetherlandsHighlySkilledMigrantRule
            from job_agent.immigration.rules.uk import UkSkilledWorkerRule

            rules = {
                Region.UK: UkSkilledWorkerRule(),
                Region.NL: NetherlandsHighlySkilledMigrantRule(),
                Region.DE: GermanyWorkRouteRule(),
                Region.IE: IrelandEmploymentPermitRule(),
                Region.HK: HongKongTtpsRule(),
            }
        self._rules = rules

    def evaluate(self, input: WorkAuthorizationInput) -> WorkAuthorizationAssessment:
        return self._rules[input.country].evaluate(input)
