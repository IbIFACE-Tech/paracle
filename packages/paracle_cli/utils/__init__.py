"""Paracle CLI Utilities.

This module provides utility functions for the CLI:
- API client for communicating with the Paracle API
- Logging helpers for action and decision logging
"""

from paracle_cli.utils.api_client import (
    DEFAULT_API_URL,
    DEFAULT_TIMEOUT,
    APIClient,
    log_action_via_api,
    log_decision_via_api,
)

__all__ = [
    "APIClient",
    "DEFAULT_API_URL",
    "DEFAULT_TIMEOUT",
    "log_action_via_api",
    "log_decision_via_api",
]
