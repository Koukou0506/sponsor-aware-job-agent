from fastapi import APIRouter, Depends
from job_agent.api.dependencies import get_product_services
from job_agent.api.schemas.applications import PackageCreateRequest, PackageView
router=APIRouter()
@router.post('/jobs/{job_id}/application-package', response_model=PackageView)
def create_package(job_id:str,payload:PackageCreateRequest,services=Depends(get_product_services)):
    return services.create_package(job_id,payload.cover_letter,payload.force)
@router.get('/application-packages/{package_id}', response_model=PackageView)
def get_package(package_id:str,services=Depends(get_product_services)): return services.get_package(package_id)
@router.post('/application-packages/{package_id}/approve', response_model=PackageView)
def approve(package_id:str,services=Depends(get_product_services)): return services.approve_package(package_id)
@router.post('/application-packages/{package_id}/reject', response_model=PackageView)
def reject(package_id:str,services=Depends(get_product_services)): return services.reject_package(package_id)
