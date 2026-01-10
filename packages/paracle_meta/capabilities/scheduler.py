"""Scheduler capability for MetaAgent.

Provides scheduled task execution:
- Cron-like scheduling
- One-time delayed execution
- Recurring tasks
- Task queue management
- Task cancellation

Uses asyncio for in-process scheduling.
For distributed scheduling, use with Celery or APScheduler.
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)

# Optional import for cron parsing
try:
    from croniter import croniter

    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False
    croniter = None  # type: ignore


class TaskStatus(str, Enum):
    """Scheduled task status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """A scheduled task."""

    id: str
    name: str
    schedule: str  # cron expression or "once"
    callback_name: str
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    next_run: datetime | None = None
    last_run: datetime | None = None
    run_count: int = 0
    max_runs: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "schedule": self.schedule,
            "callback_name": self.callback_name,
            "status": self.status.value,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "max_runs": self.max_runs,
            "created_at": self.created_at.isoformat(),
            "error": self.error,
        }


class SchedulerConfig(CapabilityConfig):
    """Configuration for scheduler capability."""

    max_concurrent_tasks: int = Field(
        default=10,
        description="Maximum concurrent task executions",
    )
    task_timeout: float = Field(
        default=300.0,
        description="Default task timeout in seconds",
    )
    check_interval: float = Field(
        default=1.0,
        description="Interval for checking scheduled tasks (seconds)",
    )
    persist_tasks: bool = Field(
        default=False,
        description="Persist tasks across restarts",
    )


