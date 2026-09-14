import pytest

from job_agent.domain.enums import (
    Region,
    RoleTrack,
    RouteOwnership,
    WorkAuthorizationStatus,
)
from job_agent.immigration.engine import ImmigrationEngine, WorkAuthorizationInput
from job_agent.matcher.classifier import classify_role
from job_agent.matcher.requirements import JobRequirements
from job_agent.matcher.scoring import ScoreInputs, calculate_track_score


@pytest.mark.parametrize(
    ("country", "updates", "expected_route", "expected_ownership"),
    [
        (
            "UK",
            {
                "entity_verified": True,
                "entity_status": "active",
                "salary_eligible": True,
                "role_eligible": True,
            },
            "UK_SKILLED_WORKER",
            RouteOwnership.EMPLOYER_SPONSORED,
        ),
        (
            "NL",
            {
                "entity_verified": True,
                "salary_eligible": True,
                "contract_eligible": True,
            },
            "NL_HIGHLY_SKILLED_MIGRANT",
            RouteOwnership.EMPLOYER_SPONSORED,
        ),
        (
            "DE",
            {"blue_card_eligible": True},
            "DE_EU_BLUE_CARD",
            RouteOwnership.JOB_SUPPORTED,
        ),
        (
            "IE",
            {"critical_skills_eligible": True},
            "IE_CRITICAL_SKILLS",
            RouteOwnership.EMPLOYER_SPONSORED,
        ),
        (
            "HK",
            {
                "candidate_route_status": "active",
                "explicit_negative": True,
            },
            "HK_TTPS_C",
            RouteOwnership.CANDIDATE_OWNED,
        ),
    ],
)
def test_representative_region_routes_are_modeled_separately(
    country: str,
    updates: dict[str, object],
    expected_route: str,
    expected_ownership: RouteOwnership,
) -> None:
    assessment = ImmigrationEngine().evaluate(
        WorkAuthorizationInput.fixture(country, **updates)
    )

    assert assessment.country is Region(country)
    assert assessment.route_type == expected_route
    assert assessment.route_ownership is expected_ownership
    assert assessment.status is WorkAuthorizationStatus.ELIGIBLE
    assert assessment.hard_fail is False


def test_hong_kong_pending_candidate_route_does_not_claim_current_work_rights() -> None:
    assessment = ImmigrationEngine().evaluate(
        WorkAuthorizationInput.fixture(
            "HK",
            candidate_route_status="likely_eligible",
            requires_permanent_rights=True,
        )
    )

    assert assessment.status is WorkAuthorizationStatus.INELIGIBLE
    assert assessment.hard_fail is True
    assert "current Hong Kong work authorisation" in assessment.hard_fail_reasons[0]


@pytest.mark.parametrize(
    ("title", "skills", "expected"),
    [
        ("Junior Data Engineer", ["python", "sql"], RoleTrack.TECHNICAL),
        (
            "Implementation Consultant",
            ["implementation", "project management"],
            RoleTrack.TECHNICAL_BUSINESS,
        ),
        ("Solutions Engineer", ["python", "api"], RoleTrack.MIXED),
    ],
)
def test_role_classifier_preserves_two_tracks_and_mixed_roles(
    title: str,
    skills: list[str],
    expected: RoleTrack,
) -> None:
    result = classify_role(title, JobRequirements(mandatory_skills=skills))
    assert result.primary_track is expected


def test_work_authorisation_gate_blocks_material_generation_below_threshold() -> None:
    blocked = ScoreInputs(
        work_authorization_fit=0.49,
        skill_fit=0.9,
        experience_fit=0.9,
        role_transition_fit=0.9,
        language_fit=1.0,
        company_signal=0.8,
        recency=1.0,
    )
    allowed = blocked.model_copy(update={"work_authorization_fit": 0.5})

    assert blocked.material_generation_allowed is False
    assert allowed.material_generation_allowed is True


def test_tracks_use_different_scoring_weights() -> None:
    inputs = ScoreInputs(
        work_authorization_fit=1.0,
        skill_fit=1.0,
        experience_fit=0.4,
        role_transition_fit=0.3,
        language_fit=1.0,
        company_signal=0.8,
        recency=1.0,
    )

    technical = calculate_track_score("technical", inputs)
    technical_business = calculate_track_score("technical_business", inputs)

    assert technical != technical_business
    assert technical > technical_business
