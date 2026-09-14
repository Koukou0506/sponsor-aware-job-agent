from job_agent.domain.enums import RouteOwnership, WorkAuthorizationStatus
from job_agent.immigration.engine import WorkAuthorizationInput, build_assessment


class IrelandEmploymentPermitRule:
    def evaluate(self, input: WorkAuthorizationInput):
        reasons: list[str] = []
        if input.explicit_negative:
            reasons.append("job explicitly states employment-permit support is unavailable")
        if input.requires_permanent_rights:
            reasons.append("job requires existing unrestricted Irish work rights")
        if input.occupation_ineligible:
            reasons.append("occupation is on the configured ineligible list")
        if input.salary_eligible is False:
            reasons.append("disclosed salary is below the configured permit threshold")
        if reasons:
            return build_assessment(input, route_type="IE_GENERAL_PERMIT", ownership=RouteOwnership.EMPLOYER_SPONSORED, status=WorkAuthorizationStatus.INELIGIBLE, fit=0.0, hard_fail_reasons=reasons, unresolved=[], evidence=[], confidence=0.95)
        if input.critical_skills_eligible is True:
            return build_assessment(input, route_type="IE_CRITICAL_SKILLS", ownership=RouteOwnership.EMPLOYER_SPONSORED, status=WorkAuthorizationStatus.ELIGIBLE, fit=1.0, hard_fail_reasons=[], unresolved=[], evidence=[], confidence=0.95)
        if input.general_permit_eligible is True:
            unresolved = [] if input.entity_verified else ["employer entity requires verification"]
            return build_assessment(input, route_type="IE_GENERAL_PERMIT", ownership=RouteOwnership.EMPLOYER_SPONSORED, status=WorkAuthorizationStatus.UNCERTAIN if unresolved else WorkAuthorizationStatus.LIKELY, fit=0.65 if unresolved else 0.8, hard_fail_reasons=[], unresolved=unresolved, evidence=[], confidence=0.7 if unresolved else 0.85)
        if input.critical_skills_eligible is None or input.general_permit_eligible is None:
            return build_assessment(input, route_type="IE_GENERAL_PERMIT", ownership=RouteOwnership.EMPLOYER_SPONSORED, status=WorkAuthorizationStatus.UNCERTAIN, fit=0.6, hard_fail_reasons=[], unresolved=["permit route eligibility is unknown"], evidence=[], confidence=0.65)
        return build_assessment(input, route_type="IE_GENERAL_PERMIT", ownership=RouteOwnership.EMPLOYER_SPONSORED, status=WorkAuthorizationStatus.INELIGIBLE, fit=0.0, hard_fail_reasons=["no configured Irish employment permit route is eligible"], unresolved=[], evidence=[], confidence=0.9)
