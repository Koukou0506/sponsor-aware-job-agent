from pydantic import BaseModel
from job_agent.api.mode import Capabilities, AppMode
class CapabilityResponse(BaseModel):
    mode: AppMode
    capabilities: Capabilities
class HealthResponse(BaseModel):
    status: str
    mode: AppMode
