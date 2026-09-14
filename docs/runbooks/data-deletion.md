# Local data deletion and fact revocation

## Resume-source deletion modes

### Retain verified facts

Use when the source file should be deleted but its already reviewed facts may remain in the local fact library.

```bash
job-agent resume delete SOURCE_ID --mode retain-facts
```

The original file is deleted and the source is marked revoked. Approved facts remain, with provenance showing that the source file is no longer available.

### Revoke dependent facts

Use when facts sourced exclusively from the deleted resume must no longer be used.

```bash
job-agent resume delete SOURCE_ID --mode revoke-facts
```

Facts whose only provenance is that source become `revoked`. Facts supported by another approved source remain available.

## Generated application materials

Delete a package directory under:

```text
artifacts/applications/PACKAGE_ID/
```

This removes local PDFs but does not falsify or erase the application-event history. Regenerate only from an approved package.

## Browser data

Close all browser workers, then delete the relevant profile directory under:

```text
browser_profiles/
```

This signs out local ATS sessions and removes cookies. It does not delete data held by the ATS provider.

## Database deletion

Back up only when legally and operationally appropriate. To reset all local dynamic data:

1. close the UI and browser workers;
2. delete `data/jobs.db`;
3. run `alembic upgrade head`;
4. reimport and reapprove facts.

## Candidate or workspace deletion

The MVP is single-user but stores `workspace_id` and `candidate_id`. A future multi-user deletion workflow must remove or revoke source files, facts, packages, autofill sessions, and application events according to explicit retention policy. Do not implement a broad SQL delete without a tested dependency map.
