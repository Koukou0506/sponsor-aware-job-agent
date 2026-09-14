# Verification

Python/API:
```bash
PYTHONPATH=src APP_MODE=demo python -m pytest tests/api tests/public tests/skills -q
PYTHONPATH=src APP_MODE=demo python -m job_agent.api.verify_contract
python -m compileall -q src/job_agent
```

Frontend, when `apps/web` exists:
```bash
cd apps/web
npm run lint
npm run typecheck
npm test -- --run
npm run build
```

Public repository scan:
```bash
python tools/public_repo_scan.py .
```

Never claim a gate passed unless the command actually ran successfully in the current environment.
