# Design Decisions

## 1. Work authorisation is evaluated before skill matching

**Decision:** run work-authorisation logic before application material generation and give it the highest ranking weight.

**Why:** for an international candidate, a role that cannot support the required work status is not merely a lower-quality lead; it may be unusable. Filtering this early reduces wasted LLM calls and manual review.

**Trade-off:** immigration rules are dynamic, so the engine must surface rule versions and uncertainty rather than claim permanent correctness.

## 2. Sponsorship is not a universal boolean

**Decision:** model routes as employer-sponsored, job-supported or candidate-owned.

**Why:** the UK/Netherlands, Germany and Hong Kong have materially different decision structures. Flattening them into `needs_sponsorship` loses information and creates false negatives.

## 3. Deterministic rules own hard decisions

**Decision:** LLMs may assist with semantic extraction and drafting, but hard work-authorisation decisions are produced by explicit rules and structured inputs.

**Why:** hard eligibility needs predictable, inspectable behavior and testable edge cases.

## 4. Resume generation is fact-constrained

**Decision:** imported resumes are split into atomic facts; facts must be approved before material generation can use them.

**Why:** a useful tailoring system must change emphasis and wording without inventing companies, dates, metrics, tools or responsibilities.

**Consequence:** generated claims can be traced back to source facts and marked unsupported/conflicting when evidence is missing.

## 5. Two role tracks use different weights

**Decision:** technical and technical-business roles are ranked separately.

**Why:** a Python/data role and an implementation/TPM role reward different evidence. A single score would systematically over- or under-value skills depending on the job family.

## 6. Human review is a product feature, not a temporary limitation

**Decision:** the browser workflow never performs the final application submission.

**Why:** work-authorisation, compensation, legal declarations and open-response questions can have material consequences. The system optimizes preparation and consistency while leaving final attestations to the candidate.

## 7. Local-first by default

**Decision:** personal configs, resumes, cookies, application artifacts and the SQLite database stay outside version control.

**Why:** the system handles highly personal job-search data. A portfolio repository should expose architecture and code, not candidate records.

## 8. Modular monolith over microservices

**Decision:** keep one Python application with explicit module boundaries.

**Why:** the MVP has one primary user and local execution. Microservices would add deployment, networking and observability overhead without improving the core product problem.

## 9. Uncertainty is preserved

**Decision:** `eligible`, `likely`, `uncertain` and `ineligible` are separate outcomes; low-confidence entity or route cases go to review.

**Why:** false-negative filtering is costly. It is better to review a borderline role than silently discard a potentially viable opportunity.
