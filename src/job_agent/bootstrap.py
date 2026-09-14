from dataclasses import dataclass

from job_agent.application.review_workspace import ReviewWorkspaceService
from job_agent.autofill.workspace import AutofillWorkspaceService
from job_agent.observability.service import OperationsService
from job_agent.resume_ingestion.extraction import HeuristicResumeExtractor
from job_agent.resume_ingestion.service import ResumeImportService
from job_agent.settings import Settings
from job_agent.storage.database import build_engine, build_session_factory
from job_agent.storage.resume_repositories import SqlAlchemyResumeRepositories


@dataclass(frozen=True)
class ServiceFactory:
    settings: Settings

    def review_workspace_service(self) -> ReviewWorkspaceService:
        engine = build_engine(self.settings.database_url)
        return ReviewWorkspaceService(
            build_session_factory(engine),
            settings=self.settings,
        )

    def autofill_workspace_service(self) -> AutofillWorkspaceService:
        engine = build_engine(self.settings.database_url)
        return AutofillWorkspaceService(
            build_session_factory(engine),
            settings=self.settings,
        )

    def operations_service(self) -> OperationsService:
        engine = build_engine(self.settings.database_url)
        return OperationsService(build_session_factory(engine))

    def resume_import_service(self) -> ResumeImportService:
        engine = build_engine(self.settings.database_url)
        repositories = SqlAlchemyResumeRepositories(build_session_factory(engine))
        return ResumeImportService(
            repositories=repositories,
            extractor=HeuristicResumeExtractor(),
            source_root=self.settings.artifact_dir / "resume_sources",
        )


def build_service_factory() -> ServiceFactory:
    settings = Settings.from_env()
    settings.ensure_directories()
    return ServiceFactory(settings=settings)
