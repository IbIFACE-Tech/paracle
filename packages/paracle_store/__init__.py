"""Paracle Store - Persistence Layer.

This package provides the Repository Pattern implementation
for persisting domain entities.

Implementations:
- InMemoryRepository: In-memory storage (testing, ephemeral)
- SQLiteRepository: SQLite-based persistence (production)

Usage:
    # In-memory (default, for testing)
    from paracle_store import AgentRepository
    repo = AgentRepository()

    # SQLite (persistent)
    from paracle_store import Database, SQLiteAgentRepository
    db = Database("sqlite:///paracle.db")
    db.connect()
    db.create_tables()
    repo = SQLiteAgentRepository(db)
"""

from paracle_store.agent_repository import AgentRepository
from paracle_store.database import (
    Base,
    ConnectionError,
    Database,
    DatabaseError,
    get_database,
    reset_database,
)
from paracle_store.models import (
    AgentModel,
    AuditModel,
    EventModel,
    ExecutionModel,
    SessionModel,
    ToolModel,
    WorkflowModel,
)
from paracle_store.repository import (
    DuplicateError,
    InMemoryRepository,
    NotFoundError,
    Repository,
    RepositoryError,
)
from paracle_store.sqlite_repository import (
    SQLiteAgentRepository,
    SQLiteEventRepository,
    SQLiteExecutionRepository,
    SQLiteToolRepository,
    SQLiteWorkflowRepository,
)
from paracle_store.tool_repository import ToolRepository
from paracle_store.workflow_repository import WorkflowRepository

__version__ = "1.0.1"

__all__ = [
    # Base repository
    "Repository",
    "InMemoryRepository",
    "RepositoryError",
    "NotFoundError",
    "DuplicateError",
    # In-memory repositories
    "AgentRepository",
    "WorkflowRepository",
    "ToolRepository",
    # Database
    "Database",
    "DatabaseError",
    "ConnectionError",
    "Base",
    "get_database",
    "reset_database",
    # SQLAlchemy models
    "AgentModel",
    "WorkflowModel",
    "ExecutionModel",
    "EventModel",
    "AuditModel",
    "SessionModel",
    "ToolModel",
    # SQLite repositories
    "SQLiteAgentRepository",
    "SQLiteWorkflowRepository",
    "SQLiteToolRepository",
    "SQLiteEventRepository",
    "SQLiteExecutionRepository",
]
