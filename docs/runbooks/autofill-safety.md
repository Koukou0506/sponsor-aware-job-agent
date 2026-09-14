# Autofill safety and manual-submit boundary

## Invariant

Production code may detect and fill supported fields, but it must not click, invoke, dispatch, or otherwise programmatically activate a final application submission control.

The user submits in the external ATS browser. The local application tracker changes to `submitted` only after a separate explicit confirmation that the user personally submitted and saw the ATS confirmation.

## Resolution order

Fields are mapped in this order:

1. ATS field ID;
2. HTML label;
3. `name` or placeholder;
4. nearby text;
5. structured semantic fallback.

Submit controls, hidden fields, and disabled fields are excluded from detection.

## Fields that always require review

- current work authorisation;
- sponsorship requirement;
- relocation willingness;
- notice period;
- salary expectation;
- legal declarations.

This applies even when confidence is `1.0`.

## Stop reasons and recovery

| Stop reason | System action | Manual recovery |
|---|---|---|
| `captcha` | Stop immediately | Complete the CAPTCHA personally; restart only after the page is accessible. |
| `authentication` | Stop | Sign in or verify email personally. Do not store credentials in configuration. |
| `duplicate_application` | Stop | Check the ATS account and tracker; do not create a second application. |
| `closed_job` | Stop | Mark the job closed or archive it. |
| `job_identity_mismatch` | Stop | Confirm the job title and URL before continuing. |
| `work_authorization_conflict` | Stop | Recheck route state and job wording; never change the answer merely to pass screening. |
| `file_upload_failed` | Stop | Verify the approved PDF exists locally and upload manually if needed. |
| `character_limit_overflow` | Stop | Edit and reapprove the answer; do not truncate legal or factual content silently. |
| `legal_declaration` | Stop | Read and answer the declaration personally. |
| `unknown_page_structure` | Stop | Fill the form manually or add a reviewed fixture and adapter update. |

## Safe operating procedure

```bash
job-agent autofill --application-id APPLICATION_ID
```

The browser remains local. Review highlighted mappings in the Autofill Queue. After field review, select **Confirm fields ready**. Submit in the external browser. Return to the Autofill Queue and select **Record manual submission** only after receiving ATS confirmation.

## Prohibited behaviour

- bypassing CAPTCHA or bot detection;
- automatically agreeing to legal declarations;
- guessing sponsorship, work-authorisation, salary, notice-period, or relocation answers;
- submitting the same application twice;
- changing an answer because a role would otherwise reject the candidate;
- programmatically clicking the final submit control.
