"""Integration layer between Workflows and Kanban tasks.

This module provides bidirectional linking and state synchronization
between workflow executions and Kanban tasks.

Key Concepts:
    - A workflow can be linked to one or more Kanban tasks
    - A Kanban task can trigger/track one or more workflows
    - Task status is synchronized with workflow execution status
    - Both systems maintain their own state but stay in sync

Use Cases:
    1. Workflow → Kanban: Track workflow progress in Kanban board
    2. Kanban → Workflow: Execute workflow when task is started
    3. Hybrid: Long-running tasks with multiple workflow executions
"""

from __future__ import annotations

from typing import Any

from paracle_core.compat import UTC, datetime
from paracle_kanban.task import Task, TaskStatus

from paracle_orchestration.context import ExecutionContext, ExecutionStatus


class WorkflowKanbanLink:
    """Bidirectional link between workflow and Kanban task.

    Attributes:
        task_id: Kanban task ID
        workflow_id: Workflow definition ID
        execution_id: Specific workflow execution ID
        created_at: When link was created
        metadata: Additional link metadata
    """

    def __init__(
        self,
        task_id: str,
        workflow_id: str,
        execution_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize workflow-kanban link.

        Args:
            task_id: Kanban task ID
            workflow_id: Workflow definition ID
            execution_id: Specific workflow execution ID (optional)
            metadata: Additional link metadata
        """
        self.task_id = task_id
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.created_at = datetime.now(UTC)
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class TaskWorkflowSync:
    """Synchronize state between Kanban tasks and workflows.

    This class handles the bidirectional state synchronization:
    - Maps workflow execution status to task status
    - Updates task when workflow progresses
    - Stores workflow references in task metadata
    """

    # Status mapping: ExecutionStatus → TaskStatus
    WORKFLOW_TO_TASK_STATUS = {
        ExecutionStatus.PENDING: TaskStatus.TODO,
        ExecutionStatus.RUNNING: TaskStatus.IN_PROGRESS,
        ExecutionStatus.AWAITING_APPROVAL: TaskStatus.REVIEW,
        ExecutionStatus.COMPLETED: TaskStatus.DONE,
        ExecutionStatus.FAILED: TaskStatus.BLOCKED,
        ExecutionStatus.CANCELLED: TaskStatus.ARCHIVED,
        ExecutionStatus.TIMEOUT: TaskStatus.BLOCKED,
    }

    # Reverse mapping: TaskStatus → ExecutionStatus (for triggering)
    TASK_TO_WORKFLOW_STATUS = {
        TaskStatus.BACKLOG: ExecutionStatus.PENDING,
        TaskStatus.TODO: ExecutionStatus.PENDING,
        TaskStatus.IN_PROGRESS: ExecutionStatus.RUNNING,
        TaskStatus.REVIEW: ExecutionStatus.AWAITING_APPROVAL,
        TaskStatus.BLOCKED: ExecutionStatus.FAILED,
        TaskStatus.DONE: ExecutionStatus.COMPLETED,
        TaskStatus.ARCHIVED: ExecutionStatus.CANCELLED,
    }

    @staticmethod
    def link_workflow_to_task(
        task: Task, workflow_id: str, execution_id: str | None = None
    ) -> None:
        """Add workflow reference to task metadata.

        Updates task.metadata with workflow information for tracking.

        Args:
            task: Kanban task to link
            workflow_id: Workflow definition ID
            execution_id: Specific execution ID (optional)
        """
        if "workflows" not in task.metadata:
            task.metadata["workflows"] = []

        task.metadata["workflows"].append(
            {
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "linked_at": datetime.now(UTC).isoformat(),
            }
        )

        # Store primary workflow for quick access
        if "primary_workflow_id" not in task.metadata:
            task.metadata["primary_workflow_id"] = workflow_id

        task.updated_at = datetime.now(UTC)

    @staticmethod
    def link_task_to_workflow(context: ExecutionContext, task_id: str) -> None:
        """Add task reference to workflow execution context.

        Updates context.metadata with task information for tracking.

        Args:
            context: Workflow execution context
            task_id: Kanban task ID to link
        """
        if "kanban_tasks" not in context.metadata:
            context.metadata["kanban_tasks"] = []

        context.metadata["kanban_tasks"].append(
            {"task_id": task_id, "linked_at": datetime.now(UTC).isoformat()}
        )

        # Store primary task for quick access
        if "primary_task_id" not in context.metadata:
            context.metadata["primary_task_id"] = task_id

    @staticmethod
    def sync_workflow_to_task(task: Task, context: ExecutionContext) -> bool:
        """Synchronize workflow execution status to task status.

        Updates task status based on workflow execution progress.

        Args:
            task: Kanban task to update
            context: Workflow execution context

        Returns:
            True if task was updated, False otherwise
        """
        # Map workflow status to task status
        new_status = TaskWorkflowSync.WORKFLOW_TO_TASK_STATUS.get(
            context.status, None
        )

        if new_status is None or task.status == new_status:
            return False

        # Check if transition is valid
        if not task.can_transition_to(new_status):
            # Store pending transition in metadata
            task.metadata["pending_status"] = new_status.value
            task.metadata["status_sync_blocked"] = True
            return False

        # Update task status
        old_status = task.status
        task.move_to(new_status)

        # Store sync metadata
        task.metadata["last_sync_at"] = datetime.now(UTC).isoformat()
        task.metadata["last_sync_from"] = context.execution_id
        task.metadata["synced_from_workflow"] = {
            "execution_id": context.execution_id,
            "workflow_id": context.workflow_id,
            "old_status": old_status.value,
            "new_status": new_status.value,
            "synced_at": datetime.now(UTC).isoformat(),
        }

        return True

    @staticmethod
    def get_workflow_info_from_task(task: Task) -> dict[str, Any]:
        """Extract workflow information from task metadata.

        Args:
            task: Kanban task with workflow metadata

        Returns:
            Dictionary with workflow info (ids, executions, etc.)
        """
        return {
            "workflows": task.metadata.get("workflows", []),
            "primary_workflow_id": task.metadata.get("primary_workflow_id"),
            "last_sync_at": task.metadata.get("last_sync_at"),
            "last_sync_from": task.metadata.get("last_sync_from"),
            "pending_status": task.metadata.get("pending_status"),
            "status_sync_blocked": task.metadata.get("status_sync_blocked", False),
        }

    @staticmethod
    def get_task_info_from_workflow(context: ExecutionContext) -> dict[str, Any]:
        """Extract task information from workflow context.

        Args:
            context: Workflow execution context

        Returns:
            Dictionary with task info (ids, links, etc.)
        """
        return {
            "kanban_tasks": context.metadata.get("kanban_tasks", []),
            "primary_task_id": context.metadata.get("primary_task_id"),
        }

    @staticmethod
    def create_task_from_workflow(
        workflow_id: str,
        execution_id: str,
        context: ExecutionContext,
        board_id: str,
    ) -> Task:
        """Create a Kanban task to track workflow execution.

        Args:
            workflow_id: Workflow definition ID
            execution_id: Specific execution ID
            context: Workflow execution context
            board_id: Target board ID

        Returns:
            New Task instance linked to workflow
        """
        from paracle_kanban.task import TaskPriority, TaskType

        # Determine title and description
        workflow_name = context.metadata.get("workflow_name", workflow_id)
        title = f"Workflow: {workflow_name}"
        description = f"Tracking execution {execution_id}"

        # Create task
        task = Task(
            board_id=board_id,
            title=title,
            description=description,
            status=TaskWorkflowSync.WORKFLOW_TO_TASK_STATUS[context.status],
            priority=TaskPriority.MEDIUM,
            task_type=TaskType.CHORE,
            assigned_to=context.metadata.get("requested_by"),
        )

        # Link workflow to task
        TaskWorkflowSync.link_workflow_to_task(task, workflow_id, execution_id)

        return task


# Helper functions for common patterns


def track_workflow_in_kanban(
    context: ExecutionContext, board_id: str, task_manager: Any = None
) -> Task:
    """Create a Kanban task to track workflow execution.

    This is a convenience function for the common pattern of creating
    a task to monitor workflow progress.

    Args:
        context: Workflow execution context
        board_id: Target board ID
        task_manager: Optional TaskManager instance for persistence

    Returns:
        Created Task instance

    Example:
        >>> context = ExecutionContext(...)
        >>> task = track_workflow_in_kanban(context, "board_123")
        >>> print(f"Tracking workflow in task: {task.id}")
    """
    task = TaskWorkflowSync.create_task_from_workflow(
        context.workflow_id, context.execution_id, context, board_id
    )

    # Save to database if manager provided
    if task_manager is not None:
        task_manager.create_task(task)

    return task


def execute_workflow_from_task(
    task: Task, workflow_engine: Any, workflow_id: str | None = None
) -> ExecutionContext:
    """Execute a workflow linked to a Kanban task.

    This is a convenience function for triggering workflow execution
    from a task (e.g., when task moves to IN_PROGRESS).

    Args:
        task: Kanban task triggering the workflow
        workflow_engine: WorkflowEngine instance
        workflow_id: Optional workflow ID (uses task metadata if not provided)

    Returns:
        Workflow execution context

    Example:
        >>> task = task_manager.get_task("task_123")
        >>> context = execute_workflow_from_task(task, engine)
        >>> print(f"Workflow execution: {context.execution_id}")
    """
    # Get workflow ID from metadata if not provided
    if workflow_id is None:
        workflow_id = task.metadata.get("primary_workflow_id")
        if workflow_id is None:
            raise ValueError(f"No workflow linked to task {task.id}")

    # Execute workflow
    context = workflow_engine.execute(
        workflow_id, inputs=task.metadata.get("inputs", {}))

    # Link task to workflow
    TaskWorkflowSync.link_task_to_workflow(context, task.id)

    # Sync status
    TaskWorkflowSync.sync_workflow_to_task(task, context)

    return context


def execute_workflow_for_tasks(
    workflow_id: str,
    task_ids: list[str],
    workflow_engine: Any,
    context: ExecutionContext,
) -> dict[str, Any]:
    """Execute a workflow that orchestrates multiple Kanban tasks.

    Use case: Create a workflow that processes a backlog of tasks and tracks
    their collective progress (e.g., Sprint workflow, Batch processing).

    The workflow will:
    - Link all tasks to the workflow
    - Track overall progress (X/N tasks completed)
    - Update workflow status based on task completion
    - Provide aggregated metrics

    Args:
        workflow_id: ID of the orchestrating workflow
        task_ids: List of Kanban task IDs to process
        workflow_engine: WorkflowEngine instance
        context: Workflow execution context

    Returns:
        Dictionary with progress information:
        - total_tasks: Total number of tasks
        - completed_tasks: Number of completed tasks
        - in_progress_tasks: Number of in-progress tasks
        - blocked_tasks: Number of blocked tasks
        - progress_percentage: Completion percentage

    Example:
        >>> # You have a backlog with 5 tasks
        >>> task_ids = ["design_task", "dev_task", "test_task", "doc_task", "deploy_task"]
        >>>
        >>> # Create a Sprint workflow to orchestrate them
        >>> context = ExecutionContext(workflow_id="sprint_1", ...)
        >>> progress = execute_workflow_for_tasks("sprint_1", task_ids, engine, context)
        >>>
        >>> print(f"Sprint progress: {progress['progress_percentage']}%")
        >>> print(f"Completed: {progress['completed_tasks']}/{progress['total_tasks']}")
    """

    # Link all tasks to workflow
    for task_id in task_ids:
        TaskWorkflowSync.link_task_to_workflow(context, task_id)

    # Store task list in metadata for tracking
    context.metadata["managed_task_ids"] = task_ids
    context.metadata["total_tasks"] = len(task_ids)

    # Calculate progress
    # Note: In production, you'd fetch actual tasks from database
    # This is a helper that expects you to update task statuses separately
    return {
        "total_tasks": len(task_ids),
        "workflow_id": workflow_id,
        "execution_id": context.execution_id,
        "managed_tasks": task_ids,
        "linked_at": datetime.now(UTC).isoformat(),
    }


def get_workflow_progress(
    context: ExecutionContext, task_manager: Any
) -> dict[str, Any]:
    """Get progress metrics for a workflow managing multiple tasks.

    Args:
        context: Workflow execution context with managed tasks
        task_manager: TaskManager instance to fetch task statuses

    Returns:
        Progress metrics dictionary

    Example:
        >>> progress = get_workflow_progress(context, task_manager)
        >>> print(f"Progress: {progress['completed']}/{progress['total']}")
    """
    from paracle_kanban.task import TaskStatus

    task_ids = context.metadata.get("managed_task_ids", [])
    if not task_ids:
        return {"total": 0, "completed": 0, "progress_percentage": 0}

    # Fetch actual tasks
    tasks = [task_manager.get_task(tid) for tid in task_ids]

    # Count by status
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.DONE)
    in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
    blocked = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)

    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "blocked": blocked,
        "progress_percentage": int((completed / total) * 100) if total > 0 else 0,
    }
