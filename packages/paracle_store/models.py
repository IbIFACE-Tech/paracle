"""SQLAlchemy models for persistent storage.

This module defines the database schema for runtime data:
- Agents: Agent instances and their status
- Workflows: Workflow definitions
- Executions: Workflow execution history
- Events: Event log for event sourcing
- Audit: Audit trail for ISO 42001 compliance
- Sessions: Work session data

Usage:
    from paracle_store.models import AgentModel, WorkflowModel

    # Create agent record
    agent = AgentModel(
        id="agent_123",
        name="code-reviewer",
        spec_hash="abc123",
    )
"""

from __future__ import annotations

from paracle_core.compat import UTC, datetime
from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from paracle_store.database import Base


class AgentModel(Base):
    """Agent runtime instance.

    Stores agent instances and their current status.
    Agent specifications are stored in YAML files.
    """

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    spec_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="Hash of agent spec for change detection"
    )
    status: Mapped[str] = mapped_column(
        String(32), default="active", comment="active, paused, archived"
    )
    parent_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AgentModel(id={self.id!r}, name={self.name!r}, status={self.status!r})>"
        )


class WorkflowModel(Base):
    """Workflow definition.

    Stores workflow definitions for quick lookup.
    Full definitions are in YAML files.
    """

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    spec_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    step_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<WorkflowModel(id={self.id!r}, name={self.name!r})>"


class ExecutionModel(Base):
    """Workflow execution record.

    Tracks workflow execution history including status,
    timing, results, and errors.
    """

    __tablename__ = "executions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    workflow_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        comment="pending, running, completed, failed, cancelled",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    inputs_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        return f"<ExecutionModel(id={self.id!r}, workflow={self.workflow_name!r}, status={self.status!r})>"


class EventModel(Base):
    """Event log for event sourcing.

    Stores all domain events for replay and audit.
    """

    __tablename__ = "events"

    sequence: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aggregate_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:
        return f"<EventModel(seq={self.sequence}, type={self.event_type!r})>"


class AuditModel(Base):
    """Audit trail for ISO 42001 compliance.

    Stores all auditable actions for compliance reporting.
    """

    __tablename__ = "audit"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="user, agent, service, system"
    )
    actor_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    resource: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    outcome: Mapped[str] = mapped_column(
        String(32), default="success", comment="success, failure, denied"
    )
    severity: Mapped[str] = mapped_column(
        String(16), default="info", comment="info, low, medium, high, critical"
    )
    old_value_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    policy_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approval_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:
        return f"<AuditModel(id={self.id!r}, category={self.category!r}, action={self.action!r})>"


class SessionModel(Base):
    """Work session data.

    Tracks work sessions for governance.
    """

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        return f"<SessionModel(id={self.id!r}, started={self.started_at!r})>"


class ToolModel(Base):
    """Tool registration data.

    Stores registered tools for discovery.
    """

    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source: Mapped[str] = mapped_column(
        String(32), default="builtin", comment="builtin, mcp, custom"
    )
    enabled: Mapped[bool] = mapped_column(default=True)
    parameters_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    permissions_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return (
            f"<ToolModel(id={self.id!r}, name={self.name!r}, source={self.source!r})>"
        )
