# Phase E — Integration, CI, and Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the combined API, web app, skills, Demo Mode, and Local Mode reproducibly verifiable and safe to publish as a portfolio repository.

**Architecture:** Add local launchers, public-repository scans, CI jobs, deterministic Demo integration tests, and deployment documentation. CI runs only synthetic Demo workflows and never needs candidate secrets.

**Tech Stack:** GitHub Actions, Python 3.12, Node LTS, pytest, Next.js build, Playwright E2E, Bash/PowerShell launchers.

**Spec:** `docs/superpowers/specs/2026-09-14-codex-skills-web-ui-design.md`

## Global Constraints

- Public CI never accesses private local config or browser profiles.
- Demo Mode is the only mode used by public E2E.
- Local launchers bind API and web to loopback by default.
- No release archive contains `config/local`, `data`, `artifacts`, browser profiles, `.env`, real resume files, or secret values.
- A final-submit browser action remains absent.

---

### Task 1: Add local developer launch scripts

**Files:**
- Create: `scripts/dev-local.sh`
- Create: `scripts/dev-local.ps1`
- Create: `docs/WEB_LOCAL_SETUP.md`
- Test: `tests/public/test_dev_launchers.py`

**Interfaces:**
- Launches FastAPI on `127.0.0.1:8000` and Next.js on `127.0.0.1:3000`.
- Streamlit remains optional and uses a separate port.

- [ ] **Step 1: Write static safety tests**

Assert launch scripts default to `127.0.0.1` and do not contain `--host 0.0.0.0`. Assert `APP_MODE=local` is explicit.

- [ ] **Step 2: Implement launchers**

Check dependencies first and print child-process PIDs. Handle Ctrl+C/PowerShell stop by terminating child processes. Do not auto-open or expose the service externally.

- [ ] **Step 3: Verify**

```bash
python -m pytest tests/public/test_dev_launchers.py -q
```

- [ ] **Step 4: Commit**

```bash
git add scripts/dev-local.* docs/WEB_LOCAL_SETUP.md tests/public/test_dev_launchers.py
git commit -m "feat(dev): add loopback-only local web launchers"
```

---

### Task 2: Add public repository privacy and invariant scanner

**Files:**
- Create: `scripts/scan_public_repo.py`
- Create: `tests/public/test_public_scan.py`

**Interfaces:**
- `python scripts/scan_public_repo.py` exits non-zero on forbidden path/secret/submit patterns.

- [ ] **Step 1: Write scanner tests with temporary fixture trees**

Detect at minimum:

- `.env` other than `.env.example`;
- `config/local/`, `data/*.db`, `artifacts/`, `browser_profiles/`;
- `.pdf`, `.docx` outside explicit test fixtures;
- obvious API key/private key patterns;
- known real-email/phone placeholders if configured in scanner denylist;
- Playwright-style final-submit action patterns such as `page.click(...submit...)`, `locator(...submit...).click()` in production source.

Allow documentation sentences explaining manual submit.

- [ ] **Step 2: Implement scanner**

Use path and content allowlists/denylists. Do not print secret values; report file path and rule ID only.

- [ ] **Step 3: Verify**

```bash
python -m pytest tests/public/test_public_scan.py -q
python scripts/scan_public_repo.py
```

- [ ] **Step 4: Commit**

```bash
git add scripts/scan_public_repo.py tests/public/test_public_scan.py
git commit -m "test(security): add public repository privacy scan"
```

---

