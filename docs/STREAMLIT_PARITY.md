# Streamlit parity during Web migration

Streamlit remains the local admin/debug console until the Web product is fully verified.

| Capability | Next.js/FastAPI | Streamlit status |
|---|---|---|
| Dashboard | implemented | retained |
| Job review | implemented | retained |
| Application package review | implemented | retained |
| Applications tracker | implemented | retained |
| Resume import / fact review | implemented | retained |
| Immigration evidence | implemented read-only | retained for deeper debugging |
| Settings summary | implemented secret-safe | retained |
| Supervised browser autofill | local API launch implemented; frontend build verification pending | retained |
| Raw operational debugging | intentionally not migrated | Streamlit-only |

No Streamlit code is deleted in this phase.
