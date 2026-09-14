# Architecture

Canonical flow:

```text
apps/web (Next.js)
  -> src/job_agent/api (FastAPI HTTP boundary)
  -> src/job_agent/application (workflow services)
  -> domain modules / repositories
  -> SQLite or PostgreSQL
```

`src/job_agent/ui` is the legacy Streamlit admin/debug interface during migration.

Runtime modes:
- `APP_MODE=demo`: deterministic synthetic data, no private/local execution capabilities.
- `APP_MODE=local`: real configured services and supervised browser autofill.

When adding a feature, place the decision in the lowest appropriate Python layer and expose it upward rather than duplicating it.
