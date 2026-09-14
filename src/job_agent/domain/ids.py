import secrets
import time

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _encode_base32(value: int, length: int) -> str:
    characters = ["0"] * length
    for index in range(length - 1, -1, -1):
        value, remainder = divmod(value, 32)
        characters[index] = _CROCKFORD[remainder]
    if value:
        raise ValueError("value does not fit requested base32 length")
    return "".join(characters)


def new_ulid() -> str:
    """Return a locally generated, lexicographically sortable ULID."""

    timestamp_ms = time.time_ns() // 1_000_000
    if timestamp_ms >= 2**48:
        raise OverflowError("ULID timestamp exceeds 48 bits")
    randomness = secrets.randbits(80)
    return _encode_base32(timestamp_ms, 10) + _encode_base32(randomness, 16)


def new_id(prefix: str) -> str:
    """Return a readable identifier whose suffix is a valid ULID."""

    normalized_prefix = prefix.strip().lower()
    if not normalized_prefix or not normalized_prefix.replace("_", "").isalnum():
        raise ValueError("prefix must contain only letters, numbers, and underscores")
    return f"{normalized_prefix}_{new_ulid()}"
