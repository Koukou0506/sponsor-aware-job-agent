# Codex Skills

The repository ships two canonical Agent Skills under `skills/`.

## Install

macOS/Linux:
```bash
bash scripts/install-skills.sh
```

Windows PowerShell:
```powershell
./scripts/install-skills.ps1
```

Dry-run first with `--dry-run` or `-DryRun`.

## Which skill should trigger?

- **sponsor-job-agent-dev** — repository changes, e.g. “Add a new immigration route to this repo” or “Add a new Next.js page”.
- **sponsor-job-agent-ops** — operating a local installation, e.g. “Run today's configured job scan and show high-fit jobs”.

Skills contain architecture and operating rules only. Candidate PII, resumes, cookies, API keys, browser profiles and the real local database remain outside skill directories.
