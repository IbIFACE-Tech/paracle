"""Unit tests for paracle_meta.capabilities.task_management module."""

import pytest
from paracle_meta.capabilities.task_management import (
    Task,
    TaskConfig,
    TaskManagementCapability,
    TaskPriority,
    TaskStatus,
    Workflow,
)


class TestTaskConfig:
    """Tests for TaskConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = TaskConfig()
        assert config.max_concurrent_tasks == 5
        assert config.default_timeout == 300.0
        assert config.retry_failed_tasks is True
        assert config.max_retries == 3
        assert config.persist_state is False

    def test_custom_values(self):
        """Test custom configuration values."""
        config = TaskConfig(
            max_concurrent_tasks=10,
            default_timeout=600.0,
            retry_failed_tasks=False,
        )
        assert config.max_concurrent_tasks == 10
        assert config.default_timeout == 600.0
        assert config.retry_failed_tasks is False


class TestTask:
    """Tests for Task model."""

    def test_create_task(self):
        """Test creating a task."""
        task = Task(
            name="Test Task",
            description="A test task",
            priority=TaskPriority.HIGH,
        )

        assert task.name == "Test Task"
        assert task.description == "A test task"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0.0
        assert task.id is not None

    def test_task_defaults(self):
        """Test task default values."""
        task = Task(name="Simple Task")

        assert task.description == ""
        assert task.priority == TaskPriority.NORMAL
        assert task.status == TaskStatus.PENDING
        assert task.result is None
        assert task.error is None
        assert task.subtasks == []
        assert task.depends_on == []

    def test_task_is_complete(self):
        """Test is_complete property."""
        task = Task(name="Test")

        # Pending - not complete
        assert task.is_complete is False

        # Running - not complete
        task.status = TaskStatus.RUNNING
        assert task.is_complete is False

        # Completed - complete
        task.status = TaskStatus.COMPLETED
        assert task.is_complete is True

        # Failed - complete
        task.status = TaskStatus.FAILED
        assert task.is_complete is True

        # Cancelled - complete
        task.status = TaskStatus.CANCELLED
        assert task.is_complete is True

    def test_task_duration(self):
        """Test duration_ms property."""
        task = Task(name="Test")

        # No start time - duration is 0
        assert task.duration_ms == 0.0


class TestWorkflow:
    """Tests for Workflow model."""

    def test_create_workflow(self):
        """Test creating a workflow."""
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow",
        )

        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert workflow.status == TaskStatus.PENDING
        assert workflow.tasks == []

    def test_workflow_progress(self):
        """Test progress calculation."""
        workflow = Workflow(name="Test")

        # No tasks - 0% progress
        assert workflow.progress == 0.0

        # Add tasks
        task1 = Task(name="Task 1", status=TaskStatus.COMPLETED)
        task2 = Task(name="Task 2", status=TaskStatus.PENDING)
        workflow.tasks = [task1, task2]

        # 1 of 2 complete - 50%
        assert workflow.progress == 50.0

    def test_workflow_is_complete(self):
        """Test is_complete property."""
        workflow = Workflow(name="Test")

        # No tasks - complete
        assert workflow.is_complete is True

        # Add incomplete task
        task = Task(name="Task 1", status=TaskStatus.PENDING)
        workflow.tasks = [task]
        assert workflow.is_complete is False

        # Complete the task
        task.status = TaskStatus.COMPLETED
        assert workflow.is_complete is True


class TestTaskManagementCapability:
    """Tests for TaskManagementCapability."""

    @pytest.fixture
    def task_capability(self):
        """Create task management capability instance."""
        return TaskManagementCapability()

    def test_initialization(self, task_capability):
        """Test capability initialization."""
        assert task_capability.name == "task_management"
        assert "task" in task_capability.description.lower()

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, task_capability):
        """Test initialize and shutdown lifecycle."""
        await task_capability.initialize()
        assert task_capability.is_initialized is True
        assert task_capability._semaphore is not None

        await task_capability.shutdown()
        assert task_capability.is_initialized is False

    @pytest.mark.asyncio
    async def test_create_task(self, task_capability):
        """Test creating a task."""
        await task_capability.initialize()

        result = await task_capability.create_task(
            name="Test Task",
            description="A test task",
            priority="high",
        )

        assert result.success is True
        assert result.output["name"] == "Test Task"
        assert result.output["priority"] == "high"
        assert "id" in result.output

        await task_capability.shutdown()

    @pytest.mark.asyncio
    async def test_get_task(self, task_capability):
        """Test getting a task by ID."""
        await task_capability.initialize()

        # Create a task first
        create_result = await task_capability.create_task(name="Test Task")
        task_id = create_result.output["id"]

        # Get the task
        get_result = await task_capability.get_task(task_id)

        assert get_result.success is True
        assert get_result.output["id"] == task_id
        assert get_result.output["name"] == "Test Task"

        await task_capability.shutdown()

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, task_capability):
        """Test getting a nonexistent task."""
        await task_capability.initialize()

        result = await task_capability.execute(
            action="get_task",
            task_id="nonexistent_id",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

        await task_capability.shutdown()

    @pytest.mark.asyncio
    async def test_run_task(self, task_capability):
        """Test running a task."""
        await task_capability.initialize()

        # Create a task
        create_result = await task_capability.create_task(name="Run Test")
        task_id = create_result.output["id"]

        # Run the task
        run_result = await task_capability.run_task(task_id)

        assert run_result.success is True
        assert run_result.output["status"] == "completed"

        await task_capability.shutdown()

    @pytest.mark.asyncio
    async def test_create_workflow(self, task_capability):
        """Test creating a workflow."""
        await task_capability.initialize()

        tasks = [
            {"name": "Step 1", "description": "First step"},
            {"name": "Step 2", "depends_on": ["Step 1"]},
            {"name": "Step 3", "depends_on": ["Step 2"]},
        ]

        result = await task_capability.create_workflow(
            name="Test Workflow",
            tasks=tasks,
        )

        assert result.success is True
        assert result.output["name"] == "Test Workflow"
        assert len(result.output["tasks"]) == 3

        await task_capability.shutdown()

    @pytest.mark.asyncio
    async def test_run_workflow_sequential(self, task_capability):
        """Test running a workflow sequentially."""
        await task_capability.initialize()

        # Create workflow
        tasks = [
            {"name": "Step 1"},
            {"name": "Step 2", "depends_on": ["Step 1"]},
        ]

        create_result = await task_capability.create_workflow(
            name="Sequential Workflow",
            tasks=tasks,
        )
        workflow_id = create_result.output["id"]

        # Run workflow
        run_result = await task_capability.run_workflow(workflow_id)

        assert run_result.success is True
        assert run_result.output["status"] == "completed"

        await task_capability.shutdown()

    @pytest.mark.asyncio
    async def test_list_tasks(self, task_capability):
        """Test listing tasks."""
        await task_capability.initialize()

        # Create some tasks
        await task_capability.create_task(name="Task 1")
        await task_capability.create_task(name="Task 2")
        await task_capability.create_task(name="Task 3")

        # List tasks
        result = await task_capability.execute(action="list_tasks")

        assert result.success is True
        assert len(result.output) >= 3

        await task_capability.shutdown()

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, task_capability):
        """Test execute with unknown action."""
        await task_capability.initialize()

        result = await task_capability.execute(action="unknown_action")

        assert result.success is False
        assert "Unknown action" in result.error

        await task_capability.shutdown()

    @pytest.mark.asyncio
    async def test_active_and_pending_counts(self, task_capability):
        """Test active_tasks and pending_tasks properties."""
        await task_capability.initialize()

        # Create tasks
        await task_capability.create_task(name="Pending Task 1")
        await task_capability.create_task(name="Pending Task 2")

        assert task_capability.pending_tasks >= 2
        assert task_capability.active_tasks == 0

        await task_capability.shutdown()

    def test_register_handler(self, task_capability):
        """Test registering a task handler."""

        async def handler(task, context):
            return {"handled": True}

        task_capability.register_handler("task_123", handler)

        assert "task_123" in task_capability._handlers


class TestTaskManagementIntegration:
    """Integration-style tests for TaskManagementCapability."""

    @pytest.fixture
    def capability(self):
        """Create capability for tests."""
        return TaskManagementCapability(config=TaskConfig(max_concurrent_tasks=3))

    @pytest.mark.asyncio
    async def test_full_workflow_lifecycle(self, capability):
        """Test full workflow lifecycle."""
        await capability.initialize()

        # Create workflow with dependencies
        tasks = [
            {"name": "Design", "priority": "high"},
            {"name": "Implement", "depends_on": ["Design"]},
            {"name": "Test", "depends_on": ["Implement"]},
            {"name": "Deploy", "depends_on": ["Test"]},
        ]

        create_result = await capability.create_workflow(
            name="Development Pipeline",
            tasks=tasks,
        )
        assert create_result.success

        workflow_id = create_result.output["id"]

        # Run workflow
        run_result = await capability.run_workflow(workflow_id)
        assert run_result.success
        assert run_result.output["status"] == "completed"

        # Check all tasks completed
        get_result = await capability.execute(
            action="get_workflow",
            workflow_id=workflow_id,
        )
        # All tasks should be completed
        tasks_data = get_result.output.get("tasks", [])
        assert len(tasks_data) == 4
        assert all(t["status"] == "completed" for t in tasks_data)

        await capability.shutdown()
