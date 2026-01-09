"""Policy models and types for governance.

This module defines the core policy data structures used by the governance
engine to evaluate and enforce policies on agent actions.
"""

import re
import signal
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Maximum regex pattern length to prevent DoS
MAX_REGEX_PATTERN_LENGTH = 1000

# Timeout for regex matching (seconds)
REGEX_TIMEOUT_SECONDS = 1

# Characters that indicate potentially dangerous regex patterns
DANGEROUS_REGEX_PATTERNS = [
    r"(.+)+",  # Nested quantifiers
    r"(.*)*",
    r"(.+)*",
    r"(.*)+",
    r"([^x]+)+",  # Nested negation with quantifier
]


class RegexTimeoutError(Exception):
    """Raised when regex matching exceeds timeout."""

    pass


def _timeout_handler(signum: int, frame: Any) -> None:
    """Signal handler for regex timeout."""
    raise RegexTimeoutError("Regex matching timed out")


@contextmanager
def _regex_timeout(seconds: int) -> Generator[None, None, None]:
    """Context manager for regex timeout (Unix only).

    On Windows, this is a no-op but the pattern validation still applies.
    """
    # signal.SIGALRM is not available on Windows
    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows: no timeout support, rely on pattern validation
        yield


def validate_regex_pattern(pattern: str) -> tuple[bool, str]:
    """Validate a regex pattern for safety.

    Checks for:
    - Pattern length limits
    - Syntactic validity
    - Known dangerous patterns (ReDoS)

    Args:
        pattern: The regex pattern to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Check length
    if len(pattern) > MAX_REGEX_PATTERN_LENGTH:
        return False, f"Pattern exceeds maximum length of {MAX_REGEX_PATTERN_LENGTH}"

    # Check for dangerous patterns
    for dangerous in DANGEROUS_REGEX_PATTERNS:
        if dangerous in pattern:
            return (
                False,
                f"Pattern contains potentially dangerous construct: {dangerous}",
            )

    # Try to compile
    try:
        re.compile(pattern)
    except re.error as e:
        return False, f"Invalid regex pattern: {e}"

    return True, ""


def safe_regex_match(pattern: str, text: str) -> bool | None:
    """Safely match a regex pattern with timeout protection.

    Args:
        pattern: The regex pattern to match.
        text: The text to match against.

    Returns:
        True if matches, False if no match, None if error/timeout.
    """
    # Validate pattern first
    is_valid, error = validate_regex_pattern(pattern)
    if not is_valid:
        return None

    try:
        with _regex_timeout(REGEX_TIMEOUT_SECONDS):
            return bool(re.match(pattern, text))
    except RegexTimeoutError:
        return None
    except re.error:
        return None


class PolicyType(str, Enum):
    """Types of governance policies."""

    ALLOW = "allow"
    """Permit specific actions."""

    DENY = "deny"
    """Block specific actions."""

    REQUIRE_APPROVAL = "require_approval"
    """Require human approval before proceeding."""

    AUDIT = "audit"
    """Log action for compliance but allow execution."""

    RATE_LIMIT = "rate_limit"
    """Limit the rate of specific actions."""

    ESCALATE = "escalate"
    """Escalate to higher authority for decision."""


class PolicyAction(str, Enum):
    """Actions that can be governed by policies."""

    # File operations
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    EXECUTE_FILE = "execute_file"

    # Data operations
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    DELETE_DATA = "delete_data"
    EXPORT_DATA = "export_data"

    # Network operations
    HTTP_REQUEST = "http_request"
    EXTERNAL_API = "external_api"

    # Shell operations
    EXECUTE_COMMAND = "execute_command"
    INSTALL_PACKAGE = "install_package"

    # Agent operations
    CREATE_AGENT = "create_agent"
    MODIFY_AGENT = "modify_agent"
    DELETE_AGENT = "delete_agent"
    EXECUTE_AGENT = "execute_agent"

    # Workflow operations
    CREATE_WORKFLOW = "create_workflow"
    EXECUTE_WORKFLOW = "execute_workflow"
    MODIFY_WORKFLOW = "modify_workflow"

    # System operations
    MODIFY_CONFIG = "modify_config"
    ACCESS_SECRETS = "access_secrets"

    # Catch-all
    ANY = "*"


class PolicyCondition(BaseModel):
    """A condition that must be met for a policy to apply.

    Conditions can check agent properties, action context, time of day,
    data sensitivity, and other contextual factors.
    """

    model_config = ConfigDict(frozen=True)

    field: str = Field(
        ...,
        description="The field to check (e.g., 'agent.name', 'context.data_type')",
    )
    operator: str = Field(
        default="eq",
        description="Comparison operator: eq, ne, in, not_in, contains, matches, gt, lt, gte, lte",
    )
    value: Any = Field(
        ...,
        description="The value to compare against",
    )

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate this condition against the given context.

        Args:
            context: The evaluation context containing field values.

        Returns:
            True if the condition is met, False otherwise.
        """
        # Get the field value from context using dot notation
        field_value = self._get_nested_value(context, self.field)

        if field_value is None:
            return self.operator == "ne"

        if self.operator == "eq":
            return field_value == self.value
        elif self.operator == "ne":
            return field_value != self.value
        elif self.operator == "in":
            return field_value in self.value
        elif self.operator == "not_in":
            return field_value not in self.value
        elif self.operator == "contains":
            return self.value in field_value
        elif self.operator == "matches":
            result = safe_regex_match(self.value, str(field_value))
            # If regex validation fails or times out, condition is not met
            return result if result is not None else False
        elif self.operator == "gt":
            return field_value > self.value
        elif self.operator == "lt":
            return field_value < self.value
        elif self.operator == "gte":
            return field_value >= self.value
        elif self.operator == "lte":
            return field_value <= self.value

        return False

    def _get_nested_value(self, data: dict[str, Any], path: str) -> Any:
        """Get a nested value from a dictionary using dot notation."""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
            if value is None:
                return None
        return value


