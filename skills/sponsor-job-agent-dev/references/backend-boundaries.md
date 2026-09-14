# Backend boundaries

## FastAPI
May validate HTTP, resolve mode/capabilities, translate errors, and serialize view models. Route handlers must not query SQLAlchemy directly or reimplement business rules.

## Application services
Own orchestration such as review actions, package generation, application transitions, resume import, and autofill workspace operations.

## Domain/rules
- `immigration/`: work-authorisation route decisions and evidence.
- `matcher/`: role classification and fit scoring.
- `materials/`: fact-grounded application content.
- `autofill/`: field mapping and supervised browser preparation.

## Storage
Only repositories/storage code should know persistence mechanics. Preserve migration compatibility.
