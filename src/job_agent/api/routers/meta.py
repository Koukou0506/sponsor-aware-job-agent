from fastapi import APIRouter, Request
from job_agent.api.schemas.meta import CapabilityResponse, HealthResponse
router=APIRouter()
@router.get('/health', response_model=HealthResponse)
def health(request: Request): return {"status":"ok","mode":request.app.state.mode}
@router.get('/meta/capabilities', response_model=CapabilityResponse)
def capabilities(request: Request): return {"mode":request.app.state.mode,"capabilities":request.app.state.capabilities}
