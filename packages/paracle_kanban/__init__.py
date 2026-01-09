"""Paracle Kanban - Task Management System.

This package provides Kanban-style task management for workflow orchestration,
enabling visual tracking of work items across different stages.
"""

from paracle_kanban.board import Board, BoardRepository
from paracle_kanban.task import AssigneeType, Task, TaskPriority, TaskStatus, TaskType

__version__ = "1.0.1"

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
    # Aliases
    "TaskBoard",
    "TaskManager",
]
