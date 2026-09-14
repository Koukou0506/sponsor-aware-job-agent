from fastapi.testclient import TestClient
from job_agent.api.app import create_app

def test_demo_application_workflow(monkeypatch):
    monkeypatch.setenv('APP_MODE','demo'); c=TestClient(create_app())
    p=c.post('/api/v1/jobs/job_demo_gb_1/application-package',json={'cover_letter':True}).json(); assert all(x['source_facts'] for x in p['claims'])
    pid=p['package_id']; approved=c.post(f'/api/v1/application-packages/{pid}/approve').json(); assert approved['review_status']=='approved'
    apps=c.get('/api/v1/applications').json(); assert len(apps)==1 and apps[0]['current_state']=='approved'
    app_id=apps[0]['application_id']; r=c.post(f'/api/v1/applications/{app_id}/transition',json={'new_state':'autofill_started'}); assert r.status_code==200
    bad=c.post(f'/api/v1/applications/{app_id}/transition',json={'new_state':'offer'}); assert bad.status_code==409
