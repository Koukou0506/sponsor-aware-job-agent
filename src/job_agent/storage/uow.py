from types import TracebackType

from sqlalchemy.orm import Session, sessionmaker

from job_agent.storage.repositories import CompanyRepository, JobRepository, RunRepository


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None
        self.companies: CompanyRepository
        self.jobs: JobRepository
        self.runs: RunRepository

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self.companies = CompanyRepository(self.session)
        self.jobs = JobRepository(self.session)
        self.runs = RunRepository(self.session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc, traceback
        if exc_type is not None:
            self.rollback()
        assert self.session is not None
        self.session.close()
        self.session = None

    def commit(self) -> None:
        assert self.session is not None
        self.session.commit()

    def rollback(self) -> None:
        assert self.session is not None
        self.session.rollback()
