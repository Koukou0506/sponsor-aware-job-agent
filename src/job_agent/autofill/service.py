from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from job_agent.autofill.adapters.base import FormAdapter, FormFillStopped
from job_agent.autofill.field_mapping import FieldMapper
from job_agent.autofill.models import (
    AutofillApplicationContext,
    AutofillSession,
    StopReason,
)
from job_agent.domain.ids import new_id


class AutofillRepositories(Protocol):
    def get_application_context(
        self,
        application_id: str,
    ) -> AutofillApplicationContext | None: ...

    def get_active_session(
        self,
        application_id: str,
    ) -> AutofillSession | None: ...

    def get_session(self, session_id: str) -> AutofillSession | None: ...

    def add_prepared_session(self, autofill_session: AutofillSession) -> None: ...

    def update_session_state(
        self,
        session_id: str,
        state: str,
        *,
        stop_reasons: list[StopReason] | None = None,
    ) -> AutofillSession: ...

    def confirm_ready(self, session_id: str) -> AutofillSession: ...

    def mark_submitted_manually(
        self,
        session_id: str,
        confirmed_at: datetime,
    ) -> AutofillSession: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class BrowserFactory(Protocol):
    async def open(self, url: str) -> Any: ...


class PlaywrightBrowserFactory:
    """Open a local browser profile without any submission capability."""

    def __init__(
        self,
        profile_dir: Path,
        *,
        headless: bool = False,
        executable_path: str | None = None,
    ) -> None:
        self._profile_dir = profile_dir
        self._headless = headless
        self._executable_path = executable_path
        self._playwright: Any | None = None
        self._context: Any | None = None

    async def open(self, url: str) -> Any:
        from playwright.async_api import async_playwright

        self._profile_dir.mkdir(parents=True, exist_ok=True)
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        if self._context is None:
            kwargs: dict[str, Any] = {
                "user_data_dir": str(self._profile_dir),
                "headless": self._headless,
                "args": ["--no-sandbox"],
            }
            if self._executable_path:
                kwargs["executable_path"] = self._executable_path
            self._context = await self._playwright.chromium.launch_persistent_context(
                **kwargs
            )
        page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        return page

    async def open_html(self, path: Path) -> Any:
        page = await self.open("about:blank")
        await page.set_content(path.read_text(encoding="utf-8"))
        return page

    async def close(self) -> None:
        if self._context is not None:
            await self._context.close()
            self._context = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None


