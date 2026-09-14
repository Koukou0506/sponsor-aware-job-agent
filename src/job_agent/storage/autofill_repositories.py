from pathlib import Path
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from job_agent.application.tracker import can_transition
from job_agent.autofill.models import (
    AutofillApplicationContext,
    AutofillSession,
    FieldMapping,
    StopReason,
)
from job_agent.domain.ids import new_id
from job_agent.storage.application_orm import (
    ApplicationEventRow,
    ApplicationPackageRow,
    ApplicationRow,
    ScreeningAnswerRow,
)
from job_agent.storage.autofill_orm import AutofillFieldMappingRow, AutofillSessionRow
from job_agent.storage.orm import JobRow

_TERMINAL_STATES = {"submitted_manually", "failed"}


class AutofillSessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, autofill_session: AutofillSession) -> None:
        if (
            autofill_session.state not in _TERMINAL_STATES
            and self.get_active_for_application(autofill_session.application_id)
            is not None
        ):
            raise ValueError(
                f"active autofill session already exists for application: "
                f"{autofill_session.application_id}"
            )
        active_key = (
            None if autofill_session.state in _TERMINAL_STATES else autofill_session.application_id
        )
        self._session.add(
            AutofillSessionRow(
                session_id=autofill_session.session_id,
                workspace_id=autofill_session.workspace_id,
                candidate_id=autofill_session.candidate_id,
                application_id=autofill_session.application_id,
                active_key=active_key,
                ats_platform=autofill_session.ats_platform,
                application_url=str(autofill_session.application_url),
                state=autofill_session.state,
                stop_reasons=[
                    reason.model_dump(mode="json")
                    for reason in autofill_session.stop_reasons
                ],
                manual_submission_confirmed_at=(
                    autofill_session.manual_submission_confirmed_at
                ),
                created_at=autofill_session.created_at,
                updated_at=autofill_session.updated_at,
            )
        )
        self._session.flush()
        for position, mapping in enumerate(autofill_session.field_mappings):
            self._session.add(
                AutofillFieldMappingRow(
                    mapping_id=mapping.mapping_id,
                    session_id=autofill_session.session_id,
                    position=position,
                    canonical_field=mapping.canonical_field,
                    page_label=mapping.page_label,
                    selector=mapping.selector,
                    value=mapping.value,
                    source=mapping.source,
                    confidence=mapping.confidence,
                    requires_review=mapping.requires_review,
                    risk_level=mapping.risk_level,
                )
            )

    def get(self, session_id: str) -> AutofillSession | None:
        row = self._session.get(AutofillSessionRow, session_id)
        if row is None:
            return None
        mappings = list(
            self._session.scalars(
                select(AutofillFieldMappingRow)
                .where(AutofillFieldMappingRow.session_id == session_id)
                .order_by(AutofillFieldMappingRow.position)
            )
        )
        return AutofillSession(
            session_id=row.session_id,
            workspace_id=row.workspace_id,
            candidate_id=row.candidate_id,
            application_id=row.application_id,
            ats_platform=row.ats_platform,
            application_url=row.application_url,
            state=row.state,
            field_mappings=[
                FieldMapping(
                    mapping_id=mapping.mapping_id,
                    canonical_field=mapping.canonical_field,
                    page_label=mapping.page_label,
                    selector=mapping.selector,
                    value=mapping.value,
                    source=mapping.source,
                    confidence=mapping.confidence,
                    requires_review=mapping.requires_review,
                    risk_level=mapping.risk_level,
                )
                for mapping in mappings
            ],
            stop_reasons=row.stop_reasons,
            manual_submission_confirmed_at=row.manual_submission_confirmed_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def get_active_for_application(self, application_id: str) -> AutofillSession | None:
        row = self._session.scalar(
            select(AutofillSessionRow).where(
                AutofillSessionRow.active_key == application_id
            )
        )
        return self.get(row.session_id) if row else None

    def update_state(
        self,
        session_id: str,
        state: str,
        *,
        stop_reasons: list[StopReason] | None = None,
        manual_submission_confirmed_at: datetime | None = None,
    ) -> AutofillSession:
        row = self._session.get(AutofillSessionRow, session_id)
        if row is None:
            raise KeyError(session_id)
        row.state = state
        row.active_key = None if state in _TERMINAL_STATES else row.application_id
        row.updated_at = datetime.now(UTC)
        if stop_reasons is not None:
            row.stop_reasons = [
                reason.model_dump(mode="json") for reason in stop_reasons
            ]
        row.manual_submission_confirmed_at = manual_submission_confirmed_at
        self._session.flush()
        loaded = self.get(session_id)
        if loaded is None:
            raise KeyError(session_id)
        return loaded


class SqlAlchemyAutofillRepositories:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        artifact_dir: Path | None = None,
    ) -> None:
        self._session = session_factory()
        self._artifact_dir = artifact_dir
        self.sessions = AutofillSessionRepository(self._session)

    def get_application_context(
        self,
        application_id: str,
    ) -> AutofillApplicationContext | None:
        application = self._session.get(ApplicationRow, application_id)
        if application is None:
            return None
        package = self._session.get(ApplicationPackageRow, application.package_id)
        job = self._session.get(JobRow, application.job_id)
        if package is None or job is None:
            return None
        answers = list(
            self._session.scalars(
                select(ScreeningAnswerRow)
                .where(ScreeningAnswerRow.package_id == package.package_id)
                .order_by(ScreeningAnswerRow.position)
            )
        )
        aliases = {
            "requires_employer_sponsorship": "sponsorship_required",
        }
        answer_catalog: dict[str, object] = {}
        requires_sponsorship = False
        for answer in answers:
            canonical = aliases.get(
                answer.canonical_question,
                answer.canonical_question,
            )
            answer_catalog[canonical] = {
                "value": answer.answer_text,
                "source": answer.source_type,
            }
            if canonical == "sponsorship_required":
                requires_sponsorship = answer.answer_text.strip().casefold().startswith(
                    "yes"
                )

        file_catalog: dict[str, str] = {}
        if self._artifact_dir is not None:
            package_dir = self._artifact_dir / "applications" / package.package_id
            for canonical, filename in (
                ("resume_upload", "resume.pdf"),
                ("cover_letter_upload", "cover_letter.pdf"),
            ):
                file_path = package_dir / filename
                if file_path.exists():
                    file_catalog[canonical] = str(file_path)
                    answer_catalog[canonical] = {
                        "value": str(file_path),
                        "source": "generated_material",
                    }

        return AutofillApplicationContext(
            application_id=application.application_id,
            workspace_id=application.workspace_id,
            candidate_id=application.candidate_id,
            package_id=application.package_id,
            current_state=application.current_state,
            ats_platform=job.source_platform,
            application_url=application.application_url,
            job_title=job.title,
            answer_catalog=answer_catalog,
            file_catalog=file_catalog,
            requires_sponsorship=requires_sponsorship,
        )

    def get_active_session(
        self,
        application_id: str,
    ) -> AutofillSession | None:
        return self.sessions.get_active_for_application(application_id)

    def get_session(self, session_id: str) -> AutofillSession | None:
        return self.sessions.get(session_id)

    def add_prepared_session(self, autofill_session: AutofillSession) -> None:
        application = self._session.get(
            ApplicationRow,
            autofill_session.application_id,
        )
        if application is None:
            raise KeyError(autofill_session.application_id)
        self.sessions.add(autofill_session)
        self._transition_application(
            application,
            "autofill_started",
            {"session_id": autofill_session.session_id},
        )
        application.autofill_status = autofill_session.state

    def update_session_state(
        self,
        session_id: str,
        state: str,
        *,
        stop_reasons: list[StopReason] | None = None,
    ) -> AutofillSession:
        autofill_session = self.sessions.update_state(
            session_id,
            state,
            stop_reasons=stop_reasons,
        )
        application = self._session.get(
            ApplicationRow,
            autofill_session.application_id,
        )
        if application is None:
            raise KeyError(autofill_session.application_id)
        application.autofill_status = state
        return autofill_session

    def confirm_ready(self, session_id: str) -> AutofillSession:
        autofill_session = self.sessions.update_state(session_id, "ready_to_submit")
        application = self._session.get(
            ApplicationRow,
            autofill_session.application_id,
        )
        if application is None:
            raise KeyError(autofill_session.application_id)
        self._transition_application(
            application,
            "ready_to_submit",
            {"session_id": session_id},
        )
        application.autofill_status = "ready_to_submit"
        return autofill_session

    def mark_submitted_manually(
        self,
        session_id: str,
        confirmed_at: datetime,
    ) -> AutofillSession:
        autofill_session = self.sessions.update_state(
            session_id,
            "submitted_manually",
            manual_submission_confirmed_at=confirmed_at,
        )
        application = self._session.get(
            ApplicationRow,
            autofill_session.application_id,
        )
        if application is None:
            raise KeyError(autofill_session.application_id)
        self._transition_application(
            application,
            "submitted",
            {
                "session_id": session_id,
                "submission_mode": "manual_browser_confirmation",
            },
            occurred_at=confirmed_at,
        )
        application.autofill_status = "submitted_manually"
        application.submitted_at = confirmed_at
        return autofill_session

    def _transition_application(
        self,
        application: ApplicationRow,
        target_state: str,
        payload: dict[str, object],
        *,
        occurred_at: datetime | None = None,
    ) -> None:
        if not can_transition(application.current_state, target_state):
            raise ValueError(
                f"cannot transition {application.current_state} to {target_state}"
            )
        now = occurred_at or datetime.now(UTC)
        self._session.add(
            ApplicationEventRow(
                event_id=new_id("event"),
                application_id=application.application_id,
                from_state=application.current_state,
                to_state=target_state,
                payload=payload,
                created_at=now,
            )
        )
        application.current_state = target_state

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def close(self) -> None:
        self._session.close()
