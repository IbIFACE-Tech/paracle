"""Audit event models and types.

This module defines the core audit event data structures used for
compliance logging and audit trail management.
"""

import hashlib
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Agent events
    AGENT_ACTION = "agent.action"
    """Agent performed an action."""

    AGENT_CREATED = "agent.created"
    """Agent was created."""

    AGENT_MODIFIED = "agent.modified"
    """Agent configuration was modified."""

    AGENT_DELETED = "agent.deleted"
    """Agent was deleted."""

    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    """Workflow execution started."""

    WORKFLOW_COMPLETED = "workflow.completed"
    """Workflow execution completed."""

    WORKFLOW_FAILED = "workflow.failed"
    """Workflow execution failed."""

    WORKFLOW_STEP = "workflow.step"
    """Workflow step executed."""

    # Policy events
    POLICY_EVALUATED = "policy.evaluated"
    """Policy was evaluated."""

    POLICY_VIOLATED = "policy.violated"
    """Policy violation occurred."""

    POLICY_CREATED = "policy.created"
    """Policy was created."""

    POLICY_MODIFIED = "policy.modified"
    """Policy was modified."""

    # Approval events
    APPROVAL_REQUESTED = "approval.requested"
    """Approval was requested."""

    APPROVAL_GRANTED = "approval.granted"
    """Approval was granted."""

    APPROVAL_DENIED = "approval.denied"
    """Approval was denied."""

    APPROVAL_ESCALATED = "approval.escalated"
    """Approval was escalated."""

    # Authentication events
    AUTH_LOGIN = "auth.login"
    """User logged in."""

    AUTH_LOGOUT = "auth.logout"
    """User logged out."""

    AUTH_FAILED = "auth.failed"
    """Authentication failed."""

    # Configuration events
    CONFIG_CHANGED = "config.changed"
    """Configuration was changed."""

    SECRET_ACCESSED = "secret.accessed"
    """Secret was accessed."""

    # Risk events
    RISK_ASSESSED = "risk.assessed"
    """Risk assessment performed."""

    RISK_THRESHOLD = "risk.threshold"
    """Risk threshold crossed."""

    # System events
    SYSTEM_START = "system.start"
    """System started."""

    SYSTEM_STOP = "system.stop"
    """System stopped."""

    SYSTEM_ERROR = "system.error"
    """System error occurred."""


class AuditOutcome(str, Enum):
    """Outcome of an audited action."""

    SUCCESS = "success"
    """Action completed successfully."""

    FAILURE = "failure"
    """Action failed."""

    DENIED = "denied"
    """Action was denied by policy."""

    PENDING = "pending"
    """Action is pending approval."""

    CANCELLED = "cancelled"
    """Action was cancelled."""

    ERROR = "error"
    """An error occurred."""


