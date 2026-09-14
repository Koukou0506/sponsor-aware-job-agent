from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from job_agent.application.daily_pipeline import ReviewItem
from job_agent.connectors.base import BoardRef
from job_agent.domain.enums import JobStatus, Region, RoleTrack
from job_agent.domain.ids import new_id
from job_agent.domain.models import Company, Job, MatchAssessment, WorkAuthorizationAssessment
from job_agent.jobs.deduplication import JobChange, content_hash
from job_agent.storage.orm import CompanyRow, ConnectorHealthRow, JobRow, JobVersionRow, MatchAssessmentRow, ReviewQueueRow, RunRecordRow, WorkAuthorizationAssessmentRow


class SqlAlchemyJobIntelligenceStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session = session_factory()
        self._current_run: RunRecordRow | None = None

    def close(self) -> None:
        self._session.close()

    def start_run(self, workspace_id: str, run_type: str = "run_daily") -> str:
        run_id = new_id("run")
        row = RunRecordRow(run_id=run_id, workspace_id=workspace_id, run_type=run_type, started_at=datetime.now(UTC), completed_at=None, processed_count=0, success_count=0, skipped_count=0, duplicate_count=0, hard_failed_count=0, failed_count=0, token_usage=0, estimated_cost=0.0, error_summary={})
        self._session.add(row)
        self._session.commit()
        self._current_run = row
        return run_id

    def finish_run(
        self,
        *,
        processed: int,
        succeeded: int,
        skipped: int,
        failed: int,
        duplicates: int = 0,
        hard_failed: int = 0,
    ) -> None:
        if self._current_run is None:
            return
        self._current_run.completed_at = datetime.now(UTC)
        self._current_run.processed_count = processed
        self._current_run.success_count = succeeded
        self._current_run.skipped_count = skipped
        self._current_run.duplicate_count = duplicates
        self._current_run.hard_failed_count = hard_failed
        self._current_run.failed_count = failed
        self._session.commit()

    def existing_job(self, platform: str, company_id: str, external_job_id: str) -> Job | None:
        row = self._session.scalar(select(JobRow).where(JobRow.source_platform == platform, JobRow.company_id == company_id, JobRow.external_job_id == external_job_id))
        return _job_from_row(row) if row else None

    def save_company(self, company: Company) -> None:
        row = self._session.get(CompanyRow, company.company_id)
        if row is None:
            self._session.add(CompanyRow(company_id=company.company_id, workspace_id=company.workspace_id, canonical_name=company.canonical_name, aliases=company.aliases, domain=company.domain))
        else:
            row.canonical_name = company.canonical_name
            row.aliases = company.aliases
            row.domain = company.domain

    def save_job(self, job: Job, raw_payload_hash: str, change: JobChange) -> None:
        row = self._session.get(JobRow, job.job_id)
        if row is None:
            row = JobRow(job_id=job.job_id, workspace_id=job.workspace_id, external_job_id=job.external_job_id, source_platform=job.source_platform, source_url=str(job.source_url), company_id=job.company_id, title=job.title, normalized_title=job.normalized_title, country=job.country.value, city=job.city, role_track=job.role_track.value, description_raw=job.description_raw, description_normalized=job.description_normalized, published_at=job.published_at, discovered_at=job.discovered_at, status=job.status.value)
            self._session.add(row)
        else:
            row.source_url = str(job.source_url)
            row.title = job.title
            row.normalized_title = job.normalized_title
            row.city = job.city
            row.description_raw = job.description_raw
            row.description_normalized = job.description_normalized
            row.published_at = job.published_at
        self._session.add(JobVersionRow(job_version_id=new_id("jobver"), job_id=job.job_id, content_hash=content_hash(job), source_payload_hash=raw_payload_hash, description_snapshot=job.description_normalized, changed_fields=["all"] if change == "new" else ["description"], captured_at=datetime.now(UTC)))

    def save_work_authorization(self, assessment: WorkAuthorizationAssessment) -> None:
        self._session.add(WorkAuthorizationAssessmentRow(assessment_id=assessment.assessment_id, workspace_id=assessment.workspace_id, candidate_id=assessment.candidate_id, job_id=assessment.job_id, country=assessment.country.value, route_type=assessment.route_type, route_ownership=assessment.route_ownership.value, status=assessment.status.value, work_authorization_fit=assessment.work_authorization_fit, hard_fail=assessment.hard_fail, hard_fail_reasons=assessment.hard_fail_reasons, unresolved_items=assessment.unresolved_items, evidence=[item.model_dump(mode="json") for item in assessment.evidence], confidence=assessment.confidence, ruleset_version=assessment.ruleset_version, assessed_at=assessment.assessed_at))
        if assessment.hard_fail:
            row = self._session.get(JobRow, assessment.job_id)
            if row:
                row.status = JobStatus.FILTERED_OUT.value

    def save_match(self, assessment: MatchAssessment) -> None:
        self._session.add(MatchAssessmentRow(assessment_id=assessment.assessment_id, workspace_id=assessment.workspace_id, candidate_id=assessment.candidate_id, job_id=assessment.job_id, selected_resume_track=assessment.selected_resume_track.value, component_scores={"visa_fit": assessment.visa_fit, "skill_fit": assessment.skill_fit, "experience_fit": assessment.experience_fit, "language_fit": assessment.language_fit, "role_transition_fit": assessment.role_transition_fit, "company_signal": assessment.company_signal, "recency_score": assessment.recency_score}, total_score=assessment.total_score, matching_evidence=assessment.matching_evidence, missing_requirements=assessment.missing_requirements, disqualifiers=assessment.disqualifiers, model_version=assessment.model_version, assessed_at=assessment.assessed_at))

    def add_review_item(self, item: ReviewItem) -> ReviewItem:
        row = self._session.get(JobRow, item.job.job_id)
        if row:
            row.status = JobStatus.SHORTLISTED.value
            row.role_track = item.job.role_track.value
        self._session.add(ReviewQueueRow(review_id=item.review_id, workspace_id=item.job.workspace_id, candidate_id=item.match.candidate_id, job_id=item.job.job_id, work_authorization_assessment_id=item.work_authorization.assessment_id, match_assessment_id=item.match.assessment_id, status="pending", materials_generated=False, created_at=datetime.now(UTC)))
        return item

    def record_connector_error(self, board: BoardRef, error_type: str, detail: str) -> None:
        key = f"{board.platform}:{board.board_token}"
        row = self._session.get(ConnectorHealthRow, key)
        if row is None:
            row = ConnectorHealthRow(connector_key=key, platform=board.platform, board_token=board.board_token, status="suspended" if error_type == "rate_limited" else "failed", checked_at=datetime.now(UTC))
            self._session.add(row)
        row.status = "suspended" if error_type == "rate_limited" else "failed"
        row.last_error_type = error_type
        row.last_error_detail = detail
        row.checked_at = datetime.now(UTC)
        if self._current_run is not None:
            errors = dict(self._current_run.error_summary)
            errors[key] = {"type": error_type, "detail": detail}
            self._current_run.error_summary = errors


    def record_connector_success(self, board: BoardRef) -> None:
        key = f"{board.platform}:{board.board_token}"
        row = self._session.get(ConnectorHealthRow, key)
        if row is None:
            row = ConnectorHealthRow(
                connector_key=key,
                platform=board.platform,
                board_token=board.board_token,
                status="healthy",
                checked_at=datetime.now(UTC),
            )
            self._session.add(row)
        row.status = "healthy"
        row.last_error_type = None
        row.last_error_detail = None
        row.checked_at = datetime.now(UTC)

    def checkpoint(self) -> None:
        self._session.commit()


def _job_from_row(row: JobRow) -> Job:
    return Job(job_id=row.job_id, workspace_id=row.workspace_id, external_job_id=row.external_job_id, source_platform=row.source_platform, source_url=row.source_url, company_id=row.company_id, title=row.title, normalized_title=row.normalized_title, country=Region(row.country), city=row.city, role_track=RoleTrack(row.role_track), description_raw=row.description_raw, description_normalized=row.description_normalized, published_at=row.published_at, discovered_at=row.discovered_at, status=JobStatus(row.status))
