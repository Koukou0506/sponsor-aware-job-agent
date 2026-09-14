from fastapi import APIRouter, Depends
from job_agent.api.dependencies import get_product_services
from job_agent.api.schemas.dashboard import DashboardResponse
router=APIRouter()
@router.get('/dashboard', response_model=DashboardResponse)
def dashboard(services=Depends(get_product_services)): return services.dashboard()
