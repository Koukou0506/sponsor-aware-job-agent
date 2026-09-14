# Phase A — FastAPI + Demo Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the existing Python job-agent workflow through a thin, versioned FastAPI API while adding a deterministic synthetic Demo Mode that cannot touch private local resources.

**Architecture:** FastAPI resolves mode and capabilities, delegates Local requests to existing application services, and delegates Demo requests to a dedicated in-memory `DemoServiceFactory`. Routers serialize view models and translate known service exceptions into the standard error envelope; they do not calculate business decisions.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, Pydantic v2, existing SQLAlchemy/application services, pytest, httpx/TestClient.

**Spec:** `docs/superpowers/specs/2026-09-14-codex-skills-web-ui-design.md`

## Global Constraints

- All API routes are under `/api/v1`.
- Route handlers do not perform direct SQL queries.
- Demo Mode does not initialize Local `Settings`, SQLite, resume storage, browser profiles, or live connectors.
- Demo Mode returns deterministic synthetic data only.
- Local Mode reuses current `ReviewWorkspaceService`, `PackageService`, `ApplicationTracker`, `ResumeImportService`, `AutofillWorkspaceService`, and repositories as applicable.
- `POST /applications/{id}/autofill` is Local-only.
- There is no endpoint that performs final application submission.
- All expected errors use `{ "error": { "code", "message", "details" } }`.
- Local CORS defaults only to configured localhost origins.

---

### Task 1: Add API dependencies and runtime mode configuration

**Files:**
- Modify: `pyproject.toml`
- Create: `src/job_agent/api/__init__.py`
- Create: `src/job_agent/api/mode.py`
- Create: `src/job_agent/api/schemas/meta.py`
- Test: `tests/api/test_mode.py`

**Interfaces:**
- Produces: `AppMode = Literal["demo", "local"]`
- Produces: `get_app_mode() -> AppMode`
- Produces: `Capabilities.for_mode(mode: AppMode) -> Capabilities`

- [ ] **Step 1: Write the failing mode/capability tests**

```python
from job_agent.api.mode import Capabilities, get_app_mode


def test_demo_mode_disables_private_capabilities(monkeypatch):
    monkeypatch.setenv("APP_MODE", "demo")
    assert get_app_mode() == "demo"
    caps = Capabilities.for_mode("demo")
    assert caps.live_job_scan is False
    assert caps.resume_upload is False
    assert caps.autofill_launch is False
    assert caps.material_generation is True
    assert caps.final_submission is False


def test_invalid_mode_fails_closed(monkeypatch):
    monkeypatch.setenv("APP_MODE", "cloud")
    try:
        get_app_mode()
    except ValueError as exc:
        assert "APP_MODE" in str(exc)
    else:
        raise AssertionError("invalid mode must fail")
```

- [ ] **Step 2: Run the tests and verify RED**

```bash
python -m pytest tests/api/test_mode.py -q
```

Expected: import failure because `job_agent.api.mode` does not yet exist.

- [ ] **Step 3: Add API dependencies**

Add to the main dependency list in `pyproject.toml`:

```toml
"fastapi>=0.115,<1",
"uvicorn>=0.30,<1",
```

Add `httpx>=0.27,<1` to `dev` as well so TestClient tests do not depend on the `web` extra.

- [ ] **Step 4: Implement mode and capability models**

`src/job_agent/api/mode.py` must contain a strict environment parser and a Pydantic capability model with these fields:

```python
class Capabilities(BaseModel):
    live_job_scan: bool
    resume_upload: bool
    autofill_launch: bool
    material_generation: bool
    application_tracking: bool
    final_submission: bool
```

`APP_MODE` defaults to `local` for backward compatibility. Any non-`demo`/`local` value raises `ValueError` during app construction.

- [ ] **Step 5: Run the test**

