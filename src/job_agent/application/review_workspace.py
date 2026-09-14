from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from shutil import rmtree
from typing import Any

import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from job_agent.application.packages import PackageService
from job_agent.application.tracker import ApplicationTracker, allowed_transitions
from job_agent.materials.rendering import ResumeRenderer, render_cover_letter_pdf
from job_agent.materials.screening import load_fixed_answer_resolver
from job_agent.materials.validation import ClaimValidation, ValidationReport
from job_agent.observability.service import OperationsService
from job_agent.settings import Settings
from job_agent.storage.application_orm import (
    ApplicationPackageRow,
    ApplicationRow,
    GeneratedClaimRow,
    ScreeningAnswerRow,
)
from job_agent.storage.application_repositories import SqlAlchemyApplicationRepositories
from job_agent.storage.orm import (
    CompanyRow,
    ConnectorHealthRow,
    JobRow,
    MatchAssessmentRow,
    ReviewQueueRow,
    RunRecordRow,
    WorkAuthorizationAssessmentRow,
)
from job_agent.storage.resume_orm import ResumeFactRow


class ReviewWorkspaceService:
    """Serialisable read models and explicit user actions for the Streamlit UI."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        settings: Settings,
        candidate_id: str = "default",
        workspace_id: str = "default",
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._candidate_id = candidate_id
        self._workspace_id = workspace_id

    def dashboard_summary(self) -> dict[str, Any]:
        with self._session_factory() as session:
            today = datetime.now(UTC).date()
            jobs = list(
                session.scalars(
                    select(JobRow).where(JobRow.workspace_id == self._workspace_id)
                )
            )
            applications = list(
                session.scalars(
                    select(ApplicationRow).where(
                        ApplicationRow.workspace_id == self._workspace_id,
                        ApplicationRow.candidate_id == self._candidate_id,
                    )
                )
            )
            pending_reviews = session.scalar(
                select(func.count()).select_from(ReviewQueueRow).where(
                    ReviewQueueRow.workspace_id == self._workspace_id,
                    ReviewQueueRow.candidate_id == self._candidate_id,
                    ReviewQueueRow.status.in_(["pending", "needs_verification", "saved"]),
                )
            )
            pending_packages = session.scalar(
                select(func.count()).select_from(ApplicationPackageRow).where(
                    ApplicationPackageRow.workspace_id == self._workspace_id,
                    ApplicationPackageRow.candidate_id == self._candidate_id,
                    ApplicationPackageRow.review_status == "awaiting_review",
                )
            )
            estimated_cost = session.scalar(
                select(func.coalesce(func.sum(RunRecordRow.estimated_cost), 0.0)).where(
                    RunRecordRow.workspace_id == self._workspace_id
                )
            )
            connector_health = list(session.scalars(select(ConnectorHealthRow)))

        state_counts = Counter(item.current_state for item in applications)
        return {
            "today_discovered": sum(
                1 for job in jobs if job.discovered_at.astimezone(UTC).date() == today
            ),
            "pending_reviews": int(pending_reviews or 0),
            "pending_packages": int(pending_packages or 0),
            "submitted": sum(
                1 for application in applications if application.submitted_at is not None
            ),
            "interviews": state_counts["interview"] + state_counts["offer"],
            "offers": state_counts["offer"],
            "regional_distribution": dict(Counter(job.country for job in jobs)),
            "track_distribution": dict(Counter(job.role_track for job in jobs)),
            "connector_health": [
                {
                    "platform": row.platform,
                    "board_token": row.board_token,
                    "status": row.status,
                    "last_error": row.last_error_detail,
                    "checked_at": row.checked_at.isoformat(),
                }
                for row in connector_health
            ],
            "estimated_cost": float(estimated_cost or 0.0),
            **OperationsService(
                self._session_factory,
                workspace_id=self._workspace_id,
                candidate_id=self._candidate_id,
            ).snapshot().model_dump(mode="json"),
        }

    def list_job_reviews(self) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            rows = session.execute(
                select(
                    ReviewQueueRow,
                    JobRow,
                    CompanyRow,
                    WorkAuthorizationAssessmentRow,
                    MatchAssessmentRow,
                )
                .join(JobRow, JobRow.job_id == ReviewQueueRow.job_id)
                .join(CompanyRow, CompanyRow.company_id == JobRow.company_id)
                .join(
                    WorkAuthorizationAssessmentRow,
                    WorkAuthorizationAssessmentRow.assessment_id
                    == ReviewQueueRow.work_authorization_assessment_id,
                )
                .join(
                    MatchAssessmentRow,
                    MatchAssessmentRow.assessment_id == ReviewQueueRow.match_assessment_id,
                )
                .where(
                    ReviewQueueRow.workspace_id == self._workspace_id,
                    ReviewQueueRow.candidate_id == self._candidate_id,
                    ReviewQueueRow.status.in_(["pending", "needs_verification", "saved"]),
                )
                .order_by(MatchAssessmentRow.total_score.desc())
            ).all()

        return [
            {
                "review_id": review.review_id,
                "job_id": job.job_id,
                "company": company.canonical_name,
                "title": job.title,
                "country": job.country,
                "city": job.city,
                "role_track": job.role_track,
                "total_score": match.total_score,
                "work_authorization_status": work_auth.status,
                "work_authorization_fit": work_auth.work_authorization_fit,
                "route_type": work_auth.route_type,
                "evidence": work_auth.evidence,
                "unresolved_items": work_auth.unresolved_items,
                "matching_evidence": match.matching_evidence,
                "missing_requirements": match.missing_requirements,
                "selected_resume_track": match.selected_resume_track,
                "materials_generated": review.materials_generated,
            }
            for review, job, company, work_auth, match in rows
        ]

    def set_job_review_status(self, review_id: str, status: str) -> None:
        allowed = {"saved", "rejected", "needs_verification", "pending"}
        if status not in allowed:
            raise ValueError(f"unsupported review status: {status}")
        with self._session_factory.begin() as session:
            row = session.get(ReviewQueueRow, review_id)
            if row is None:
                raise KeyError(review_id)
            row.status = status

    def generate_package(
        self,
        job_id: str,
        *,
        cover_letter: bool = False,
        force: bool = False,
    ) -> str:
        repositories = SqlAlchemyApplicationRepositories(self._session_factory)
        try:
            package = PackageService(
                repositories,
                load_fixed_answer_resolver(
                    self._settings.config_dir / "screening_answers.yaml"
                ),
            ).generate(
                job_id,
                self._candidate_id,
                cover_letter=cover_letter,
                force=force,
            )
        finally:
            repositories.close()
        return package.package_id

    def list_pending_package_ids(self) -> list[str]:
        with self._session_factory() as session:
            return list(
                session.scalars(
                    select(ApplicationPackageRow.package_id)
                    .where(
                        ApplicationPackageRow.workspace_id == self._workspace_id,
                        ApplicationPackageRow.candidate_id == self._candidate_id,
                        ApplicationPackageRow.review_status == "awaiting_review",
                    )
                    .order_by(ApplicationPackageRow.created_at.desc())
                )
            )

    def get_package_review_view(self, package_id: str) -> dict[str, Any]:
        with self._session_factory() as session:
            package = session.get(ApplicationPackageRow, package_id)
            if package is None:
                raise KeyError(package_id)
            job = session.get(JobRow, package.job_id)
            if job is None:
                raise KeyError(package.job_id)
            company = session.get(CompanyRow, job.company_id)
            claims = list(
                session.scalars(
                    select(GeneratedClaimRow)
                    .where(GeneratedClaimRow.package_id == package_id)
                    .order_by(GeneratedClaimRow.position)
                )
            )
            fact_ids = {
                fact_id for claim in claims for fact_id in claim.source_fact_ids
            }
            facts = {
                row.fact_id: row
                for row in session.scalars(
                    select(ResumeFactRow).where(ResumeFactRow.fact_id.in_(fact_ids))
                )
            }
            answers = list(
                session.scalars(
                    select(ScreeningAnswerRow)
                    .where(ScreeningAnswerRow.package_id == package_id)
                    .order_by(ScreeningAnswerRow.position)
                )
            )

        return {
            "package_id": package.package_id,
            "job_title": job.title,
            "company": company.canonical_name if company else "Unknown company",
            "base_resume_id": package.base_resume_id,
            "validation_status": package.validation_status,
            "review_status": package.review_status,
            "claims": [
                {
                    "claim_id": claim.claim_id,
                    "text": claim.text,
                    "source_fact_ids": claim.source_fact_ids,
                    "transformation_type": claim.transformation_type,
                    "validation_status": claim.validation_status,
                    "reviewer_approved": claim.reviewer_approved,
                    "original_sources": [
                        facts[fact_id].raw_fact
                        for fact_id in claim.source_fact_ids
                        if fact_id in facts
                    ],
                }
                for claim in claims
            ],
            "screening_answers": [
                {
                    "question": answer.displayed_question,
                    "answer": answer.answer_text,
                    "source_type": answer.source_type,
                    "requires_review": answer.requires_review,
                    "risk_level": answer.risk_level,
                }
                for answer in answers
            ],
            "cover_letter_text": package.cover_letter_text,
        }

    def approve_package(self, package_id: str) -> None:
        artifact_dir = self._render_package_artifacts(package_id)
        repositories = SqlAlchemyApplicationRepositories(self._session_factory)
        try:
            PackageService(repositories).approve(package_id)
        except Exception:
            rmtree(artifact_dir, ignore_errors=True)
            raise
        finally:
            repositories.close()

    def _render_package_artifacts(self, package_id: str) -> Path:
        with self._session_factory() as session:
            package = session.get(ApplicationPackageRow, package_id)
            if package is None:
                raise KeyError(package_id)
            claims = list(
                session.scalars(
                    select(GeneratedClaimRow)
                    .where(GeneratedClaimRow.package_id == package_id)
                    .order_by(GeneratedClaimRow.position)
                )
            )
            facts = list(
                session.scalars(
                    select(ResumeFactRow).where(
                        ResumeFactRow.fact_id.in_(package.fact_references)
                    )
                )
            )
        profile_path = self._settings.config_dir / "profile.yaml"
        profile = {}
        if profile_path.exists():
            profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
        full_name = profile.get("full_name")
        if not isinstance(full_name, str) or not full_name.strip():
            raise ValueError("profile.yaml must define full_name before package approval")
        name = full_name.strip()
        verified_claims = [claim for claim in claims if claim.validation_status == "verified"]
        report = ValidationReport(
            claim_results=[
                ClaimValidation(text=claim.text, status="verified", reasons=[])
                for claim in verified_claims
            ],
            export_allowed=bool(verified_claims),
        )
        artifact_dir = self._settings.artifact_dir / "applications" / package_id
        ResumeRenderer(
            Path(__file__).resolve().parents[1] / "materials" / "templates"
        ).render_pdf(
            {
                "name": name,
                "contact": [
                    str(profile[field]).strip()
                    for field in (
                        "email",
                        "phone",
                        "location",
                        "linkedin_url",
                        "github_url",
                    )
                    if isinstance(profile.get(field), str)
                    and str(profile[field]).strip()
                ],
                "summary": [verified_claims[0].text] if verified_claims else [],
                "skills": list(
                    dict.fromkeys(
                        skill for fact in facts for skill in fact.skills
                    )
                ),
                "sections": [
                    {
                        "heading": "Verified Experience",
                        "bullets": [claim.text for claim in verified_claims[1:]],
                    }
                ],
            },
            report,
            artifact_dir / "resume.pdf",
        )
        if package.cover_letter_text:
            render_cover_letter_pdf(
                package.cover_letter_text,
                artifact_dir / "cover_letter.pdf",
            )
        return artifact_dir

    def reject_package(self, package_id: str) -> None:
        repositories = SqlAlchemyApplicationRepositories(self._session_factory)
        try:
            PackageService(repositories).reject(package_id)
        finally:
            repositories.close()

    def list_applications(self) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            rows = session.execute(
                select(ApplicationRow, JobRow, CompanyRow)
                .join(JobRow, JobRow.job_id == ApplicationRow.job_id)
                .join(CompanyRow, CompanyRow.company_id == JobRow.company_id)
                .where(
                    ApplicationRow.workspace_id == self._workspace_id,
                    ApplicationRow.candidate_id == self._candidate_id,
                )
                .order_by(ApplicationRow.created_at.desc())
            ).all()
        return [
            {
                "application_id": application.application_id,
                "package_id": application.package_id,
                "job_id": job.job_id,
                "job_title": job.title,
                "company": company.canonical_name,
                "country": job.country,
                "current_state": application.current_state,
                "autofill_status": application.autofill_status,
                "submitted_at": (
                    application.submitted_at.isoformat()
                    if application.submitted_at
                    else None
                ),
                "outcome": application.outcome,
            }
            for application, job, company in rows
        ]

    def allowed_transitions(self, current_state: str) -> list[str]:
        return list(allowed_transitions(current_state))

    def transition_application(
        self,
        application_id: str,
        new_state: str,
        payload: dict[str, Any] | None = None,
    ) -> str:
        repositories = SqlAlchemyApplicationRepositories(self._session_factory)
        try:
            event = ApplicationTracker(repositories).transition(
                application_id,
                new_state,
                payload,
            )
        finally:
            repositories.close()
        return event.event_id

    def settings_summary(self) -> dict[str, Any]:
        database_label = (
            self._settings.database_url
            if self._settings.database_url.startswith("sqlite:///")
            else "configured (credentials hidden)"
        )
        return {
            "environment": self._settings.env,
            "database": database_label,
            "config_dir": str(self._settings.config_dir),
            "artifact_dir": str(self._settings.artifact_dir),
            "browser_profile_dir": str(self._settings.browser_profile_dir),
            "workspace_id": self._workspace_id,
            "candidate_id": self._candidate_id,
        }
