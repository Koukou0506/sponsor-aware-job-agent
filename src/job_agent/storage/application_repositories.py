from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from job_agent.materials.models import (
    Application,
    ApplicationEvent,
    ApplicationPackage,
    GeneratedClaim,
    ScreeningAnswer,
)
from job_agent.storage.application_orm import (
    ApplicationEventRow,
    ApplicationPackageRow,
    ApplicationRow,
    GeneratedClaimRow,
    ScreeningAnswerRow,
)

_ACTIVE_STATUSES = {"draft", "awaiting_review", "approved"}


def package_active_key(package: ApplicationPackage) -> str:
    return "|".join(
        (
            package.job_id,
            package.candidate_id,
            package.job_version_id,
            package.base_resume_id,
        )
    )


class PackageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, package: ApplicationPackage) -> None:
        active_key = (
            package_active_key(package)
            if package.review_status in _ACTIVE_STATUSES
            else None
        )
        self._session.add(
            ApplicationPackageRow(
                package_id=package.package_id,
                workspace_id=package.workspace_id,
                candidate_id=package.candidate_id,
                job_id=package.job_id,
                job_version_id=package.job_version_id,
                base_resume_id=package.base_resume_id,
                active_key=active_key,
                tailored_resume_version=package.tailored_resume_version,
                screening_answers_version=package.screening_answers_version,
                cover_letter_version=package.cover_letter_version,
                fact_references=package.fact_references,
                validation_status=package.validation_status,
                review_status=package.review_status,
                cover_letter_text=package.cover_letter_text,
                created_at=package.created_at,
            )
        )
        for position, claim in enumerate(package.generated_claims):
            self._session.add(
                GeneratedClaimRow(
                    claim_id=claim.claim_id,
                    package_id=package.package_id,
                    position=position,
                    text=claim.text,
                    source_fact_ids=claim.source_fact_ids,
                    transformation_type=claim.transformation_type,
                    confidence=claim.confidence,
                    validation_status=claim.validation_status,
                    reviewer_approved=claim.reviewer_approved,
                )
            )
        for position, answer in enumerate(package.screening_answers):
            self._session.add(
                ScreeningAnswerRow(
                    answer_id=answer.answer_id,
                    package_id=package.package_id,
                    position=position,
                    canonical_question=answer.canonical_question,
                    displayed_question=answer.displayed_question,
                    answer_text=answer.answer_text,
                    source_type=answer.source_type,
                    source_fact_ids=answer.source_fact_ids,
                    requires_review=answer.requires_review,
                    risk_level=answer.risk_level,
                )
            )

    def get(self, package_id: str) -> ApplicationPackage | None:
        row = self._session.get(ApplicationPackageRow, package_id)
        if row is None:
            return None
        claims = list(
            self._session.scalars(
                select(GeneratedClaimRow)
                .where(GeneratedClaimRow.package_id == package_id)
                .order_by(GeneratedClaimRow.position)
            )
        )
        answers = list(
            self._session.scalars(
                select(ScreeningAnswerRow)
                .where(ScreeningAnswerRow.package_id == package_id)
                .order_by(ScreeningAnswerRow.position)
            )
        )
        return ApplicationPackage(
            package_id=row.package_id,
            workspace_id=row.workspace_id,
            candidate_id=row.candidate_id,
            job_id=row.job_id,
            job_version_id=row.job_version_id,
            base_resume_id=row.base_resume_id,
            tailored_resume_version=row.tailored_resume_version,
            screening_answers_version=row.screening_answers_version,
            cover_letter_version=row.cover_letter_version,
            generated_claims=[
                GeneratedClaim(
                    claim_id=item.claim_id,
                    text=item.text,
                    source_fact_ids=item.source_fact_ids,
                    transformation_type=item.transformation_type,
                    confidence=item.confidence,
                    validation_status=item.validation_status,
                    reviewer_approved=item.reviewer_approved,
                )
                for item in claims
            ],
            screening_answers=[
                ScreeningAnswer(
                    answer_id=item.answer_id,
                    canonical_question=item.canonical_question,
                    displayed_question=item.displayed_question,
                    answer_text=item.answer_text,
                    source_type=item.source_type,
                    source_fact_ids=item.source_fact_ids,
                    requires_review=item.requires_review,
                    risk_level=item.risk_level,
                )
                for item in answers
            ],
            fact_references=row.fact_references,
            validation_status=row.validation_status,
            review_status=row.review_status,
            cover_letter_text=row.cover_letter_text,
            created_at=row.created_at,
        )

    def set_review_status(self, package_id: str, status: str) -> None:
        row = self._session.get(ApplicationPackageRow, package_id)
        if row is None:
            raise KeyError(package_id)
        row.review_status = status
        row.active_key = row.active_key if status in _ACTIVE_STATUSES else None

    def find_active(
        self,
        job_id: str,
        candidate_id: str,
        job_version_id: str,
        base_resume_id: str,
    ) -> ApplicationPackage | None:
        key = "|".join((job_id, candidate_id, job_version_id, base_resume_id))
        row = self._session.scalar(
            select(ApplicationPackageRow).where(
                ApplicationPackageRow.active_key == key
            )
        )
        return self.get(row.package_id) if row else None


class ApplicationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, application: Application) -> None:
        self._session.add(ApplicationRow(**application.model_dump()))

    def get(self, application_id: str) -> Application | None:
        row = self._session.get(ApplicationRow, application_id)
        return Application.model_validate(row, from_attributes=True) if row else None

    def get_by_package(self, package_id: str) -> Application | None:
        row = self._session.scalar(
            select(ApplicationRow).where(ApplicationRow.package_id == package_id)
        )
        return Application.model_validate(row, from_attributes=True) if row else None

    def update_state(
        self,
        application_id: str,
        state: str,
        submitted_at=None,
    ) -> None:
        row = self._session.get(ApplicationRow, application_id)
        if row is None:
            raise KeyError(application_id)
        row.current_state = state
        row.submitted_at = submitted_at

    def add_event(self, event: ApplicationEvent) -> None:
        self._session.add(ApplicationEventRow(**event.model_dump()))


class SqlAlchemyApplicationRepositories:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session = session_factory()
        self.packages = PackageRepository(self._session)
        self.applications = ApplicationRepository(self._session)

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def get_generation_context(self, job_id: str, candidate_id: str):
        return _generation_context(self._session, job_id, candidate_id)

    def find_active_package(
        self,
        job_id: str,
        candidate_id: str,
        job_version_id: str,
        base_resume_id: str,
    ) -> ApplicationPackage | None:
        return self.packages.find_active(
            job_id,
            candidate_id,
            job_version_id,
            base_resume_id,
        )

    def add_package(
        self,
        package: ApplicationPackage,
        application: Application,
    ) -> None:
        self.packages.add(package)
        self.applications.add(application)

    def mark_review_materials_generated(
        self,
        job_id: str,
        candidate_id: str,
    ) -> None:
        from job_agent.storage.orm import ReviewQueueRow

        self._session.execute(
            update(ReviewQueueRow)
            .where(
                ReviewQueueRow.job_id == job_id,
                ReviewQueueRow.candidate_id == candidate_id,
            )
            .values(materials_generated=True, status="package_generated")
        )

    def set_package_review_status(
        self,
        package_id: str,
        status: str,
        approve_claims: bool = False,
    ) -> None:
        self.packages.set_review_status(package_id, status)
        if approve_claims:
            claims = list(
                self._session.scalars(
                    select(GeneratedClaimRow).where(
                        GeneratedClaimRow.package_id == package_id
                    )
                )
            )
            for claim in claims:
                claim.reviewer_approved = True

    def get_application(self, application_id: str) -> Application | None:
        return self.applications.get(application_id)

    def get_application_by_package(self, package_id: str) -> Application | None:
        return self.applications.get_by_package(package_id)

    def save_application_event(
        self,
        application: Application,
        event: ApplicationEvent,
    ) -> None:
        self.applications.update_state(
            application.application_id,
            application.current_state,
            application.submitted_at,
        )
        self.applications.add_event(event)

    def close(self) -> None:
        self._session.close()


