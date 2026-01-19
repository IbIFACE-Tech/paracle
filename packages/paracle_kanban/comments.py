"""Task comments and activity tracking.

This module provides commenting functionality for tasks,
enabling collaboration and activity tracking.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from paracle_domain.models import generate_id
from pydantic import BaseModel, Field, ConfigDict


class TaskComment(BaseModel):
    """Comment on a task.

    Attributes:
        id: Unique comment identifier
        task_id: Task this comment belongs to
        author: User who created the comment
        content: Comment text
        created_at: When comment was created
        updated_at: When comment was last edited
        edited: Whether comment has been edited
        parent_id: Parent comment for threaded replies
        mentions: List of mentioned users/agents
        attachments: List of attached file references
    """

    id: str = Field(default_factory=lambda: generate_id("comment"))
    task_id: str
    author: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    edited: bool = False
    parent_id: str | None = None
    mentions: list[str] = Field(default_factory=list)
    attachments: list[dict[str, str]] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)


class TaskActivity(BaseModel):
    """Activity log entry for a task.

    Tracks all changes and actions on a task for audit trail.

    Attributes:
        id: Unique activity identifier
        task_id: Task this activity belongs to
        user: User who performed the action
        action: Type of action (status_change, assignment, comment, etc.)
        timestamp: When action occurred
        details: Additional details about the action
        old_value: Previous value (for changes)
        new_value: New value (for changes)
    """

    id: str = Field(default_factory=lambda: generate_id("activity"))
    task_id: str
    user: str
    action: str  # status_change, assignment, comment, edit, etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: str = ""
    old_value: Any = None
    new_value: Any = None

    model_config = ConfigDict(use_enum_values=True)
