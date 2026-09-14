# Phase B — Next.js Core Product Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a recruiter-presentable Next.js product frontend that completes the core job-search workflow against the Phase A API in both Demo and Local modes.

**Architecture:** `apps/web` is a pure API client. TanStack Query owns server state, URL search params own job filters, and mode/capability state comes exclusively from `/api/v1/meta/capabilities`. The frontend renders immigration and fit outputs but never derives them.

**Tech Stack:** Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, TanStack Table, React Hook Form, Zod, Recharts, Vitest, Testing Library, Playwright E2E.

**Spec:** `docs/superpowers/specs/2026-09-14-codex-skills-web-ui-design.md`

## Global Constraints

- No direct database access from `apps/web`.
- No immigration, scoring, fact-validation, or transition logic in TypeScript.
- Every gated action derives from backend capabilities.
- `Demo Mode` or `Local Mode` is visible in the shell on every page.
- There is no user-facing mode switch.
- Work Authorisation appears before Match in job-list and job-detail hierarchy.
- The Autofill CTA is `Launch Autofill`, never `Auto Apply`.
- Final submission is always described as manual.
- Demo E2E must run with no secrets.

---

### Task 1: Scaffold `apps/web` and verification toolchain

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/next.config.ts`
- Create: `apps/web/app/layout.tsx`
- Create: `apps/web/app/globals.css`
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/playwright.config.ts`
- Create: `apps/web/eslint.config.mjs`
- Create: `apps/web/components/ui/` shadcn primitives used by Phase B
- Test: `apps/web/tests/smoke.test.tsx`

**Interfaces:**
- Produces npm scripts: `dev`, `build`, `lint`, `typecheck`, `test`, `e2e`.

- [ ] **Step 1: Create package manifest with pinned major versions**

Dependencies must include Next.js, React, TanStack Query/Table, React Hook Form, Zod, Recharts, and the minimal shadcn/Radix dependencies actually used. Dev dependencies include TypeScript, ESLint, Vitest, jsdom, Testing Library, and `@playwright/test`.

- [ ] **Step 2: Add a failing smoke test for the root layout**

The test renders the shell and expects the product name `Sponsor-Aware Job Agent`.

- [ ] **Step 3: Run RED**

```bash
cd apps/web
npm install
npm test -- --run tests/smoke.test.tsx
```

- [ ] **Step 4: Implement minimal App Router shell and styles**

Use accessible semantic markup and CSS variables. Do not implement product pages yet.

- [ ] **Step 5: Run GREEN plus typecheck/lint**

```bash
npm run typecheck
npm run lint
npm test -- --run
```

- [ ] **Step 6: Commit**

```bash
git add apps/web
git commit -m "feat(web): scaffold Next.js product frontend"
```

---

### Task 2: Add typed API client, capability provider, and global shell

**Files:**
- Create: `apps/web/lib/api/client.ts`
- Create: `apps/web/lib/api/types.ts`
- Create: `apps/web/lib/api/queries.ts`
- Create: `apps/web/components/providers/query-provider.tsx`
- Create: `apps/web/components/shell/app-shell.tsx`
- Create: `apps/web/components/shell/mode-badge.tsx`
- Create: `apps/web/components/shell/api-status.tsx`
- Modify: `apps/web/app/layout.tsx`
- Test: `apps/web/tests/capabilities.test.tsx`

**Interfaces:**
- Consumes: `GET /api/v1/meta/capabilities`, `GET /api/v1/health`.
- Produces: `apiFetch<T>()`, typed capability query, global mode badge.

- [ ] **Step 1: Write failing capability tests**

Mock Demo response and assert:

- badge renders `Demo Mode`;
- Autofill capability is false in provider state;
- no UI control exists for switching to Local Mode;
- API offline state renders an explicit connectivity warning.

- [ ] **Step 2: Implement typed fetch wrapper**

`apiFetch` reads `NEXT_PUBLIC_API_BASE_URL`, parses the standard API error envelope, and throws an `ApiError` containing status/code/details. It never reads any local candidate config.

- [ ] **Step 3: Implement provider and shell**

Navigation includes Dashboard, Discover Jobs, Applications. Mode badge is persistent.

- [ ] **Step 4: Verify**

```bash
cd apps/web
npm run typecheck && npm run lint && npm test -- --run
```

- [ ] **Step 5: Commit**

```bash
git add apps/web
git commit -m "feat(web): add typed API client and mode-aware shell"
```

