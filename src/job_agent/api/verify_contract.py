from job_agent.api.app import create_app
REQUIRED={
 '/api/v1/health','/api/v1/meta/capabilities','/api/v1/dashboard','/api/v1/jobs','/api/v1/jobs/{job_id}',
 '/api/v1/jobs/{job_id}/review-status','/api/v1/jobs/{job_id}/application-package','/api/v1/application-packages/{package_id}',
 '/api/v1/application-packages/{package_id}/approve','/api/v1/application-packages/{package_id}/reject','/api/v1/applications',
 '/api/v1/applications/{application_id}/transition','/api/v1/applications/{application_id}/autofill','/api/v1/autofill/{session_id}',
 '/api/v1/autofill/{session_id}/confirm-ready','/api/v1/autofill/{session_id}/mark-submitted-manually'}
def verify()->None:
    spec=create_app().openapi(); paths=set(spec['paths'])
    missing=REQUIRED-paths
    if missing: raise SystemExit(f'Missing API paths: {sorted(missing)}')
    forbidden=[p for p in paths if p.endswith('/submit') or 'auto-submit' in p]
    operation_ids=[op.get('operationId','') for item in spec['paths'].values() for op in item.values() if isinstance(op,dict)]
    if forbidden or any('submit_application' in x or 'auto_submit' in x for x in operation_ids): raise SystemExit('Final-submit invariant violated')
if __name__=='__main__': verify(); print('API contract OK')