```bash
python -m pytest tests/api/test_mode.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/job_agent/api tests/api/test_mode.py
git commit -m "feat(api): add runtime modes and capability model"
```

---

### Task 2: Add error envelope and FastAPI app shell

**Files:**
- Create: `src/job_agent/api/errors.py`
- Create: `src/job_agent/api/app.py`
- Create: `src/job_agent/api/routers/__init__.py`
- Create: `src/job_agent/api/routers/meta.py`
- Test: `tests/api/test_meta.py`

**Interfaces:**
- Produces: `app: FastAPI`
- Produces: `ApiError(code: str, message: str, status_code: int, details: dict[str, Any] | None = None)`

- [ ] **Step 1: Write failing health/capability tests**

```python
from fastapi.testclient import TestClient
from job_agent.api.app import create_app


def test_demo_meta_contract(monkeypatch):
    monkeypatch.setenv("APP_MODE", "demo")
    client = TestClient(create_app())
    response = client.get("/api/v1/meta/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "demo"
    assert payload["capabilities"]["autofill_launch"] is False


def test_health_has_no_candidate_pii(monkeypatch):
    monkeypatch.setenv("APP_MODE", "demo")
    client = TestClient(create_app())
    payload = client.get("/api/v1/health").json()
    assert payload == {"status": "ok", "mode": "demo"}
```

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/api/test_meta.py -q
```

Expected: failure because app/routers do not exist.

- [ ] **Step 3: Implement the app factory**

`create_app()` must:

- resolve mode once at app creation;
- add only explicitly configured CORS origins;
- include routers under `/api/v1`;
- install handlers for `ApiError`, `KeyError`, and `ValueError` with no stack traces in responses;
- export module-level `app = create_app()` for Uvicorn.

- [ ] **Step 4: Implement `/health` and `/meta/capabilities`**

Return the exact mode/capability contract from the spec. Health returns only process status and mode.

- [ ] **Step 5: Run GREEN**

```bash
python -m pytest tests/api/test_meta.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/job_agent/api tests/api/test_meta.py
git commit -m "feat(api): add FastAPI shell and meta endpoints"
```

---

### Task 3: Build deterministic DemoServiceFactory and fixtures

**Files:**
- Create: `src/job_agent/api/demo/__init__.py`
- Create: `src/job_agent/api/demo/fixtures.py`
- Create: `src/job_agent/api/demo/services.py`
- Create: `tests/api/test_demo_services.py`

**Interfaces:**
- Produces: `DemoServiceFactory.create() -> DemoServices`
- Produces service methods matching API-facing use cases: `dashboard()`, `list_jobs(filters)`, `get_job(job_id)`, `set_review_status(...)`, `create_package(...)`, `get_package(...)`, `approve_package(...)`, `reject_package(...)`, `list_applications()`, `transition_application(...)`, `reset()`.

- [ ] **Step 1: Write a failing deterministic fixture test**

Test exact invariants rather than brittle prose:

```python
services = DemoServiceFactory.create()
jobs = services.list_jobs({})["items"]
assert {job["country"] for job in jobs} >= {"GB", "NL", "DE", "IE", "HK"}
assert {job["work_authorisation"]["status"] for job in jobs} >= {
    "eligible", "likely", "uncertain", "ineligible"
}
assert {job["role_track"] for job in jobs} >= {"technical", "technical_business"}
```

Also assert two fresh factories serialize identically before mutation.

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/api/test_demo_services.py -q
```

- [ ] **Step 3: Implement synthetic fixtures**

Use obviously fictitious company/candidate identifiers. Include at least 8 jobs so all five regions and four work-authorisation statuses are represented. Every work-authorisation result includes route, confidence, evidence, unresolved checks, and a synthetic ruleset version.

- [ ] **Step 4: Implement in-memory workflow state**

Use deep-copied fixture state per factory. No file access, database access, environment secret access, or network calls are allowed. Package generation is deterministic and every generated resume claim points to a synthetic approved fact.

