from __future__ import annotations
import os, subprocess, sys
from pathlib import Path

def run(cmd:list[str], cwd:Path, env:dict[str,str]|None=None)->None:
    print('+',' '.join(cmd))
    subprocess.run(cmd,cwd=cwd,env=env,check=True)

def main()->int:
    root=Path(__file__).resolve().parents[3]
    env=os.environ.copy(); env['PYTHONPATH']=str(root/'src'); env['APP_MODE']='demo'
    run([sys.executable,'-m','pytest','tests/api','tests/public','tests/skills','-q'],root,env)
    run([sys.executable,'-m','job_agent.api.verify_contract'],root,env)
    run([sys.executable,'-m','compileall','-q','src/job_agent'],root,env)
    web=root/'apps/web'
    if web.joinpath('package.json').exists():
        if not web.joinpath('node_modules').exists():
            raise SystemExit('apps/web exists but frontend dependencies are not installed; run npm install/npm ci before verification')
        for script in ('lint','typecheck'):
            run(['npm','run',script],web)
        run(['npm','test','--','--run'],web)
        run(['npm','run','build'],web)
    return 0
if __name__=='__main__': raise SystemExit(main())
