from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]

def test_bash_dry_run_creates_nothing(tmp_path):
    r=subprocess.run(['bash','scripts/install-skills.sh','--dry-run','--target',str(tmp_path)],cwd=ROOT,text=True,capture_output=True,check=True)
    assert 'sponsor-job-agent-dev' in r.stdout and not any(tmp_path.iterdir())

def test_bash_installs_exactly_two_skills(tmp_path):
    subprocess.run(['bash','scripts/install-skills.sh','--target',str(tmp_path)],cwd=ROOT,check=True)
    assert sorted(p.name for p in tmp_path.iterdir())==['sponsor-job-agent-dev','sponsor-job-agent-ops']
