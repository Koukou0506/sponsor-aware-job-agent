import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from job_agent.connectors.base import BoardRef, JobConnector, RawJob
from job_agent.connectors.http import ConnectorRateLimited
from job_agent.domain.enums import JobStatus, Region, RoleTrack
from job_agent.domain.ids import new_id
from job_agent.domain.models import Company, Job, MatchAssessment, WorkAuthorizationAssessment
from job_agent.immigration.engine import ImmigrationEngine, WorkAuthorizationInput
from job_agent.immigration.models import RegistryRecord
from job_agent.jobs.company_resolution import resolve_entity
from job_agent.jobs.deduplication import JobChange, classify_job_change
from job_agent.jobs.normalization import normalize_raw_job
from job_agent.matcher.classifier import RoleClassification, classify_role
from job_agent.matcher.requirements import JobRequirements, extract_requirements
from job_agent.matcher.scoring import ScoreInputs, build_match_assessment, calculate_track_score


class CandidateSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: str = "default"
    candidate_id: str = "default"
    skills: set[str] = Field(default_factory=set)
    languages: set[str] = Field(default_factory=lambda: {"english"})
    experience_years: float = Field(default=0, ge=0)
    route_status: dict[str, str] = Field(default_factory=dict)


@dataclass(frozen=True)
class ReviewItem:
    review_id: str
    job: Job
    work_authorization: WorkAuthorizationAssessment
    match: MatchAssessment
    materials_generated: bool = False

    @property
    def work_authorization_fit(self) -> float:
        return self.work_authorization.work_authorization_fit


@dataclass(frozen=True)
class PipelineSummary:
    discovered_count: int
    duplicate_count: int
    hard_failed_count: int
    review_queue_count: int
    review_items: list[ReviewItem]
    connector_errors: dict[str, str] = field(default_factory=dict)


class JobIntelligenceStore(Protocol):
    def start_run(self, workspace_id: str, run_type: str = "run_daily") -> str: ...
    def finish_run(
        self,
        *,
        processed: int,
        succeeded: int,
        skipped: int,
        failed: int,
        duplicates: int = 0,
        hard_failed: int = 0,
    ) -> None: ...
    def existing_job(self, platform: str, company_id: str, external_job_id: str) -> Job | None: ...
    def save_company(self, company: Company) -> None: ...
    def save_job(self, job: Job, raw_payload_hash: str, change: JobChange) -> None: ...
    def save_work_authorization(self, assessment: WorkAuthorizationAssessment) -> None: ...
    def save_match(self, assessment: MatchAssessment) -> None: ...
    def add_review_item(self, item: ReviewItem) -> ReviewItem: ...
    def record_connector_error(self, board: BoardRef, error_type: str, detail: str) -> None: ...
    def record_connector_success(self, board: BoardRef) -> None: ...
    def checkpoint(self) -> None: ...


class InMemoryJobIntelligenceStore:
    def __init__(self) -> None:
        self.companies: dict[str, Company] = {}
        self.jobs: dict[tuple[str, str, str], Job] = {}
        self.payload_hashes: dict[str, str] = {}
        self.work_authorizations: list[WorkAuthorizationAssessment] = []
        self.matches: list[MatchAssessment] = []
        self.review_items: list[ReviewItem] = []
        self.errors: list[tuple[str, str, str]] = []

    def start_run(self, workspace_id: str, run_type: str = "run_daily") -> str:
        del workspace_id, run_type
        return new_id("run")

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
        del processed, succeeded, skipped, failed, duplicates, hard_failed

    def existing_job(self, platform: str, company_id: str, external_job_id: str) -> Job | None:
        return self.jobs.get((platform, company_id, external_job_id))

    def save_company(self, company: Company) -> None:
        self.companies[company.company_id] = company

    def save_job(self, job: Job, raw_payload_hash: str, change: JobChange) -> None:
        del change
        self.jobs[(job.source_platform, job.company_id, job.external_job_id)] = job
        self.payload_hashes[job.job_id] = raw_payload_hash

    def save_work_authorization(self, assessment: WorkAuthorizationAssessment) -> None:
        self.work_authorizations.append(assessment)

    def save_match(self, assessment: MatchAssessment) -> None:
        self.matches.append(assessment)

    def add_review_item(self, item: ReviewItem) -> ReviewItem:
        self.review_items.append(item)
        return item

    def record_connector_error(self, board: BoardRef, error_type: str, detail: str) -> None:
        self.errors.append((board.board_token, error_type, detail))

    def record_connector_success(self, board: BoardRef) -> None:
        del board

    def checkpoint(self) -> None:
        return None


