import re

from rapidfuzz.fuzz import ratio

from job_agent.immigration.models import CompanyEntityMatch, RegistryRecord

_SUFFIXES = {"limited", "ltd", "plc", "gmbh", "bv", "b", "v", "inc", "llc", "company", "co"}


def _normalise_name(name: str) -> str:
    tokens = re.sub(r"[^a-z0-9 ]+", " ", name.casefold()).split()
    return " ".join(token for token in tokens if token not in _SUFFIXES)


def resolve_entity(company_name: str, domain: str | None, country: str, records: list[RegistryRecord]) -> CompanyEntityMatch:
    candidates = [record for record in records if record.country == country and record.status.casefold() == "active"]
    normalised = _normalise_name(company_name)
    for record in candidates:
        if company_name.casefold() == record.legal_name.casefold():
            return CompanyEntityMatch(registry_record_id=record.registry_record_id, match_type="exact", confidence=1.0, verified=True, requires_review=False)
        if normalised == _normalise_name(record.legal_name):
            return CompanyEntityMatch(registry_record_id=record.registry_record_id, match_type="exact_normalized", confidence=0.98, verified=True, requires_review=False)
        if domain and record.canonical_domain and domain.casefold().removeprefix("www.") == record.canonical_domain.casefold().removeprefix("www."):
            return CompanyEntityMatch(registry_record_id=record.registry_record_id, match_type="domain", confidence=0.97, verified=True, requires_review=False)
        if any(normalised == _normalise_name(alias) for alias in record.aliases):
            return CompanyEntityMatch(registry_record_id=record.registry_record_id, match_type="verified_alias", confidence=0.96, verified=True, requires_review=False)
    if candidates:
        best = max(candidates, key=lambda record: ratio(normalised, _normalise_name(record.legal_name)))
        score = ratio(normalised, _normalise_name(best.legal_name)) / 100
        if score >= 0.75:
            return CompanyEntityMatch(registry_record_id=best.registry_record_id, match_type="fuzzy", confidence=score, verified=False, requires_review=True)
    return CompanyEntityMatch(registry_record_id=None, match_type="none", confidence=0.0, verified=False, requires_review=True)
