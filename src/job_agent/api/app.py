from __future__ import annotations
import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from job_agent.api.demo.services import DemoServiceFactory
from job_agent.api.errors import ApiError, envelope
from job_agent.api.mode import Capabilities, get_app_mode
from job_agent.api.routers import meta, dashboard, jobs, application_packages, applications, autofill, resume, immigration, settings

def create_app() -> FastAPI:
    mode=get_app_mode()
    app=FastAPI(title='Sponsor-Aware Job Agent API',version='0.2.0')
    app.state.mode=mode
    app.state.capabilities=Capabilities.for_mode(mode)
    if mode=='demo': app.state.product_services=DemoServiceFactory.create()
    origins=[x.strip() for x in os.getenv('JOB_AGENT_CORS_ORIGINS','http://localhost:3000,http://127.0.0.1:3000').split(',') if x.strip()]
    app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=False,allow_methods=['*'],allow_headers=['*'])
    @app.exception_handler(ApiError)
    async def api_error(_:Request,exc:ApiError): return JSONResponse(status_code=exc.status_code,content=envelope(exc.code,exc.message,exc.details))
    @app.exception_handler(KeyError)
    async def not_found(_:Request,exc:KeyError): return JSONResponse(status_code=404,content=envelope('NOT_FOUND','Resource not found.',{"resource":str(exc.args[0]) if exc.args else ''}))
    @app.exception_handler(ValueError)
    async def conflict(_:Request,exc:ValueError): return JSONResponse(status_code=409,content=envelope('WORKFLOW_CONFLICT',str(exc)))
    @app.exception_handler(RequestValidationError)
    async def validation(_:Request,exc:RequestValidationError): return JSONResponse(status_code=422,content=envelope('VALIDATION_ERROR','Request validation failed.',{"errors":exc.errors()}))
    for router in (meta.router,dashboard.router,jobs.router,application_packages.router,applications.router,autofill.router,resume.router,immigration.router,settings.router):
        app.include_router(router,prefix='/api/v1')
    return app
app=create_app()
