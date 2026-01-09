"""Task Manager.

Manages A2A task lifecycle and persistence.
"""

import asyncio
from collections import OrderedDict
from datetime import datetime
from typing import Any

from ulid import ULID

from paracle_a2a.config import A2AServerConfig
from paracle_a2a.exceptions import TaskNotFoundError
from paracle_a2a.models import (
    Artifact,
    Message,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    create_message,
    create_task,
    is_task_terminal,
)


class TaskManager:
    """Manages A2A task lifecycle.

    Handles task creation, updates, queries, and cleanup.
    Stores tasks in memory with optional persistence.
    """

    def __init__(
        self,
        config: A2AServerConfig | None = None,
        on_status_update: Any | None = None,
        on_artifact_update: Any | None = None,
    ):
        """Initialize task manager.

        Args:
            config: Server configuration
            on_status_update: Callback for status updates
            on_artifact_update: Callback for artifact updates
        """
        self.config = config or A2AServerConfig()
        self._on_status_update = on_status_update
        self._on_artifact_update = on_artifact_update

        # Task storage (LRU-like with max size)
        self._tasks: OrderedDict[str, Task] = OrderedDict()
        self._task_messages: dict[str, list[Message]] = {}
        self._task_artifacts: dict[str, list[Artifact]] = {}

        # Locks for concurrent access
        self._lock = asyncio.Lock()

    async def create_task(
        self,
        message: Message,
        context_id: str | None = None,
        session_id: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Task:
        """Create a new task.

        Args:
            message: Initial message
            context_id: Optional context ID
            session_id: Optional session ID
            task_id: Optional task ID (for continuing)
            metadata: Optional metadata

        Returns:
            Created Task
        """
        async with self._lock:
            # Check if continuing existing task
            if task_id and task_id in self._tasks:
                task = self._tasks[task_id]
                self._task_messages.setdefault(task_id, []).append(message)
                # Move to end (LRU)
                self._tasks.move_to_end(task_id)
                return task

            # Create new task
            new_id = task_id or str(ULID())
            history = [] if self.config.enable_state_transition_history else None

            # SDK Task requires context_id, generate one if not provided
            ctx_id = context_id or str(ULID())

            task = create_task(
                task_id=new_id,
                context_id=ctx_id,
                status=TaskStatus(state=TaskState.submitted),
                metadata=metadata or {},
                history=history,
            )
            # Store session_id in metadata for Paracle-specific tracking
            if session_id:
                task_meta = dict(task.metadata or {})
                task_meta["session_id"] = session_id
                task = Task(
                    id=task.id,
                    context_id=task.context_id,
                    status=task.status,
                    metadata=task_meta,
                    history=task.history,
                    artifacts=task.artifacts,
                )

            # Store task and initial message
            self._tasks[new_id] = task
            self._task_messages[new_id] = [message]
            self._task_artifacts[new_id] = []

            # Enforce max tasks limit
            await self._cleanup_old_tasks()

            return task

    async def get_task(self, task_id: str) -> Task:
        """Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task object

        Raises:
            TaskNotFoundError: If task not found
        """
        async with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(task_id)
            # Move to end (LRU)
            self._tasks.move_to_end(task_id)
            return self._tasks[task_id]

    async def get_task_messages(self, task_id: str) -> list[Message]:
        """Get messages for a task.

        Args:
            task_id: Task identifier

        Returns:
            List of messages

        Raises:
            TaskNotFoundError: If task not found
        """
        async with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(task_id)
            return self._task_messages.get(task_id, [])

    async def get_task_artifacts(self, task_id: str) -> list[Artifact]:
        """Get artifacts for a task.

        Args:
            task_id: Task identifier

        Returns:
            List of artifacts

        Raises:
            TaskNotFoundError: If task not found
        """
        async with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(task_id)
            return self._task_artifacts.get(task_id, [])

    async def update_status(
        self,
        task_id: str,
        state: TaskState,
        message: str | None = None,
        progress: float | None = None,
        error: dict[str, Any] | None = None,
    ) -> Task:
        """Update task status.

        Args:
            task_id: Task identifier
            state: New state
            message: Optional status message
            progress: Optional progress (0.0-1.0)
            error: Optional error details

        Returns:
            Updated Task

        Raises:
            TaskNotFoundError: If task not found
        """
        async with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(task_id)

            task = self._tasks[task_id]

            # Create new status with optional message
            status_message = None
            if message:
                status_message = create_message(message, role="agent")

            new_status = TaskStatus(
                state=state,
                message=status_message,
                timestamp=datetime.utcnow().isoformat(),
            )

            # Build updated history if tracking
            new_history = task.history
            if self.config.enable_state_transition_history:
                new_history = list(task.history or [])
                # Add status change as a message in history
                if status_message:
                    new_history.append(status_message)

            # Create new task with updated status (SDK types are immutable)
            updated_task = Task(
                id=task.id,
                context_id=task.context_id,
                status=new_status,
                metadata=task.metadata,
                history=new_history,
                artifacts=task.artifacts,
            )
            self._tasks[task_id] = updated_task

            # Emit event
            if self._on_status_update:
                event = TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=updated_task.context_id,
                    status=updated_task.status,
                    final=is_task_terminal(updated_task),
                )
                await self._on_status_update(event)

            return updated_task

    async def add_message(
        self,
        task_id: str,
        message: Message,
    ) -> Task:
        """Add message to task.

        Args:
            task_id: Task identifier
            message: Message to add

        Returns:
            Updated Task

        Raises:
            TaskNotFoundError: If task not found
        """
        async with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(task_id)

            self._task_messages.setdefault(task_id, []).append(message)
            task = self._tasks[task_id]
            # SDK Task is immutable, no updated_at field
            return task

    async def add_artifact(
        self,
        task_id: str,
        artifact: Artifact,
    ) -> Task:
        """Add artifact to task.

        Args:
            task_id: Task identifier
            artifact: Artifact to add

        Returns:
            Updated Task

        Raises:
            TaskNotFoundError: If task not found
        """
        async with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(task_id)

            self._task_artifacts.setdefault(task_id, []).append(artifact)
            task = self._tasks[task_id]
            # SDK Task is immutable, no updated_at field

            # Emit event
            if self._on_artifact_update:
                event = TaskArtifactUpdateEvent(
                    task_id=task_id,
                    context_id=task.context_id,
                    artifact=artifact,
                )
                await self._on_artifact_update(event)

            return task

    async def cancel_task(
        self,
        task_id: str,
        reason: str | None = None,
    ) -> Task:
        """Cancel a task.

        Args:
            task_id: Task identifier
            reason: Cancellation reason

        Returns:
            Updated Task

        Raises:
            TaskNotFoundError: If task not found
        """
        return await self.update_status(
            task_id=task_id,
            state=TaskState.canceled,  # SDK uses lowercase 'canceled'
            message=reason or "Task cancelled by user",
        )

    async def list_tasks(
        self,
        context_id: str | None = None,
        session_id: str | None = None,
        states: list[TaskState] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Task]:
        """List tasks with filtering.

        Args:
            context_id: Filter by context ID
            session_id: Filter by session ID (stored in metadata)
            states: Filter by states
            limit: Maximum results
            offset: Results offset

        Returns:
            List of matching tasks
        """
        async with self._lock:
            tasks = list(self._tasks.values())

            # Apply filters
            if context_id:
                tasks = [t for t in tasks if t.context_id == context_id]
            if session_id:
                # session_id is stored in metadata for SDK compatibility
                tasks = [
                    t
                    for t in tasks
                    if (t.metadata or {}).get("session_id") == session_id
                ]
            if states:
                tasks = [t for t in tasks if t.status.state in states]

            # SDK Task has no created_at, sort by id (ULID is time-ordered)
            tasks.sort(key=lambda t: t.id, reverse=True)

            # Apply pagination
            return tasks[offset : offset + limit]

    async def _cleanup_old_tasks(self) -> None:
        """Remove old tasks when limit exceeded."""
        while len(self._tasks) > self.config.task_history_limit:
            # Remove oldest (first item in OrderedDict)
            task_id = next(iter(self._tasks))
            task = self._tasks.pop(task_id)

            # Only remove completed tasks
            if not is_task_terminal(task):
                # Put it back at the end
                self._tasks[task_id] = task
                break

            # Clean up associated data
            self._task_messages.pop(task_id, None)
            self._task_artifacts.pop(task_id, None)
