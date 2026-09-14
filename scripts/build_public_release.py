from __future__ import annotations
import hashlib, shutil, subprocess, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
NAME='sponsor-aware-job-agent'
VERSION='0.2.0'
INCLUDE_DIRS=['.github','alembic','apps','config','docs','scheduler_examples','scripts','skills','src','tests','tools','user_files']
INCLUDE_FILES=['.env.example','.gitignore','README.md','README_ZH.md','GITHUB_UPLOAD_GUIDE_ZH.md','VERSION.txt','alembic.ini','pyproject.toml','Dockerfile.api','docker-compose.yml']
EXCLUDED_PARTS={'.git','.venv','node_modules','.next','config/local','data','artifacts','browser_profiles','dist','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','.superpowers'}

def allowed(rel:Path)->bool:
    posix=rel.as_posix()
    if posix=='.env': return False
    if any(part in EXCLUDED_PARTS for part in rel.parts): return False
    if any(posix.startswith(x+'/') for x in ['config/local','data','artifacts','browser_profiles']): return False
    if rel.suffix.lower() in {'.pdf','.docx'} and not posix.startswith('tests/fixtures/'): return False
    return True

def build(out_dir:Path=DIST)->tuple[Path,Path]:
    subprocess.run([sys.executable,str(ROOT/'scripts/scan_public_repo.py')],cwd=ROOT,check=True)
    out_dir.mkdir(parents=True,exist_ok=True)
    stage=out_dir/f'{NAME}-v{VERSION}'
    shutil.rmtree(stage,ignore_errors=True); stage.mkdir()
    for file in INCLUDE_FILES:
        src=ROOT/file
        if src.exists(): shutil.copy2(src,stage/file)
    for dirname in INCLUDE_DIRS:
        src=ROOT/dirname
        if not src.exists(): continue
        for path in src.rglob('*'):
            if not path.is_file(): continue
            rel=path.relative_to(ROOT)
            if not allowed(rel): continue
            dest=stage/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,dest)
    zip_path=out_dir/f'Sponsor-Aware-Job-Agent-GitHub-Web-v{VERSION}.zip'
    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(stage.rglob('*')):
            if path.is_file(): z.write(path,Path(NAME)/path.relative_to(stage))
    digest=hashlib.sha256(zip_path.read_bytes()).hexdigest()
    sha=zip_path.with_suffix(zip_path.suffix+'.sha256'); sha.write_text(f'{digest}  {zip_path.name}\n',encoding='utf-8')
    print(zip_path); print(sha)
    return zip_path,sha
if __name__=='__main__': build()