### Task 3: Add CI for Python, frontend, Demo E2E, skills, and public scan

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`

- [ ] **Step 1: Create separate CI jobs**

Jobs:

```text
python
web
skills
public-scan
demo-e2e
```

Use Python 3.12 and a supported Node LTS. Cache pip/npm where safe. No secrets are declared.

- [ ] **Step 2: Python job commands**

```bash
python -m pip install -e '.[all,dev]'
python -m pytest -q
python -m compileall -q src
python -m job_agent.api.verify_contract
```

- [ ] **Step 3: Web job commands**

```bash
cd apps/web
npm ci
npm run lint
npm run typecheck
npm test -- --run
npm run build
```

- [ ] **Step 4: Skills/public-scan commands**

```bash
python -m pytest tests/skills -q
python skills/sponsor-job-agent-dev/scripts/verify_repo.py
python scripts/scan_public_repo.py
```

- [ ] **Step 5: Demo E2E job**

Start API with `APP_MODE=demo`, start Next.js pointing to it, wait on health endpoints, then execute `npm run e2e`. Install only Playwright browser dependencies needed for E2E.

- [ ] **Step 6: Validate workflow syntax and commit**

If GitHub CLI is available, run workflow lint tooling; otherwise parse YAML locally and rely on branch push for hosted validation.

```bash
git add .github/workflows/ci.yml README.md
git commit -m "ci: verify API web skills demo and privacy invariants"
```

---

### Task 4: Add public Demo deployment contract and Docker convenience

**Files:**
- Create: `Dockerfile.api`
- Create: `apps/web/Dockerfile`
- Create: `docker-compose.yml`
- Create: `docs/DEMO_DEPLOYMENT.md`
- Test: `tests/public/test_demo_deployment_config.py`

- [ ] **Step 1: Write deployment-config tests**

Assert Demo service config sets `APP_MODE=demo`, does not mount private directories, and does not expose browser profile volumes. Local compose may mount local storage only in a clearly separate profile/service configuration.

- [ ] **Step 2: Implement API container**

Default command binds container service appropriately inside container, but deployment docs must explain that Local real-use mode is not the public container profile. Image contains source and synthetic fixtures only.

- [ ] **Step 3: Implement frontend container and compose**

Frontend receives only API base URL. Demo compose profile has no real database volume and no Playwright worker.

- [ ] **Step 4: Verify**

```bash
python -m pytest tests/public/test_demo_deployment_config.py -q
```

If Docker is available:

```bash
docker compose config
```

- [ ] **Step 5: Commit**

```bash
git add Dockerfile.api apps/web/Dockerfile docker-compose.yml docs/DEMO_DEPLOYMENT.md tests/public/test_demo_deployment_config.py
git commit -m "feat(deploy): add synthetic demo deployment profile"
```

---

### Task 5: Update portfolio README and architecture docs honestly

**Files:**
- Modify: `README.md`
- Modify: `README_ZH.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/DEMO.md`
- Modify: `docs/PORTFOLIO_RESUME_BULLETS.md`

- [ ] **Step 1: Update product screenshots section only if real screenshots exist**

If no screenshots have been captured, omit the section. Do not add placeholder or fabricated images.

- [ ] **Step 2: Document exact modes and safety boundary**

README must explicitly distinguish:

```text
Public Demo = synthetic, no live ATS, no resume upload, no Playwright
Local Mode = real configured workflow, supervised autofill, human final Submit
```

- [ ] **Step 3: Update architecture diagram**

Show Next.js -> FastAPI -> application/domain -> storage/Playwright and the two skills as separate developer/operations assets.

- [ ] **Step 4: Update resume bullets only with implemented, verifiable claims**

Do not state user counts, production traffic, hosted uptime, interview conversion, or performance metrics that have not been measured.

- [ ] **Step 5: Commit**

```bash
git add README.md README_ZH.md docs
git commit -m "docs: present web product and Codex skill architecture"
```

---

### Task 6: Run final release gate and produce GitHub-ready archive

**Files:**
- Create: `scripts/build_public_release.py`
- Test: `tests/public/test_release_archive.py`

- [ ] **Step 1: Write archive-content test**

Build into a temp directory and assert source, web app, skills, docs, tests, and config examples exist while private/local paths are absent.

- [ ] **Step 2: Implement release builder**

Use an explicit include/exclude policy, not `zip -r .`. Run `scan_public_repo.py` before archiving. Produce SHA-256 alongside ZIP.

- [ ] **Step 3: Run fresh full verification**

```bash
python -m pytest -q
python -m compileall -q src
python -m job_agent.api.verify_contract
cd apps/web
npm ci
npm run lint
npm run typecheck
npm test -- --run
npm run build
cd ../..
python skills/sponsor-job-agent-dev/scripts/verify_repo.py
python scripts/scan_public_repo.py
python scripts/build_public_release.py
```

Then extract the ZIP into a fresh temporary directory and rerun at least:

```bash
python scripts/scan_public_repo.py
python -m pytest tests/public tests/api -q
cd apps/web && npm ci && npm run typecheck && npm test -- --run
```

- [ ] **Step 4: Verify Demo E2E from the release tree**

Run the Demo API, web frontend, and `npm run e2e` from the extracted release. Expected: PASS with no secrets.

- [ ] **Step 5: Commit release tooling**

```bash
git add scripts/build_public_release.py tests/public/test_release_archive.py
git commit -m "build: add verified public release packaging"
```
