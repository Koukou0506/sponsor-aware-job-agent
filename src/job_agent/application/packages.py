from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from job_agent.domain.enums import RoleTrack
from job_agent.domain.ids import new_id
from job_agent.domain.models import Job, MatchAssessment, WorkAuthorizationAssessment
from job_agent.materials.models import (
    Application,
    ApplicationEvent,
    ApplicationPackage,
    GeneratedClaim,
)
from job_agent.materials.screening import FixedAnswerResolver
from job_agent.materials.tailoring import (
    TailoredClaimProposal,
    TailoringProposal,
)
from job_agent.materials.validation import validate_proposal
from job_agent.matcher.requirements import extract_requirements


@dataclass(frozen=True)
class GenerationContext:
    job: Job
    job_version_id: str
    work_authorization: WorkAuthorizationAssessment
    match: MatchAssessment
    approved_facts: dict[str, dict[str, Any]]
    company_name: str


class PackageRepositories(Protocol):
    def get_generation_context(
        self,
        job_id: str,
        candidate_id: str,
    ) -> GenerationContext | None: ...
    def find_active_package(
        self,
        job_id: str,
        candidate_id: str,
        job_version_id: str,
        base_resume_id: str,
    ) -> ApplicationPackage | None: ...
    def add_package(
        self,
        package: ApplicationPackage,
        application: Application,
    ) -> None: ...
    def mark_review_materials_generated(
        self,
        job_id: str,
        candidate_id: str,
    ) -> None: ...
    def set_package_review_status(
        self,
        package_id: str,
        status: str,
        approve_claims: bool = False,
    ) -> None: ...
    def get_application_by_package(self, package_id: str) -> Application | None: ...
    def save_application_event(
        self,
        application: Application,
        event: ApplicationEvent,
    ) -> None: ...
    def commit(self) -> None: ...


class PackageService:
    def __init__(
        self,
        repositories: PackageRepositories,
        screening_resolver: FixedAnswerResolver | None = None,
    ) -> None:
        self._repositories = repositories
        self._screening_resolver = screening_resolver or FixedAnswerResolver({})

    def generate(
        self,
        job_id: str,
        candidate_id: str,
        *,
        cover_letter: bool = False,
        force: bool = False,
    ) -> ApplicationPackage:
        context = self._repositories.get_generation_context(job_id, candidate_id)
        if context is None:
            raise KeyError(job_id)
        if context.work_authorization.hard_fail:
            raise ValueError("work authorization assessment hard-failed")
        if context.work_authorization.work_authorization_fit < 0.5:
            raise ValueError("work authorization fit is below the generation gate")
        if context.match.total_score < 60 and not force:
            raise ValueError("match score is below the generation gate")
        if not context.approved_facts:
            raise ValueError("no approved resume facts are available")

        base_resume_id = (
            "technical-v1"
            if context.match.selected_resume_track is RoleTrack.TECHNICAL
            else "technical-business-v1"
        )
        active = self._repositories.find_active_package(
            job_id,
            candidate_id,
            context.job_version_id,
            base_resume_id,
        )
        if active is not None:
            raise ValueError(f"active package already exists: {active.package_id}")

        proposal = _deterministic_proposal(context)
        requirements = extract_requirements(context.job.description_raw)
        approved_skills = {
            str(skill)
            for fact in context.approved_facts.values()
            for skill in fact.get("skills", [])
        }
        requested_skills = {
            *requirements.mandatory_skills,
            *requirements.preferred_skills,
        }
        report = validate_proposal(
            proposal,
            facts=context.approved_facts,
            approved_skills=approved_skills,
            requested_skills=requested_skills,
        )
        if not report.export_allowed:
            raise ValueError("tailoring proposal failed fact validation")

        now = datetime.now(UTC)
        generated_claims = [
            GeneratedClaim(
                claim_id=new_id("claim"),
                text=claim.text,
                source_fact_ids=claim.source_fact_ids,
                transformation_type=claim.transformation_type,
                confidence=1.0,
                validation_status="verified",
                reviewer_approved=False,
            )
            for claim in [*proposal.professional_summary, *proposal.bullet_claims]
        ]
        fact_references = list(
            dict.fromkeys(
                fact_id
                for claim in generated_claims
                for fact_id in claim.source_fact_ids
            )
        )
        screening_answers = [
            self._screening_resolver.resolve(
                question,
                context.job.country.value,
                context.work_authorization.status.value,
            )
            for question in (
                "currently_authorized",
                "requires_employer_sponsorship",
                "relocation_willingness",
                "notice_period",
                "salary_expectation",
            )
        ]
        package = ApplicationPackage(
            package_id=new_id("package"),
            workspace_id=context.job.workspace_id,
            candidate_id=candidate_id,
            job_id=job_id,
            job_version_id=context.job_version_id,
            base_resume_id=base_resume_id,
            tailored_resume_version=1,
            screening_answers_version=1,
            cover_letter_version=1 if cover_letter else None,
            generated_claims=generated_claims,
            screening_answers=screening_answers,
            fact_references=fact_references,
            validation_status="verified",
            review_status="awaiting_review",
            cover_letter_text=(
                _deterministic_cover_letter(context, fact_references)
                if cover_letter
                else None
            ),
            created_at=now,
        )
        application = Application(
            application_id=new_id("application"),
            workspace_id=context.job.workspace_id,
            candidate_id=candidate_id,
            job_id=job_id,
            package_id=package.package_id,
            application_url=str(context.job.source_url),
            current_state="awaiting_review",
            created_at=now,
        )
        self._repositories.add_package(package, application)
        self._repositories.mark_review_materials_generated(job_id, candidate_id)
        self._repositories.commit()
        return package

    def approve(self, package_id: str) -> None:
        self._review(package_id, package_status="approved", application_state="approved")

    def reject(self, package_id: str) -> None:
        self._review(package_id, package_status="rejected", application_state="rejected")

    def _review(
        self,
        package_id: str,
        *,
        package_status: str,
        application_state: str,
    ) -> None:
        application = self._repositories.get_application_by_package(package_id)
        if application is None:
            raise KeyError(package_id)
        if application.current_state != "awaiting_review":
            raise ValueError(
                f"application is not awaiting review: {application.current_state}"
            )
        now = datetime.now(UTC)
        updated = application.model_copy(update={"current_state": application_state})
        event = ApplicationEvent(
            event_id=new_id("event"),
            application_id=application.application_id,
            from_state=application.current_state,
            to_state=application_state,
            payload={"package_id": package_id},
            created_at=now,
        )
        self._repositories.set_package_review_status(
            package_id,
            package_status,
            approve_claims=package_status == "approved",
        )
        self._repositories.save_application_event(updated, event)
        self._repositories.commit()

    def supersede(self, package_id: str) -> None:
        self._repositories.set_package_review_status(package_id, "superseded")
        self._repositories.commit()


