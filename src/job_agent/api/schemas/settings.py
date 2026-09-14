from typing import Any
from pydantic import BaseModel
class SettingsSummary(BaseModel):
    mode: str
    database: dict[str, Any]
    candidate_profile: dict[str, Any]
    registries: dict[str, Any]
    browser_profile: dict[str, Any]
    llm: dict[str, Any]
