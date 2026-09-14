from pathlib import Path
import importlib.util,zipfile
ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location('release',ROOT/'scripts/build_public_release.py'); mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)
def test_release_contains_product_and_excludes_private(tmp_path):
    z,_=mod.build(tmp_path)
    with zipfile.ZipFile(z) as archive:
        names=set(archive.namelist())
    required=['sponsor-aware-job-agent/src/job_agent/api/app.py','sponsor-aware-job-agent/apps/web/package.json','sponsor-aware-job-agent/skills/sponsor-job-agent-dev/SKILL.md','sponsor-aware-job-agent/README.md']
    assert all(x in names for x in required)
    forbidden=['/config/local/','/data/','/artifacts/','/browser_profiles/']
    assert not any(any(f in n for f in forbidden) for n in names)
    assert not any(n.endswith('/.env') for n in names)