class Policy(BaseModel):
    """A governance policy that controls agent actions.

    Policies define rules that govern what actions agents can perform,
    under what conditions, and what happens when policies are triggered.
    """

    model_config = ConfigDict(frozen=False)

    id: str = Field(
        ...,
        description="Unique policy identifier",
    )
    name: str = Field(
        ...,
        description="Human-readable policy name",
    )
    description: str = Field(
        default="",
        description="Detailed policy description",
    )
    type: PolicyType = Field(
        ...,
        description="Policy type (allow, deny, require_approval, etc.)",
    )
    actions: list[PolicyAction | str] = Field(
        default_factory=list,
        description="Actions this policy applies to",
    )
    conditions: list[PolicyCondition] = Field(
        default_factory=list,
        description="Conditions that must be met for policy to apply",
    )
    priority: int = Field(
        default=100,
        ge=0,
        le=1000,
        description="Policy priority (higher = evaluated first)",
    )
    enabled: bool = Field(
        default=True,
        description="Whether the policy is active",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional policy metadata",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Policy creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Policy last update timestamp",
    )

    # ISO 42001 specific fields
    iso_control: str | None = Field(
        default=None,
        description="ISO 42001 control reference (e.g., '6.1', '8.2')",
    )
    risk_level: str | None = Field(
        default=None,
        description="Associated risk level (low, medium, high, critical)",
    )
    approval_required_by: list[str] = Field(
        default_factory=list,
        description="Roles required for approval (if type=require_approval)",
    )

    def matches_action(self, action: str | PolicyAction) -> bool:
        """Check if this policy applies to the given action.

        Args:
            action: The action to check.

        Returns:
            True if this policy applies to the action.
        """
        if not self.enabled:
            return False

        action_str = action.value if isinstance(action, PolicyAction) else action

        for policy_action in self.actions:
            policy_action_str = (
                policy_action.value
                if isinstance(policy_action, PolicyAction)
                else policy_action
            )
            if policy_action_str == "*" or policy_action_str == action_str:
                return True

        return False

    def evaluate_conditions(self, context: dict[str, Any]) -> bool:
        """Evaluate all conditions against the given context.

        Args:
            context: The evaluation context.

        Returns:
            True if all conditions are met (or no conditions exist).
        """
        if not self.conditions:
            return True

        return all(condition.evaluate(context) for condition in self.conditions)


class PolicyResult(BaseModel):
    """Result of policy evaluation.

    Contains the evaluation outcome and details about which policies
    were triggered and why.
    """

    model_config = ConfigDict(frozen=True)

    allowed: bool = Field(
        ...,
        description="Whether the action is allowed",
    )
    policy_id: str | None = Field(
        default=None,
        description="ID of the policy that determined the outcome",
    )
    policy_type: PolicyType | None = Field(
        default=None,
        description="Type of the determining policy",
    )
    reason: str = Field(
        default="",
        description="Human-readable explanation of the decision",
    )
    requires_approval: bool = Field(
        default=False,
        description="Whether human approval is required",
    )
    approval_roles: list[str] = Field(
        default_factory=list,
        description="Roles that can approve (if approval required)",
    )
    risk_score: float | None = Field(
        default=None,
        description="Calculated risk score for the action",
    )
    audit_required: bool = Field(
        default=False,
        description="Whether the action should be audited",
    )
    evaluated_policies: list[str] = Field(
        default_factory=list,
        description="List of policy IDs that were evaluated",
    )
    evaluation_time_ms: float = Field(
        default=0.0,
        description="Time taken to evaluate policies (milliseconds)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional result metadata",
    )


# Pre-defined policy templates
DEFAULT_POLICIES = {
    "deny_delete_system_files": Policy(
        id="deny_delete_system_files",
        name="Deny System File Deletion",
        description="Prevent agents from deleting system files",
        type=PolicyType.DENY,
        actions=[PolicyAction.DELETE_FILE],
        conditions=[
            PolicyCondition(
                field="context.path",
                operator="matches",
                value=r"^/(etc|usr|bin|sbin|var/log).*",
            )
        ],
        priority=900,
        iso_control="8.2",
        risk_level="critical",
    ),
    "require_approval_external_api": Policy(
        id="require_approval_external_api",
        name="Require Approval for External APIs",
        description="Require human approval before calling external APIs",
        type=PolicyType.REQUIRE_APPROVAL,
        actions=[PolicyAction.EXTERNAL_API],
        priority=800,
        iso_control="6.2",
        risk_level="high",
        approval_required_by=["admin", "security"],
    ),
    "audit_all_file_writes": Policy(
        id="audit_all_file_writes",
        name="Audit All File Writes",
        description="Log all file write operations for compliance",
        type=PolicyType.AUDIT,
        actions=[PolicyAction.WRITE_FILE],
        priority=100,
        iso_control="9.1",
        risk_level="medium",
    ),
    "deny_secret_access_untrusted": Policy(
        id="deny_secret_access_untrusted",
        name="Deny Secret Access for Untrusted Agents",
        description="Prevent untrusted agents from accessing secrets",
        type=PolicyType.DENY,
        actions=[PolicyAction.ACCESS_SECRETS],
        conditions=[
            PolicyCondition(
                field="agent.trust_level",
                operator="in",
                value=["untrusted", "low"],
            )
        ],
        priority=950,
        iso_control="7.2",
        risk_level="critical",
    ),
}
