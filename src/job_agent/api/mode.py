from typing import Literal
import os
from pydantic import BaseModel

AppMode = Literal["demo", "local"]


class Capabilities(BaseModel):
    live_job_scan: bool
    resume_upload: bool
    autofill_launch: bool
    material_generation: bool
    application_tracking: bool
    final_submission: bool

    @classmethod
    def for_mode(cls, mode: AppMode) -> "Capabilities":
        if mode == "demo":
            return cls(
                live_job_scan=False,
                resume_upload=False,
                autofill_launch=False,
                material_generation=True,
                application_tracking=True,
                final_submission=False,
            )
        return cls(
            live_job_scan=True,
            resume_upload=True,
            autofill_launch=True,
            material_generation=True,
            application_tracking=True,
            final_submission=False,
        )


def get_app_mode() -> AppMode:
    value = os.getenv("APP_MODE", "local").strip().lower()
    if value not in {"demo", "local"}:
        raise ValueError("APP_MODE must be either 'demo' or 'local'")
    return value  # type: ignore[return-value]
