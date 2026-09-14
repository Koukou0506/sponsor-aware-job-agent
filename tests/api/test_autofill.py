from fastapi.testclient import TestClient
from job_agent.api.app import create_app

def test_demo_autofill_is_forbidden(monkeypatch):
    monkeypatch.setenv('APP_MODE','demo'); c=TestClient(create_app()); r=c.post('/api/v1/applications/app_demo/autofill')
    assert r.status_code==403 and r.json()['error']['code']=='CAPABILITY_DISABLED'
