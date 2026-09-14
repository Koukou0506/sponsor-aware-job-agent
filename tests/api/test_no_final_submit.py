from job_agent.api.app import create_app

def test_no_final_submit_route(monkeypatch):
    monkeypatch.setenv('APP_MODE','demo'); spec=create_app().openapi(); paths=set(spec['paths'])
    assert not any(p.endswith('/submit') or 'auto-submit' in p for p in paths)
    ids=[op.get('operationId','') for item in spec['paths'].values() for op in item.values() if isinstance(op,dict)]
    assert not any('submit_application' in x or 'auto_submit' in x for x in ids)
