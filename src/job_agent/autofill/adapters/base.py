from pathlib import Path
from typing import Any, Protocol

from job_agent.autofill.models import DetectedField, FieldMapping, StopReason
from job_agent.autofill.page_inspection import body_text, detect_visible_fields

_CAPTCHA_SELECTOR = "iframe[src*='recaptcha'], .g-recaptcha, [data-sitekey], iframe[src*='hcaptcha']"
_AUTH_TERMS = (
    "sign in to continue",
    "log in to continue",
    "verify your email",
    "email verification required",
)
_DUPLICATE_TERMS = (
    "already applied",
    "application already exists",
    "you have already submitted",
)
_CLOSED_TERMS = (
    "no longer accepting applications",
    "job is closed",
    "position has been filled",
    "vacancy is no longer available",
)
_NEGATIVE_SPONSORSHIP_TERMS = (
    "no visa sponsorship",
    "do not provide visa sponsorship",
    "unable to sponsor",
    "no sponsorship provided",
)
_LEGAL_TERMS = (
    "i certify that the information",
    "legal declaration",
    "i declare that",
)


class FormAdapter(Protocol):
    platform: str

    async def detect_fields(self, page: Any) -> list[DetectedField]: ...

    async def inspect_stop_reasons(
        self,
        page: Any,
        expected_job: dict[str, str],
    ) -> list[StopReason]: ...

    async def fill(
        self,
        page: Any,
        mappings: list[FieldMapping],
        files: dict[str, Path],
    ) -> None: ...


class FormFillStopped(RuntimeError):
    def __init__(self, reason: StopReason) -> None:
        super().__init__(reason.detail)
        self.reason = reason


class BaseFormAdapter:
    platform = "generic"
    form_selector = "form"

    async def detect_fields(self, page: Any) -> list[DetectedField]:
        return await detect_visible_fields(page, form_selector=self.form_selector)

    async def inspect_stop_reasons(
        self,
        page: Any,
        expected_job: dict[str, str],
    ) -> list[StopReason]:
        reasons: list[StopReason] = []
        if await page.locator(_CAPTCHA_SELECTOR).count():
            reasons.append(StopReason(code="captcha", detail="CAPTCHA detected"))

        body = (await body_text(page)).casefold()
        if any(term in body for term in _AUTH_TERMS):
            reasons.append(
                StopReason(
                    code="authentication",
                    detail="Login or email verification is required",
                )
            )
        if any(term in body for term in _DUPLICATE_TERMS):
            reasons.append(
                StopReason(
                    code="duplicate_application",
                    detail="Page reports an existing application",
                )
            )
        if any(term in body for term in _CLOSED_TERMS):
            reasons.append(
                StopReason(code="closed_job", detail="Job page is closed")
            )

        expected_title = expected_job.get("title", "").strip().casefold()
        if expected_title and expected_title not in body:
            reasons.append(
                StopReason(
                    code="job_identity_mismatch",
                    detail="Expected job title is absent from the page",
                )
            )
        if (
            expected_job.get("requires_sponsorship", "false").casefold() == "true"
            and any(term in body for term in _NEGATIVE_SPONSORSHIP_TERMS)
        ):
            reasons.append(
                StopReason(
                    code="work_authorization_conflict",
                    detail="Page excludes sponsorship required by the candidate route",
                )
            )
        if any(term in body for term in _LEGAL_TERMS):
            reasons.append(
                StopReason(
                    code="legal_declaration",
                    detail="A legal declaration requires direct user action",
                )
            )
        if not await page.locator(self.form_selector).count():
            reasons.append(
                StopReason(
                    code="unknown_page_structure",
                    detail="Expected application form was not found",
                )
            )
        return _deduplicate_reasons(reasons)

    async def fill(
        self,
        page: Any,
        mappings: list[FieldMapping],
        files: dict[str, Path],
    ) -> None:
        for mapping in mappings:
            if mapping.canonical_field == "legal_declaration":
                continue
            if mapping.source in {"unresolved", "user_required"}:
                continue
            locator = page.locator(mapping.selector)
            if await locator.count() != 1:
                raise FormFillStopped(
                    StopReason(
                        code="unknown_page_structure",
                        detail=f"Field selector did not resolve uniquely: {mapping.selector}",
                        selector=mapping.selector,
                    )
                )
            if mapping.canonical_field in {
                "resume_upload",
                "cover_letter_upload",
            }:
                file_path = files.get(mapping.canonical_field)
                if file_path is None or not file_path.exists():
                    raise FormFillStopped(
                        StopReason(
                            code="file_upload_failed",
                            detail=f"Missing upload file for {mapping.canonical_field}",
                            selector=mapping.selector,
                        )
                    )
                try:
                    await locator.set_input_files(str(file_path))
                except Exception as exc:
                    raise FormFillStopped(
                        StopReason(
                            code="file_upload_failed",
                            detail=f"Upload failed for {mapping.canonical_field}: {exc}",
                            selector=mapping.selector,
                        )
                    ) from exc
                continue

            max_length = await locator.get_attribute("maxlength")
            if (
                max_length
                and isinstance(mapping.value, str)
                and len(mapping.value) > int(max_length)
            ):
                raise FormFillStopped(
                    StopReason(
                        code="character_limit_overflow",
                        detail=(
                            f"Value exceeds {max_length} characters for "
                            f"{mapping.page_label}"
                        ),
                        selector=mapping.selector,
                    )
                )

            tag_name = str(await locator.evaluate("element => element.tagName.toLowerCase()"))
            input_type = (await locator.get_attribute("type") or "").casefold()
            if tag_name == "select":
                if isinstance(mapping.value, list):
                    await locator.select_option(label=mapping.value)
                else:
                    value = str(mapping.value)
                    try:
                        await locator.select_option(label=value)
                    except Exception:
                        await locator.select_option(value=value)
            elif input_type in {"checkbox", "radio"}:
                if bool(mapping.value):
                    await locator.check()
                elif input_type == "checkbox":
                    await locator.uncheck()
            else:
                await locator.fill(str(mapping.value))


def _deduplicate_reasons(reasons: list[StopReason]) -> list[StopReason]:
    seen: set[tuple[str, str | None]] = set()
    output: list[StopReason] = []
    for reason in reasons:
        key = (reason.code, reason.selector)
        if key in seen:
            continue
        seen.add(key)
        output.append(reason)
    return output
