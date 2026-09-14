# Demo Walkthrough

This walkthrough uses only example configuration and synthetic evaluation cases. It does not require committing a real resume or personal data.

## 1. Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -e ".[all,dev]"
```

## 2. Prepare local configuration

Copy the safe templates:

```bash
mkdir -p config/local
cp config/examples/*.yaml config/local/
```

The committed examples use `Example Candidate` / `Example Ltd`; replace local copies only.

## 3. Initialise storage

```bash
alembic upgrade head
job-agent doctor
```

Expected behavior: the CLI checks configuration and local storage without requiring real application data.

## 4. Run the synthetic rule evaluation

```bash
job-agent evaluate-golden tests/golden/jobs/synthetic
```

The five synthetic cases exercise the configured regional route conclusions and safety metrics without calling live job sites.

## 5. Inspect the ranking model

The public smoke tests demonstrate two important invariants:

- a job with work-authorisation fit below `0.5` is not allowed to enter material generation;
- technical and technical-business tracks use different scoring weights.

Run:

```bash
pytest tests/public -q
```

## 6. Use the UI locally

```bash
job-agent-ui
```

The workspace is organized around:

1. Dashboard
2. Job Review
3. Application Package
4. Autofill Queue
5. Application Tracker
6. Operations / Settings
7. Resume Import

## 7. Real-use flow

For real use, keep all candidate-specific files local:

```text
config/local/
data/
artifacts/
browser_profiles/
```

Then:

```bash
job-agent run-daily --board-config config/local/boards.yaml
job-agent generate --job-id JOB_ID --candidate default
job-agent autofill --application-id APPLICATION_ID
```

The final browser submit action remains manual.
