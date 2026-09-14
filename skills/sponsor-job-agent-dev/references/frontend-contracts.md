# Frontend contract

The product frontend lives in `apps/web` and consumes `/api/v1` only.

Required hierarchy:
- job list: Work Authorisation before Match.
- job detail: Job -> Work Authorisation -> Candidate Fit.
- application workspace: Resume -> Screening -> Cover Letter -> Autofill.

The frontend must use `/api/v1/meta/capabilities`; it must not infer capabilities from mode names.

Use `Launch Autofill`, not `Auto Apply`. Final submission is manual.