def _deterministic_proposal(context: GenerationContext) -> TailoringProposal:
    requirements = extract_requirements(context.job.description_raw)
    requested = {
        *requirements.mandatory_skills,
        *requirements.preferred_skills,
    }
    ranked = sorted(
        context.approved_facts.items(),
        key=lambda item: (
            -len(
                {str(skill).casefold() for skill in item[1].get("skills", [])}
                & {skill.casefold() for skill in requested}
            ),
            item[0],
        ),
    )
    selected = ranked[:8]
    proposals = [
        TailoredClaimProposal(
            text=str(fact["raw_fact"]),
            source_fact_ids=[fact_id],
            transformation_type="verbatim",
        )
        for fact_id, fact in selected
    ]
    approved_skills = list(
        dict.fromkeys(
            str(skill)
            for _fact_id, fact in selected
            for skill in fact.get("skills", [])
        )
    )
    ordered_skills = sorted(
        approved_skills,
        key=lambda skill: (
            skill.casefold() not in {item.casefold() for item in requested},
            skill.casefold(),
        ),
    )
    return TailoringProposal(
        professional_summary=proposals[:1],
        ordered_skill_names=ordered_skills,
        ordered_project_fact_ids=[fact_id for fact_id, _fact in selected],
        bullet_claims=proposals[1:] or proposals[:1],
    )


def _deterministic_cover_letter(
    context: GenerationContext,
    fact_references: list[str],
) -> str:
    selected = [
        str(context.approved_facts[fact_id]["raw_fact"])
        for fact_id in fact_references[:2]
    ]
    evidence = " ".join(selected)
    return (
        f"Dear Hiring Team,\n\nI am applying for the {context.job.title} role at "
        f"{context.company_name}. {evidence} These verified experiences align with "
        f"the responsibilities described in the role.\n\nSincerely"
    )
