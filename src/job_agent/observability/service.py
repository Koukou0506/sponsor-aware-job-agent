from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from job_agent.observability.models import ConnectorHealthMetric, OperationsSnapshot
from job_agent.storage.application_orm import ApplicationPackageRow
from job_agent.storage.autofill_orm import AutofillSessionRow
from job_agent.storage.orm import (
    ConnectorHealthRow,
    RunRecordRow,
    WorkAuthorizationAssessmentRow,
)


def calculate_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 2)


class OperationsService:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        workspace_id: str = "default",
        candidate_id: str = "default",
    ) -> None:
        self._session_factory = session_factory
        self._workspace_id = workspace_id
        self._candidate_id = candidate_id

    def snapshot(self) -> OperationsSnapshot:
        with self._session_factory() as session:
            runs = list(
                session.scalars(
                    select(RunRecordRow).where(
                        RunRecordRow.workspace_id == self._workspace_id
                    )
                )
            )
            work_auth = list(
                session.scalars(
                    select(WorkAuthorizationAssessmentRow).where(
                        WorkAuthorizationAssessmentRow.workspace_id == self._workspace_id,
                        WorkAuthorizationAssessmentRow.candidate_id == self._candidate_id,
                    )
                )
            )
            packages = list(
                session.scalars(
                    select(ApplicationPackageRow).where(
                        ApplicationPackageRow.workspace_id == self._workspace_id,
                        ApplicationPackageRow.candidate_id == self._candidate_id,
                    )
                )
            )
            autofill_sessions = list(
                session.scalars(
                    select(AutofillSessionRow).where(
                        AutofillSessionRow.workspace_id == self._workspace_id,
                        AutofillSessionRow.candidate_id == self._candidate_id,
                    )
                )
            )
            connector_rows = list(session.scalars(select(ConnectorHealthRow)))

        processed = sum(row.processed_count for row in runs)
        succeeded = sum(row.success_count for row in runs)
        skipped = sum(row.skipped_count for row in runs)
        duplicates = sum(row.duplicate_count for row in runs)
        failed = sum(row.failed_count for row in runs)
        low_confidence = sum(row.confidence < 0.7 for row in work_auth)
        hard_fails = [row for row in work_auth if row.hard_fail]
        hard_fail_distribution: Counter[str] = Counter()
        for row in hard_fails:
            hard_fail_distribution.update(row.hard_fail_reasons)
        invalid_packages = sum(
            row.validation_status not in {"verified", "valid"} for row in packages
        )
        completed_autofill = sum(
            row.state in {"ready_to_submit", "submitted_manually"}
            for row in autofill_sessions
        )
        manual_submissions = sum(
            row.state == "submitted_manually" for row in autofill_sessions
        )
        return OperationsSnapshot(
            total_runs=len(runs),
            processed_jobs=processed,
            successful_jobs=succeeded,
            skipped_jobs=skipped,
            failed_jobs=failed,
            run_success_rate=calculate_rate(succeeded, processed),
            low_confidence_work_authorization_rate=calculate_rate(
                low_confidence,
                len(work_auth),
            ),
            hard_fail_rate=calculate_rate(len(hard_fails), len(work_auth)),
            duplicate_suppression_rate=calculate_rate(duplicates, processed),
            validation_failure_rate=calculate_rate(invalid_packages, len(packages)),
            autofill_completion_rate=calculate_rate(
                completed_autofill,
                len(autofill_sessions),
            ),
            manual_submission_count=manual_submissions,
            token_usage=sum(row.token_usage for row in runs),
            estimated_cost=round(sum(row.estimated_cost for row in runs), 4),
            hard_fail_distribution=dict(hard_fail_distribution),
            connector_health=[
                ConnectorHealthMetric(
                    platform=row.platform,
                    board_token=row.board_token,
                    status=row.status,
                    checked_at=row.checked_at,
                    last_error=row.last_error_detail,
                )
                for row in connector_rows
            ],
        )

    def settings_summary(self) -> dict[str, object]:
        return self.snapshot().model_dump(mode="json")
