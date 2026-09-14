from pathlib import Path
import importlib.util
SPEC=importlib.util.spec_from_file_location('scan_public_repo',Path(__file__).resolve().parents[2]/'scripts/scan_public_repo.py'); mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)
def test_scanner_detects_private_and_secret_material(tmp_path):
    (tmp_path/'.env').write_text('OPENAI_API_KEY=sk-'+'x'*24)
    (tmp_path/'src').mkdir(); (tmp_path/'src/app.py').write_text("page.locator('button[type=submit]').click()")
    findings=mod.scan(tmp_path); rules={r for _,r in findings}; assert 'forbidden-path' in rules and 'openai-key' in rules and 'final-submit-action' in rules
def test_example_env_and_manual_submit_docs_are_allowed(tmp_path):
    (tmp_path/'.env.example').write_text('OPENAI_API_KEY=')
    (tmp_path/'README.md').write_text('Final Submit is always manual.')
    assert mod.scan(tmp_path)==[]
