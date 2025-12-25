"""Paracle Store - Persistence Layer.

This package provides the Repository Pattern implementation
for persisting domain entities.

Current implementations:
- InMemoryRepository: In-memory storage (default for v0.0.1)

Future implementations planned:
- SQLiteRepository: SQLite-based persistence
- PostgresRepository: PostgreSQL-based persistence
"""

from paracle_store.agent_repository import AgentRepository
from paracle_store.repository import (
    DuplicateError,
    InMemoryRepository,
    NotFoundError,
    Repository,
    RepositoryError,
)
from paracle_store.tool_repository import ToolRepository
from paracle_store.workflow_repository import WorkflowRepository

__version__ = "0.0.1"

__all__ = [
    # Base
    "Repository",
    "InMemoryRepository",
    "RepositoryError",
    "NotFoundError",
    "DuplicateError",
    # Specialized
    "AgentRepository",
    "WorkflowRepository",
    "ToolRepository",
]
