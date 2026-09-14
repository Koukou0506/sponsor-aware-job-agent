# Phase D — Management UI Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate Resume & Facts, Immigration, and safe Settings views into the Next.js/FastAPI product without exposing secrets or removing Streamlit before verified parity.

**Architecture:** Add narrow Phase 2 API endpoints that delegate to existing ingestion/immigration/config services. Next.js adds management pages that display and mutate only explicitly allowed fields. Secret-bearing configuration stays local and is never returned raw.

**Tech Stack:** Existing Python services, FastAPI, Next.js, React Hook Form, Zod, TanStack Query.

**Spec:** `docs/superpowers/specs/2026-09-14-codex-skills-web-ui-design.md`

## Global Constraints

- Resume import is Local-only.
- Uploaded file type and size are validated before invoking ingestion services.
- Resume facts cannot be used in generated materials until approved.
- Immigration page displays evidence and rule metadata; it does not make or edit rules in the browser.
- Settings API returns non-secret summaries only.
- API keys, cookies, raw browser sessions, and full secret config values are never returned.
- Streamlit pages remain available until parity review explicitly marks them deprecated.

---

### Task 1: Add Resume & Facts API

**Files:**
- Create: `src/job_agent/api/schemas/resume.py`
- Create: `src/job_agent/api/routers/resume.py`
- Modify: `src/job_agent/api/app.py`
- Test: `tests/api/test_resume_management.py`

**Interfaces:**
- `POST /api/v1/resumes/import`
- `GET /api/v1/resume-imports/{session_id}`
- `GET /api/v1/resume-facts`
- `POST /api/v1/resume-facts/{fact_id}/approve`
- `POST /api/v1/resume-facts/{fact_id}/reject`

- [ ] **Step 1: Write Demo capability-denial tests**

All upload/mutation endpoints return `403 CAPABILITY_DISABLED` in Demo Mode.

- [ ] **Step 2: Write Local delegation tests with fake service**

Validate PDF/DOCX/TXT/MD allowlist and configured size limit before calling the ingestion adapter. Facts response includes provenance and verification state but no unrelated private data.

- [ ] **Step 3: Implement router and schema**

Use `UploadFile` streaming to a controlled local temporary path in Local Mode; clean temp files after service import. Do not persist uploaded file in API code—the existing ingestion service owns source persistence.

- [ ] **Step 4: Verify**

```bash
python -m pytest tests/api/test_resume_management.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/job_agent/api tests/api/test_resume_management.py
git commit -m "feat(api): expose guarded resume fact management"
```

---

### Task 2: Build Resume & Facts frontend

**Files:**
- Create: `apps/web/app/resume/page.tsx`
- Create: `apps/web/features/resume/api.ts`
- Create: `apps/web/features/resume/resume-upload.tsx`
- Create: `apps/web/features/resume/fact-review-table.tsx`
- Create: `apps/web/features/resume/provenance-drawer.tsx`
- Modify: `apps/web/components/shell/app-shell.tsx`
- Test: `apps/web/tests/resume-management.test.tsx`

- [ ] **Step 1: Write capability and review tests**

Demo renders upload disabled with reason. Local mock allows file selection, import session status, approve/reject fact, and provenance inspection.

- [ ] **Step 2: Implement page**

No parsing logic in browser. Client-side validation is convenience only; backend remains authoritative.

- [ ] **Step 3: Verify**

```bash
cd apps/web && npm run typecheck && npm test -- --run tests/resume-management.test.tsx
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/app/resume apps/web/features/resume apps/web/tests/resume-management.test.tsx
git commit -m "feat(web): migrate resume and fact review"
```

---

### Task 3: Add Immigration API and frontend evidence view

**Files:**
- Create: `src/job_agent/api/schemas/immigration.py`
- Create: `src/job_agent/api/routers/immigration.py`
- Modify: `src/job_agent/api/app.py`
- Create: `apps/web/app/immigration/page.tsx`
- Create: `apps/web/features/immigration/api.ts`
- Create: `apps/web/features/immigration/routes-table.tsx`
- Create: `apps/web/features/immigration/registry-status.tsx`
- Test: `tests/api/test_immigration_management.py`
- Test: `apps/web/tests/immigration.test.tsx`

