from job_agent.domain.enums import RouteOwnership, WorkAuthorizationStatus
from job_agent.immigration.engine import WorkAuthorizationInput, build_assessment


class NetherlandsHighlySkilledMigrantRule:
    def evaluate(self, input: WorkAuthorizationInput):
        reasons: list[str] = []
        unresolved: list[str] = []
        if input.explicit_negative:
            reasons.append("job explicitly states sponsorship or immigration support is unavailable")
        if input.requires_permanent_rights:
            reasons.append("job requires existing unrestricted Dutch work rights")
        if input.entity_match_uncertain:
            unresolved.append("employer legal entity match requires review")
        elif not input.entity_verified:
            reasons.append("employer legal entity is not a verified recognised sponsor")
        if input.salary_eligible is False:
            reasons.append("disclosed salary is below the configured highly skilled migrant threshold")
        if input.contract_eligible is False:
            reasons.append("contract is incompatible with the configured route")
        if reasons:
            return build_assessment(input, route_type="NL_HIGHLY_SKILLED_MIGRANT", ownership=RouteOwnership.EMPLOYER_SPONSORED, status=WorkAuthorizationStatus.INELIGIBLE, fit=0.0, hard_fail_reasons=reasons, unresolved=[], evidence=[], confidence=0.95)
        if input.salary_eligible is None:
            unresolved.append("salary eligibility is unknown")
        if input.contract_eligible is None:
            unresolved.append("contract eligibility is unknown")
        return build_assessment(input, route_type="NL_HIGHLY_SKILLED_MIGRANT", ownership=RouteOwnership.EMPLOYER_SPONSORED, status=WorkAuthorizationStatus.UNCERTAIN if unresolved else WorkAuthorizationStatus.ELIGIBLE, fit=0.6 if unresolved else 1.0, hard_fail_reasons=[], unresolved=unresolved, evidence=[], confidence=0.75 if unresolved else 0.95)
