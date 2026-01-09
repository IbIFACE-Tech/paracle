"""Audit logging for ISO 42001 compliance.

Provides audit trail capabilities for:
- AI decision tracking
- Access logging
- Data modification tracking
- Compliance evidence
- Approval workflows

ISO 42001 Requirements Addressed:
- 6.1.3: Risk treatment audit trail
- 8.2: Operational planning evidence
- 9.1: Monitoring and measurement records
- 9.2: Internal audit evidence
- 10.1: Nonconformity and corrective action tracking
"""

import hashlib
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from paracle_core.logging.context import get_correlation_id
from paracle_core.logging.handlers import AuditFileHandler


class AuditCategory(str, Enum):
    """Categories of audit events for ISO 42001."""

    # AI System Events
    AI_DECISION = "ai.decision"  # AI-made decisions
    AI_OUTPUT = "ai.output"  # AI-generated outputs
    AI_TRAINING = "ai.training"  # Model training events

    # Agent Events
    AGENT_CREATED = "agent.created"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

    # Workflow Events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_ROLLBACK = "workflow.rollback"

    # Access Events
    ACCESS_LOGIN = "access.login"
    ACCESS_LOGOUT = "access.logout"
    ACCESS_DENIED = "access.denied"
    ACCESS_GRANTED = "access.granted"

    # Data Events
    DATA_READ = "data.read"
    DATA_WRITE = "data.write"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"

    # Configuration Events
    CONFIG_CHANGED = "config.changed"
    POLICY_CHANGED = "policy.changed"
    PERMISSION_CHANGED = "permission.changed"

    # Compliance Events
    APPROVAL_REQUESTED = "compliance.approval_requested"
    APPROVAL_GRANTED = "compliance.approval_granted"
    APPROVAL_DENIED = "compliance.approval_denied"
    RISK_ASSESSED = "compliance.risk_assessed"
    INCIDENT_REPORTED = "compliance.incident_reported"

    # System Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"


class AuditOutcome(str, Enum):
    """Outcome of an audited action."""

    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    PENDING = "pending"
    CANCELLED = "cancelled"


class AuditSeverity(str, Enum):
    """Severity level for audit events."""

    INFO = "info"  # Normal operations
    LOW = "low"  # Minor concerns
    MEDIUM = "medium"  # Moderate concerns
    HIGH = "high"  # Significant concerns
    CRITICAL = "critical"  # Security/compliance critical


