import pytest
from job_agent.api.mode import Capabilities,get_app_mode

def test_demo_mode_disables_private_capabilities(monkeypatch):
    monkeypatch.setenv('APP_MODE','demo'); assert get_app_mode()=='demo'; caps=Capabilities.for_mode('demo')
    assert not caps.live_job_scan and not caps.resume_upload and not caps.autofill_launch and caps.material_generation and not caps.final_submission

def test_invalid_mode_fails_closed(monkeypatch):
    monkeypatch.setenv('APP_MODE','cloud')
    with pytest.raises(ValueError): get_app_mode()
