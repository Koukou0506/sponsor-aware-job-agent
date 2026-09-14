from job_agent.domain.enums import RouteOwnership, WorkAuthorizationStatus
from job_agent.immigration.engine import WorkAuthorizationInput, build_assessment


class GermanyWorkRouteRule:
    def evaluate(self, input: WorkAuthorizationInput):
        if input.explicit_negative and input.requires_permanent_rights:
            return build_assessment(input, route_type="DE_SKILLED_WORKER", ownership=RouteOwnership.JOB_SUPPORTED, status=WorkAuthorizationStatus.INELIGIBLE, fit=0.0, hard_fail_reasons=["job requires existing unrestricted German work rights"], unresolved=[], evidence=[], confidence=0.95)
        if input.blue_card_eligible is True:
            return build_assessment(input, route_type="DE_EU_BLUE_CARD", ownership=RouteOwnership.JOB_SUPPORTED, status=WorkAuthorizationStatus.ELIGIBLE, fit=1.0, hard_fail_reasons=[], unresolved=[], evidence=[], confidence=0.95)
        if input.skilled_worker_eligible is True:
            unresolved = []
            if input.blue_card_eligible is None or input.salary_eligible is None:
                unresolved.append("Blue Card salary or eligibility is unknown")
            if input.degree_aligned is None:
                unresolved.append("degree-to-role alignment is not verified")
            return build_assessment(input, route_type="DE_SKILLED_WORKER", ownership=RouteOwnership.JOB_SUPPORTED, status=WorkAuthorizationStatus.UNCERTAIN if unresolved else WorkAuthorizationStatus.ELIGIBLE, fit=0.7 if unresolved else 0.9, hard_fail_reasons=[], unresolved=unresolved, evidence=[], confidence=0.75 if unresolved else 0.9)
        if input.blue_card_eligible is None or input.skilled_worker_eligible is None:
            return build_assessment(input, route_type="DE_SKILLED_WORKER", ownership=RouteOwnership.JOB_SUPPORTED, status=WorkAuthorizationStatus.UNCERTAIN, fit=0.6, hard_fail_reasons=[], unresolved=["job-supported route eligibility is unknown"], evidence=[], confidence=0.65)
        return build_assessment(input, route_type="DE_SKILLED_WORKER", ownership=RouteOwnership.JOB_SUPPORTED, status=WorkAuthorizationStatus.INELIGIBLE, fit=0.0, hard_fail_reasons=["neither configured German work route is eligible"], unresolved=[], evidence=[], confidence=0.9)
