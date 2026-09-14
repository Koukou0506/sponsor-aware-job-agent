# Codex Skills + Product Web UI Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a portfolio-quality Next.js frontend, a thin FastAPI adapter, public Demo Mode, local real-use mode, and two installable Codex skills without moving business rules out of the existing Python services.

**Architecture:** Keep the current Python application/domain/storage layers as the source of truth. Add `/api/v1` as a thin HTTP boundary, then build one Next.js application that renders either Demo or Local capabilities from the API. Codex skills live under `skills/` as reviewable repository assets and are installed into `~/.agents/skills/` by explicit scripts.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite, Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query/Table, React Hook Form, Zod, Recharts, Playwright, pytest, Vitest, Testing Library, Playwright E2E.

**Spec:** `docs/superpowers/specs/2026-09-14-codex-skills-web-ui-design.md`

## Global Constraints

- All user-visible decisions follow `Web UI -> HTTP API -> Application Service -> Domain/Repository`.
- Next.js must never read SQLite/PostgreSQL directly.
- Frontend code must never calculate immigration eligibility, match scores, resume-fact validity, or application-state transitions.
- FastAPI route handlers remain adapters; business decisions stay in existing application/domain services.
- Every product endpoint is versioned under `/api/v1`.
- Demo Mode must not read `config/local/`, real SQLite data, resume files, browser profiles, cookies, API keys, or real candidate PII.
- Local FastAPI binds to `127.0.0.1` by default; `0.0.0.0` requires explicit user configuration.
- Demo Mode must not launch Playwright or live ATS scans.
- Generated resume claims remain grounded in approved facts.
- Autofill may reach `ready_to_submit` but no API, frontend action, skill, or helper may click final Submit.
- CAPTCHA, login challenges, email verification, and anti-bot controls are never bypassed.
- Streamlit remains available as an admin/debug console until explicit parity review.
- `skills/` is the canonical source for both Codex skills; skills contain no private candidate data.
- The public Demo uses deterministic synthetic fixtures spanning UK, Netherlands, Germany, Ireland, and Hong Kong.
- Public CI requires no secrets and runs only in Demo Mode.

---

## Delivery sequence

Implement these plans in order. Each plan must leave the repository in a working, independently testable state.

1. **Phase A — FastAPI + Demo backend foundation**  
   `docs/superpowers/plans/2026-09-14-phase-a-fastapi-demo-backend.md`
2. **Phase B — Next.js core product frontend**  
   `docs/superpowers/plans/2026-09-14-phase-b-nextjs-core-ui.md`
3. **Phase C — Codex development and operations skills**  
   `docs/superpowers/plans/2026-09-14-phase-c-codex-skills.md`
4. **Phase D — Resume/Facts, Immigration, Settings migration**  
   `docs/superpowers/plans/2026-09-14-phase-d-management-ui.md`
5. **Phase E — Integrated release, CI, demo deployment contract**  
   `docs/superpowers/plans/2026-09-14-phase-e-integration-release.md`

## Cross-phase interfaces

The following names are stable across plans and must not be silently renamed:

```text
APP_MODE = "demo" | "local"
GET  /api/v1/health
GET  /api/v1/meta/capabilities
GET  /api/v1/dashboard
GET  /api/v1/jobs
GET  /api/v1/jobs/{job_id}
POST /api/v1/jobs/{job_id}/review-status
POST /api/v1/jobs/{job_id}/application-package
GET  /api/v1/application-packages/{package_id}
POST /api/v1/application-packages/{package_id}/approve
POST /api/v1/application-packages/{package_id}/reject
GET  /api/v1/applications
POST /api/v1/applications/{application_id}/transition
POST /api/v1/applications/{application_id}/autofill
GET  /api/v1/autofill/{session_id}
POST /api/v1/autofill/{session_id}/confirm-ready
POST /api/v1/autofill/{session_id}/mark-submitted-manually
```

Phase D adds:

```text
POST /api/v1/resumes/import
GET  /api/v1/resume-imports/{session_id}
GET  /api/v1/resume-facts
POST /api/v1/resume-facts/{fact_id}/approve
POST /api/v1/resume-facts/{fact_id}/reject
GET  /api/v1/immigration/routes
GET  /api/v1/immigration/registries/status
POST /api/v1/immigration/reassess/{job_id}
GET  /api/v1/settings/summary
```

## Final acceptance command set

Run from repository root after Phase E:

```bash
python -m pytest -q
python -m compileall -q src
python -m job_agent.api.verify_contract
cd apps/web && npm ci && npm run lint && npm run typecheck && npm test -- --run && npm run build
cd ../..
python skills/sponsor-job-agent-dev/scripts/verify_repo.py
python scripts/scan_public_repo.py
```

Then run Demo E2E with the backend and frontend in Demo Mode:

```bash
APP_MODE=demo uvicorn job_agent.api.app:app --host 127.0.0.1 --port 8000
# second terminal
cd apps/web
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
# third terminal
cd apps/web && npm run e2e
```

Expected outcomes:

- all Python and frontend tests pass;
- Demo E2E reaches Dashboard -> Jobs -> Job Detail -> Prepare Application -> sourced claim -> Autofill simulation -> Applications;
- no public file contains real candidate data or secrets;
- no source path contains a final-submit browser action;
- Demo Mode cannot access Local-only endpoints;
- Local Mode still uses SQLite and the existing services by default.
