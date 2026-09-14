from typing import Any
from pydantic import BaseModel
class ConfirmationRequest(BaseModel):
    confirmation: bool
class AutofillLaunchResponse(BaseModel):
    application_id: str
    process_id: int | None = None
    session_id: str | None = None
    status: str
class AutofillSessionView(BaseModel):
    session_id: str
    application_id: str
    state: str
    ats_platform: str | None = None
    application_url: str | None = None
    mappings: list[dict[str, Any]] = []
    stop_reasons: list[dict[str, Any]] = []
    manual_submission_confirmed_at: str | None = None
