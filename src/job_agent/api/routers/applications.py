from fastapi import APIRouter, Depends
from job_agent.api.dependencies import get_product_services
from job_agent.api.schemas.applications import ApplicationView, TransitionRequest
router=APIRouter()
@router.get('/applications', response_model=list[ApplicationView])
def list_applications(services=Depends(get_product_services)): return services.list_applications()
@router.post('/applications/{application_id}/transition', response_model=ApplicationView)
def transition(application_id:str,payload:TransitionRequest,services=Depends(get_product_services)):
    return services.transition_application(application_id,payload.new_state,payload.payload)
