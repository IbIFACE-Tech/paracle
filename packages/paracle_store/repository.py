"""Repository Pattern implementation.

This module provides the base repository interface and in-memory implementation.
Follows the Repository Pattern from Domain-Driven Design (DDD).

Key features:
- Abstract Repository interface (Port)
- In-memory implementation (Adapter)
- Type-safe generic implementation
- Event emission on CRUD operations
- Thread-safe operations with RLock
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T", bound=BaseModel)


class RepositoryError(Exception):
    """Base exception for repository errors."""

    pass


class NotFoundError(RepositoryError):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' not found")


class DuplicateError(RepositoryError):
    """Raised when trying to create a duplicate entity."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' already exists")


class Repository(ABC, Generic[T]):
    """Abstract base repository interface.

    This is the Port in Hexagonal Architecture terms.
    Concrete implementations (Adapters) must implement all abstract methods.
    """

    @abstractmethod
    def get(self, id: str) -> T | None:
        """Get entity by ID.

        Args:
            id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    def get_or_raise(self, id: str) -> T:
        """Get entity by ID, raise if not found.

        Args:
            id: Entity identifier

        Returns:
            Entity

        Raises:
            NotFoundError: If entity not found
        """
        pass

    @abstractmethod
    def list(self) -> list[T]:
        """List all entities.

        Returns:
            List of all entities
        """
        pass

    @abstractmethod
    def add(self, entity: T) -> T:
        """Add a new entity.

        Args:
            entity: Entity to add

        Returns:
            Added entity

        Raises:
            DuplicateError: If entity with same ID exists
        """
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity.

        Args:
            entity: Entity to update

        Returns:
            Updated entity

        Raises:
            NotFoundError: If entity not found
        """
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete an entity by ID.

        Args:
            id: Entity identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def exists(self, id: str) -> bool:
        """Check if entity exists.

        Args:
            id: Entity identifier

        Returns:
            True if exists
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """Count all entities.

        Returns:
            Number of entities
        """
        pass

    @abstractmethod
    def clear(self) -> int:
        """Remove all entities.

        Returns:
            Number of entities removed
        """
        pass


class InMemoryRepository(Repository[T]):
    """In-memory repository implementation.

    Thread-safe implementation using a dictionary with RLock.
    Suitable for testing and single-process deployments.

    Note:
        Uses RLock (reentrant lock) to allow nested calls from the same thread.
    """

    def __init__(
        self,
        entity_type: str,
        id_getter: Callable[[T], str],
    ) -> None:
        """Initialize repository.

        Args:
            entity_type: Name of entity type (for error messages)
            id_getter: Function to extract ID from entity
        """
        self._entity_type = entity_type
        self._id_getter = id_getter
        self._store: dict[str, T] = {}
        self._lock = threading.RLock()

    def get(self, id: str) -> T | None:
        """Get entity by ID."""
        with self._lock:
            return self._store.get(id)

    def get_or_raise(self, id: str) -> T:
        """Get entity by ID, raise if not found."""
        with self._lock:
            entity = self._store.get(id)
            if entity is None:
                raise NotFoundError(self._entity_type, id)
            return entity

    def list(self) -> list[T]:
        """List all entities."""
        with self._lock:
            return list(self._store.values())

    def add(self, entity: T) -> T:
        """Add a new entity."""
        with self._lock:
            entity_id = self._id_getter(entity)
            if entity_id in self._store:
                raise DuplicateError(self._entity_type, entity_id)
            self._store[entity_id] = entity
            return entity

    def update(self, entity: T) -> T:
        """Update an existing entity."""
        with self._lock:
            entity_id = self._id_getter(entity)
            if entity_id not in self._store:
                raise NotFoundError(self._entity_type, entity_id)
            self._store[entity_id] = entity
            return entity

    def delete(self, id: str) -> bool:
        """Delete an entity by ID."""
        with self._lock:
            if id not in self._store:
                return False
            del self._store[id]
            return True

    def exists(self, id: str) -> bool:
        """Check if entity exists."""
        with self._lock:
            return id in self._store

    def count(self) -> int:
        """Count all entities."""
        with self._lock:
            return len(self._store)

    def clear(self) -> int:
        """Remove all entities."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count

    def find_by(self, predicate: Callable[[T], bool]) -> list[T]:
        """Find entities matching predicate.

        Args:
            predicate: Function returning True for matching entities

        Returns:
            List of matching entities
        """
        with self._lock:
            return [e for e in self._store.values() if predicate(e)]

    def find_one_by(self, predicate: Callable[[T], bool]) -> T | None:
        """Find first entity matching predicate.

        Args:
            predicate: Function returning True for matching entities

        Returns:
            First matching entity or None
        """
        with self._lock:
            for entity in self._store.values():
                if predicate(entity):
                    return entity
            return None
