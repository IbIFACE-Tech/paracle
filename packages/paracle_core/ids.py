"""ID generation utilities for Paracle.

Provides ULID (Universally Unique Lexicographically Sortable Identifier)
generation for consistent, sortable unique identifiers.
"""

import time
import uuid
from datetime import datetime


def generate_ulid() -> str:
    """Generate a ULID-like identifier.

    Returns a 26-character string that is:
    - Lexicographically sortable by creation time
    - Globally unique
    - URL-safe

    Format: TTTTTTTTTT-RRRRRRRRRRRRRRRR
    - T: Timestamp component (base32, 10 chars)
    - R: Random component (16 chars)

    Returns:
        A unique identifier string.

    Example:
        >>> ulid = generate_ulid()
        >>> len(ulid)
        26
    """
    # Get timestamp in milliseconds
    timestamp_ms = int(time.time() * 1000)

    # Encode timestamp to base32 (10 chars)
    timestamp_chars = _encode_base32(timestamp_ms, 10)

    # Generate random component (16 chars)
    random_part = uuid.uuid4().hex[:16]

    return f"{timestamp_chars}{random_part}"


def generate_short_id() -> str:
    """Generate a short unique identifier.

    Returns an 8-character hex string suitable for display.

    Returns:
        An 8-character hex string.
    """
    return uuid.uuid4().hex[:8]


def generate_correlation_id() -> str:
    """Generate a correlation ID for tracing.

    Returns a 32-character hex string for request tracing.

    Returns:
        A 32-character correlation ID.
    """
    return uuid.uuid4().hex


def generate_session_id() -> str:
    """Generate a session identifier.

    Returns a UUID4 string for session tracking.

    Returns:
        A UUID4 string.
    """
    return str(uuid.uuid4())


def ulid_to_timestamp(ulid: str) -> datetime:
    """Extract timestamp from a ULID.

    Args:
        ulid: A ULID string (26 characters).

    Returns:
        The datetime when the ULID was created.

    Raises:
        ValueError: If the ULID format is invalid.
    """
    if len(ulid) < 10:
        raise ValueError(f"Invalid ULID format: {ulid}")

    timestamp_ms = _decode_base32(ulid[:10])
    return datetime.fromtimestamp(timestamp_ms / 1000)


# Base32 encoding alphabet (Crockford's Base32)
_CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_CROCKFORD_DECODE = {c: i for i, c in enumerate(_CROCKFORD_ALPHABET)}


def _encode_base32(value: int, length: int) -> str:
    """Encode an integer to Crockford's Base32."""
    result = []
    for _ in range(length):
        result.append(_CROCKFORD_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(result))


def _decode_base32(encoded: str) -> int:
    """Decode Crockford's Base32 to integer."""
    value = 0
    for char in encoded.upper():
        value = value * 32 + _CROCKFORD_DECODE.get(char, 0)
    return value
