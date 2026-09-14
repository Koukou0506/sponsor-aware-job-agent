from datetime import UTC, datetime
from pathlib import Path
from shutil import copy2
from typing import Literal, Protocol

from job_agent.domain.ids import new_id
from job_agent.resume_ingestion.extraction import ResumeExtractionProvider
from job_agent.resume_ingestion.merge import classify_candidate
from job_agent.resume_ingestion.models import (
    ExtractedFactCandidate,
    ImportSession,
    Provenance,
    ResumeFact,
    ResumeSource,
)
from job_agent.resume_ingestion.parsers import ResumeParser
from job_agent.resume_ingestion.segmentation import segment_bullet


class SourceRepository(Protocol):
    def get_by_hash(self, file_hash: str) -> ResumeSource | None: ...
    def add(self, source: ResumeSource) -> None: ...
    def get(self, source_id: str) -> ResumeSource | None: ...
    def save(self, source: ResumeSource) -> None: ...


class FactRepository(Protocol):
    def list_approved(self, candidate_id: str) -> list[ResumeFact]: ...
    def add(self, fact: ResumeFact) -> None: ...
    def get(self, fact_id: str) -> ResumeFact | None: ...
    def save(self, fact: ResumeFact) -> None: ...
    def list_by_source(self, source_id: str) -> list[ResumeFact]: ...


class ImportRepository(Protocol):
    def add(self, import_session: ImportSession) -> None: ...
    def get(self, import_id: str) -> ImportSession | None: ...
    def save(self, import_session: ImportSession) -> None: ...


class ResumeRepositories(Protocol):
    sources: SourceRepository
    facts: FactRepository
    imports: ImportRepository

    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class DuplicateResumeSource(ValueError):
    pass


class ReviewConflict(ValueError):
    pass