---

### Task 3: Build Dashboard

**Files:**
- Create: `apps/web/app/page.tsx`
- Create: `apps/web/features/dashboard/api.ts`
- Create: `apps/web/features/dashboard/dashboard-view.tsx`
- Create: `apps/web/features/dashboard/metric-card.tsx`
- Create: `apps/web/features/dashboard/distribution-chart.tsx`
- Test: `apps/web/tests/dashboard.test.tsx`

**Interfaces:**
- Consumes: `GET /api/v1/dashboard`.

- [ ] **Step 1: Write tests for decision-focused metrics**

Assert the six named metrics render, high-fit jobs are linkable, and empty/error states are explicit.

- [ ] **Step 2: Implement query and visual blocks**

Use Recharts only for aggregate visualisation. Never recompute backend counts from job rows.

- [ ] **Step 3: Verify**

```bash
cd apps/web && npm run typecheck && npm test -- --run tests/dashboard.test.tsx
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/app/page.tsx apps/web/features/dashboard apps/web/tests/dashboard.test.tsx
git commit -m "feat(web): add decision-focused dashboard"
```

---

### Task 4: Build Discover Jobs with URL-backed filters

**Files:**
- Create: `apps/web/app/jobs/page.tsx`
- Create: `apps/web/features/jobs/api.ts`
- Create: `apps/web/features/jobs/job-table.tsx`
- Create: `apps/web/features/jobs/job-filters.tsx`
- Create: `apps/web/features/jobs/work-authorisation-badge.tsx`
- Test: `apps/web/tests/jobs-list.test.tsx`

**Interfaces:**
- Consumes: `GET /api/v1/jobs`.
- Produces URL params matching backend query names.

- [ ] **Step 1: Write hierarchy/filter tests**

Assert:

- column order is Company, Role, Location, Track, Work Authorisation, Match, Age, Action;
- setting country/min score updates URL query params;
- loading/empty/error states are distinct;
- pagination preserves filters.

- [ ] **Step 2: Implement filters and TanStack Table**

Do not calculate fit or WA in cell renderers. Render backend values only.

- [ ] **Step 3: Verify**

```bash
cd apps/web && npm run typecheck && npm run lint && npm test -- --run tests/jobs-list.test.tsx
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/app/jobs apps/web/features/jobs apps/web/tests/jobs-list.test.tsx
git commit -m "feat(web): add sponsor-aware job discovery table"
```

---

### Task 5: Build Job Detail / Review

**Files:**
- Create: `apps/web/app/jobs/[jobId]/page.tsx`
- Create: `apps/web/features/jobs/job-detail.tsx`
- Create: `apps/web/features/jobs/work-authorisation-panel.tsx`
- Create: `apps/web/features/jobs/fit-panel.tsx`
- Create: `apps/web/features/jobs/review-actions.tsx`
- Test: `apps/web/tests/job-detail.test.tsx`

**Interfaces:**
- Consumes: `GET /api/v1/jobs/{job_id}` and `POST /review-status`.

- [ ] **Step 1: Write tests for conceptual order and actions**

Assert DOM section order: Job -> Work Authorisation -> Candidate Fit. Verify evidence, unresolved items, confidence, strengths, gaps. Review action mutation invalidates both job detail and jobs list query keys.

- [ ] **Step 2: Implement detail panels**

`Prepare Application` links to `/applications/new/{jobId}`. Capability-disabled actions render reason text rather than silently disappearing.

- [ ] **Step 3: Verify**

```bash
cd apps/web && npm run typecheck && npm test -- --run tests/job-detail.test.tsx
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/app/jobs/'[jobId]' apps/web/features/jobs apps/web/tests/job-detail.test.tsx
git commit -m "feat(web): add job review workspace"
```

---

### Task 6: Build Application Workspace — Resume and Screening tabs

**Files:**
- Create: `apps/web/app/applications/new/[jobId]/page.tsx`
- Create: `apps/web/features/application-workspace/api.ts`
- Create: `apps/web/features/application-workspace/workspace.tsx`
- Create: `apps/web/features/application-workspace/resume-tab.tsx`
- Create: `apps/web/features/application-workspace/claim-provenance.tsx`
- Create: `apps/web/features/application-workspace/screening-tab.tsx`
- Test: `apps/web/tests/application-resume-screening.test.tsx`

