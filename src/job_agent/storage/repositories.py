from sqlalchemy.orm import Session

from job_agent.domain.enums import JobStatus, Region, RoleTrack
from job_agent.domain.models import Company, Job, RunRecord
from job_agent.storage.orm import CompanyRow, JobRow, RunRecordRow


class CompanyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, company_id: str) -> Company | None:
        row = self._session.get(CompanyRow, company_id)
        if row is None:
            return None
        return Company(
            company_id=row.company_id,
            workspace_id=row.workspace_id,
            canonical_name=row.canonical_name,
            aliases=row.aliases,
            domain=row.domain,
        )

    def upsert(self, company: Company) -> None:
        row = self._session.get(CompanyRow, company.company_id)
        if row is None:
            self._session.add(
                CompanyRow(
                    company_id=company.company_id,
                    workspace_id=company.workspace_id,
                    canonical_name=company.canonical_name,
                    aliases=company.aliases,
                    domain=company.domain,
                )
            )
            return
        row.canonical_name = company.canonical_name
        row.aliases = company.aliases
        row.domain = company.domain


class JobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, job: Job) -> None:
        self._session.add(
            JobRow(
                job_id=job.job_id,
                workspace_id=job.workspace_id,
                external_job_id=job.external_job_id,
                source_platform=job.source_platform,
                source_url=str(job.source_url),
                company_id=job.company_id,
                title=job.title,
                normalized_title=job.normalized_title,
                country=job.country.value,
                city=job.city,
                role_track=job.role_track.value,
                description_raw=job.description_raw,
                description_normalized=job.description_normalized,
                published_at=job.published_at,
                discovered_at=job.discovered_at,
                status=job.status.value,
            )
        )

    def get(self, job_id: str) -> Job | None:
        row = self._session.get(JobRow, job_id)
        if row is None:
            return None
        return Job(
            job_id=row.job_id,
            workspace_id=row.workspace_id,
            external_job_id=row.external_job_id,
            source_platform=row.source_platform,
            source_url=row.source_url,
            company_id=row.company_id,
            title=row.title,
            normalized_title=row.normalized_title,
            country=Region(row.country),
            city=row.city,
            role_track=RoleTrack(row.role_track),
            description_raw=row.description_raw,
            description_normalized=row.description_normalized,
            published_at=row.published_at,
            discovered_at=row.discovered_at,
            status=JobStatus(row.status),
        )


class RunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: RunRecord) -> None:
        self.save(record)

    def save(self, record: RunRecord) -> None:
        row = self._session.get(RunRecordRow, record.run_id)
        payload = {
            "workspace_id": record.workspace_id,
            "run_type": record.run_type,
            "started_at": record.started_at,
            "completed_at": record.completed_at,
            "processed_count": record.processed_count,
            "success_count": record.success_count,
            "skipped_count": record.skipped_count,
            "duplicate_count": record.duplicate_count,
            "hard_failed_count": record.hard_failed_count,
            "failed_count": record.failed_count,
            "token_usage": record.token_usage,
            "estimated_cost": record.estimated_cost,
            "error_summary": record.error_summary,
        }
        if row is None:
            self._session.add(RunRecordRow(run_id=record.run_id, **payload))
            return
        for field_name, value in payload.items():
            setattr(row, field_name, value)

    def get(self, run_id: str) -> RunRecord | None:
        row = self._session.get(RunRecordRow, run_id)
        if row is None:
            return None
        return RunRecord(
            run_id=row.run_id,
            workspace_id=row.workspace_id,
            run_type=row.run_type,
            started_at=row.started_at,
            completed_at=row.completed_at,
            processed_count=row.processed_count,
            success_count=row.success_count,
            skipped_count=row.skipped_count,
            duplicate_count=row.duplicate_count,
            hard_failed_count=row.hard_failed_count,
            failed_count=row.failed_count,
            token_usage=row.token_usage,
            estimated_cost=row.estimated_cost,
            error_summary=row.error_summary,
        )
