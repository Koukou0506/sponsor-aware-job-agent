from fastapi import APIRouter, Depends, Request
from job_agent.api.dependencies import get_product_services
from job_agent.api.errors import ApiError
from job_agent.api.schemas.immigration import ImmigrationOverview
router=APIRouter()
@router.get('/immigration/routes', response_model=list[dict])
def routes(services=Depends(get_product_services)): return services.immigration_overview()['routes']
@router.get('/immigration/registries/status', response_model=list[dict])
def registries(services=Depends(get_product_services)): return services.immigration_overview()['registry_status']
@router.post('/immigration/reassess/{job_id}', response_model=dict)
def reassess(job_id:str,request:Request,services=Depends(get_product_services)):
    if request.app.state.mode!='local': raise ApiError('CAPABILITY_DISABLED','Real immigration reassessment is Local Mode only.',403)
    return services.reassess_immigration(job_id)