def stable_company_id(company_name: str) -> str:
    normalized = " ".join(re.sub(r"[^a-z0-9]+", " ", company_name.casefold()).split())
    return f"company_{sha256(normalized.encode()).hexdigest()[:24]}"


def payload_hash(raw: RawJob) -> str:
    payload = json.dumps(raw.source_payload, ensure_ascii=False, sort_keys=True, default=str)
    return sha256(payload.encode()).hexdigest()


def _signals(text: str) -> tuple[bool, bool, bool]:
    lowered = text.casefold()
    explicit_positive = any(term in lowered for term in ("visa sponsorship available", "sponsorship available", "relocation support"))
    explicit_negative = any(term in lowered for term in ("no visa sponsorship", "do not provide visa sponsorship", "does not provide visa sponsorship", "unable to sponsor", "sponsorship is unavailable", "no sponsorship provided"))
    permanent = any(term in lowered for term in ("unrestricted right to work", "permanent right to work", "must already be authorised", "must already be authorized", "eu citizens only", "uk citizens only"))
    return explicit_positive, explicit_negative, permanent


def _country_input(
    job: Job,
    raw: RawJob,
    candidate: CandidateSnapshot,
    route_track: RoleTrack,
    entity_verified: bool,
    entity_match_uncertain: bool,
) -> WorkAuthorizationInput:
    positive, negative, permanent = _signals(f"{job.description_raw} {raw.metadata}")
    common: dict[str, object] = {
        "workspace_id": candidate.workspace_id,
        "candidate_id": candidate.candidate_id,
        "job_id": job.job_id,
        "country": job.country,
        "entity_verified": entity_verified,
        "entity_status": "active" if entity_verified else None,
        "entity_match_uncertain": entity_match_uncertain,
        "explicit_positive": positive,
        "explicit_negative": negative,
        "requires_permanent_rights": permanent,
        "ruleset_version": f"{job.country.value.casefold()}-deterministic-v1",
    }
    if job.country is Region.UK:
        common.update(
            salary_eligible=None,
            role_eligible=route_track is not RoleTrack.IRRELEVANT,
        )
    elif job.country is Region.NL:
        common.update(salary_eligible=None, contract_eligible=True)
    elif job.country is Region.DE:
        common.update(
            blue_card_eligible=None,
            skilled_worker_eligible=route_track is not RoleTrack.IRRELEVANT,
            salary_eligible=None,
            degree_aligned=None,
        )
    elif job.country is Region.IE:
        common.update(
            critical_skills_eligible=route_track in {
                RoleTrack.TECHNICAL,
                RoleTrack.MIXED,
            },
            general_permit_eligible=route_track is not RoleTrack.IRRELEVANT,
            salary_eligible=None,
        )
    elif job.country is Region.HK:
        common.update(candidate_route_status=candidate.route_status.get("HK"))
    return WorkAuthorizationInput.model_validate(common)


def _score_inputs(requirements: JobRequirements, classification: RoleClassification, candidate: CandidateSnapshot, work_auth: WorkAuthorizationAssessment, entity_verified: bool) -> ScoreInputs:
    candidate_skills = {skill.casefold() for skill in candidate.skills}
    mandatory = {skill.casefold() for skill in requirements.mandatory_skills}
    skill_fit = len(mandatory & candidate_skills) / len(mandatory) if mandatory else 0.7
    if requirements.minimum_years:
        experience_fit = min(1.0, candidate.experience_years / requirements.minimum_years)
    else:
        experience_fit = 0.7
    required_languages = {language.casefold() for language in requirements.languages}
    language_fit = 1.0 if required_languages.issubset({language.casefold() for language in candidate.languages}) else 0.35
    if classification.primary_track is RoleTrack.TECHNICAL:
        transition = 0.65
    elif classification.primary_track is RoleTrack.IRRELEVANT:
        transition = 0.0
    else:
        transition = 0.85
    return ScoreInputs(work_authorization_fit=work_auth.work_authorization_fit, skill_fit=skill_fit, experience_fit=experience_fit, role_transition_fit=transition, language_fit=language_fit, company_signal=0.9 if entity_verified else 0.5, recency=1.0)


