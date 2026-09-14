---
name: sponsor-job-agent-ops
description: Use when operating a local Sponsor-Aware Job Agent installation to scan jobs, review work-authorisation evidence and fit, prepare application materials, supervise autofill, or track application status.
---

# Sponsor Job Agent Operations

Before any action, inspect the runtime mode and backend capabilities. Use the product's API/CLI rather than recreating sponsor or scoring logic yourself.

Read:
- `references/daily-workflow.md`
- `references/application-safety.md`
- `references/visa-answer-rules.md`

## Invariants

- Preserve work-authorisation uncertainty; never invent or upgrade status.
- Candidate facts must come from approved local facts/configuration.
- Fixed visa, sponsorship, salary, notice-period, legal, and work-authorisation answers are not guessed by an LLM.
- Stop for CAPTCHA, login, email verification, or anti-bot challenges.
- Autofill may prepare a form, but final submission is human-only.
- Stop at `ready_to_submit`; never perform the final Submit action.
