from typing import Any
from pydantic import BaseModel
class ImmigrationOverview(BaseModel):
    routes: list[dict[str, Any]]
    registry_status: list[dict[str, Any]]
