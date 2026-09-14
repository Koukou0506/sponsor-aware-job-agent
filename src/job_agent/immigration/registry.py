import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from job_agent.immigration.models import RegistryRecord


def load_registry(path: Path) -> tuple[list[RegistryRecord], str]:
    raw = path.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    if path.suffix.casefold() == ".json":
        document = json.loads(raw)
        metadata = document.get("metadata", {})
        rows = document.get("records", [])
    elif path.suffix.casefold() == ".csv":
        rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
        metadata = rows[0] if rows else {}
    else:
        raise ValueError("registry must be JSON or CSV")
    version = metadata.get("ruleset_version") or metadata.get("version")
    source = metadata.get("source")
    if not version or not source:
        raise ValueError("registry file requires version/ruleset_version and source")
    retrieved_at = datetime.now(UTC)
    records: list[RegistryRecord] = []
    for row in rows:
        aliases_value = row.get("aliases", ())
        if isinstance(aliases_value, str):
            aliases = tuple(
                alias.strip()
                for alias in aliases_value.split("|")
                if alias.strip()
            )
        else:
            aliases = tuple(aliases_value)
        records.append(
            RegistryRecord.model_validate(
                {
                    **row,
                    "ruleset_version": row.get("ruleset_version") or version,
                    "source": row.get("source") or source,
                    "retrieved_at": row.get("retrieved_at") or retrieved_at,
                    "aliases": aliases,
                }
            )
        )
    return records, checksum