**Interfaces:**
- Consumes package create/read endpoints.

- [ ] **Step 1: Write provenance and risk-style tests**

Assert each proposed claim renders source fact IDs and original text. Unsupported/conflicting claims show blocking state. Screening answers display one of `fixed_fact`, `generated_draft`, `manual_required`; work-authorisation/salary/notice/legal questions receive the high-risk component style.

- [ ] **Step 2: Implement create-or-load package flow**

Page first calls package-create then reads the package. Do not fabricate missing answer text client-side.

- [ ] **Step 3: Verify**

```bash
cd apps/web && npm run typecheck && npm test -- --run tests/application-resume-screening.test.tsx
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/app/applications/new apps/web/features/application-workspace apps/web/tests/application-resume-screening.test.tsx
git commit -m "feat(web): add sourced resume and screening workspace"
```

---

### Task 7: Add Cover Letter and Autofill tabs

**Files:**
- Create: `apps/web/features/application-workspace/cover-letter-tab.tsx`
- Create: `apps/web/features/application-workspace/autofill-tab.tsx`
- Create: `apps/web/features/application-workspace/autofill-session.tsx`
- Test: `apps/web/tests/application-cover-autofill.test.tsx`

**Interfaces:**
- Consumes package cover-letter section, capability contract, and autofill endpoints.

- [ ] **Step 1: Write Demo vs Local autofill tests**

Demo:

- shows simulated read-only walkthrough;
- does not issue POST `/autofill`;
- labels final submission as manual.

Local-capability mock:

- renders `Launch Autofill`;
- launch mutation creates session;
- confirm-ready requires user confirmation;
- `mark submitted manually` records the human action.

- [ ] **Step 2: Implement tabs**

No button text may imply automatic final submission.

- [ ] **Step 3: Verify**

```bash
cd apps/web && npm run typecheck && npm run lint && npm test -- --run tests/application-cover-autofill.test.tsx
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/features/application-workspace apps/web/tests/application-cover-autofill.test.tsx
git commit -m "feat(web): add optional cover letter and supervised autofill UI"
```

---

### Task 8: Build Applications table and Kanban from one backend state

**Files:**
- Create: `apps/web/app/applications/page.tsx`
- Create: `apps/web/features/applications/api.ts`
- Create: `apps/web/features/applications/applications-view.tsx`
- Create: `apps/web/features/applications/applications-table.tsx`
- Create: `apps/web/features/applications/applications-kanban.tsx`
- Test: `apps/web/tests/applications.test.tsx`

**Interfaces:**
- Consumes: list/transition application endpoints.

- [ ] **Step 1: Write same-source and transition tests**

Render both views from the same query result fixture. Transition mutation posts requested state but does not encode allowed transitions client-side; a 409 renders the backend conflict message.

- [ ] **Step 2: Implement table/Kanban toggle**

Columns match the eight spec states. Use backend state values directly.

- [ ] **Step 3: Verify**

```bash
cd apps/web && npm run typecheck && npm test -- --run tests/applications.test.tsx
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/app/applications apps/web/features/applications apps/web/tests/applications.test.tsx
git commit -m "feat(web): add application table and kanban tracker"
```

---

### Task 9: Add deterministic Demo E2E flow

**Files:**
- Create: `apps/web/e2e/demo-flow.spec.ts`
- Modify: `apps/web/playwright.config.ts`
- Modify: `README.md`

**Interfaces:**
- Requires Phase A Demo API running on `127.0.0.1:8000`.

- [ ] **Step 1: Write the E2E scenario**

The test must navigate:

```text
Dashboard
-> Discover Jobs
-> select high-fit job
-> inspect Work Authorisation panel
-> Prepare Application
-> expand a source-fact provenance item
-> open Autofill tab and see Demo simulation
-> open Applications tracker
```

It must not require authentication, secrets, local files, or browser profiles.

- [ ] **Step 2: Run E2E**

```bash
# terminal 1
APP_MODE=demo uvicorn job_agent.api.app:app --host 127.0.0.1 --port 8000
# terminal 2
cd apps/web && NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
# terminal 3
cd apps/web && npm run e2e
```

Expected: PASS.

- [ ] **Step 3: Run complete Phase B gate**

```bash
cd apps/web
npm run lint
npm run typecheck
npm test -- --run
npm run build
npm run e2e
```

Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/web README.md
git commit -m "test(web): add public demo end-to-end flow"
```
