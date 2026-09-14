# Work-authorisation registry refresh

## Principle

Official registries are deterministic evidence, not a complete sponsorship decision. The system combines employer eligibility, job text, occupation or route eligibility, salary evidence, and candidate route state. A missing company match is not automatically a rejection unless the route legally requires a registered sponsor.

## Region-specific inputs

### United Kingdom

Store the current licensed sponsor register under `config/local/registries/`. Preserve the publication date, source URL, legal entity name, licence status, and registry identifier.

### Netherlands

Store the current IND recognised sponsor list. Match the Dutch legal entity, not only the global parent brand.

### Germany

No single employer sponsor list governs the route. Refresh salary thresholds and route rules in `immigration_rules.yaml`; retain degree-recognition and job-alignment evidence separately.

### Ireland

Refresh the Critical Skills and ineligible occupations rules, salary thresholds, and employer restrictions. Keep Critical Skills and General Employment Permit conclusions distinct.

### Hong Kong

Track the candidate-owned TTPS route in `visa_answers.yaml`. A `no sponsorship` statement does not disqualify a role after independent work authorisation is active. Before approval, the system must answer current-authorisation questions truthfully as not yet authorised.

## Refresh procedure

1. Download the official source manually.
2. Record source date and checksum.
3. Convert it to CSV or JSON without altering legal names.
4. Place it under `config/local/registries/`.
5. Run a fixture or local daily scan.
6. Review low-confidence entity matches.
7. Run the golden evaluator.

```bash
job-agent run-daily --board-config config/local/boards.yaml
job-agent evaluate-golden tests/golden/jobs/synthetic
```

## Entity matching controls

The resolver applies:

1. exact legal-name match;
2. legal-suffix normalisation;
3. verified domain match;
4. approved alias match;
5. approved parent–subsidiary mapping;
6. fuzzy match sent to human review.

A fuzzy match must never become official-registry evidence without human confirmation.

## Failure handling

- Stale registry: mark evidence unresolved; do not silently reuse an expired conclusion.
- Parsing error: retain the previous snapshot but display its date and a connector warning.
- Ambiguous subsidiary: send to verification; do not assign the parent licence automatically.
- Rule threshold change: version the ruleset and recompute assessments instead of overwriting history.
