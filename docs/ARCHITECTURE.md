# Architecture

## Boundary

```text
Next.js Web
   -> FastAPI /api/v1
      -> Application Services
         -> Immigration / Matcher / Materials / Resume / Autofill
         -> Repositories
            -> SQLite (default local storage)
```

### Rules

1. Web code never queries the database directly.
2. FastAPI route handlers validate/serialize and delegate; they do not calculate visa eligibility or match scores.
3. Generated claims must retain approved fact provenance.
4. Work-authorisation results retain route/evidence/unresolved items/ruleset metadata.
5. Autofill prepares the browser only; final Submit stays manual.

## Runtime isolation

`APP_MODE=demo` creates an in-memory deterministic `DemoServiceFactory`. It does not initialize local settings, database, resume storage, live connectors, browser profile, or Playwright.

`APP_MODE=local` lazily constructs adapters around the existing Python application services.

## Streamlit

`src/job_agent/ui` remains the Admin/Debug console during migration. See `STREAMLIT_PARITY.md`.

## Agent Skills

Skills do not embed business data. They encode architecture/operation guardrails and live under `skills/`; installation copies them to `~/.agents/skills/`.
