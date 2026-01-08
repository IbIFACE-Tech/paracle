"""Task models and state machine for Kanban board.

This module provides the Task model with status transitions,
priority levels, and assignment tracking.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from paracle_domain.models import generate_id
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status in the Kanban workflow."""

    BACKLOG = "backlog"  # Not yet started, in backlog
    TODO = "todo"  # Ready to start
    IN_PROGRESS = "in_progress"  # Currently being worked on
    REVIEW = "review"  # Awaiting review
    BLOCKED = "blocked"  # Blocked by dependency or issue
    DONE = "done"  # Completed
    ARCHIVED = "archived"  # Archived/removed from board


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskType(str, Enum):
    """Task types."""

    FEATURE = "feature"  # New feature development
    BUG = "bug"  # Bug fix
    REFACTOR = "refactor"  # Code refactoring
    DOCS = "docs"  # Documentation
    TEST = "test"  # Testing
    CHORE = "chore"  # Maintenance/chores


class AssigneeType(str, Enum):
    """Assignee type for task assignment.

    Convention:
    - AGENT: AI agents (coder, reviewer, security, etc.)
    - HUMAN: Human team members
    - TEAM: Team/group assignment

    Format in assigned_to field:
    - Agents: "coder", "reviewer", "security" (plain ID)
    - Humans: "human:john", "human:jane.doe"
    - Teams: "team:platform", "team:security"
    """

    AGENT = "agent"
    HUMAN = "human"
    TEAM = "team"


