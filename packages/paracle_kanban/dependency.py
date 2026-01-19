"""Task dependency validation and management.

This module provides dependency checking, circular dependency detection,
and dependency chain resolution for Kanban tasks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paracle_kanban.task import Task


class DependencyError(Exception):
    """Raised when dependency validation fails."""

    pass


class CircularDependencyError(DependencyError):
    """Raised when circular dependency is detected."""

    pass


class DependencyValidator:
    """Validates task dependencies and prevents circular references."""

    def __init__(self, tasks: dict[str, Task]) -> None:
        """Initialize validator with task registry.

        Args:
            tasks: Dictionary of task_id -> Task
        """
        self.tasks = tasks

    def validate_dependencies(self, task: Task) -> list[str]:
        """Validate task dependencies.

        Args:
            task: Task to validate

        Returns:
            List of validation errors (empty if valid)

        Raises:
            CircularDependencyError: If circular dependency detected
        """
        errors = []

        # Check that all dependencies exist
        for dep_id in task.depends_on:
            if dep_id not in self.tasks:
                errors.append(f"Dependency task '{dep_id}' does not exist")

        # Check for circular dependencies
        if self._has_circular_dependency(task.id, task.depends_on):
            raise CircularDependencyError(
                f"Circular dependency detected for task '{task.id}'"
            )

        return errors

    def _has_circular_dependency(
        self,
        task_id: str,
        dependencies: list[str],
        visited: set[str] | None = None,
    ) -> bool:
        """Check for circular dependencies using DFS.

        Args:
            task_id: Current task ID
            dependencies: List of dependency IDs
            visited: Set of visited task IDs

        Returns:
            True if circular dependency found, False otherwise
        """
        if visited is None:
            visited = set()

        if task_id in visited:
            return True

        visited.add(task_id)

        for dep_id in dependencies:
            if dep_id in self.tasks:
                dep_task = self.tasks[dep_id]
                if self._has_circular_dependency(
                    dep_id, dep_task.depends_on, visited.copy()
                ):
                    return True

        return False

    def get_dependency_chain(self, task_id: str) -> list[str]:
        """Get full dependency chain for a task.

        Args:
            task_id: Task ID

        Returns:
            Ordered list of task IDs from dependencies to task
        """
        if task_id not in self.tasks:
            return []

        chain = []
        visited = set()

        def _build_chain(tid: str) -> None:
            if tid in visited or tid not in self.tasks:
                return

            visited.add(tid)
            task = self.tasks[tid]

            # Add dependencies first (depth-first)
            for dep_id in task.depends_on:
                _build_chain(dep_id)

            chain.append(tid)

        _build_chain(task_id)
        return chain

    def can_complete_task(self, task_id: str) -> tuple[bool, list[str]]:
        """Check if task can be completed based on dependencies.

        Args:
            task_id: Task ID to check

        Returns:
            Tuple of (can_complete, list of incomplete dependencies)
        """
        if task_id not in self.tasks:
            return False, [f"Task '{task_id}' not found"]

        task = self.tasks[task_id]
        incomplete = []

        for dep_id in task.depends_on:
            if dep_id in self.tasks:
                dep_task = self.tasks[dep_id]
                if not dep_task.is_complete():
                    incomplete.append(dep_id)

        return len(incomplete) == 0, incomplete

    def get_blocked_tasks(self, task_id: str) -> list[str]:
        """Get list of tasks blocked by this task.

        Args:
            task_id: Task ID

        Returns:
            List of task IDs that depend on this task
        """
        blocked = []
        for tid, task in self.tasks.items():
            if task_id in task.depends_on:
                blocked.append(tid)
        return blocked