class AuditEvent(BaseModel):
    """An audit event record.

    Audit events capture all significant actions in the system
    for compliance and forensic purposes.
    """

    model_config = ConfigDict(frozen=True)

    # Identification
    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique event identifier",
    )
    event_type: AuditEventType = Field(
        ...,
        description="Type of audit event",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Event timestamp (UTC)",
    )

    # Actor information
    actor: str = Field(
        ...,
        description="Actor who performed the action (agent name, user ID)",
    )
    actor_type: str = Field(
        default="agent",
        description="Type of actor (agent, user, system)",
    )

    # Action details
    action: str = Field(
        ...,
        description="Action that was performed",
    )
    target: str | None = Field(
        default=None,
        description="Target resource of the action",
    )
    outcome: AuditOutcome = Field(
        default=AuditOutcome.SUCCESS,
        description="Outcome of the action",
    )

    # Risk and policy
    risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Risk score for the action",
    )
    risk_level: str | None = Field(
        default=None,
        description="Risk level (low, medium, high, critical)",
    )
    policy_id: str | None = Field(
        default=None,
        description="ID of policy that applied (if any)",
    )
    policy_result: str | None = Field(
        default=None,
        description="Policy evaluation result",
    )

    # Context
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional event context",
    )
    correlation_id: str | None = Field(
        default=None,
        description="Correlation ID for related events",
    )
    session_id: str | None = Field(
        default=None,
        description="Session ID",
    )

    # Integrity
    previous_hash: str | None = Field(
        default=None,
        description="Hash of the previous event (for chain integrity)",
    )
    event_hash: str | None = Field(
        default=None,
        description="Hash of this event",
    )

    # ISO 42001 fields
    iso_control: str | None = Field(
        default=None,
        description="Related ISO 42001 control",
    )
    data_classification: str | None = Field(
        default=None,
        description="Data classification level",
    )

    def compute_hash(self) -> str:
        """Compute the hash of this event for integrity verification.

        Returns:
            SHA-256 hash of the event data.
        """
        # Create canonical representation for hashing
        hash_data = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "actor_type": self.actor_type,
            "action": self.action,
            "target": self.target,
            "outcome": self.outcome.value,
            "risk_score": self.risk_score,
            "policy_id": self.policy_id,
            "previous_hash": self.previous_hash,
        }

        # Create deterministic JSON
        json_str = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def with_hash(self, previous_hash: str | None = None) -> "AuditEvent":
        """Create a copy of this event with computed hash.

        Args:
            previous_hash: Hash of the previous event in the chain.

        Returns:
            New event with hash fields populated.
        """
        # First create event with previous_hash
        event_with_prev = AuditEvent(
            event_id=self.event_id,
            event_type=self.event_type,
            timestamp=self.timestamp,
            actor=self.actor,
            actor_type=self.actor_type,
            action=self.action,
            target=self.target,
            outcome=self.outcome,
            risk_score=self.risk_score,
            risk_level=self.risk_level,
            policy_id=self.policy_id,
            policy_result=self.policy_result,
            context=self.context,
            correlation_id=self.correlation_id,
            session_id=self.session_id,
            previous_hash=previous_hash,
            event_hash=None,
            iso_control=self.iso_control,
            data_classification=self.data_classification,
        )

        # Then compute hash
        computed_hash = event_with_prev.compute_hash()

        # Return event with hash
        return AuditEvent(
            event_id=self.event_id,
            event_type=self.event_type,
            timestamp=self.timestamp,
            actor=self.actor,
            actor_type=self.actor_type,
            action=self.action,
            target=self.target,
            outcome=self.outcome,
            risk_score=self.risk_score,
            risk_level=self.risk_level,
            policy_id=self.policy_id,
            policy_result=self.policy_result,
            context=self.context,
            correlation_id=self.correlation_id,
            session_id=self.session_id,
            previous_hash=previous_hash,
            event_hash=computed_hash,
            iso_control=self.iso_control,
            data_classification=self.data_classification,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert event to a dictionary.

        Returns:
            Dictionary representation of the event.
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "actor_type": self.actor_type,
            "action": self.action,
            "target": self.target,
            "outcome": self.outcome.value,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "policy_id": self.policy_id,
            "policy_result": self.policy_result,
            "context": self.context,
            "correlation_id": self.correlation_id,
            "session_id": self.session_id,
            "previous_hash": self.previous_hash,
            "event_hash": self.event_hash,
            "iso_control": self.iso_control,
            "data_classification": self.data_classification,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary with event data.

        Returns:
            AuditEvent instance.
        """
        return cls(
            event_id=data["event_id"],
            event_type=AuditEventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            actor=data["actor"],
            actor_type=data.get("actor_type", "agent"),
            action=data["action"],
            target=data.get("target"),
            outcome=AuditOutcome(data.get("outcome", "success")),
            risk_score=data.get("risk_score"),
            risk_level=data.get("risk_level"),
            policy_id=data.get("policy_id"),
            policy_result=data.get("policy_result"),
            context=data.get("context", {}),
            correlation_id=data.get("correlation_id"),
            session_id=data.get("session_id"),
            previous_hash=data.get("previous_hash"),
            event_hash=data.get("event_hash"),
            iso_control=data.get("iso_control"),
            data_classification=data.get("data_classification"),
        )
