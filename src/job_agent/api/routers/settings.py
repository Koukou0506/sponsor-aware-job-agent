from fastapi import APIRouter, Depends
from job_agent.api.dependencies import get_product_services
from job_agent.api.schemas.settings import SettingsSummary
router=APIRouter()
@router.get('/settings/summary', response_model=SettingsSummary)
def summary(services=Depends(get_product_services)): return services.settings_summary()
