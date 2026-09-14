# Local setup and verification

## Supported environment

- Python 3.12 or newer
- Git
- Chromium or a Playwright-managed Chromium build
- Local SQLite database

The application is local-first. Real resumes, generated documents, cookies, browser profiles, configuration containing personal data, and the SQLite database must remain outside Git.

## Installation

### POSIX

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[all,dev]"
python -m playwright install chromium
mkdir -p config/local
cp config/examples/*.yaml config/local/
alembic upgrade head
job-agent doctor
```

When Playwright cannot download its browser, install system Chromium and set:

```bash
export JOB_AGENT_BROWSER_EXECUTABLE=/usr/bin/chromium
```

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[all,dev]"
python -m playwright install chromium
New-Item -ItemType Directory -Force config\local
Copy-Item config\examples\*.yaml config\local\
alembic upgrade head
job-agent doctor
```

## Local configuration

Edit only files under `config/local/`:

- `profile.yaml`: name and standard contact fields.
- `preferences.yaml`: regions and role tracks.
- `visa_answers.yaml`: candidate-owned and employer-sponsored route state.
- `screening_answers.yaml`: fixed, reviewed answers for work authorisation, relocation, notice period, and salary.
- `boards.yaml`: ATS board references.
- `registries/`: official employer-register snapshots.

A missing answer remains unresolved and is highlighted for manual entry. It is never guessed.

## First run

```bash
job-agent resume import /absolute/path/to/resume.pdf
job-agent run-daily --board-config config/local/boards.yaml
job-agent-ui
```

In the UI:

1. Review and approve extracted resume facts.
2. Review work-authorisation evidence and match scores.
3. Generate and approve an application package.
4. Open the Autofill Queue.
5. Review every mapped field.
6. Submit only in the external browser.
7. Record manual submission after the ATS confirms receipt.

## Scheduled scan

Windows and POSIX examples are in `scheduler_examples/`. The scheduled task runs only discovery, normalisation, work-authorisation assessment, scoring, and review-queue creation. It never generates materials or opens application forms.

## Verification commands

```bash
alembic upgrade head
job-agent doctor
job-agent evaluate-golden tests/golden/jobs/synthetic
python -m compileall -q src
pytest -q
git diff --check
```

Optional development checks when installed:

```bash
ruff check .
mypy src
```

## Filesystem locations

Default paths:

```text
config/local/                  local personal configuration
data/jobs.db                   SQLite database
artifacts/resume_sources/      imported source resumes
artifacts/applications/        generated resumes and cover letters
browser_profiles/default/      local ATS browser session
```

These paths are ignored by Git.
