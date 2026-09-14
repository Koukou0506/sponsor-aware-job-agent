from fastapi.testclient import TestClient
from job_agent.api.app import create_app

def demo(monkeypatch): monkeypatch.setenv('APP_MODE','demo'); return TestClient(create_app())

def test_demo_resume_upload_denied(monkeypatch):
    c=demo(monkeypatch); r=c.post('/api/v1/resumes/import',files={'file':('resume.pdf',b'%PDF-demo','application/pdf')})
    assert r.status_code==403 and r.json()['error']['code']=='CAPABILITY_DISABLED'

def test_demo_resume_facts_are_synthetic(monkeypatch):
    p=demo(monkeypatch).get('/api/v1/resume-facts').json(); assert p['approved_facts'] and p['pending_imports']==[]

def test_demo_immigration_exposes_evidence_and_ruleset(monkeypatch):
    p=demo(monkeypatch).get('/api/v1/immigration/routes').json(); assert p and all(x['evidence'] and x['ruleset_version'] for x in p)

def test_demo_reassessment_denied(monkeypatch):
    r=demo(monkeypatch).post('/api/v1/immigration/reassess/job_demo_gb_1'); assert r.status_code==403

def test_demo_settings_are_secret_safe(monkeypatch):
    text=demo(monkeypatch).get('/api/v1/settings/summary').text
    assert 'sk-' not in text and 'cookie' not in text.lower() and 'browser_profile' in text
