"""Governance package exceptions.

Error codes: PARACLE-GOV-XXX
- PARACLE-GOV-001: Policy not found
- PARACLE-GOV-002: Policy violation
- PARACLE-GOV-003: Policy evaluation error
- PARACLE-GOV-004: Risk threshold exceeded
- PARACLE-GOV-005: Invalid policy configuration
- PARACLE-GOV-006: Policy conflict detected
"""

from typing import Any


class GovernanceError(Exception):
    """Base exception for governance operations.

    Attributes:
        code: Error code (PARACLE-GOV-XXX)
        message: Human-readable error message
        context: Additional context data
    """

    code: str = "PARACLE-GOV-000"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.context = context or {}

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class PolicyNotFoundError(GovernanceError):
    """Raised when a policy cannot be found."""

    code: str = "PARACLE-GOV-001"

    def __init__(self, policy_id: str):
        super().__init__(
            f"Policy not found: {policy_id}",
            context={"policy_id": policy_id},
        )
        self.policy_id = policy_id


class PolicyViolationError(GovernanceError):
    """Raised when an action violates a policy."""

    code: str = "PARACLE-GOV-002"

    def __init__(
        self,
        policy_id: str,
        action: str,
        reason: str,
        *,
        agent: str | None = None,
        risk_score: float | None = None,
    ):
        message = f"Policy violation: {policy_id} - {reason}"
        super().__init__(
            message,
            context={
                "policy_id": policy_id,
                "action": action,
                "reason": reason,
                "agent": agent,
                "risk_score": risk_score,
            },
        )
        self.policy_id = policy_id
        self.action = action
        self.reason = reason
        self.agent = agent
        self.risk_score = risk_score


class PolicyEvaluationError(GovernanceError):
    """Raised when policy evaluation fails."""

    code: str = "PARACLE-GOV-003"

    def __init__(self, message: str, *, policy_id: str | None = None):
        super().__init__(
            message,
            context={"policy_id": policy_id},
        )
        self.policy_id = policy_id


class RiskThresholdExceededError(GovernanceError):
    """Raised when an action exceeds the risk threshold."""

    code: str = "PARACLE-GOV-004"

    def __init__(
        self,
        action: str,
        risk_score: float,
        threshold: float,
        *,
        agent: str | None = None,
        risk_level: str | None = None,
    ):
        message = (
            f"Risk threshold exceeded for action '{action}': "
            f"score {risk_score:.1f} > threshold {threshold:.1f}"
        )
        super().__init__(
            message,
            context={
                "action": action,
                "risk_score": risk_score,
                "threshold": threshold,
                "agent": agent,
                "risk_level": risk_level,
            },
        )
        self.action = action
        self.risk_score = risk_score
        self.threshold = threshold
        self.agent = agent
        self.risk_level = risk_level


class InvalidPolicyConfigError(GovernanceError):
    """Raised when policy configuration is invalid."""

    code: str = "PARACLE-GOV-005"

    def __init__(self, message: str, *, policy_id: str | None = None):
        super().__init__(
            message,
            context={"policy_id": policy_id},
        )
        self.policy_id = policy_id


class PolicyConflictError(GovernanceError):
    """Raised when conflicting policies are detected."""

    code: str = "PARACLE-GOV-006"

    def __init__(
        self,
        policy_ids: list[str],
        action: str,
        *,
        resolution: str | None = None,
    ):
        message = f"Conflicting policies for action '{action}': {', '.join(policy_ids)}"
        super().__init__(
            message,
            context={
                "policy_ids": policy_ids,
                "action": action,
                "resolution": resolution,
            },
        )
        self.policy_ids = policy_ids
        self.action = action
        self.resolution = resolution
