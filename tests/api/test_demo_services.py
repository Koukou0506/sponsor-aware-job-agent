from job_agent.api.demo.services import DemoServiceFactory

def test_demo_fixture_coverage_and_determinism():
    a=DemoServiceFactory.create(); b=DemoServiceFactory.create(); ja=a.list_jobs({})['items']; jb=b.list_jobs({})['items']
    assert ja==jb
    assert {j['country'] for j in ja}>={'GB','NL','DE','IE','HK'}
    assert {j['work_authorisation']['status'] for j in ja}>={'eligible','likely','uncertain','ineligible'}
    assert {j['role_track'] for j in ja}>={'technical','technical_business'}

def test_demo_package_claims_are_fact_grounded():
    s=DemoServiceFactory.create(); p=s.create_package('job_demo_hk_1')
    assert p['claims'] and all(c['source_facts'] for c in p['claims'])
