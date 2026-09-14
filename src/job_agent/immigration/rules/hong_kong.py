from job_agent.domain.enums import RouteOwnership, WorkAuthorizationStatus
from job_agent.immigration.engine import WorkAuthorizationInput, build_assessment


class HongKongTtpsRule:
    def evaluate(self, input: WorkAuthorizationInput):
        route_status = input.candidate_route_status
        if route_status == "active":
            return build_assessment(input, route_type="HK_TTPS_C", ownership=RouteOwnership.CANDIDATE_OWNED, status=WorkAuthorizationStatus.ELIGIBLE, fit=1.0, hard_fail_reasons=[], unresolved=[], evidence=[], confidence=1.0)
        if (
            route_status in {
                "approved_not_activated",
                "submitted",
                "documents_preparing",
                "likely_eligible",
            }
            and input.requires_permanent_rights
        ):
            return build_assessment(
                input,
                route_type="HK_TTPS_C",
                ownership=RouteOwnership.CANDIDATE_OWNED,
                status=WorkAuthorizationStatus.INELIGIBLE,
                fit=0.0,
                hard_fail_reasons=[
                    "job requires current Hong Kong work authorisation before the route is active"
                ],
                unresolved=[],
                evidence=[],
                confidence=0.95,
            )
        if route_status in {"approved_not_activated", "submitted", "documents_preparing", "likely_eligible"}:
            return build_assessment(input, route_type="HK_TTPS_C", ownership=RouteOwnership.CANDIDATE_OWNED, status=WorkAuthorizationStatus.LIKELY, fit=0.7, hard_fail_reasons=[], unresolved=["route approval not yet active"], evidence=[], confidence=0.8)
        return build_assessment(input, route_type="HK_TTPS_C", ownership=RouteOwnership.CANDIDATE_OWNED, status=WorkAuthorizationStatus.INELIGIBLE, fit=0.0, hard_fail_reasons=["candidate-owned route is unavailable or expired"], unresolved=[], evidence=[], confidence=0.95)
