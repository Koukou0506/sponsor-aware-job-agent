from enum import StrEnum


class Region(StrEnum):
    UK = "UK"
    NL = "NL"
    DE = "DE"
    IE = "IE"
    HK = "HK"


class RoleTrack(StrEnum):
    TECHNICAL = "technical"
    TECHNICAL_BUSINESS = "technical_business"
    MIXED = "mixed"
    IRRELEVANT = "irrelevant"


class RouteOwnership(StrEnum):
    CANDIDATE_OWNED = "candidate_owned"
    EMPLOYER_SPONSORED = "employer_sponsored"
    JOB_SUPPORTED = "job_supported"


class WorkAuthorizationStatus(StrEnum):
    ELIGIBLE = "eligible"
    LIKELY = "likely"
    UNCERTAIN = "uncertain"
    INELIGIBLE = "ineligible"


class EvidenceLevel(StrEnum):
    A = "A"
    B = "B"
    C = "C"


class ValidationStatus(StrEnum):
    VERIFIED = "verified"
    NEEDS_REVIEW = "needs_review"
    UNSUPPORTED = "unsupported"
    CONFLICTING = "conflicting"


class JobStatus(StrEnum):
    DISCOVERED = "discovered"
    FILTERED_OUT = "filtered_out"
    SHORTLISTED = "shortlisted"
    MATERIALS_GENERATED = "materials_generated"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    AUTOFILL_STARTED = "autofill_started"
    READY_TO_SUBMIT = "ready_to_submit"
    SUBMITTED = "submitted"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
