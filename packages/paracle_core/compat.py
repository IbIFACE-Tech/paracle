"""Compatibility helpers for different Python versions."""

import sys
from datetime import datetime, timedelta, timezone

# Python 3.11+ has datetime.UTC, older versions need timezone.utc
if sys.version_info >= (3, 11):
    from datetime import UTC
else:
    UTC = timezone.utc

__all__ = ["UTC", "datetime", "timedelta", "timezone"]
