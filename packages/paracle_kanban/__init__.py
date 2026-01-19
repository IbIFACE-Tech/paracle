"""Paracle Kanban - Task Management System.

This package provides Kanban-style task management for workflow orchestration,
enabling visual tracking of work items across different stages.
"""

__version__ = "1.1.0"

from paracle_kanban.analytics import KanbanAnalytics
from paracle_kanban.board import Board, BoardRepository
from paracle_kanban.comments import TaskActivity, TaskComment
from paracle_kanban.dependency import (
    CircularDependencyError,
    DependencyError,
    DependencyValidator,
)
from paracle_kanban.filters import TaskFilter
from paracle_kanban.notifications import (
    Notification,
    NotificationChannel,
    NotificationEvent,
    NotificationManager,
    NotificationRule,
)
from paracle_kanban.task import (
    AssigneeType,
    Task,
    TaskPriority,
    TaskStatus,
    TaskType,
)
from paracle_kanban.templates import TaskTemplate, TemplateManager
from paracle_kanban.wip_limits import WIPLimitError, WIPLimitValidator

__version__ = "1.1.0"

# Aliases for backward compatibility with tests
TaskBoard = Board
TaskManager = BoardRepository

__all__ = [
    # Task
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskType",
    "AssigneeType",
    # Board
    "Board",
    "BoardRepository",
    # Comments & Activity
    "TaskComment",
    "TaskActivity",
    # Dependencies
    "DependencyValidator",
    "DependencyError",
    "CircularDependencyError",
    # Notifications
    "Notification",
    "NotificationEvent",
    "NotificationChannel",
    "NotificationRule",
    "NotificationManager",
    # Templates
    "TaskTemplate",
    "TemplateManager",
    # WIP Limits
    "WIPLimitValidator",
    "WIPLimitError",
    # Analytics
    "KanbanAnalytics",
    # Filters
    "TaskFilter",
    # Aliases
    "TaskBoard",
    "TaskManager",
]
