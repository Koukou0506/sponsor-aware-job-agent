from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_launchers_are_loopback_only_and_local_mode():
    for name in ['scripts/dev-local.sh','scripts/dev-local.ps1']:
        text=(ROOT/name).read_text(encoding='utf-8')
        assert '127.0.0.1' in text and 'APP_MODE' in text and 'local' in text
        assert '--host 0.0.0.0' not in text