**Interfaces:**
- `GET /api/v1/immigration/routes`
- `GET /api/v1/immigration/registries/status`
- `POST /api/v1/immigration/reassess/{job_id}`

- [ ] **Step 1: Write API tests**

Assert route/evidence/ruleset metadata are surfaced, reassessment is Local-only where real registry/config is required, and the router delegates to the immigration/application layer.

- [ ] **Step 2: Implement API**

No editable rule expressions or raw registry private paths in responses.

- [ ] **Step 3: Write frontend tests**

Verify evidence source, ruleset version, unresolved checks, and registry freshness state render. No UI control edits the rule engine.

- [ ] **Step 4: Implement frontend and verify**

```bash
python -m pytest tests/api/test_immigration_management.py -q
cd apps/web && npm run typecheck && npm test -- --run tests/immigration.test.tsx
```

- [ ] **Step 5: Commit**

```bash
git add src/job_agent/api apps/web/app/immigration apps/web/features/immigration tests/api/test_immigration_management.py apps/web/tests/immigration.test.tsx
git commit -m "feat(web): add immigration evidence management view"
```

---

### Task 4: Add secret-safe Settings summary

**Files:**
- Create: `src/job_agent/api/schemas/settings.py`
- Create: `src/job_agent/api/routers/settings.py`
- Modify: `src/job_agent/api/app.py`
- Create: `apps/web/app/settings/page.tsx`
- Create: `apps/web/features/settings/api.ts`
- Create: `apps/web/features/settings/settings-summary.tsx`
- Test: `tests/api/test_settings_summary.py`
- Test: `apps/web/tests/settings.test.tsx`

**Interfaces:**
- `GET /api/v1/settings/summary`

- [ ] **Step 1: Write explicit redaction tests**

Create local test config containing sentinel secrets (`sk-test-secret`, cookie sentinel). Assert serialized response contains neither the value nor raw secret field names. Return only booleans/status such as `openai_configured: true`, `browser_profile_present: true`, registry freshness, and config-file presence.

- [ ] **Step 2: Implement allowlist-based summary serializer**

Never serialize arbitrary `Settings.model_dump()` and redact afterward. Construct the response from an explicit safe-field allowlist.

- [ ] **Step 3: Implement settings page**

Display status and links/instructions for local file editing. Do not add secret-edit forms in this phase.

- [ ] **Step 4: Verify**

```bash
python -m pytest tests/api/test_settings_summary.py -q
cd apps/web && npm run typecheck && npm test -- --run tests/settings.test.tsx
```

- [ ] **Step 5: Commit**

```bash
git add src/job_agent/api apps/web/app/settings apps/web/features/settings tests/api/test_settings_summary.py apps/web/tests/settings.test.tsx
git commit -m "feat(web): add secret-safe settings summary"
```

---

### Task 5: Perform Streamlit parity review without premature deletion

**Files:**
- Create: `docs/STREAMLIT_PARITY.md`
- Modify only if parity is proven: `src/job_agent/ui/pages/*.py` deprecation notices, not deletion.
- Test: `tests/public/test_streamlit_still_importable.py`

- [ ] **Step 1: Inventory every current Streamlit page**

Map each operation to one of:

```text
web parity verified
intentionally CLI-only
still Streamlit-only
```

- [ ] **Step 2: Add importability regression test**

Assert `job_agent.ui.launcher` and current pages still import. This protects the transition period.

- [ ] **Step 3: Add deprecation notices only where parity is verified**

Do not remove the Streamlit launcher or any page with remaining operational value.

- [ ] **Step 4: Run Phase D gate**

```bash
python -m pytest tests/api tests/public/test_streamlit_still_importable.py -q
cd apps/web && npm run lint && npm run typecheck && npm test -- --run
```

- [ ] **Step 5: Commit**

```bash
git add docs/STREAMLIT_PARITY.md src/job_agent/ui tests/public/test_streamlit_still_importable.py
git commit -m "docs(ui): record Streamlit migration parity"
```
