from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from job_agent.autofill.adapters.ashby import AshbyFormAdapter
from job_agent.autofill.adapters.base import FormAdapter
from job_agent.autofill.adapters.greenhouse import GreenhouseFormAdapter
from job_agent.autofill.adapters.lever import LeverFormAdapter
from job_agent.autofill.adapters.smartrecruiters import SmartRecruitersFormAdapter
from job_agent.autofill.field_mapping import FieldMapper
from job_agent.autofill.service import AutofillService
from job_agent.settings import Settings
from job_agent.storage.application_orm import ApplicationRow
from job_agent.storage.autofill_orm import AutofillSessionRow
from job_agent.storage.autofill_repositories import SqlAlchemyAutofillRepositories
from job_agent.storage.orm import CompanyRow, JobRow


def default_adapters() -> dict[str, FormAdapter]:
    return {
        "greenhouse": GreenhouseFormAdapter(),
        "lever": LeverFormAdapter(),
        "ashby": AshbyFormAdapter(),
        "smartrecruiters": SmartRecruitersFormAdapter(),
    }


class AutofillWorkspaceService:
    """Read models and explicit user actions for the autofill review queue."""

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

    def list_queue(self) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            rows = session.execute(
                select(ApplicationRow, JobRow, CompanyRow)
                .join(JobRow, JobRow.job_id == ApplicationRow.job_id)
                .join(CompanyRow, CompanyRow.company_id == JobRow.company_id)
                .where(
                    ApplicationRow.workspace_id == self._workspace_id,
                    ApplicationRow.candidate_id == self._candidate_id,
                    ApplicationRow.current_state.in_(
                        ["approved", "autofill_started", "ready_to_submit"]
                    ),
                )
                .order_by(ApplicationRow.created_at.desc())
            ).all()
            session_rows = list(
                session.scalars(
                    select(AutofillSessionRow).where(
                        AutofillSessionRow.workspace_id == self._workspace_id,
                        AutofillSessionRow.candidate_id == self._candidate_id,
                    )
                )
            )
        active_by_application = {
            row.application_id: row
            for row in session_rows
            if row.active_key is not None
        }
        return [
            {
                "application_id": application.application_id,
                "job_title": job.title,
                "company": company.canonical_name,
                "country": job.country,
                "ats_platform": job.source_platform,
                "application_url": application.application_url,
                "current_state": application.current_state,
                "autofill_status": application.autofill_status,
                "session_id": (
                    active_by_application[application.application_id].session_id
                    if application.application_id in active_by_application
                    else None
                ),
            }
            for application, job, company in rows
        ]

    def get_session_view(self, session_id: str) -> dict[str, Any]:
        repositories = SqlAlchemyAutofillRepositories(
            self._session_factory,
            artifact_dir=self._settings.artifact_dir,
        )
        try:
            session = repositories.get_session(session_id)
        finally:
            repositories.close()
        if session is None:
            raise KeyError(session_id)
        return {
            "session_id": session.session_id,
            "application_id": session.application_id,
            "state": session.state,
            "ats_platform": session.ats_platform,
            "application_url": str(session.application_url),
            "mappings": [mapping.model_dump(mode="json") for mapping in session.field_mappings],
            "stop_reasons": [reason.model_dump(mode="json") for reason in session.stop_reasons],
            "manual_submission_confirmed_at": (
                session.manual_submission_confirmed_at.isoformat()
                if session.manual_submission_confirmed_at
                else None
            ),
        }

    def launch_browser(self, application_id: str) -> int:
        env = os.environ.copy()
        source_root = str(Path(__file__).resolve().parents[2])
        current_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{source_root}{os.pathsep}{current_pythonpath}"
            if current_pythonpath
            else source_root
        )
        command = [
            sys.executable,
            "-m",
            "job_agent.cli",
            "autofill",
            "--application-id",
            application_id,
            "--keep-open",
        ]
        executable = os.environ.get("JOB_AGENT_BROWSER_EXECUTABLE")
        if executable:
            command.extend(["--browser-executable", executable])
        process = subprocess.Popen(  # noqa: S603 - fixed local command, no shell
            command,
            cwd=Path.cwd(),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return process.pid

    def confirm_ready(self, session_id: str, *, confirmation: bool) -> dict[str, Any]:
        repositories = SqlAlchemyAutofillRepositories(
            self._session_factory,
            artifact_dir=self._settings.artifact_dir,
        )
        try:
            updated = AutofillService(
                repositories,
                default_adapters(),
                FieldMapper(),
            ).confirm_ready(session_id, confirmation=confirmation)
        finally:
            repositories.close()
        return updated.model_dump(mode="json")

    def mark_submitted_manually(
        self,
        session_id: str,
        *,
        confirmation: bool,
    ) -> dict[str, Any]:
        repositories = SqlAlchemyAutofillRepositories(
            self._session_factory,
            artifact_dir=self._settings.artifact_dir,
        )
        try:
            updated = AutofillService(
                repositories,
                default_adapters(),
                FieldMapper(),
            ).mark_submitted_manually(session_id, confirmation=confirmation)
        finally:
            repositories.close()
        return updated.model_dump(mode="json")
