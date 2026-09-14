---
name: sponsor-job-agent-dev
description: Use when modifying, extending, debugging, testing, or reviewing the Sponsor-Aware Job Agent repository, including its API, web UI, immigration rules, ATS connectors, resume facts, scoring, application workflow, or autofill.
---

# Sponsor Job Agent Development

## Core invariant

All user-visible decisions follow:

`Web -> API -> Application Service -> Domain/Repository`

Read the relevant references before editing:

- architecture: `references/architecture.md`
- backend boundaries: `references/backend-boundaries.md`
- frontend/API contract: `references/frontend-contracts.md`
- immigration rules: `references/immigration-engine.md`
- verification: `references/testing.md`

## Non-negotiable rules

- Never implement immigration, scoring, fact validation, or transition logic independently in Next.js.
- Never query SQLite/PostgreSQL directly from `apps/web`.
- Never add an automatic final application Submit action.
- Never bypass CAPTCHA, login, email verification, or anti-bot controls.
- Resume claims must be supported by approved facts and preserve provenance.
- Immigration conclusions must retain evidence, unresolved items, and a ruleset version.
- Demo Mode must not read real candidate data, local config, cookies, browser profiles, or the real job database.
- Run targeted tests for the changed boundary and `scripts/verify_repo.py` before completion.
