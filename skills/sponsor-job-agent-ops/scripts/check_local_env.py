from __future__ import annotations
import argparse, os
from pathlib import Path

def main()->int:
    parser=argparse.ArgumentParser(description='Check Sponsor-Aware Job Agent local prerequisites without printing secrets.')
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--require',choices=['scan','resume','autofill'],action='append',default=[])
    args=parser.parse_args(); root=args.root.resolve()
    checks={
      'project_root': root.joinpath('pyproject.toml').exists(),
      'config_dir': root.joinpath('config/local').exists(),
      'database_path': root.joinpath('data/jobs.db').exists(),
      'browser_profile': root.joinpath('browser_profiles/default').exists(),
    }
    print('mode:',os.getenv('APP_MODE','local'))
    for k,v in checks.items(): print(f'{k}:', 'present' if v else 'missing')
    required={'scan':['config_dir'],'resume':['config_dir'],'autofill':['config_dir','database_path','browser_profile']}
    missing=[key for op in args.require for key in required[op] if not checks[key]]
    return 2 if missing else 0
if __name__=='__main__': raise SystemExit(main())
