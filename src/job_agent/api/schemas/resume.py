from typing import Any
from pydantic import BaseModel
class ResumeImportView(BaseModel):
    import_id: str
    source_id: str
    status: str
    created_at: str
    extracted_facts: list[dict[str, Any]]
class ResumeFactsView(BaseModel):
    approved_facts: list[dict[str, Any]]
    pending_imports: list[dict[str, Any]]
class FactDecision(BaseModel):
    import_id: str
