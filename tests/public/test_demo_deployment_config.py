from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]
def test_compose_is_synthetic_and_has_no_private_mounts():
    data=yaml.safe_load((ROOT/'docker-compose.yml').read_text())
    api=data['services']['demo-api']; assert api['environment']['APP_MODE']=='demo'
    text=(ROOT/'docker-compose.yml').read_text();
    for forbidden in ['config/local','browser_profiles','artifacts','data/jobs.db']:
        assert forbidden not in text
    assert '127.0.0.1:8000:8000' in text and '127.0.0.1:3000:3000' in text
