from pathlib import Path
from fastapi import APIRouter, Depends, File, Request, UploadFile
from job_agent.api.dependencies import get_product_services
from job_agent.api.errors import ApiError
from job_agent.api.schemas.resume import FactDecision, ResumeFactsView, ResumeImportView
router=APIRouter()
ALLOWED={'.pdf','.docx','.txt','.md'}; MAX_BYTES=10*1024*1024
@router.post('/resumes/import', response_model=ResumeImportView)
async def import_resume(request:Request,file:UploadFile=File(...),services=Depends(get_product_services)):
    if not request.app.state.capabilities.resume_upload: raise ApiError('CAPABILITY_DISABLED','Resume upload is unavailable in Demo Mode.',403)
    suffix=Path(file.filename or '').suffix.casefold()
    if suffix not in ALLOWED: raise ApiError('UNSUPPORTED_FILE_TYPE','Supported files: PDF, DOCX, TXT, MD.',400)
    content=await file.read(MAX_BYTES+1)
    if len(content)>MAX_BYTES: raise ApiError('FILE_TOO_LARGE','Resume upload exceeds the 10 MB limit.',400)
    return services.import_resume(Path(file.filename or 'resume').name,content)
@router.get('/resume-imports/{import_id}', response_model=ResumeImportView)
def get_import(import_id:str,services=Depends(get_product_services)): return services.get_resume_import(import_id)
@router.get('/resume-facts', response_model=ResumeFactsView)
def facts(services=Depends(get_product_services)): return services.list_resume_facts()
@router.post('/resume-facts/{fact_id}/approve', response_model=dict)
def approve(fact_id:str,payload:FactDecision,request:Request,services=Depends(get_product_services)):
    if not request.app.state.capabilities.resume_upload: raise ApiError('CAPABILITY_DISABLED','Resume fact mutation is unavailable in Demo Mode.',403)
    return services.approve_resume_fact(fact_id,payload.import_id)
@router.post('/resume-facts/{fact_id}/reject', response_model=dict)
def reject(fact_id:str,payload:FactDecision,request:Request,services=Depends(get_product_services)):
    if not request.app.state.capabilities.resume_upload: raise ApiError('CAPABILITY_DISABLED','Resume fact mutation is unavailable in Demo Mode.',403)
    return services.reject_resume_fact(fact_id,payload.import_id)
