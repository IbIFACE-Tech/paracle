"""Task and workflow management capability for MetaAgent.

Provides task orchestration, workflow execution, and
progress tracking capabilities for the MetaAgent.
"""

import asyncio
import time
import uuid
from collections.abc import Callable, Coroutine
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskConfig(CapabilityConfig):
    """Configuration for task management capability."""

    max_concurrent_tasks: int = Field(
        default=5, ge=1, le=50, description="Max concurrent task executions"
    )
    default_timeout: float = Field(
        default=300.0, ge=1.0, le=3600.0, description="Default task timeout (seconds)"
    )
    retry_failed_tasks: bool = Field(
        default=True, description="Auto-retry failed tasks"
    )
    max_retries: int = Field(default=3, ge=0, le=10, description="Max retry attempts")
    persist_state: bool = Field(default=False, description="Persist task state to disk")


class Task(BaseModel):
    """A managed task."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    result: Any = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retries: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    subtasks: list["Task"] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        """Get task duration in milliseconds."""
        if not self.started_at:
            return 0.0
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds() * 1000

    @property
    def is_complete(self) -> bool:
        """Check if task is complete (success or failure)."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )


class Workflow(BaseModel):
    """A workflow composed of multiple tasks."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    tasks: list[Task] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def progress(self) -> float:
        """Calculate overall workflow progress."""
        if not self.tasks:
            return 0.0
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        return (completed / len(self.tasks)) * 100

    @property
    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return all(t.is_complete for t in self.tasks)


# Type alias for task handlers
TaskHandler = Callable[["Task", dict[str, Any]], Coroutine[Any, Any, Any]]


class TaskManagementCapability(BaseCapability):
    """Task and workflow management capability for MetaAgent.

    Provides:
    - Task creation and tracking
    - Workflow orchestration
    - Progress monitoring
    - Dependency management
    - Concurrent task execution

    Example:
        >>> tasks = TaskManagementCapability()
        >>> await tasks.initialize()
        >>>
        >>> # Create a task
        >>> result = await tasks.execute(
        ...     action="create_task",
        ...     name="Generate Agent",
        ...     description="Generate a new agent spec"
        ... )
        >>> task_id = result.output["id"]
        >>>
        >>> # Update task progress
        >>> await tasks.execute(
        ...     action="update_task",
        ...     task_id=task_id,
        ...     progress=50.0
        ... )
        >>>
        >>> # Create a workflow
        >>> result = await tasks.execute(
        ...     action="create_workflow",
        ...     name="Feature Implementation",
        ...     tasks=[
        ...         {"name": "Design", "description": "Design the feature"},
        ...         {"name": "Implement", "depends_on": ["Design"]},
        ...         {"name": "Test", "depends_on": ["Implement"]},
        ...     ]
        ... )
    """

    name = "task_management"
    description = "Task orchestration, workflow execution, and progress tracking"

    def __init__(self, config: TaskConfig | None = None):
        """Initialize task management capability.

        Args:
            config: Task management configuration
        """
        super().__init__(config or TaskConfig())
        self.config: TaskConfig = self.config
        self._tasks: dict[str, Task] = {}
        self._workflows: dict[str, Workflow] = {}
        self._handlers: dict[str, TaskHandler] = {}
        self._running_tasks: set[str] = set()
        self._semaphore: asyncio.Semaphore | None = None

    async def initialize(self) -> None:
        """Initialize task management."""
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        await super().initialize()

    async def shutdown(self) -> None:
        """Cleanup task management."""
        # Cancel any running tasks
        for task_id in list(self._running_tasks):
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.CANCELLED
        self._running_tasks.clear()
        await super().shutdown()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute task management capability.

        Args:
            action: Action to perform
            **kwargs: Action-specific parameters

        Returns:
            CapabilityResult with task operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "list_tasks")
        start_time = time.time()

        try:
            if action == "create_task":
                result = await self._create_task(**kwargs)
            elif action == "update_task":
                result = await self._update_task(**kwargs)
            elif action == "get_task":
                result = await self._get_task(**kwargs)
            elif action == "list_tasks":
                result = await self._list_tasks(**kwargs)
            elif action == "run_task":
                result = await self._run_task(**kwargs)
            elif action == "cancel_task":
                result = await self._cancel_task(**kwargs)
            elif action == "create_workflow":
                result = await self._create_workflow(**kwargs)
            elif action == "run_workflow":
                result = await self._run_workflow(**kwargs)
            elif action == "get_workflow":
                result = await self._get_workflow(**kwargs)
            elif action == "list_workflows":
                result = await self._list_workflows(**kwargs)
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result,
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    async def _create_task(
        self,
        name: str,
        description: str = "",
        priority: str = "normal",
        depends_on: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create a new task.

        Args:
            name: Task name
            description: Task description
            priority: Task priority
            depends_on: List of task IDs this depends on
            metadata: Additional metadata

        Returns:
            Task data dictionary
        """
        task = Task(
            name=name,
            description=description,
            priority=TaskPriority(priority),
            depends_on=depends_on or [],
            metadata=metadata or {},
        )

        self._tasks[task.id] = task
        return task.model_dump()

    async def _update_task(
        self,
        task_id: str,
        status: str | None = None,
        progress: float | None = None,
        result: Any = None,
        error: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Update an existing task.

        Args:
            task_id: Task ID to update
            status: New status
            progress: New progress (0-100)
            result: Task result
            error: Error message

        Returns:
            Updated task data
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if status:
            task.status = TaskStatus(status)
            if task.status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.utcnow()
            elif task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                task.completed_at = datetime.utcnow()

        if progress is not None:
            task.progress = progress

        if result is not None:
            task.result = result

        if error:
            task.error = error

        return task.model_dump()

    async def _get_task(self, task_id: str, **kwargs) -> dict[str, Any]:
        """Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task data dictionary
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        return task.model_dump()

    async def _list_tasks(
        self,
        status: str | None = None,
        limit: int = 100,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """List tasks with optional filtering.

        Args:
            status: Filter by status
            limit: Max tasks to return

        Returns:
            List of task data dictionaries
        """
        tasks = list(self._tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == TaskStatus(status)]

        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return [t.model_dump() for t in tasks[:limit]]

    async def _run_task(
        self,
        task_id: str,
        handler: TaskHandler | None = None,
        context: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Run a task.

        Args:
            task_id: Task ID to run
            handler: Optional task handler function
            context: Execution context

        Returns:
            Task execution result
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # Check dependencies
        for dep_id in task.depends_on:
            dep_task = self._tasks.get(dep_id)
            if dep_task and dep_task.status != TaskStatus.COMPLETED:
                raise ValueError(
                    f"Dependency not satisfied: {dep_id} (status: {dep_task.status})"
                )

        # Acquire semaphore for concurrent task limit
        if not self._semaphore:
            self._semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)

        async with self._semaphore:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            self._running_tasks.add(task_id)

            try:
                # Run the handler if provided
                if handler:
                    result = await handler(task, context or {})
                    task.result = result
                elif task_id in self._handlers:
                    result = await self._handlers[task_id](task, context or {})
                    task.result = result
                else:
                    # No handler - just mark as complete
                    task.result = {"message": "Task completed (no handler)"}

                task.status = TaskStatus.COMPLETED
                task.progress = 100.0
                task.completed_at = datetime.utcnow()

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.utcnow()

                # Retry if configured
                if (
                    self.config.retry_failed_tasks
                    and task.retries < self.config.max_retries
                ):
                    task.retries += 1
                    task.status = TaskStatus.PENDING
                    task.error = None

            finally:
                self._running_tasks.discard(task_id)

        return task.model_dump()

    async def _cancel_task(self, task_id: str, **kwargs) -> dict[str, Any]:
        """Cancel a task.

        Args:
            task_id: Task ID to cancel

        Returns:
            Cancelled task data
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()

        return task.model_dump()

    async def _create_workflow(
        self,
        name: str,
        description: str = "",
        tasks: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create a new workflow.

        Args:
            name: Workflow name
            description: Workflow description
            tasks: List of task definitions
            metadata: Additional metadata

        Returns:
            Workflow data dictionary
        """
        workflow = Workflow(
            name=name,
            description=description,
            metadata=metadata or {},
        )

        # Create tasks from definitions
        task_id_map: dict[str, str] = {}  # name -> id mapping

        for task_def in tasks or []:
            task_name = task_def.get("name", f"task_{len(workflow.tasks)}")

            # Resolve dependencies by name
            depends_on = []
            for dep_name in task_def.get("depends_on", []):
                if dep_name in task_id_map:
                    depends_on.append(task_id_map[dep_name])

            task = Task(
                name=task_name,
                description=task_def.get("description", ""),
                priority=TaskPriority(task_def.get("priority", "normal")),
                depends_on=depends_on,
                metadata=task_def.get("metadata", {}),
            )

            workflow.tasks.append(task)
            self._tasks[task.id] = task
            task_id_map[task_name] = task.id

        self._workflows[workflow.id] = workflow
        return workflow.model_dump()

    async def _run_workflow(
        self,
        workflow_id: str,
        parallel: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Run a workflow.

        Args:
            workflow_id: Workflow ID to run
            parallel: Run independent tasks in parallel

        Returns:
            Workflow execution result
        """
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow.status = TaskStatus.RUNNING
        workflow.started_at = datetime.utcnow()

        try:
            if parallel:
                await self._run_workflow_parallel(workflow)
            else:
                await self._run_workflow_sequential(workflow)

            workflow.status = TaskStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()

        except Exception:
            workflow.status = TaskStatus.FAILED
            workflow.completed_at = datetime.utcnow()
            raise

        return workflow.model_dump()

    async def _run_workflow_sequential(self, workflow: Workflow) -> None:
        """Run workflow tasks sequentially."""
        for task in workflow.tasks:
            await self._run_task(task.id)
            if task.status == TaskStatus.FAILED:
                raise RuntimeError(f"Task failed: {task.name}")

    async def _run_workflow_parallel(self, workflow: Workflow) -> None:
        """Run workflow tasks in parallel where possible."""
        completed_ids: set[str] = set()
        pending_tasks = list(workflow.tasks)

        while pending_tasks:
            # Find tasks with satisfied dependencies
            ready_tasks = [
                t
                for t in pending_tasks
                if all(dep in completed_ids for dep in t.depends_on)
            ]

            if not ready_tasks:
                if pending_tasks:
                    raise RuntimeError("Circular dependency detected in workflow")
                break

            # Run ready tasks in parallel
            results = await asyncio.gather(
                *[self._run_task(t.id) for t in ready_tasks],
                return_exceptions=True,
            )

            # Check for failures
            for task, result in zip(ready_tasks, results, strict=False):
                if isinstance(result, Exception):
                    raise RuntimeError(f"Task failed: {task.name} - {result}")

                task_data = self._tasks[task.id]
                if task_data.status == TaskStatus.FAILED:
                    raise RuntimeError(f"Task failed: {task.name}")

                completed_ids.add(task.id)
                pending_tasks.remove(task)

    async def _get_workflow(self, workflow_id: str, **kwargs) -> dict[str, Any]:
        """Get a workflow by ID."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        return workflow.model_dump()

    async def _list_workflows(self, limit: int = 50, **kwargs) -> list[dict[str, Any]]:
        """List all workflows."""
        workflows = list(self._workflows.values())
        workflows.sort(key=lambda w: w.created_at, reverse=True)
        return [w.model_dump() for w in workflows[:limit]]

    # Convenience methods
    def register_handler(self, task_id: str, handler: TaskHandler) -> None:
        """Register a handler for a task.

        Args:
            task_id: Task ID
            handler: Async handler function
        """
        self._handlers[task_id] = handler

    async def create_task(self, name: str, **kwargs) -> CapabilityResult:
        """Create a new task."""
        return await self.execute(action="create_task", name=name, **kwargs)

    async def get_task(self, task_id: str) -> CapabilityResult:
        """Get a task by ID."""
        return await self.execute(action="get_task", task_id=task_id)

    async def run_task(self, task_id: str, **kwargs) -> CapabilityResult:
        """Run a task."""
        return await self.execute(action="run_task", task_id=task_id, **kwargs)

    async def create_workflow(
        self, name: str, tasks: list[dict[str, Any]]
    ) -> CapabilityResult:
        """Create a new workflow."""
        return await self.execute(action="create_workflow", name=name, tasks=tasks)

    async def run_workflow(self, workflow_id: str, **kwargs) -> CapabilityResult:
        """Run a workflow."""
        return await self.execute(
            action="run_workflow", workflow_id=workflow_id, **kwargs
        )

    @property
    def active_tasks(self) -> int:
        """Get count of active tasks."""
        return len(self._running_tasks)

    @property
    def pending_tasks(self) -> int:
        """Get count of pending tasks."""
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)