- [ ] **Step 5: Run GREEN**

```bash
python -m pytest tests/api/test_demo_services.py -q
```

- [ ] **Step 6: Commit**

```bash
git add src/job_agent/api/demo tests/api/test_demo_services.py
git commit -m "feat(api): add deterministic demo service factory"
```

---

### Task 4: Add dependency/provider boundary for Demo vs Local services

**Files:**
- Create: `src/job_agent/api/dependencies.py`
- Create: `src/job_agent/api/protocols.py`
- Test: `tests/api/test_dependencies.py`

**Interfaces:**
- Produces: `ProductServices` Protocol exposing API-facing operations.
- Produces: `get_product_services(request: Request) -> ProductServices`
- Produces: `LocalProductServices` adapter around existing services.

- [ ] **Step 1: Write tests proving Demo construction does not bootstrap Local settings**

Monkeypatch `job_agent.bootstrap.build_services` (or the actual local bootstrap entry point) to raise if called. Create a Demo app request and assert it succeeds. Then set `APP_MODE=local` and assert Local service resolution uses the local bootstrap.

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/api/test_dependencies.py -q
```

- [ ] **Step 3: Implement the protocol and adapters**

Keep route code unaware of concrete Streamlit/service classes. `LocalProductServices` may compose existing services but must not reimplement business rules.

- [ ] **Step 4: Run GREEN**

```bash
python -m pytest tests/api/test_dependencies.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/job_agent/api tests/api/test_dependencies.py
git commit -m "refactor(api): isolate demo and local service providers"
```

---

### Task 5: Implement Dashboard and Jobs API

**Files:**
- Create: `src/job_agent/api/schemas/dashboard.py`
- Create: `src/job_agent/api/schemas/jobs.py`
- Create: `src/job_agent/api/routers/dashboard.py`
- Create: `src/job_agent/api/routers/jobs.py`
- Modify: `src/job_agent/api/app.py`
- Test: `tests/api/test_dashboard_jobs.py`

**Interfaces:**
- Produces the exact Phase 1 contracts for `GET /dashboard`, `GET /jobs`, `GET /jobs/{job_id}`, and `POST /jobs/{job_id}/review-status`.

- [ ] **Step 1: Write API contract tests in Demo Mode**

Cover:

- dashboard count object and distributions;
- pagination shape (`items`, `page`, `page_size`, `total`);
- query filters for country, track, work-authorisation, minimum score;
- job detail includes WA before/independently from fit fields at schema level;
- missing job returns `404` envelope;
- invalid review status returns `400` or `409` envelope, never raw traceback.

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/api/test_dashboard_jobs.py -q
```

- [ ] **Step 3: Implement Pydantic response models and routers**

Routers call `ProductServices` only. Do not import SQLAlchemy models in router modules.

- [ ] **Step 4: Run GREEN**

```bash
python -m pytest tests/api/test_dashboard_jobs.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/job_agent/api tests/api/test_dashboard_jobs.py
git commit -m "feat(api): expose dashboard and job review endpoints"
```

---

### Task 6: Implement application packages and tracker API

**Files:**
- Create: `src/job_agent/api/schemas/applications.py`
- Create: `src/job_agent/api/routers/application_packages.py`
- Create: `src/job_agent/api/routers/applications.py`
- Modify: `src/job_agent/api/app.py`
- Test: `tests/api/test_applications.py`

**Interfaces:**
- Produces: `POST /api/v1/jobs/{job_id}/application-package`.
- Produces: `GET /api/v1/application-packages/{package_id}`.
- Produces: `POST /api/v1/application-packages/{package_id}/approve`.
- Produces: `POST /api/v1/application-packages/{package_id}/reject`.
- Produces: `GET /api/v1/applications`.
- Produces: `POST /api/v1/applications/{application_id}/transition`.

- [ ] **Step 1: Write failing workflow tests**

