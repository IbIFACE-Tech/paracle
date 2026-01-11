"""Advanced filtering and search for Kanban tasks.

This module provides sophisticated filtering, sorting, and search
capabilities for task management.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from paracle_kanban.task import Task, TaskPriority, TaskStatus, TaskType


class TaskFilter:
    """Advanced task filtering and search."""

    def __init__(self, tasks: list[Task]) -> None:
        """Initialize filter with task list.

        Args:
            tasks: Tasks to filter
        """
        self.tasks = tasks

    def filter(
        self,
        status: TaskStatus | list[TaskStatus] | None = None,
        priority: TaskPriority | list[TaskPriority] | None = None,
        task_type: TaskType | list[TaskType] | None = None,
        assigned_to: str | list[str] | None = None,
        tags: list[str] | None = None,
        swimlane: str | None = None,
        sprint_id: str | None = None,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
        overdue: bool | None = None,
        has_dependencies: bool | None = None,
        is_blocked: bool | None = None,
        search_text: str | None = None,
        custom_filter: Callable[[Task], bool] | None = None,
    ) -> list[Task]:
        """Filter tasks by multiple criteria.

        Args:
            status: Filter by status (single or list)
            priority: Filter by priority (single or list)
            task_type: Filter by type (single or list)
            assigned_to: Filter by assignee (single or list)
            tags: Filter by tags (any match)
            swimlane: Filter by swimlane
            sprint_id: Filter by sprint
            due_before: Tasks due before this date
            due_after: Tasks due after this date
            overdue: Filter overdue tasks
            has_dependencies: Filter tasks with/without dependencies
            is_blocked: Filter blocked tasks
            search_text: Full-text search in title/description
            custom_filter: Custom filter function

        Returns:
            Filtered task list
        """
        result = self.tasks

        # Status filter
        if status is not None:
            statuses = (
                [status] if not isinstance(status, list) else status
            )
            result = [t for t in result if t.status in statuses]

        # Priority filter
        if priority is not None:
            priorities = (
                [priority]
                if not isinstance(priority, list)
                else priority
            )
            result = [t for t in result if t.priority in priorities]

        # Type filter
        if task_type is not None:
            types = (
                [task_type]
                if not isinstance(task_type, list)
                else task_type
            )
            result = [t for t in result if t.task_type in types]

        # Assigned filter
        if assigned_to is not None:
            assignees = (
                [assigned_to]
                if not isinstance(assigned_to, list)
                else assigned_to
            )
            result = [
                t for t in result if t.assigned_to in assignees
            ]

        # Tags filter (any match)
        if tags:
            result = [
                t
                for t in result
                if any(tag in t.tags for tag in tags)
            ]

        # Swimlane filter
        if swimlane is not None:
            result = [t for t in result if t.swimlane == swimlane]

        # Sprint filter
        if sprint_id is not None:
            result = [t for t in result if t.sprint_id == sprint_id]

        # Due date filters
        if due_before is not None:
            result = [
                t
                for t in result
                if t.due_date and t.due_date <= due_before
            ]

        if due_after is not None:
            result = [
                t
                for t in result
                if t.due_date and t.due_date >= due_after
            ]

        # Overdue filter
        if overdue is not None:
            now = datetime.utcnow()
            if overdue:
                result = [
                    t
                    for t in result
                    if t.due_date
                    and t.due_date < now
                    and not t.is_complete()
                ]
            else:
                result = [
                    t
                    for t in result
                    if not t.due_date
                    or t.due_date >= now
                    or t.is_complete()
                ]

        # Dependencies filter
        if has_dependencies is not None:
            if has_dependencies:
                result = [t for t in result if t.depends_on]
            else:
                result = [t for t in result if not t.depends_on]

        # Blocked filter
        if is_blocked is not None:
            if is_blocked:
                result = [t for t in result if t.is_blocked()]
            else:
                result = [t for t in result if not t.is_blocked()]

        # Text search
        if search_text:
            pattern = re.compile(re.escape(search_text), re.IGNORECASE)
            result = [
                t
                for t in result
                if pattern.search(t.title)
                or pattern.search(t.description)
            ]

        # Custom filter
        if custom_filter:
            result = [t for t in result if custom_filter(t)]

        return result

    def sort(
        self,
        tasks: list[Task] | None = None,
        key: str = "created_at",
        reverse: bool = False,
    ) -> list[Task]:
        """Sort tasks by key.

        Args:
            tasks: Tasks to sort (uses filtered tasks if None)
            key: Sort key (created_at, updated_at, due_date, priority,
                 status, title)
            reverse: Sort in descending order

        Returns:
            Sorted task list
        """
        if tasks is None:
            tasks = self.tasks

        sort_keys = {
            "created_at": lambda t: t.created_at,
            "updated_at": lambda t: t.updated_at,
            "due_date": lambda t: t.due_date or datetime.max,
            "priority": lambda t: self._priority_value(t.priority),
            "status": lambda t: t.status.value,
            "title": lambda t: t.title.lower(),
            "estimated_hours": lambda t: t.estimated_hours or 0,
            "actual_hours": lambda t: t.actual_hours,
            "story_points": lambda t: t.story_points or 0,
        }

        sort_fn = sort_keys.get(key, lambda t: t.created_at)
        return sorted(tasks, key=sort_fn, reverse=reverse)

    def _priority_value(self, priority: TaskPriority) -> int:
        """Convert priority to numeric value for sorting.

        Args:
            priority: Task priority

        Returns:
            Numeric value (higher = more urgent)
        """
        values = {
            TaskPriority.CRITICAL: 4,
            TaskPriority.HIGH: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 1,
        }
        return values.get(priority, 0)

    def group_by(
        self, tasks: list[Task] | None = None, key: str = "status"
    ) -> dict[Any, list[Task]]:
        """Group tasks by a key.

        Args:
            tasks: Tasks to group (uses filtered tasks if None)
            key: Grouping key (status, priority, assignee, swimlane,
                 sprint, type)

        Returns:
            Dictionary of grouped tasks
        """
        if tasks is None:
            tasks = self.tasks

        groups: dict[Any, list[Task]] = {}

        for task in tasks:
            if key == "status":
                group_key = task.status
            elif key == "priority":
                group_key = task.priority
            elif key == "assignee":
                group_key = task.assigned_to or "unassigned"
            elif key == "swimlane":
                group_key = task.swimlane or "default"
            elif key == "sprint":
                group_key = task.sprint_id or "no_sprint"
            elif key == "type":
                group_key = task.task_type
            else:
                group_key = getattr(task, key, "unknown")

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(task)

        return groups

    def get_due_soon(
        self, days: int = 7, tasks: list[Task] | None = None
    ) -> list[Task]:
        """Get tasks due within specified days.

        Args:
            days: Number of days ahead to check
            tasks: Tasks to check (uses filtered tasks if None)

        Returns:
            Tasks due soon
        """
        if tasks is None:
            tasks = self.tasks

        now = datetime.utcnow()
        threshold = now + timedelta(days=days)

        return [
            t
            for t in tasks
            if t.due_date
            and now <= t.due_date <= threshold
            and not t.is_complete()
        ]

    def get_overdue(
        self, tasks: list[Task] | None = None
    ) -> list[Task]:
        """Get overdue tasks.

        Args:
            tasks: Tasks to check (uses filtered tasks if None)

        Returns:
            Overdue tasks
        """
        if tasks is None:
            tasks = self.tasks

        now = datetime.utcnow()
        return [
            t
            for t in tasks
            if t.due_date and t.due_date < now and not t.is_complete()
        ]

    def search(self, query: str) -> list[Task]:
        """Full-text search across tasks.

        Args:
            query: Search query

        Returns:
            Matching tasks
        """
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return [
            t
            for t in self.tasks
            if pattern.search(t.title)
            or pattern.search(t.description)
            or any(pattern.search(tag) for tag in t.tags)
        ]