class AutofillService:
    def __init__(
        self,
        repositories: AutofillRepositories,
        adapters: Mapping[str, FormAdapter],
        mapper: FieldMapper,
        browser_factory: BrowserFactory | None = None,
        base_answer_catalog: dict[str, object] | None = None,
    ) -> None:
        self._repositories = repositories
        self._adapters = dict(adapters)
        self._mapper = mapper
        self._browser_factory = browser_factory
        self._base_answer_catalog = base_answer_catalog or {}

    async def prepare(
        self,
        application_id: str,
        *,
        page: Any | None = None,
        dry_run: bool = False,
    ) -> AutofillSession:
        context = self._repositories.get_application_context(application_id)
        if context is None:
            raise KeyError(application_id)
        if context.current_state != "approved":
            raise ValueError("application package must be approved before autofill")
        active = self._repositories.get_active_session(application_id)
        if active is not None:
            raise ValueError(f"active autofill session already exists: {active.session_id}")
        adapter = self._adapters.get(context.ats_platform)
        if adapter is None:
            raise ValueError(f"unsupported ATS platform: {context.ats_platform}")
        if page is None:
            if self._browser_factory is None:
                raise ValueError("browser factory is required when no page is supplied")
            page = await self._browser_factory.open(str(context.application_url))

        expected_job = {
            "title": context.job_title,
            "requires_sponsorship": str(context.requires_sponsorship).casefold(),
        }
        stop_reasons = await adapter.inspect_stop_reasons(page, expected_job)
        detected_fields = await adapter.detect_fields(page)
        answers = {**self._base_answer_catalog, **context.answer_catalog}
        mappings = self._mapper.map_all(detected_fields, answers)
        stop_reasons.extend(
            _mapping_stop_reasons(detected_fields, mappings)
        )
        stop_reasons = _deduplicate_stop_reasons(stop_reasons)
        now = datetime.now(UTC)
        initial_state = (
            "needs_review"
            if dry_run
            or stop_reasons
            or any(mapping.requires_review for mapping in mappings)
            else "fields_mapped"
        )
        autofill_session = AutofillSession(
            session_id=new_id("autofill"),
            workspace_id=context.workspace_id,
            candidate_id=context.candidate_id,
            application_id=context.application_id,
            ats_platform=context.ats_platform,
            application_url=context.application_url,
            state=initial_state,
            field_mappings=mappings,
            stop_reasons=stop_reasons,
            created_at=now,
            updated_at=now,
        )
        if dry_run:
            return autofill_session

        self._repositories.add_prepared_session(autofill_session)
        self._repositories.commit()

        if stop_reasons:
            return autofill_session
        try:
            await adapter.fill(
                page,
                mappings,
                {
                    canonical: Path(path)
                    for canonical, path in context.file_catalog.items()
                },
            )
        except FormFillStopped as exc:
            reasons = _deduplicate_stop_reasons([*stop_reasons, exc.reason])
            updated = self._repositories.update_session_state(
                autofill_session.session_id,
                "needs_review",
                stop_reasons=reasons,
            )
            self._repositories.commit()
            return updated
        updated = self._repositories.update_session_state(
            autofill_session.session_id,
            "needs_review",
        )
        self._repositories.commit()
        return updated

    def confirm_ready(self, session_id: str, *, confirmation: bool) -> AutofillSession:
        if not confirmation:
            raise ValueError("explicit field-review confirmation is required")
        autofill_session = self._repositories.get_session(session_id)
        if autofill_session is None:
            raise KeyError(session_id)
        if autofill_session.state not in {
            "fields_mapped",
            "autofilled",
            "needs_review",
        }:
            raise ValueError(
                f"session cannot become ready from state: {autofill_session.state}"
            )
        updated = self._repositories.confirm_ready(session_id)
        self._repositories.commit()
        return updated

    def mark_submitted_manually(
        self,
        session_id: str,
        *,
        confirmation: bool,
    ) -> AutofillSession:
        if not confirmation:
            raise ValueError("manual browser submission confirmation is required")
        autofill_session = self._repositories.get_session(session_id)
        if autofill_session is None:
            raise KeyError(session_id)
        if autofill_session.state != "ready_to_submit":
            raise ValueError("session must be ready_to_submit before confirmation")
        updated = self._repositories.mark_submitted_manually(
            session_id,
            datetime.now(UTC),
        )
        self._repositories.commit()
        return updated


def _mapping_stop_reasons(
    detected_fields: list[Any],
    mappings: list[Any],
) -> list[StopReason]:
    reasons: list[StopReason] = []
    detected_by_selector = {field.selector: field for field in detected_fields}
    if not mappings:
        reasons.append(
            StopReason(
                code="unknown_page_structure",
                detail="No supported application fields were detected",
            )
        )
    for mapping in mappings:
        if mapping.canonical_field == "legal_declaration":
            reasons.append(
                StopReason(
                    code="legal_declaration",
                    detail="Legal declaration requires direct user action",
                    selector=mapping.selector,
                )
            )
        detected = detected_by_selector.get(mapping.selector)
        if (
            detected is not None
            and detected.max_length is not None
            and isinstance(mapping.value, str)
            and len(mapping.value) > detected.max_length
        ):
            reasons.append(
                StopReason(
                    code="character_limit_overflow",
                    detail=(
                        f"Value exceeds {detected.max_length} characters for "
                        f"{mapping.page_label}"
                    ),
                    selector=mapping.selector,
                )
            )
    return reasons


def _deduplicate_stop_reasons(reasons: list[StopReason]) -> list[StopReason]:
    output: list[StopReason] = []
    seen: set[tuple[str, str | None]] = set()
    for reason in reasons:
        key = (reason.code, reason.selector)
        if key in seen:
            continue
        seen.add(key)
        output.append(reason)
    return output