Test Demo path:

```text
job -> create package -> inspect source_facts -> approve -> list applications -> transition
```

Assertions:

- every claim has `source_facts`;
- unsupported/conflicting claim status cannot be approved;
- invalid transition returns `409`;
- table/Kanban consumers receive the same application state object.

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/api/test_applications.py -q
```

- [ ] **Step 3: Implement schemas and routers**

Map service `KeyError` to 404 and workflow `ValueError` to 409 where it represents a state conflict. Do not create a second transition table in FastAPI.

- [ ] **Step 4: Run GREEN**

```bash
python -m pytest tests/api/test_applications.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/job_agent/api tests/api/test_applications.py
git commit -m "feat(api): expose application package and tracker workflow"
```

---

### Task 7: Implement guarded autofill API and prove no submit endpoint exists

**Files:**
- Create: `src/job_agent/api/schemas/autofill.py`
- Create: `src/job_agent/api/routers/autofill.py`
- Modify: `src/job_agent/api/app.py`
- Test: `tests/api/test_autofill.py`
- Test: `tests/api/test_no_final_submit.py`

**Interfaces:**
- Produces: `POST /api/v1/applications/{application_id}/autofill` (Local Mode only).
- Produces: `GET /api/v1/autofill/{session_id}`.
- Produces: `POST /api/v1/autofill/{session_id}/confirm-ready`.
- Produces: `POST /api/v1/autofill/{session_id}/mark-submitted-manually`.

- [ ] **Step 1: Write capability-gate tests**

In Demo Mode:

```python
response = client.post("/api/v1/applications/app_demo_1/autofill")
assert response.status_code == 403
assert response.json()["error"]["code"] == "CAPABILITY_DISABLED"
```

In Local Mode, use a fake `ProductServices` dependency to assert the router delegates launch instead of constructing Playwright directly.

- [ ] **Step 2: Write no-final-submit route test**

Inspect the generated OpenAPI path set and assert no path or operation ID contains a final-submit action such as `/submit`, `auto-submit`, or `submit_application`.

- [ ] **Step 3: Run RED**

```bash
python -m pytest tests/api/test_autofill.py tests/api/test_no_final_submit.py -q
```

- [ ] **Step 4: Implement guarded routers**

`confirm-ready` and `mark-submitted-manually` require explicit `confirmation: true`. `mark-submitted-manually` records an external human action; it never interacts with a browser page.

- [ ] **Step 5: Run GREEN**

```bash
python -m pytest tests/api/test_autofill.py tests/api/test_no_final_submit.py -q
```

- [ ] **Step 6: Commit**

```bash
git add src/job_agent/api tests/api/test_autofill.py tests/api/test_no_final_submit.py
git commit -m "feat(api): add supervised autofill endpoints"
```

---

### Task 8: Add API contract verification and Phase A regression gate

**Files:**
- Create: `src/job_agent/api/verify_contract.py`
- Create: `tests/api/test_openapi_contract.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `python -m job_agent.api.verify_contract` returning exit 0 only when required routes/capabilities and no-submit invariant are present.

- [ ] **Step 1: Write failing OpenAPI contract test**

Assert the required Phase 1 route set exactly exists under `/api/v1` and response models are not untyped `dict` for core endpoints.

- [ ] **Step 2: Run RED, then implement verifier**

```bash
python -m pytest tests/api/test_openapi_contract.py -q
```

The verifier should construct a Demo app, inspect `app.openapi()`, and validate required paths plus forbidden submit operations without network access.

- [ ] **Step 3: Run full Phase A gate**

```bash
python -m pytest tests/api -q
python -m job_agent.api.verify_contract
python -m compileall -q src/job_agent/api
```

Expected: all PASS / exit 0.

- [ ] **Step 4: Commit**

```bash
git add src/job_agent/api tests/api README.md
git commit -m "test(api): add contract verification gate"
```
