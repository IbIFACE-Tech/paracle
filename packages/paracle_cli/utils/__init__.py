"""Paracle CLI Utilities.

This module provides utility functions for the CLI:
- API client for communicating with the Paracle API
- Logging helpers for action and decision logging
- Common helper functions for CLI commands
"""

from paracle_cli.utils.api_client import (
    DEFAULT_API_URL,
    DEFAULT_TIMEOUT,
    APIClient,
    log_action_via_api,
    log_decision_via_api,
)
from paracle_cli.utils.helpers import (
    get_api_client,
    get_parac_root_or_exit,
    get_skills_dir,
    get_system_skills_dir,
)

__all__ = [
    # API client
    "APIClient",
    "DEFAULT_API_URL",
    "DEFAULT_TIMEOUT",
    "log_action_via_api",
    "log_decision_via_api",
    # Helper functions
    "get_parac_root_or_exit",
    "get_api_client",
    "get_skills_dir",
    "get_system_skills_dir",
]