class SchedulerCapability(BaseCapability):
    """Scheduler capability for MetaAgent.

    Provides scheduled task execution with cron-like scheduling:
    - Schedule tasks with cron expressions
    - One-time delayed execution
    - Recurring tasks with max run limits
    - Task queue management
    - Task cancellation

    Example:
        >>> scheduler = SchedulerCapability()
        >>> await scheduler.initialize()

        >>> # Schedule a cron task (every 5 minutes)
        >>> result = await scheduler.schedule(
        ...     name="cleanup",
        ...     cron="*/5 * * * *",
        ...     callback="cleanup_temp_files"
        ... )

        >>> # Schedule a one-time task (in 30 seconds)
        >>> result = await scheduler.delay(
        ...     name="send_reminder",
        ...     seconds=30,
        ...     callback="send_email",
        ...     args=["user@example.com", "Reminder!"]
        ... )

        >>> # List scheduled tasks
        >>> result = await scheduler.list_tasks()

        >>> # Cancel a task
        >>> result = await scheduler.cancel(task_id="...")
    """

    name = "scheduler"
    description = "Scheduled task execution with cron-like scheduling"

    def __init__(self, config: SchedulerConfig | None = None):
        """Initialize scheduler capability."""
        super().__init__(config or SchedulerConfig())
        self.config: SchedulerConfig = self.config
        self._tasks: dict[str, ScheduledTask] = {}
        self._callbacks: dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {}
        self._scheduler_task: asyncio.Task | None = None
        self._running = False
        self._semaphore: asyncio.Semaphore | None = None

    async def initialize(self) -> None:
        """Initialize scheduler."""
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        await super().initialize()

    async def shutdown(self) -> None:
        """Stop scheduler and cleanup."""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None

        # Cancel all pending tasks
        for task in self._tasks.values():
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED

        await super().shutdown()

    def register_callback(
        self,
        name: str,
        callback: Callable[..., Coroutine[Any, Any, Any]],
    ) -> None:
        """Register a callback function for scheduled tasks.

        Args:
            name: Callback name to use in schedule()
            callback: Async function to call
        """
        self._callbacks[name] = callback

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute scheduler operation.

        Args:
            action: Operation (schedule, delay, cancel, list, status, pause, resume)
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "list")
        start_time = time.time()

        try:
            if action == "schedule":
                result = await self._schedule_task(**kwargs)
            elif action == "delay":
                result = await self._delay_task(**kwargs)
            elif action == "cancel":
                result = await self._cancel_task(**kwargs)
            elif action == "list":
                result = self._list_tasks(**kwargs)
            elif action == "status":
                result = self._get_status(**kwargs)
            elif action == "pause":
                result = await self._pause_task(**kwargs)
            elif action == "resume":
                result = await self._resume_task(**kwargs)
            elif action == "run_now":
                result = await self._run_now(**kwargs)
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

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop that checks and runs due tasks."""
        while self._running:
            try:
                now = datetime.utcnow()

                for task in list(self._tasks.values()):
                    if task.status != TaskStatus.PENDING:
                        continue

                    if task.next_run and task.next_run <= now:
                        # Run the task
                        asyncio.create_task(self._execute_task(task))

                await asyncio.sleep(self.config.check_interval)

            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but keep running
                await asyncio.sleep(self.config.check_interval)

    async def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a scheduled task."""
        if not self._semaphore:
            return

        async with self._semaphore:
            task.status = TaskStatus.RUNNING
            task.last_run = datetime.utcnow()

            try:
                callback = self._callbacks.get(task.callback_name)
                if not callback:
                    raise ValueError(f"Callback not found: {task.callback_name}")

                # Execute with timeout
                await asyncio.wait_for(
                    callback(*task.args, **task.kwargs),
                    timeout=self.config.task_timeout,
                )

                task.run_count += 1
                task.error = None

                # Check if task should continue
                if task.max_runs and task.run_count >= task.max_runs:
                    task.status = TaskStatus.COMPLETED
                elif task.schedule == "once":
                    task.status = TaskStatus.COMPLETED
                else:
                    # Schedule next run
                    task.status = TaskStatus.PENDING
                    task.next_run = self._get_next_run(task.schedule)

            except asyncio.TimeoutError:
                task.status = TaskStatus.FAILED
                task.error = f"Task timed out after {self.config.task_timeout}s"
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)

    def _get_next_run(self, schedule: str, base: datetime | None = None) -> datetime:
        """Calculate next run time from cron expression."""
        base = base or datetime.utcnow()

        if schedule == "once":
            return base

        if not CRONITER_AVAILABLE:
            raise RuntimeError("croniter required for cron scheduling: pip install croniter")

        cron = croniter(schedule, base)
        return cron.get_next(datetime)

    def _generate_task_id(self, name: str) -> str:
        """Generate unique task ID."""
        unique = f"{name}-{time.time()}"
        return hashlib.md5(unique.encode()).hexdigest()[:12]

    async def _schedule_task(
        self,
        name: str,
        cron: str,
        callback: str,
        args: tuple = (),
        kwargs: dict = None,
        max_runs: int | None = None,
        **extra,
    ) -> dict[str, Any]:
        """Schedule a recurring task with cron expression.

        Args:
            name: Task name
            cron: Cron expression (e.g., "*/5 * * * *" for every 5 minutes)
            callback: Registered callback name
            args: Positional arguments for callback
            kwargs: Keyword arguments for callback
            max_runs: Maximum number of runs (None = unlimited)

        Returns:
            Task info dict
        """
        task_id = self._generate_task_id(name)
        next_run = self._get_next_run(cron)

        task = ScheduledTask(
            id=task_id,
            name=name,
            schedule=cron,
            callback_name=callback,
            args=args,
            kwargs=kwargs or {},
            next_run=next_run,
            max_runs=max_runs,
        )

        self._tasks[task_id] = task

        return {
            "task_id": task_id,
            "name": name,
            "schedule": cron,
            "next_run": next_run.isoformat(),
            "status": "scheduled",
        }

    async def _delay_task(
        self,
        name: str,
        callback: str,
        seconds: float = 0,
        minutes: float = 0,
        hours: float = 0,
        args: tuple = (),
        kwargs: dict = None,
        **extra,
    ) -> dict[str, Any]:
        """Schedule a one-time delayed task.

        Args:
            name: Task name
            callback: Registered callback name
            seconds: Delay in seconds
            minutes: Delay in minutes
            hours: Delay in hours
            args: Positional arguments for callback
            kwargs: Keyword arguments for callback

        Returns:
            Task info dict
        """
        total_seconds = seconds + (minutes * 60) + (hours * 3600)
        next_run = datetime.utcnow() + timedelta(seconds=total_seconds)

        task_id = self._generate_task_id(name)

        task = ScheduledTask(
            id=task_id,
            name=name,
            schedule="once",
            callback_name=callback,
            args=args,
            kwargs=kwargs or {},
            next_run=next_run,
            max_runs=1,
        )

        self._tasks[task_id] = task

        return {
            "task_id": task_id,
            "name": name,
            "delay_seconds": total_seconds,
            "scheduled_for": next_run.isoformat(),
            "status": "scheduled",
        }

    async def _cancel_task(self, task_id: str, **kwargs) -> dict[str, Any]:
        """Cancel a scheduled task.

        Args:
            task_id: Task ID to cancel

        Returns:
            Cancellation result
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")

        task = self._tasks[task_id]
        if task.status == TaskStatus.RUNNING:
            raise ValueError("Cannot cancel running task")

        task.status = TaskStatus.CANCELLED

        return {
            "task_id": task_id,
            "name": task.name,
            "status": "cancelled",
        }

    def _list_tasks(self, status: str | None = None, **kwargs) -> dict[str, Any]:
        """List scheduled tasks.

        Args:
            status: Filter by status (pending, running, completed, failed, cancelled)

        Returns:
            List of tasks
        """
        tasks = list(self._tasks.values())

        if status:
            tasks = [t for t in tasks if t.status.value == status]

        return {
            "tasks": [t.to_dict() for t in tasks],
            "count": len(tasks),
            "status_filter": status,
        }

    def _get_status(self, task_id: str, **kwargs) -> dict[str, Any]:
        """Get status of a specific task.

        Args:
            task_id: Task ID

        Returns:
            Task status
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")

        return self._tasks[task_id].to_dict()

    async def _pause_task(self, task_id: str, **kwargs) -> dict[str, Any]:
        """Pause a scheduled task (prevents next run).

        Args:
            task_id: Task ID

        Returns:
            Pause result
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")

        task = self._tasks[task_id]
        if task.status != TaskStatus.PENDING:
            raise ValueError(f"Cannot pause task with status: {task.status.value}")

        # Store original next_run and clear it
        task.kwargs["_paused_next_run"] = task.next_run
        task.next_run = None

        return {
            "task_id": task_id,
            "name": task.name,
            "status": "paused",
        }

    async def _resume_task(self, task_id: str, **kwargs) -> dict[str, Any]:
        """Resume a paused task.

        Args:
            task_id: Task ID

        Returns:
            Resume result
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")

        task = self._tasks[task_id]
        paused_next_run = task.kwargs.pop("_paused_next_run", None)

        if paused_next_run:
            # Reschedule from now if paused time has passed
            if paused_next_run < datetime.utcnow():
                task.next_run = self._get_next_run(task.schedule)
            else:
                task.next_run = paused_next_run
        else:
            task.next_run = self._get_next_run(task.schedule)

        return {
            "task_id": task_id,
            "name": task.name,
            "next_run": task.next_run.isoformat() if task.next_run else None,
            "status": "resumed",
        }

    async def _run_now(self, task_id: str, **kwargs) -> dict[str, Any]:
        """Run a task immediately.

        Args:
            task_id: Task ID

        Returns:
            Execution result
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")

        task = self._tasks[task_id]
        if task.status == TaskStatus.RUNNING:
            raise ValueError("Task is already running")

        # Execute immediately
        await self._execute_task(task)

        return {
            "task_id": task_id,
            "name": task.name,
            "status": task.status.value,
            "run_count": task.run_count,
            "error": task.error,
        }

    # Convenience methods
    async def schedule(
        self,
        name: str,
        cron: str,
        callback: str,
        **kwargs,
    ) -> CapabilityResult:
        """Schedule a recurring task."""
        return await self.execute(
            action="schedule", name=name, cron=cron, callback=callback, **kwargs
        )

    async def delay(
        self,
        name: str,
        callback: str,
        seconds: float = 0,
        **kwargs,
    ) -> CapabilityResult:
        """Schedule a one-time delayed task."""
        return await self.execute(
            action="delay", name=name, callback=callback, seconds=seconds, **kwargs
        )

    async def cancel(self, task_id: str) -> CapabilityResult:
        """Cancel a scheduled task."""
        return await self.execute(action="cancel", task_id=task_id)

    async def list_tasks(self, status: str = None) -> CapabilityResult:
        """List scheduled tasks."""
        return await self.execute(action="list", status=status)

    async def status(self, task_id: str) -> CapabilityResult:
        """Get task status."""
        return await self.execute(action="status", task_id=task_id)

    async def run_now(self, task_id: str) -> CapabilityResult:
        """Run a task immediately."""
        return await self.execute(action="run_now", task_id=task_id)