class ResumeImportService:
    def __init__(
        self,
        repositories: ResumeRepositories,
        extractor: ResumeExtractionProvider,
        source_root: Path = Path("data/resume_sources"),
    ) -> None:
        self._repositories = repositories
        self._extractor = extractor
        self._source_root = source_root

    def stage_uploaded_file(self, filename: str, content: bytes) -> Path:
        safe_name = Path(filename).name
        if safe_name != filename or not safe_name:
            raise ValueError("invalid upload filename")
        stage_dir = self._source_root / ".staging"
        stage_dir.mkdir(parents=True, exist_ok=True)
        path = stage_dir / f"{new_id('upload')}_{safe_name}"
        path.write_bytes(content)
        return path

    def import_file(self, path: Path, *, dry_run: bool = False) -> ImportSession:
        parsed = ResumeParser().parse(path)
        if self._repositories.sources.get_by_hash(parsed.file_hash) is not None:
            raise DuplicateResumeSource(parsed.file_hash)
        source_id = new_id("source")
        destination = self._source_root / source_id / path.name
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            copy2(path, destination)
        extracted = self._extractor.extract(parsed, source_id)
        approved = self._repositories.facts.list_approved("default")
        candidates = [
            classify_candidate(candidate, approved)
            for bullet in extracted.bullets
            for candidate in segment_bullet(bullet)
        ]
        for skill in extracted.skills:
            candidates.append(
                classify_candidate(
                    ExtractedFactCandidate(
                        candidate_fact_id=new_id("candidate"),
                        raw_fact=f"Skill: {skill}",
                        category="skill",
                        skills=[skill],
                        provenance=Provenance(
                            source_id=source_id,
                            page_number=None,
                            section="skills",
                            original_text=skill,
                            extraction_method="structured_extraction",
                            extraction_confidence=0.9,
                        ),
                    ),
                    approved,
                )
            )
        source = ResumeSource(
            source_id=source_id,
            workspace_id="default",
            candidate_id="default",
            filename=path.name,
            file_hash=parsed.file_hash,
            uploaded_at=datetime.now(UTC),
            language=extracted.language,
            resume_track=extracted.resume_track,
            extraction_method=parsed.extraction_method,
            local_path=str(destination),
        )
        session = ImportSession(
            import_id=new_id("import"),
            workspace_id="default",
            candidate_id="default",
            source_id=source_id,
            status="awaiting_review",
            created_at=datetime.now(UTC),
            extracted_facts=candidates,
        )
        if not dry_run:
            try:
                self._repositories.sources.add(source)
                self._repositories.imports.add(session)
                self._repositories.commit()
            except Exception:
                self._repositories.rollback()
                destination.unlink(missing_ok=True)
                raise
        return session

    def approve_candidate(
        self,
        import_id: str,
        candidate_fact_id: str,
        edited_fact: str | None = None,
    ) -> ResumeFact:
        session, candidate = self._get_candidate(import_id, candidate_fact_id)
        if candidate.merge_classification == "wording_variant":
            return self.merge_wording_variant(import_id, candidate_fact_id)
        if candidate.merge_classification == "duplicate" and candidate.matched_fact_id:
            existing = self._repositories.facts.get(candidate.matched_fact_id)
            if existing is None:
                raise KeyError(candidate.matched_fact_id)
            return existing
        if candidate.merge_classification in {
            "metric_conflict",
            "date_conflict",
            "status_conflict",
            "unsupported_claim",
        } and edited_fact is None:
            raise ReviewConflict(candidate.merge_classification)
        fact = self._candidate_to_fact(candidate, raw_fact=edited_fact or candidate.raw_fact)
        try:
            self._repositories.facts.add(fact)
            self._remove_candidate(session, candidate_fact_id)
            self._repositories.commit()
        except Exception:
            self._repositories.rollback()
            raise
        return fact

    def reject_candidate(self, import_id: str, candidate_fact_id: str) -> ImportSession:
        session, _ = self._get_candidate(import_id, candidate_fact_id)
        self._remove_candidate(session, candidate_fact_id)
        self._repositories.commit()
        updated = self._repositories.imports.get(import_id)
        assert updated is not None
        return updated

    def merge_wording_variant(self, import_id: str, candidate_fact_id: str) -> ResumeFact:
        session, candidate = self._get_candidate(import_id, candidate_fact_id)
        if not candidate.matched_fact_id:
            raise ReviewConflict("wording variant has no matched fact")
        fact = self._repositories.facts.get(candidate.matched_fact_id)
        if fact is None:
            raise KeyError(candidate.matched_fact_id)
        allowed_claims = list(dict.fromkeys([*fact.allowed_claims, candidate.raw_fact]))
        updated = fact.model_copy(update={"allowed_claims": allowed_claims})
        self._repositories.facts.save(updated)
        self._remove_candidate(session, candidate_fact_id)
        self._repositories.commit()
        return updated

    def delete_source(
        self,
        source_id: str,
        mode: Literal["retain-facts", "revoke-facts"],
    ) -> ResumeSource:
        source = self._repositories.sources.get(source_id)
        if source is None:
            raise KeyError(source_id)
        Path(source.local_path).unlink(missing_ok=True)
        revoked_source = source.model_copy(update={"revoked_at": datetime.now(UTC)})
        self._repositories.sources.save(revoked_source)
        if mode == "revoke-facts":
            for fact in self._repositories.facts.list_by_source(source_id):
                provenance_sources = {item.source_id for item in fact.provenance}
                if provenance_sources == {source_id}:
                    self._repositories.facts.save(
                        fact.model_copy(update={"verification_status": "revoked"})
                    )
        self._repositories.commit()
        return revoked_source

    def apply_review_decision(
        self,
        import_id: str,
        candidate_fact_id: str,
        decision: str,
    ) -> ResumeFact | ImportSession:
        if decision == "Accept":
            return self.approve_candidate(import_id, candidate_fact_id)
        if decision == "Reject":
            return self.reject_candidate(import_id, candidate_fact_id)
        if decision in {"Merge with Existing", "Mark as Wording Variant"}:
            return self.merge_wording_variant(import_id, candidate_fact_id)
        raise ReviewConflict(f"decision requires edited data: {decision}")

    def _get_candidate(
        self, import_id: str, candidate_fact_id: str
    ) -> tuple[ImportSession, ExtractedFactCandidate]:
        session = self._repositories.imports.get(import_id)
        if session is None:
            raise KeyError(import_id)
        candidate = next(
            (item for item in session.extracted_facts if item.candidate_fact_id == candidate_fact_id),
            None,
        )
        if candidate is None:
            raise KeyError(candidate_fact_id)
        return session, candidate

    def _remove_candidate(self, session: ImportSession, candidate_fact_id: str) -> None:
        remaining = [
            item for item in session.extracted_facts if item.candidate_fact_id != candidate_fact_id
        ]
        status = "approved" if not remaining else session.status
        self._repositories.imports.save(
            session.model_copy(update={"extracted_facts": remaining, "status": status})
        )

    @staticmethod
    def _candidate_to_fact(candidate: ExtractedFactCandidate, raw_fact: str) -> ResumeFact:
        return ResumeFact(
            fact_id=new_id("fact"),
            workspace_id="default",
            candidate_id="default",
            category=candidate.category,
            organisation=candidate.organisation,
            role_or_project=candidate.role_or_project,
            start_date=candidate.start_date,
            end_date=candidate.end_date,
            raw_fact=raw_fact,
            claim_status=candidate.claim_status,
            metrics=candidate.metrics,
            skills=candidate.skills,
            allowed_claims=[raw_fact],
            verification_status="approved",
            provenance=[candidate.provenance],
        )
