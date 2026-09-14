from fastapi.testclient import TestClient
from job_agent.api.app import create_app

def test_demo_meta_contract(monkeypatch):
    monkeypatch.setenv('APP_MODE','demo'); c=TestClient(create_app()); p=c.get('/api/v1/meta/capabilities').json()
    assert p['mode']=='demo' and p['capabilities']['autofill_launch'] is False and p['capabilities']['final_submission'] is False

def test_health_has_no_candidate_pii(monkeypatch):
    monkeypatch.setenv('APP_MODE','demo'); c=TestClient(create_app()); assert c.get('/api/v1/health').json()=={'status':'ok','mode':'demo'}
