from datetime import datetime
from fastapi import APIRouter, Depends, Query
from job_agent.api.dependencies import get_product_services
from job_agent.api.schemas.jobs import JobDetail, JobsPage, ReviewStatusRequest
router=APIRouter()
@router.get('/jobs', response_model=JobsPage)
def list_jobs(country:str|None=None, role_track:str|None=None, work_authorisation:str|None=None, min_score:float|None=None,
              company:str|None=None, language:str|None=None, ats:str|None=None, published_after:datetime|None=None,
              page:int=Query(1,ge=1), page_size:int=Query(25,ge=1,le=100), services=Depends(get_product_services)):
    return services.list_jobs({"country":country,"role_track":role_track,"work_authorisation":work_authorisation,"min_score":min_score,
                               "company":company,"language":language,"ats":ats,"published_after":published_after.isoformat() if published_after else None,
                               "page":page,"page_size":page_size})
@router.get('/jobs/{job_id}', response_model=JobDetail)
def get_job(job_id:str, services=Depends(get_product_services)): return services.get_job(job_id)
@router.post('/jobs/{job_id}/review-status', response_model=JobDetail)
def review(job_id:str, payload:ReviewStatusRequest, services=Depends(get_product_services)): return services.set_review_status(job_id,payload.status)