class AuditEvent(BaseModel):
    """Immutable audit event for ISO 42001 compliance.

    This model captures all required information for:
    - Regulatory compliance
    - Forensic investigation
    - Security monitoring
    - Change tracking
    """

    # Event identification
    event_id: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"),
        description="Unique event identifier",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event timestamp (UTC)",
    )
    correlation_id: str | None = Field(
        default=None,
        description="Correlation ID for request tracing",
    )

    # Event classification
    category: AuditCategory = Field(
        description="Category of audit event",
    )
    action: str = Field(
        description="Specific action performed",
    )
    outcome: AuditOutcome = Field(
        default=AuditOutcome.SUCCESS,
        description="Outcome of the action",
    )
    severity: AuditSeverity = Field(
        default=AuditSeverity.INFO,
        description="Severity level",
    )

    # Actor information
    actor: str = Field(
        description="Who performed the action (user, agent, system)",
    )
    actor_type: str = Field(
        default="system",
        description="Type of actor (user, agent, service, system)",
    )
    actor_ip: str | None = Field(
        default=None,
        description="IP address of actor (if applicable)",
    )

    # Resource information
    resource: str = Field(
        description="Resource affected (e.g., agent/code-reviewer)",
    )
    resource_type: str | None = Field(
        default=None,
        description="Type of resource",
    )

    # Change details
    old_value: Any | None = Field(
        default=None,
        description="Previous value (for modifications)",
    )
    new_value: Any | None = Field(
        default=None,
        description="New value (for modifications)",
    )

    # Context and evidence
    reason: str | None = Field(
        default=None,
        description="Reason for action",
    )
    evidence: dict | None = Field(
        default=None,
        description="Supporting evidence/context",
    )

    # Compliance metadata
    policy_reference: str | None = Field(
        default=None,
        description="Reference to applicable policy",
    )
    approval_reference: str | None = Field(
        default=None,
        description="Reference to approval (if required)",
    )

    model_config = {"frozen": True}  # Immutable

    def to_log_line(self) -> str:
        """Convert to log line format.

        Returns:
            Formatted log line for file output
        """
        parts = [
            self.timestamp.isoformat(),
            f"[{self.severity.value.upper()}]",
            f"[{self.category.value}]",
            f"actor={self.actor}",
            f"resource={self.resource}",
            f"action={self.action}",
            f"outcome={self.outcome.value}",
        ]

        if self.correlation_id:
            parts.insert(2, f"[{self.correlation_id[:8]}]")

        if self.reason:
            parts.append(f'reason="{self.reason}"')

        return " ".join(parts)

    def to_json(self) -> str:
        """Convert to JSON format.

        Returns:
            JSON string representation
        """
        return self.model_dump_json()

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the event.

        Used for tamper detection and chain of custody.

        Returns:
            Hex-encoded SHA-256 hash
        """
        content = self.model_dump_json(exclude={"event_id"})
        return hashlib.sha256(content.encode()).hexdigest()


class AuditLogger:
    """Audit logger for ISO 42001 compliance.

    Features:
    - Immutable audit events
    - Multiple output targets (file, external)
    - Chain of custody support
    - Event hashing for integrity
    """

    def __init__(
        self,
        audit_dir: Path | None = None,
        include_hash: bool = True,
        external_handler: Callable[[AuditEvent], None] | None = None,
    ):
        """Initialize audit logger.

        Args:
            audit_dir: Directory for audit logs
            include_hash: Include event hash for integrity
            external_handler: Optional external handler (e.g., SIEM)
        """
        self.include_hash = include_hash
        self.external_handler = external_handler
        self._logger = logging.getLogger("paracle.audit")
        self._logger.setLevel(logging.INFO)

        # Add file handler if directory provided
        if audit_dir:
            handler = AuditFileHandler(
                log_dir=audit_dir,
                prefix="audit",
                include_checksum=include_hash,
            )
            self._logger.addHandler(handler)

    def log(self, event: AuditEvent) -> AuditEvent:
        """Log an audit event.

        Args:
            event: The audit event to log

        Returns:
            The logged event (with correlation ID if not set)
        """
        # Add correlation ID if not set
        if event.correlation_id is None:
            cid = get_correlation_id()
            if cid:
                # Create new event with correlation ID (events are immutable)
                event = event.model_copy(update={"correlation_id": cid})

        # Compute hash if enabled
        event_hash = event.compute_hash() if self.include_hash else None

        # Create log record
        log_line = event.to_log_line()
        if event_hash:
            log_line += f" hash={event_hash[:16]}"

        # Log to Python logger
        level = self._severity_to_level(event.severity)
        self._logger.log(level, log_line, extra={"audit_event": event.model_dump()})

        # Send to external handler
        if self.external_handler:
            try:
                self.external_handler(event)
            except Exception as e:
                self._logger.error(f"External audit handler failed: {e}")

        return event

    def _severity_to_level(self, severity: AuditSeverity) -> int:
        """Convert audit severity to logging level.

        Args:
            severity: Audit severity

        Returns:
            Python logging level
        """
        mapping = {
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.LOW: logging.INFO,
            AuditSeverity.MEDIUM: logging.WARNING,
            AuditSeverity.HIGH: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL,
        }
        return mapping.get(severity, logging.INFO)

    # Convenience methods for common audit events

    def log_agent_action(
        self,
        agent_name: str,
        action: str,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        **kwargs,
    ) -> AuditEvent:
        """Log an agent action.

        Args:
            agent_name: Name of the agent
            action: Action performed
            outcome: Action outcome
            **kwargs: Additional event fields
        """
        category_map = {
            "created": AuditCategory.AGENT_CREATED,
            "started": AuditCategory.AGENT_STARTED,
            "completed": AuditCategory.AGENT_COMPLETED,
            "failed": AuditCategory.AGENT_FAILED,
        }
        category = category_map.get(action.lower(), AuditCategory.AGENT_STARTED)

        event = AuditEvent(
            category=category,
            action=action,
            actor=agent_name,
            actor_type="agent",
            resource=f"agent/{agent_name}",
            resource_type="agent",
            outcome=outcome,
            **kwargs,
        )
        return self.log(event)

    def log_access(
        self,
        actor: str,
        resource: str,
        action: str,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        **kwargs,
    ) -> AuditEvent:
        """Log an access event.

        Args:
            actor: Who accessed
            resource: What was accessed
            action: Type of access (read, write, etc.)
            outcome: Access outcome
            **kwargs: Additional fields
        """
        category_map = {
            "login": AuditCategory.ACCESS_LOGIN,
            "logout": AuditCategory.ACCESS_LOGOUT,
            "denied": AuditCategory.ACCESS_DENIED,
            "granted": AuditCategory.ACCESS_GRANTED,
        }
        category = category_map.get(action.lower(), AuditCategory.ACCESS_GRANTED)

        severity = AuditSeverity.INFO
        if outcome == AuditOutcome.DENIED:
            severity = AuditSeverity.MEDIUM
            category = AuditCategory.ACCESS_DENIED

        event = AuditEvent(
            category=category,
            action=action,
            actor=actor,
            actor_type="user",
            resource=resource,
            outcome=outcome,
            severity=severity,
            **kwargs,
        )
        return self.log(event)

    def log_ai_decision(
        self,
        agent_name: str,
        decision: str,
        rationale: str,
        confidence: float | None = None,
        **kwargs,
    ) -> AuditEvent:
        """Log an AI decision (ISO 42001 requirement).

        Args:
            agent_name: Name of AI agent
            decision: The decision made
            rationale: Explanation/reasoning
            confidence: Decision confidence (0-1)
            **kwargs: Additional fields
        """
        evidence = {
            "decision": decision,
            "rationale": rationale,
        }
        if confidence is not None:
            evidence["confidence"] = confidence

        event = AuditEvent(
            category=AuditCategory.AI_DECISION,
            action="decision",
            actor=agent_name,
            actor_type="agent",
            resource=f"agent/{agent_name}",
            resource_type="ai_decision",
            reason=rationale,
            evidence=evidence,
            **kwargs,
        )
        return self.log(event)

    def log_data_access(
        self,
        actor: str,
        resource: str,
        action: str,
        data_type: str | None = None,
        **kwargs,
    ) -> AuditEvent:
        """Log data access for privacy compliance.

        Args:
            actor: Who accessed data
            resource: Data resource accessed
            action: Type of access (read, write, delete, export)
            data_type: Type of data (PII, sensitive, etc.)
            **kwargs: Additional fields
        """
        category_map = {
            "read": AuditCategory.DATA_READ,
            "write": AuditCategory.DATA_WRITE,
            "delete": AuditCategory.DATA_DELETE,
            "export": AuditCategory.DATA_EXPORT,
        }
        category = category_map.get(action.lower(), AuditCategory.DATA_READ)

        severity = AuditSeverity.INFO
        if data_type in ("pii", "sensitive", "confidential"):
            severity = AuditSeverity.MEDIUM

        event = AuditEvent(
            category=category,
            action=action,
            actor=actor,
            resource=resource,
            resource_type=data_type or "data",
            severity=severity,
            **kwargs,
        )
        return self.log(event)


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger(
    audit_dir: Path | None = None,
    **kwargs,
) -> AuditLogger:
    """Get or create the global audit logger.

    Args:
        audit_dir: Optional audit directory
        **kwargs: Additional configuration

    Returns:
        AuditLogger instance
    """
    global _audit_logger

    if _audit_logger is None:
        _audit_logger = AuditLogger(audit_dir=audit_dir, **kwargs)

    return _audit_logger


def audit_log(event: AuditEvent) -> AuditEvent:
    """Convenience function to log an audit event.

    Args:
        event: The audit event

    Returns:
        The logged event
    """
    logger = get_audit_logger()
    return logger.log(event)