class Task(BaseModel):
    """Kanban task model.

    Represents a single work item on the Kanban board with status,
    priority, assignment, and metadata tracking.

    Attributes:
        id: Unique task identifier
        board_id: ID of the board this task belongs to
        title: Short task title
        description: Detailed task description
        status: Current task status
        priority: Task priority level
        task_type: Type of task
        assigned_to: Assignee ID (agent, human, or team)
        created_at: When task was created
        updated_at: When task was last updated
        started_at: When work started (status → IN_PROGRESS)
        completed_at: When task was completed (status → DONE)
        tags: List of tags for categorization
        metadata: Additional metadata
        depends_on: List of task IDs this task depends on
        blocked_by: Optional reason for BLOCKED status

    Assignment Convention:
        - Agents: plain ID (e.g., "coder", "reviewer", "security")
        - Humans: "human:<name>" (e.g., "human:john", "human:jane.doe")
        - Teams: "team:<name>" (e.g., "team:platform", "team:backend")
    """

    id: str = Field(default_factory=lambda: generate_id("task"))
    board_id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.BACKLOG
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: TaskType = TaskType.FEATURE
    assigned_to: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    blocked_by: str | None = None

    class Config:
        """Pydantic configuration."""

        use_enum_values = True

    def can_transition_to(self, new_status: TaskStatus) -> bool:
        """Check if task can transition to new status.

        Implements state machine logic for valid transitions.

        Args:
            new_status: Target status

        Returns:
            True if transition is valid, False otherwise
        """
        # Define valid transitions
        valid_transitions = {
            TaskStatus.BACKLOG: [TaskStatus.TODO, TaskStatus.ARCHIVED],
            TaskStatus.TODO: [
                TaskStatus.IN_PROGRESS,
                TaskStatus.BACKLOG,
                TaskStatus.ARCHIVED,
            ],
            TaskStatus.IN_PROGRESS: [
                TaskStatus.REVIEW,
                TaskStatus.BLOCKED,
                TaskStatus.TODO,
                TaskStatus.DONE,
            ],
            TaskStatus.REVIEW: [
                TaskStatus.IN_PROGRESS,
                TaskStatus.DONE,
                TaskStatus.TODO,
            ],
            TaskStatus.BLOCKED: [TaskStatus.IN_PROGRESS, TaskStatus.TODO],
            TaskStatus.DONE: [TaskStatus.IN_PROGRESS, TaskStatus.ARCHIVED],
            TaskStatus.ARCHIVED: [],  # Cannot transition from archived
        }

        return new_status in valid_transitions.get(self.status, [])

    def move_to(self, new_status: TaskStatus, reason: str | None = None) -> None:
        """Move task to new status.

        Updates status and timestamps based on transition.

        Args:
            new_status: Target status
            reason: Optional reason for transition (required for BLOCKED)

        Raises:
            ValueError: If transition is invalid
        """
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )

        # Update timestamps
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()

        # Track started_at when moving to IN_PROGRESS
        if new_status == TaskStatus.IN_PROGRESS and not self.started_at:
            self.started_at = datetime.utcnow()

        # Track completed_at when moving to DONE
        if new_status == TaskStatus.DONE and not self.completed_at:
            self.completed_at = datetime.utcnow()

        # Handle BLOCKED status
        if new_status == TaskStatus.BLOCKED:
            self.blocked_by = reason or "No reason provided"
        elif old_status == TaskStatus.BLOCKED:
            self.blocked_by = None

    def assign(self, assignee_id: str) -> None:
        """Assign task to an agent (default behavior).

        For human or team assignment, use assign_to_human() or assign_to_team().

        Args:
            assignee_id: ID of the agent to assign
        """
        self.assigned_to = assignee_id
        self.updated_at = datetime.utcnow()

    def assign_to_human(self, name: str) -> None:
        """Assign task to a human team member.

        Args:
            name: Human name/identifier (e.g., "john", "jane.doe")

        Example:
            task.assign_to_human("john")  # Sets assigned_to = "human:john"
        """
        self.assigned_to = f"human:{name}"
        self.updated_at = datetime.utcnow()

    def assign_to_team(self, team_name: str) -> None:
        """Assign task to a team.

        Args:
            team_name: Team name (e.g., "platform", "security")

        Example:
            task.assign_to_team("platform")  # Sets assigned_to = "team:platform"
        """
        self.assigned_to = f"team:{team_name}"
        self.updated_at = datetime.utcnow()

    def unassign(self) -> None:
        """Unassign task from current assignee."""
        self.assigned_to = None
        self.updated_at = datetime.utcnow()

    def get_assignee_type(self) -> AssigneeType | None:
        """Get the type of current assignee.

        Returns:
            AssigneeType (AGENT, HUMAN, or TEAM) or None if unassigned
        """
        if not self.assigned_to:
            return None
        if self.assigned_to.startswith("human:"):
            return AssigneeType.HUMAN
        if self.assigned_to.startswith("team:"):
            return AssigneeType.TEAM
        return AssigneeType.AGENT

    def get_assignee_name(self) -> str | None:
        """Get the assignee name without prefix.

        Returns:
            Assignee name (e.g., "john" from "human:john") or None if unassigned
        """
        if not self.assigned_to:
            return None
        if ":" in self.assigned_to:
            return self.assigned_to.split(":", 1)[1]
        return self.assigned_to

    def is_assigned_to_human(self) -> bool:
        """Check if task is assigned to a human.

        Returns:
            True if assigned to a human, False otherwise
        """
        return self.get_assignee_type() == AssigneeType.HUMAN

    def is_assigned_to_agent(self) -> bool:
        """Check if task is assigned to an agent.

        Returns:
            True if assigned to an agent, False otherwise
        """
        return self.get_assignee_type() == AssigneeType.AGENT

    def is_assigned_to_team(self) -> bool:
        """Check if task is assigned to a team.

        Returns:
            True if assigned to a team, False otherwise
        """
        return self.get_assignee_type() == AssigneeType.TEAM

    def add_tag(self, tag: str) -> None:
        """Add a tag to the task.

        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the task.

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()

    def is_blocked(self) -> bool:
        """Check if task is blocked.

        Returns:
            True if task is blocked, False otherwise
        """
        return self.status == TaskStatus.BLOCKED

    def is_complete(self) -> bool:
        """Check if task is complete.

        Returns:
            True if task is done or archived, False otherwise
        """
        return self.status in [TaskStatus.DONE, TaskStatus.ARCHIVED]

    def cycle_time(self) -> float | None:
        """Calculate cycle time (started → completed) in hours.

        Returns:
            Cycle time in hours, or None if not completed
        """
        if not self.started_at or not self.completed_at:
            return None

        delta = self.completed_at - self.started_at
        return delta.total_seconds() / 3600  # Convert to hours

    def lead_time(self) -> float | None:
        """Calculate lead time (created → completed) in hours.

        Returns:
            Lead time in hours, or None if not completed
        """
        if not self.completed_at:
            return None

        delta = self.completed_at - self.created_at
        return delta.total_seconds() / 3600  # Convert to hours