def _select_track(classification: RoleClassification, inputs: ScoreInputs) -> RoleTrack:
    if classification.primary_track is not RoleTrack.MIXED:
        return classification.primary_track
    technical = calculate_track_score("technical", inputs)
    business = calculate_track_score("technical_business", inputs)
    return RoleTrack.TECHNICAL if technical >= business else RoleTrack.TECHNICAL_BUSINESS


class DailyPipeline:
    def __init__(self, connectors: dict[str, JobConnector], store: JobIntelligenceStore, registry_records: list[RegistryRecord] | None = None, immigration_engine: ImmigrationEngine | None = None, clock: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self._connectors = connectors
        self._store = store
        self._registry_records = registry_records or []
        self._immigration_engine = immigration_engine or ImmigrationEngine()
        self._clock = clock

    async def run(self, boards: list[BoardRef], candidate: CandidateSnapshot) -> PipelineSummary:
        self._store.start_run(candidate.workspace_id)
        discovered = duplicates = hard_failed = 0
        review_items: list[ReviewItem] = []
        connector_errors: dict[str, str] = {}
        for board in boards:
            jobs = await self._fetch_board(board, connector_errors)
            for raw in jobs:
                discovered += 1
                company_id = stable_company_id(raw.company_name)
                company = Company(company_id=company_id, workspace_id=candidate.workspace_id, canonical_name=raw.company_name)
                self._store.save_company(company)
                incoming = normalize_raw_job(raw, company_id, self._clock(), workspace_id=candidate.workspace_id, region_hint=board.region_hint)
                existing = self._store.existing_job(incoming.source_platform, company_id, incoming.external_job_id)
                if existing is not None:
                    incoming = incoming.model_copy(update={"job_id": existing.job_id})
                change = classify_job_change(existing, incoming)
                if change == "duplicate":
                    duplicates += 1
                    continue
                self._store.save_job(incoming, payload_hash(raw), change)
                self._store.checkpoint()
                route_classification = classify_role(
                    incoming.title,
                    JobRequirements(),
                )
                entity = resolve_entity(
                    raw.company_name,
                    None,
                    incoming.country.value,
                    self._registry_records,
                )
                work_auth_input = _country_input(
                    incoming,
                    raw,
                    candidate,
                    route_classification.primary_track,
                    entity.verified,
                    entity.match_type == "fuzzy",
                )
                work_auth = self._immigration_engine.evaluate(work_auth_input)
                self._store.save_work_authorization(work_auth)
                self._store.checkpoint()
                if work_auth.hard_fail:
                    hard_failed += 1
                    continue

                requirements = extract_requirements(incoming.description_raw)
                classification = classify_role(incoming.title, requirements)
                inputs = _score_inputs(
                    requirements,
                    classification,
                    candidate,
                    work_auth,
                    entity.verified,
                )
                selected_track = _select_track(classification, inputs)
                match = build_match_assessment(incoming.job_id, candidate.workspace_id, candidate.candidate_id, selected_track, inputs, evidence=list(classification.evidence), missing=[skill for skill in requirements.mandatory_skills if skill.casefold() not in {candidate_skill.casefold() for candidate_skill in candidate.skills}])
                self._store.save_match(match)
                self._store.checkpoint()
                if match.total_score >= 60 and inputs.material_generation_allowed and classification.primary_track is not RoleTrack.IRRELEVANT:
                    shortlisted = incoming.model_copy(update={"status": JobStatus.SHORTLISTED, "role_track": selected_track})
                    item = ReviewItem(review_id=new_id("review"), job=shortlisted, work_authorization=work_auth, match=match)
                    review_items.append(self._store.add_review_item(item))
                    self._store.checkpoint()
        self._store.finish_run(
            processed=discovered,
            succeeded=len(review_items),
            skipped=duplicates + hard_failed,
            failed=len(connector_errors),
            duplicates=duplicates,
            hard_failed=hard_failed,
        )
        return PipelineSummary(discovered, duplicates, hard_failed, len(review_items), review_items, connector_errors)

    async def _fetch_board(self, board: BoardRef, errors: dict[str, str]) -> list[RawJob]:
        try:
            connector = self._connectors[board.platform]
            jobs = await connector.list_jobs(board)
            self._store.record_connector_success(board)
            return jobs
        except ConnectorRateLimited as exc:
            errors[board.board_token] = "rate_limited"
            self._store.record_connector_error(board, "rate_limited", str(exc))
        except Exception as exc:
            errors[board.board_token] = "connector_failure"
            self._store.record_connector_error(board, "connector_failure", str(exc))
        return []
