from fastapi.testclient import TestClient
from job_agent.api.app import create_app

def client(monkeypatch): monkeypatch.setenv('APP_MODE','demo'); return TestClient(create_app())
def test_dashboard(monkeypatch):
    p=client(monkeypatch).get('/api/v1/dashboard').json(); assert p['counts']['new_jobs']>=8 and p['country_distribution']
def test_jobs_filters_and_pagination(monkeypatch):
    c=client(monkeypatch); p=c.get('/api/v1/jobs?country=HK&min_score=80').json(); assert p['total']==1 and p['items'][0]['job_id']=='job_demo_hk_1'
def test_job_detail_prioritises_work_authorisation(monkeypatch):
    p=client(monkeypatch).get('/api/v1/jobs/job_demo_nl_1').json(); assert p['work_authorisation']['route']=='NL_HIGHLY_SKILLED_MIGRANT'; assert p['fit']['total']==84
def test_missing_job_envelope(monkeypatch):
    r=client(monkeypatch).get('/api/v1/jobs/nope'); assert r.status_code==404 and r.json()['error']['code']=='NOT_FOUND'
