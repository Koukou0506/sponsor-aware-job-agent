from fastapi import APIRouter, Depends, Request
from job_agent.api.dependencies import get_product_services
from job_agent.api.errors import ApiError
from job_agent.api.schemas.autofill import AutofillLaunchResponse, AutofillSessionView, ConfirmationRequest
router=APIRouter()
@router.post('/applications/{application_id}/autofill', response_model=AutofillLaunchResponse)
def launch(application_id:str,request:Request,services=Depends(get_product_services)):
    if not request.app.state.capabilities.autofill_launch: raise ApiError('CAPABILITY_DISABLED','Autofill is unavailable in Demo Mode.',403)
    return services.launch_autofill(application_id)
@router.get('/autofill/{session_id}', response_model=AutofillSessionView)
def get_session(session_id:str,services=Depends(get_product_services)): return services.get_autofill(session_id)
@router.post('/autofill/{session_id}/confirm-ready', response_model=dict)
def confirm_ready(session_id:str,payload:ConfirmationRequest,services=Depends(get_product_services)):
    if not payload.confirmation: raise ApiError('CONFIRMATION_REQUIRED','Explicit confirmation=true is required.',400)
    return services.confirm_ready(session_id,True)
@router.post('/autofill/{session_id}/mark-submitted-manually', response_model=dict)
def mark_submitted(session_id:str,payload:ConfirmationRequest,services=Depends(get_product_services)):
    if not payload.confirmation: raise ApiError('CONFIRMATION_REQUIRED','Explicit confirmation=true is required.',400)
    return services.mark_submitted_manually(session_id,True)
