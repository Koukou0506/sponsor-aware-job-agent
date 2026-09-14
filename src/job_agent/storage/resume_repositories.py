from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from job_agent.resume_ingestion.models import ImportSession, ResumeFact, ResumeSource
from job_agent.storage.resume_orm import ResumeFactRow, ResumeImportSessionRow, ResumeSourceRow


class ResumeSourceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, source: ResumeSource) -> None:
        self._session.add(
            ResumeSourceRow(
                source_id=source.source_id,
                workspace_id=source.workspace_id,
                candidate_id=source.candidate_id,
                filename=source.filename,
                file_hash=source.file_hash,
                uploaded_at=source.uploaded_at,
                language=source.language,
                resume_track=source.resume_track,
                extraction_method=source.extraction_method,
                local_path=source.local_path,
                revoked_at=source.revoked_at,
            )
        )
        # SQLAlchemy has no ORM relationship between source and import rows, so
        # flush the parent explicitly before an import row references it.
        self._session.flush()

    def get(self, source_id: str) -> ResumeSource | None:
        row = self._session.get(ResumeSourceRow, source_id)
        return self._to_model(row) if row is not None else None

    def get_by_hash(
        self,
        file_hash: str,
        workspace_id: str = "default",
        candidate_id: str = "default",
    ) -> ResumeSource | None:
        row = self._session.scalar(
            select(ResumeSourceRow).where(
                ResumeSourceRow.workspace_id == workspace_id,
                ResumeSourceRow.candidate_id == candidate_id,
                ResumeSourceRow.file_hash == file_hash,
            )
        )
        return self._to_model(row) if row is not None else None

    def save(self, source: ResumeSource) -> None:
        row = self._session.get(ResumeSourceRow, source.source_id)
        if row is None:
            self.add(source)
            return
        for field in (
            "filename",
            "file_hash",
            "uploaded_at",
            "language",
            "resume_track",
            "extraction_method",
            "local_path",
            "revoked_at",
        ):
            setattr(row, field, getattr(source, field))

    @staticmethod
    def _to_model(row: ResumeSourceRow) -> ResumeSource:
        return ResumeSource(
            source_id=row.source_id,
            workspace_id=row.workspace_id,
            candidate_id=row.candidate_id,
            filename=row.filename,
            file_hash=row.file_hash,
            uploaded_at=row.uploaded_at,
            language=row.language,
            resume_track=row.resume_track,
            extraction_method=row.extraction_method,
            local_path=row.local_path,
            revoked_at=row.revoked_at,
        )


class ResumeFactRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, fact: ResumeFact) -> None:
        self._session.add(
            ResumeFactRow(
                fact_id=fact.fact_id,
                workspace_id=fact.workspace_id,
                candidate_id=fact.candidate_id,
                category=fact.category,
                organisation=fact.organisation,
                role_or_project=fact.role_or_project,
                start_date=fact.start_date,
                end_date=fact.end_date,
                raw_fact=fact.raw_fact,
                claim_status=fact.claim_status,
                metrics=fact.metrics,
                skills=fact.skills,
                allowed_claims=fact.allowed_claims,
                verification_status=fact.verification_status,
                provenance=[item.model_dump(mode="json") for item in fact.provenance],
            )
        )

    def get(self, fact_id: str) -> ResumeFact | None:
        row = self._session.get(ResumeFactRow, fact_id)
        return self._to_model(row) if row is not None else None

    def save(self, fact: ResumeFact) -> None:
        row = self._session.get(ResumeFactRow, fact.fact_id)
        if row is None:
            self.add(fact)
            return
        row.raw_fact = fact.raw_fact
        row.claim_status = fact.claim_status
        row.metrics = fact.metrics
        row.skills = fact.skills
        row.allowed_claims = fact.allowed_claims
        row.verification_status = fact.verification_status
        row.provenance = [item.model_dump(mode="json") for item in fact.provenance]

    def list_approved(self, candidate_id: str, workspace_id: str = "default") -> list[ResumeFact]:
        rows = self._session.scalars(
            select(ResumeFactRow).where(
                ResumeFactRow.workspace_id == workspace_id,
                ResumeFactRow.candidate_id == candidate_id,
                ResumeFactRow.verification_status == "approved",
            )
        ).all()
        return [self._to_model(row) for row in rows]

    def list_by_source(self, source_id: str) -> list[ResumeFact]:
        rows = self._session.scalars(select(ResumeFactRow)).all()
        return [
            self._to_model(row)
            for row in rows
            if any(item.get("source_id") == source_id for item in row.provenance)
        ]

    @staticmethod
    def _to_model(row: ResumeFactRow) -> ResumeFact:
        return ResumeFact(
            fact_id=row.fact_id,
            workspace_id=row.workspace_id,
            candidate_id=row.candidate_id,
            category=row.category,
            organisation=row.organisation,
            role_or_project=row.role_or_project,
            start_date=row.start_date,
            end_date=row.end_date,
            raw_fact=row.raw_fact,
            claim_status=row.claim_status,
            metrics=row.metrics,
            skills=row.skills,
            allowed_claims=row.allowed_claims,
            verification_status=row.verification_status,
            provenance=row.provenance,
        )


class ImportSessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, import_session: ImportSession) -> None:
        self._session.add(
            ResumeImportSessionRow(
                import_id=import_session.import_id,
                workspace_id=import_session.workspace_id,
                candidate_id=import_session.candidate_id,
                source_id=import_session.source_id,
                status=import_session.status,
                created_at=import_session.created_at,
                extracted_facts=[item.model_dump(mode="json") for item in import_session.extracted_facts],
            )
        )

    def get(self, import_id: str) -> ImportSession | None:
        row = self._session.get(ResumeImportSessionRow, import_id)
        if row is None:
            return None
        return ImportSession(
            import_id=row.import_id,
            workspace_id=row.workspace_id,
            candidate_id=row.candidate_id,
            source_id=row.source_id,
            status=row.status,
            created_at=row.created_at,
            extracted_facts=row.extracted_facts,
        )

    def save(self, import_session: ImportSession) -> None:
        row = self._session.get(ResumeImportSessionRow, import_session.import_id)
        if row is None:
            self.add(import_session)
            return
        row.status = import_session.status
        row.extracted_facts = [item.model_dump(mode="json") for item in import_session.extracted_facts]


class SqlAlchemyResumeRepositories:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session = session_factory()
        self.sources = ResumeSourceRepository(self._session)
        self.facts = ResumeFactRepository(self._session)
        self.imports = ImportSessionRepository(self._session)

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def close(self) -> None:
        self._session.close()