# Application-service facade methods are kept here so UI and CLI never import ORM rows.
def _generation_context(
    session: Session,
    job_id: str,
    candidate_id: str,
):
    from job_agent.application.packages import GenerationContext
    from job_agent.domain.enums import (
        JobStatus,
        Region,
        RoleTrack,
        RouteOwnership,
        WorkAuthorizationStatus,
    )
    from job_agent.domain.models import Job, MatchAssessment, WorkAuthorizationAssessment
    from job_agent.storage.orm import (
        CompanyRow,
        JobRow,
        JobVersionRow,
        MatchAssessmentRow,
        WorkAuthorizationAssessmentRow,
    )
    from job_agent.storage.resume_orm import ResumeFactRow

    job_row = session.get(JobRow, job_id)
    if job_row is None:
        return None
    version = session.scalar(
        select(JobVersionRow)
        .where(JobVersionRow.job_id == job_id)
        .order_by(JobVersionRow.captured_at.desc())
    )
    work_auth_row = session.scalar(
        select(WorkAuthorizationAssessmentRow)
        .where(
            WorkAuthorizationAssessmentRow.job_id == job_id,
            WorkAuthorizationAssessmentRow.candidate_id == candidate_id,
        )
        .order_by(WorkAuthorizationAssessmentRow.assessed_at.desc())
    )
    match_row = session.scalar(
        select(MatchAssessmentRow)
        .where(
            MatchAssessmentRow.job_id == job_id,
            MatchAssessmentRow.candidate_id == candidate_id,
        )
        .order_by(MatchAssessmentRow.assessed_at.desc())
    )
    if version is None or work_auth_row is None or match_row is None:
        return None
    company = session.get(CompanyRow, job_row.company_id)
    fact_rows = list(
        session.scalars(
            select(ResumeFactRow).where(
                ResumeFactRow.candidate_id == candidate_id,
                ResumeFactRow.verification_status == "approved",
            )
        )
    )
    facts = {
        row.fact_id: {
            "raw_fact": row.raw_fact,
            "metrics": row.metrics,
            "skills": row.skills,
            "category": row.category,
            "organisation": row.organisation,
            "role_or_project": row.role_or_project,
            "claim_status": row.claim_status,
        }
        for row in fact_rows
    }
    scores = match_row.component_scores
    return GenerationContext(
        job=Job(
            job_id=job_row.job_id,
            workspace_id=job_row.workspace_id,
            external_job_id=job_row.external_job_id,
            source_platform=job_row.source_platform,
            source_url=job_row.source_url,
            company_id=job_row.company_id,
            title=job_row.title,
            normalized_title=job_row.normalized_title,
            country=Region(job_row.country),
            city=job_row.city,
            role_track=RoleTrack(job_row.role_track),
            description_raw=job_row.description_raw,
            description_normalized=job_row.description_normalized,
            published_at=job_row.published_at,
            discovered_at=job_row.discovered_at,
            status=JobStatus(job_row.status),
        ),
        job_version_id=version.job_version_id,
        work_authorization=WorkAuthorizationAssessment(
            assessment_id=work_auth_row.assessment_id,
            workspace_id=work_auth_row.workspace_id,
            candidate_id=work_auth_row.candidate_id,
            job_id=work_auth_row.job_id,
            country=Region(work_auth_row.country),
            route_type=work_auth_row.route_type,
            route_ownership=RouteOwnership(work_auth_row.route_ownership),
            status=WorkAuthorizationStatus(work_auth_row.status),
            work_authorization_fit=work_auth_row.work_authorization_fit,
            hard_fail=work_auth_row.hard_fail,
            hard_fail_reasons=work_auth_row.hard_fail_reasons,
            unresolved_items=work_auth_row.unresolved_items,
            evidence=work_auth_row.evidence,
            confidence=work_auth_row.confidence,
            ruleset_version=work_auth_row.ruleset_version,
            assessed_at=work_auth_row.assessed_at,
        ),
        match=MatchAssessment(
            assessment_id=match_row.assessment_id,
            workspace_id=match_row.workspace_id,
            candidate_id=match_row.candidate_id,
            job_id=match_row.job_id,
            selected_resume_track=RoleTrack(match_row.selected_resume_track),
            visa_fit=scores["visa_fit"],
            skill_fit=scores["skill_fit"],
            experience_fit=scores["experience_fit"],
            language_fit=scores["language_fit"],
            role_transition_fit=scores["role_transition_fit"],
            company_signal=scores["company_signal"],
            recency_score=scores["recency_score"],
            total_score=match_row.total_score,
            matching_evidence=match_row.matching_evidence,
            missing_requirements=match_row.missing_requirements,
            disqualifiers=match_row.disqualifiers,
            model_version=match_row.model_version,
            assessed_at=match_row.assessed_at,
        ),
        approved_facts=facts,
        company_name=company.canonical_name if company else "Unknown company",
    )
