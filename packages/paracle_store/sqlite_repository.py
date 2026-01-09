"""SQLite repository implementations.

This module provides SQLite-backed implementations of the Repository pattern.
These repositories persist data to SQLite, surviving restarts.

Usage:
    from paracle_store.database import Database
    from paracle_store.sqlite_repository import SQLiteAgentRepository

    db = Database("sqlite:///paracle.db")
    db.connect()
    db.create_tables()

    repo = SQLiteAgentRepository(db)
    repo.add(agent)
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

from paracle_core.compat import UTC, datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from paracle_store.models import (
    AgentModel,
    EventModel,
    ExecutionModel,
    ToolModel,
    WorkflowModel,
)
from paracle_store.repository import DuplicateError, NotFoundError, Repository

if TYPE_CHECKING:

    from paracle_domain.models import Agent, ToolSpec, WorkflowSpec
    from paracle_events.events import DomainEvent

    from paracle_store.database import Database


def _compute_hash(data: dict) -> str:
    """Compute hash of dictionary for change detection."""
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]


class SQLiteAgentRepository(Repository["Agent"]):
    """SQLite-backed agent repository.

    Persists Agent domain objects to SQLite.
    Agents are stored with their spec hash for change detection.
    """

    def __init__(self, database: Database) -> None:
        """Initialize repository.

        Args:
            database: Database connection manager.
        """
        self._db = database
        self._entity_type = "Agent"

    def _to_model(self, entity: Agent) -> AgentModel:
        """Convert domain entity to database model."""
        spec_dict = entity.spec.model_dump(mode="json") if entity.spec else {}
        # Store provider in metadata for reconstruction
        metadata = (
            dict(entity.spec.metadata) if entity.spec and entity.spec.metadata else {}
        )
        if entity.spec and entity.spec.provider:
            metadata["provider"] = entity.spec.provider
        # Extract status phase as string (AgentStatus has a phase field with EntityStatus)
        status_str = (
            entity.status.phase.value
            if hasattr(entity.status, "phase")
            else str(entity.status)
        )
        return AgentModel(
            id=entity.id,
            name=entity.spec.name if entity.spec else entity.id,
            spec_hash=_compute_hash(spec_dict),
            status=status_str,
            parent_id=entity.spec.parent if entity.spec else None,
            model=entity.spec.model if entity.spec else None,
            created_at=entity.created_at,
            updated_at=datetime.now(UTC),
            metadata_json=metadata,
        )

    def _to_entity(self, model: AgentModel) -> Agent:
        """Convert database model to domain entity."""
        from paracle_domain.models import Agent, AgentSpec, AgentStatus, EntityStatus

        # Extract provider from metadata or model string
        metadata = model.metadata_json or {}
        provider = metadata.get("provider", "openai")

        spec = AgentSpec(
            name=model.name,
            parent=model.parent_id,
            model=model.model or "gpt-4",
            provider=provider,
            metadata=metadata,
        )
        # Reconstruct AgentStatus from stored phase string
        try:
            phase = EntityStatus(model.status)
        except ValueError:
            phase = EntityStatus.PENDING
        status = AgentStatus(phase=phase)

        return Agent(
            id=model.id,
            spec=spec,
            status=status,
            created_at=model.created_at,
        )

    def get(self, id: str) -> Agent | None:
        """Get agent by ID."""
        with self._db.session() as session:
            model = session.get(AgentModel, id)
            if model is None:
                return None
            return self._to_entity(model)

    def get_or_raise(self, id: str) -> Agent:
        """Get agent by ID, raise if not found."""
        entity = self.get(id)
        if entity is None:
            raise NotFoundError(self._entity_type, id)
        return entity

    def get_by_name(self, name: str) -> Agent | None:
        """Get agent by name."""
        with self._db.session() as session:
            stmt = select(AgentModel).where(AgentModel.name == name)
            model = session.execute(stmt).scalar_one_or_none()
            if model is None:
                return None
            return self._to_entity(model)

    def list(self) -> list[Agent]:
        """List all agents."""
        with self._db.session() as session:
            stmt = select(AgentModel).order_by(AgentModel.name)
            models = session.execute(stmt).scalars().all()
            return [self._to_entity(m) for m in models]

    def add(self, entity: Agent) -> Agent:
        """Add a new agent."""
        model = self._to_model(entity)
        try:
            with self._db.session() as session:
                session.add(model)
        except IntegrityError as e:
            raise DuplicateError(self._entity_type, entity.id) from e
        return entity

    def update(self, entity: Agent) -> Agent:
        """Update an existing agent."""
        with self._db.session() as session:
            existing = session.get(AgentModel, entity.id)
            if existing is None:
                raise NotFoundError(self._entity_type, entity.id)

            # Update fields
            spec_dict = entity.spec.model_dump(mode="json") if entity.spec else {}
            # Store provider in metadata for reconstruction
            metadata = (
                dict(entity.spec.metadata)
                if entity.spec and entity.spec.metadata
                else {}
            )
            if entity.spec and entity.spec.provider:
                metadata["provider"] = entity.spec.provider
            # Extract status phase as string
            status_str = (
                entity.status.phase.value
                if hasattr(entity.status, "phase")
                else str(entity.status)
            )
            existing.name = entity.spec.name if entity.spec else entity.id
            existing.spec_hash = _compute_hash(spec_dict)
            existing.status = status_str
            existing.parent_id = entity.spec.parent if entity.spec else None
            existing.model = entity.spec.model if entity.spec else None
            existing.metadata_json = metadata
            existing.updated_at = datetime.now(UTC)

        return entity

    def delete(self, id: str) -> bool:
        """Delete an agent by ID."""
        with self._db.session() as session:
            model = session.get(AgentModel, id)
            if model is None:
                return False
            session.delete(model)
        return True

    def exists(self, id: str) -> bool:
        """Check if agent exists."""
        with self._db.session() as session:
            return session.get(AgentModel, id) is not None

    def count(self) -> int:
        """Count all agents."""
        with self._db.session() as session:
            from sqlalchemy import func

            stmt = select(func.count()).select_from(AgentModel)
            return session.execute(stmt).scalar() or 0

    def clear(self) -> int:
        """Remove all agents."""
        with self._db.session() as session:
            from sqlalchemy import delete

            stmt = delete(AgentModel)
            result = session.execute(stmt)
            return result.rowcount or 0


class SQLiteWorkflowRepository(Repository["WorkflowSpec"]):
    """SQLite-backed workflow repository."""

    def __init__(self, database: Database) -> None:
        self._db = database
        self._entity_type = "Workflow"

    def _to_model(self, entity: WorkflowSpec) -> WorkflowModel:
        spec_dict = entity.model_dump(mode="json")
        return WorkflowModel(
            id=entity.name,  # Use name as ID
            name=entity.name,
            description=entity.description,
            spec_hash=_compute_hash(spec_dict),
            step_count=len(entity.steps) if entity.steps else 0,
            metadata_json=entity.metadata or {},
        )

    def _to_entity(self, model: WorkflowModel) -> WorkflowSpec:
        from paracle_domain.models import WorkflowSpec

        return WorkflowSpec(
            name=model.name,
            description=model.description,
            steps=[],  # Steps need to be loaded from YAML
            metadata=model.metadata_json or {},
        )

    def get(self, id: str) -> WorkflowSpec | None:
        with self._db.session() as session:
            model = session.get(WorkflowModel, id)
            if model is None:
                return None
            return self._to_entity(model)

    def get_or_raise(self, id: str) -> WorkflowSpec:
        entity = self.get(id)
        if entity is None:
            raise NotFoundError(self._entity_type, id)
        return entity

    def list(self) -> list[WorkflowSpec]:
        with self._db.session() as session:
            stmt = select(WorkflowModel).order_by(WorkflowModel.name)
            models = session.execute(stmt).scalars().all()
            return [self._to_entity(m) for m in models]

    def add(self, entity: WorkflowSpec) -> WorkflowSpec:
        model = self._to_model(entity)
        try:
            with self._db.session() as session:
                session.add(model)
        except IntegrityError as e:
            raise DuplicateError(self._entity_type, entity.name) from e
        return entity

    def update(self, entity: WorkflowSpec) -> WorkflowSpec:
        with self._db.session() as session:
            existing = session.get(WorkflowModel, entity.name)
            if existing is None:
                raise NotFoundError(self._entity_type, entity.name)

            spec_dict = entity.model_dump(mode="json")
            existing.description = entity.description
            existing.spec_hash = _compute_hash(spec_dict)
            existing.step_count = len(entity.steps) if entity.steps else 0
            existing.metadata_json = entity.metadata or {}
            existing.updated_at = datetime.now(UTC)

        return entity

    def delete(self, id: str) -> bool:
        with self._db.session() as session:
            model = session.get(WorkflowModel, id)
            if model is None:
                return False
            session.delete(model)
        return True

    def exists(self, id: str) -> bool:
        with self._db.session() as session:
            return session.get(WorkflowModel, id) is not None

    def count(self) -> int:
        with self._db.session() as session:
            from sqlalchemy import func

            stmt = select(func.count()).select_from(WorkflowModel)
            return session.execute(stmt).scalar() or 0

    def clear(self) -> int:
        with self._db.session() as session:
            from sqlalchemy import delete

            stmt = delete(WorkflowModel)
            result = session.execute(stmt)
            return result.rowcount or 0


class SQLiteToolRepository(Repository["ToolSpec"]):
    """SQLite-backed tool repository."""

    def __init__(self, database: Database) -> None:
        self._db = database
        self._entity_type = "Tool"

    def _to_model(self, entity: ToolSpec) -> ToolModel:
        return ToolModel(
            id=entity.name,
            name=entity.name,
            description=entity.description,
            category=entity.category,
            source="builtin",
            enabled=not entity.disabled,
            parameters_json=entity.parameters or {},
            permissions_json=entity.permissions or [],
        )

    def _to_entity(self, model: ToolModel) -> ToolSpec:
        from paracle_domain.models import ToolSpec

        return ToolSpec(
            name=model.name,
            description=model.description or "",
            category=model.category,
            parameters=model.parameters_json or {},
            permissions=model.permissions_json or [],
            disabled=not model.enabled,
        )

    def get(self, id: str) -> ToolSpec | None:
        with self._db.session() as session:
            model = session.get(ToolModel, id)
            if model is None:
                return None
            return self._to_entity(model)

    def get_or_raise(self, id: str) -> ToolSpec:
        entity = self.get(id)
        if entity is None:
            raise NotFoundError(self._entity_type, id)
        return entity

    def list(self) -> list[ToolSpec]:
        with self._db.session() as session:
            stmt = select(ToolModel).order_by(ToolModel.name)
            models = session.execute(stmt).scalars().all()
            return [self._to_entity(m) for m in models]

    def list_by_category(self, category: str) -> list[ToolSpec]:
        """List tools by category."""
        with self._db.session() as session:
            stmt = (
                select(ToolModel)
                .where(ToolModel.category == category)
                .order_by(ToolModel.name)
            )
            models = session.execute(stmt).scalars().all()
            return [self._to_entity(m) for m in models]

    def add(self, entity: ToolSpec) -> ToolSpec:
        model = self._to_model(entity)
        try:
            with self._db.session() as session:
                session.add(model)
        except IntegrityError as e:
            raise DuplicateError(self._entity_type, entity.name) from e
        return entity

    def update(self, entity: ToolSpec) -> ToolSpec:
        with self._db.session() as session:
            existing = session.get(ToolModel, entity.name)
            if existing is None:
                raise NotFoundError(self._entity_type, entity.name)

            existing.description = entity.description
            existing.category = entity.category
            existing.enabled = not entity.disabled
            existing.parameters_json = entity.parameters or {}
            existing.permissions_json = entity.permissions or []
            existing.updated_at = datetime.now(UTC)

        return entity

    def delete(self, id: str) -> bool:
        with self._db.session() as session:
            model = session.get(ToolModel, id)
            if model is None:
                return False
            session.delete(model)
        return True

    def exists(self, id: str) -> bool:
        with self._db.session() as session:
            return session.get(ToolModel, id) is not None

    def count(self) -> int:
        with self._db.session() as session:
            from sqlalchemy import func

            stmt = select(func.count()).select_from(ToolModel)
            return session.execute(stmt).scalar() or 0

    def clear(self) -> int:
        with self._db.session() as session:
            from sqlalchemy import delete

            stmt = delete(ToolModel)
            result = session.execute(stmt)
            return result.rowcount or 0


class SQLiteEventRepository:
    """SQLite-backed event repository for event sourcing.

    Not a Repository[T] because events are append-only
    and have different semantics.
    """

    def __init__(self, database: Database) -> None:
        self._db = database

    def append(self, event: DomainEvent) -> int:
        """Append event to log, returns sequence number."""
        with self._db.session() as session:
            model = EventModel(
                event_id=event.event_id,
                event_type=event.event_type,
                source=getattr(event, "source", None),
                aggregate_id=event.aggregate_id,
                timestamp=event.timestamp,
                data_json=event.data or {},
                correlation_id=getattr(event, "correlation_id", None),
            )
            session.add(model)
            session.flush()
            return model.sequence

    def get_by_sequence(self, sequence: int) -> DomainEvent | None:
        """Get event by sequence number."""
        with self._db.session() as session:
            model = session.get(EventModel, sequence)
            if model is None:
                return None
            return self._to_event(model)

    def list_since(
        self, sequence: int = 0, limit: int = 100
    ) -> list[tuple[int, DomainEvent]]:
        """List events since sequence number."""
        with self._db.session() as session:
            stmt = (
                select(EventModel)
                .where(EventModel.sequence > sequence)
                .order_by(EventModel.sequence)
                .limit(limit)
            )
            models = session.execute(stmt).scalars().all()
            return [(m.sequence, self._to_event(m)) for m in models]

    def list_by_type(self, event_type: str, limit: int = 100) -> list[DomainEvent]:
        """List events by type."""
        with self._db.session() as session:
            stmt = (
                select(EventModel)
                .where(EventModel.event_type == event_type)
                .order_by(EventModel.sequence.desc())
                .limit(limit)
            )
            models = session.execute(stmt).scalars().all()
            return [self._to_event(m) for m in models]

    def list_by_aggregate(self, aggregate_id: str) -> list[DomainEvent]:
        """List all events for an aggregate."""
        with self._db.session() as session:
            stmt = (
                select(EventModel)
                .where(EventModel.aggregate_id == aggregate_id)
                .order_by(EventModel.sequence)
            )
            models = session.execute(stmt).scalars().all()
            return [self._to_event(m) for m in models]

    def count(self) -> int:
        """Count all events."""
        with self._db.session() as session:
            from sqlalchemy import func

            stmt = select(func.count()).select_from(EventModel)
            return session.execute(stmt).scalar() or 0

    def _to_event(self, model: EventModel) -> DomainEvent:
        """Convert model to domain event."""
        from paracle_events.events import DomainEvent

        return DomainEvent(
            event_id=model.event_id,
            event_type=model.event_type,
            aggregate_id=model.aggregate_id or "",
            timestamp=model.timestamp,
            data=model.data_json or {},
        )


class SQLiteExecutionRepository:
    """SQLite-backed execution repository.

    Tracks workflow execution history.
    """

    def __init__(self, database: Database) -> None:
        self._db = database

    def create(
        self,
        execution_id: str,
        workflow_id: str,
        workflow_name: str,
        inputs: dict | None = None,
    ) -> None:
        """Create new execution record."""
        with self._db.session() as session:
            model = ExecutionModel(
                id=execution_id,
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                status="pending",
                inputs_json=inputs,
            )
            session.add(model)

    def start(self, execution_id: str) -> None:
        """Mark execution as started."""
        with self._db.session() as session:
            model = session.get(ExecutionModel, execution_id)
            if model:
                model.status = "running"
                model.started_at = datetime.now(UTC)

    def complete(self, execution_id: str, result: dict | None = None) -> None:
        """Mark execution as completed."""
        with self._db.session() as session:
            model = session.get(ExecutionModel, execution_id)
            if model:
                model.status = "completed"
                model.completed_at = datetime.now(UTC)
                model.result_json = result

    def fail(self, execution_id: str, error: str) -> None:
        """Mark execution as failed."""
        with self._db.session() as session:
            model = session.get(ExecutionModel, execution_id)
            if model:
                model.status = "failed"
                model.completed_at = datetime.now(UTC)
                model.error = error

    def cancel(self, execution_id: str) -> None:
        """Mark execution as cancelled."""
        with self._db.session() as session:
            model = session.get(ExecutionModel, execution_id)
            if model:
                model.status = "cancelled"
                model.completed_at = datetime.now(UTC)

    def get(self, execution_id: str) -> dict | None:
        """Get execution by ID."""
        with self._db.session() as session:
            model = session.get(ExecutionModel, execution_id)
            if model is None:
                return None
            return {
                "id": model.id,
                "workflow_id": model.workflow_id,
                "workflow_name": model.workflow_name,
                "status": model.status,
                "started_at": model.started_at,
                "completed_at": model.completed_at,
                "inputs": model.inputs_json,
                "result": model.result_json,
                "error": model.error,
            }

    def list_by_workflow(self, workflow_id: str, limit: int = 10) -> list[dict]:
        """List executions for a workflow."""
        with self._db.session() as session:
            stmt = (
                select(ExecutionModel)
                .where(ExecutionModel.workflow_id == workflow_id)
                .order_by(ExecutionModel.created_at.desc())
                .limit(limit)
            )
            models = session.execute(stmt).scalars().all()
            return [
                {
                    "id": m.id,
                    "workflow_id": m.workflow_id,
                    "workflow_name": m.workflow_name,
                    "status": m.status,
                    "started_at": m.started_at,
                    "completed_at": m.completed_at,
                }
                for m in models
            ]

    def list_recent(self, limit: int = 20) -> list[dict]:
        """List recent executions."""
        with self._db.session() as session:
            stmt = (
                select(ExecutionModel)
                .order_by(ExecutionModel.created_at.desc())
                .limit(limit)
            )
            models = session.execute(stmt).scalars().all()
            return [
                {
                    "id": m.id,
                    "workflow_id": m.workflow_id,
                    "workflow_name": m.workflow_name,
                    "status": m.status,
                    "started_at": m.started_at,
                    "completed_at": m.completed_at,
                }
                for m in models
            ]
