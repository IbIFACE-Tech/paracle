"""API Client utilities for CLI.

Provides HTTP client helpers for calling the Paracle API.
"""

from typing import Any

import httpx

DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 5.0  # seconds


class APIClient:
    """HTTP client for Paracle API."""

    def __init__(
        self, base_url: str = DEFAULT_API_URL, timeout: float = DEFAULT_TIMEOUT
    ):
        """Initialize API client.

        Args:
            base_url: Base URL of the Paracle API.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def post(
        self, endpoint: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """POST request to API.

        Args:
            endpoint: API endpoint (e.g., "/logs/action").
            json: JSON payload.

        Returns:
            Response JSON, or None if request failed.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}{endpoint}",
                    json=json,
                )
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException):
            return None

    def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """GET request to API.

        Args:
            endpoint: API endpoint (e.g., "/logs/recent").
            params: Query parameters.

        Returns:
            Response JSON, or None if request failed.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                )
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException):
            return None


def log_action_via_api(
    action: str,
    description: str,
    agent: str = "SystemAgent",
    details: dict | None = None,
) -> bool:
    """Log an action via the API.

    Args:
        action: Action type (e.g., "SYNC", "VALIDATION").
        description: Description of the action.
        agent: Agent performing the action.
        details: Optional additional details.

    Returns:
        True if logged successfully, False otherwise.
    """
    client = APIClient()

    payload = {
        "action": action,
        "description": description,
        "agent": agent,
    }

    if details:
        payload["details"] = details

    response = client.post("/logs/action", json=payload)

    if response is None:
        # API not available, try fallback to direct logging
        try:
            from paracle_core.parac.logger import ActionType, AgentType
            from paracle_core.parac.logger import log_action as direct_log

            # Convert strings to enums
            action_type = ActionType(action)
            agent_type = AgentType(agent)

            entry = direct_log(action_type, description, agent_type, details)
            return entry is not None
        except Exception:
            # Even fallback failed, silently fail
            return False

    return response.get("success", False)


def log_decision_via_api(
    agent: str,
    decision: str,
    rationale: str,
    impact: str,
) -> bool:
    """Log a decision via the API.

    Args:
        agent: Agent making the decision.
        decision: What was decided.
        rationale: Why this decision was made.
        impact: Expected impact.

    Returns:
        True if logged successfully, False otherwise.
    """
    client = APIClient()

    payload = {
        "agent": agent,
        "decision": decision,
        "rationale": rationale,
        "impact": impact,
    }

    response = client.post("/logs/decision", json=payload)

    if response is None:
        # API not available, try fallback
        try:
            from paracle_core.parac.logger import AgentType, get_logger

            agent_type = AgentType(agent)
            logger = get_logger()
            logger.log_decision(agent_type, decision, rationale, impact)
            return True
        except Exception:
            return False

    return response.get("success", False)
