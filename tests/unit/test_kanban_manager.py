"""Unit tests for paracle_kanban package - TaskManager and TaskBoard."""

import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from paracle_kanban import Task, TaskBoard, TaskManager, TaskPriority, TaskStatus
from paracle_kanban.storage import TaskStorage


@pytest.fixture
def temp_db():
    """Create temporary database directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def task_manager(temp_db):
    """Create TaskManager with temporary database."""
    db_path = temp_db / "tasks.db"
    return TaskManager(str(db_path))


@pytest.fixture
def task_board():
    """Create TaskBoard with default columns."""
    return TaskBoard()


@pytest.fixture
def sample_task():
    """Create sample task."""
    return Task(
        id="task-001",
        title="Implement feature X",
        description="Add new feature to API",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        tags=["backend", "api"],
        assigned_to="coder_agent",
        created_by="pm_agent",
    )


class TestTaskBoard:
    """Test TaskBoard functionality."""

    def test_initialization(self, task_board):
        """Test TaskBoard initialization with default columns."""
        assert task_board.name == "default"
        assert len(task_board.columns) == 4
        assert "TODO" in task_board.columns
        assert "IN_PROGRESS" in task_board.columns
        assert "BLOCKED" in task_board.columns
        assert "DONE" in task_board.columns

    def test_custom_board_name(self):
        """Test creating board with custom name."""
        board = TaskBoard(
            name="sprint-1", columns=["Backlog", "Active", "Done"])
        assert board.name == "sprint-1"
        assert len(board.columns) == 3
        assert "Backlog" in board.columns

    def test_add_task(self, task_board, sample_task):
        """Test adding task to board."""
        task_board.add_task(sample_task)

        assert len(task_board.tasks) == 1
        assert sample_task.id in task_board.tasks
        assert task_board.tasks[sample_task.id] == sample_task

    def test_get_task(self, task_board, sample_task):
        """Test getting task by ID."""
        task_board.add_task(sample_task)

        retrieved = task_board.get_task(sample_task.id)
        assert retrieved is not None
        assert retrieved.id == sample_task.id
        assert retrieved.title == sample_task.title

    def test_get_nonexistent_task(self, task_board):
        """Test getting task that doesn't exist."""
        result = task_board.get_task("nonexistent")
        assert result is None

    def test_update_task(self, task_board, sample_task):
        """Test updating task."""
        task_board.add_task(sample_task)

        updated = task_board.update_task(
            sample_task.id,
            title="Updated title",
            priority=TaskPriority.CRITICAL,
        )

        assert updated is not None
        assert updated.title == "Updated title"
        assert updated.priority == TaskPriority.CRITICAL
        assert updated.description == sample_task.description  # Unchanged

    def test_move_task(self, task_board, sample_task):
        """Test moving task between columns."""
        task_board.add_task(sample_task)

        moved = task_board.move_task(sample_task.id, TaskStatus.IN_PROGRESS)

        assert moved is not None
        assert moved.status == TaskStatus.IN_PROGRESS

    def test_complete_task(self, task_board, sample_task):
        """Test completing task."""
        task_board.add_task(sample_task)

        completed = task_board.complete_task(sample_task.id)

        assert completed is not None
        assert completed.status == TaskStatus.DONE
        assert completed.completed_at is not None

    def test_delete_task(self, task_board, sample_task):
        """Test deleting task."""
        task_board.add_task(sample_task)

        assert len(task_board.tasks) == 1

        success = task_board.delete_task(sample_task.id)

        assert success is True
        assert len(task_board.tasks) == 0

    def test_get_tasks_by_status(self, task_board):
        """Test filtering tasks by status."""
        task1 = Task(id="t1", title="Task 1", status=TaskStatus.TODO)
        task2 = Task(id="t2", title="Task 2", status=TaskStatus.TODO)
        task3 = Task(id="t3", title="Task 3", status=TaskStatus.IN_PROGRESS)

        task_board.add_task(task1)
        task_board.add_task(task2)
        task_board.add_task(task3)

        todo_tasks = task_board.get_tasks_by_status(TaskStatus.TODO)
        assert len(todo_tasks) == 2

        in_progress_tasks = task_board.get_tasks_by_status(
            TaskStatus.IN_PROGRESS)
        assert len(in_progress_tasks) == 1

    def test_get_tasks_by_priority(self, task_board):
        """Test filtering tasks by priority."""
        task1 = Task(id="t1", title="Task 1", priority=TaskPriority.HIGH)
        task2 = Task(id="t2", title="Task 2", priority=TaskPriority.HIGH)
        task3 = Task(id="t3", title="Task 3", priority=TaskPriority.LOW)

        task_board.add_task(task1)
        task_board.add_task(task2)
        task_board.add_task(task3)

        high_priority = task_board.get_tasks_by_priority(TaskPriority.HIGH)
        assert len(high_priority) == 2

    def test_get_statistics(self, task_board):
        """Test getting board statistics."""
        task_board.add_task(
            Task(id="t1", title="Task 1", status=TaskStatus.TODO))
        task_board.add_task(Task(id="t2", title="Task 2",
                            status=TaskStatus.IN_PROGRESS))
        task_board.add_task(
            Task(id="t3", title="Task 3", status=TaskStatus.DONE))

        stats = task_board.get_statistics()

        assert stats["total_tasks"] == 3
        assert stats["by_status"][TaskStatus.TODO] == 1
        assert stats["by_status"][TaskStatus.IN_PROGRESS] == 1
        assert stats["by_status"][TaskStatus.DONE] == 1


class TestTaskManager:
    """Test TaskManager with persistence."""

    def test_initialization(self, task_manager):
        """Test TaskManager initialization."""
        assert task_manager is not None
        assert task_manager.storage is not None

    def test_create_task(self, task_manager):
        """Test creating task with persistence."""
        task = task_manager.create_task(
            title="New task",
            description="Task description",
            priority=TaskPriority.MEDIUM,
            tags=["test"],
        )

        assert task is not None
        assert task.id is not None
        assert task.title == "New task"
        assert task.status == TaskStatus.TODO

    def test_get_task(self, task_manager):
        """Test retrieving task from storage."""
        created = task_manager.create_task(title="Test task")

        retrieved = task_manager.get_task(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == created.title

    def test_update_task(self, task_manager):
        """Test updating task in storage."""
        created = task_manager.create_task(title="Original")

        updated = task_manager.update_task(
            created.id,
            title="Updated",
            status=TaskStatus.IN_PROGRESS,
        )

        assert updated is not None
        assert updated.title == "Updated"
        assert updated.status == TaskStatus.IN_PROGRESS

        # Verify persistence
        retrieved = task_manager.get_task(created.id)
        assert retrieved.title == "Updated"

    def test_delete_task(self, task_manager):
        """Test deleting task from storage."""
        created = task_manager.create_task(title="To delete")

        success = task_manager.delete_task(created.id)

        assert success is True

        retrieved = task_manager.get_task(created.id)
        assert retrieved is None

    def test_list_tasks(self, task_manager):
        """Test listing all tasks."""
        task_manager.create_task(title="Task 1")
        task_manager.create_task(title="Task 2")
        task_manager.create_task(title="Task 3")

        tasks = task_manager.list_tasks()

        assert len(tasks) >= 3

    def test_search_tasks(self, task_manager):
        """Test searching tasks by query."""
        task_manager.create_task(title="Backend API feature")
        task_manager.create_task(title="Frontend UI update")
        task_manager.create_task(title="Backend database migration")

        results = task_manager.search_tasks("backend")

        assert len(results) == 2

    def test_archive_completed(self, task_manager):
        """Test archiving completed tasks."""
        task1 = task_manager.create_task(
            title="Task 1", status=TaskStatus.DONE)
        task2 = task_manager.create_task(
            title="Task 2", status=TaskStatus.TODO)

        archived_count = task_manager.archive_completed()

        assert archived_count >= 1

        # Completed task should be archived
        retrieved = task_manager.get_task(task1.id)
        assert retrieved is None or retrieved.status == TaskStatus.DONE

    def test_export_import(self, task_manager, temp_db):
        """Test exporting and importing tasks."""
        task_manager.create_task(title="Task 1", tags=["export"])
        task_manager.create_task(title="Task 2", tags=["export"])

        export_path = temp_db / "export.json"

        # Export
        task_manager.export_to_json(str(export_path))
        assert export_path.exists()

        # Clear database
        task_manager.clear_all()
        assert len(task_manager.list_tasks()) == 0

        # Import
        task_manager.import_from_json(str(export_path))
        imported = task_manager.list_tasks()

        assert len(imported) == 2

    def test_get_metrics(self, task_manager):
        """Test getting board metrics."""
        task_manager.create_task(title="High", priority=TaskPriority.HIGH)
        task_manager.create_task(title="Medium", priority=TaskPriority.MEDIUM)
        task_manager.create_task(title="Done", status=TaskStatus.DONE)

        metrics = task_manager.get_metrics()

        assert "total_tasks" in metrics
        assert "by_status" in metrics
        assert "by_priority" in metrics
        assert metrics["total_tasks"] >= 3


class TestTask:
    """Test Task model."""

    def test_task_creation(self):
        """Test creating task with required fields."""
        task = Task(
            id="test-001",
            title="Test task",
        )

        assert task.id == "test-001"
        assert task.title == "Test task"
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM

    def test_task_with_all_fields(self):
        """Test creating task with all fields."""
        due_date = datetime.now() + timedelta(days=7)

        task = Task(
            id="test-002",
            title="Complete task",
            description="Full description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.CRITICAL,
            tags=["urgent", "backend"],
            assigned_to="coder_agent",
            created_by="pm_agent",
            due_date=due_date,
        )

        assert task.description == "Full description"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.CRITICAL
        assert len(task.tags) == 2
        assert task.assigned_to == "coder_agent"
        assert task.due_date == due_date

    def test_task_timestamps(self):
        """Test task timestamp fields."""
        task = Task(id="test-003", title="Timestamp test")

        assert task.created_at is not None
        assert task.updated_at is not None
        assert task.completed_at is None

        # Complete task
        task.status = TaskStatus.DONE
        task.completed_at = datetime.now()

        assert task.completed_at is not None

    def test_task_serialization(self):
        """Test task JSON serialization."""
        task = Task(
            id="test-004",
            title="Serialize me",
            tags=["test", "json"],
        )

        task_dict = task.model_dump()

        assert task_dict["id"] == "test-004"
        assert task_dict["title"] == "Serialize me"
        assert "tags" in task_dict


class TestTaskStorage:
    """Test TaskStorage persistence."""

    def test_storage_initialization(self, temp_db):
        """Test storage initialization."""
        db_path = temp_db / "test_storage.db"
        storage = TaskStorage(str(db_path))

        assert storage.db_path == db_path
        assert db_path.exists()

    def test_save_and_load(self, temp_db):
        """Test saving and loading tasks."""
        db_path = temp_db / "test_storage.db"
        storage = TaskStorage(str(db_path))

        task = Task(id="store-001", title="Store me")

        storage.save_task(task)
        loaded = storage.load_task(task.id)

        assert loaded is not None
        assert loaded.id == task.id
        assert loaded.title == task.title

    def test_delete_task(self, temp_db):
        """Test deleting task from storage."""
        db_path = temp_db / "test_storage.db"
        storage = TaskStorage(str(db_path))

        task = Task(id="delete-001", title="Delete me")
        storage.save_task(task)

        success = storage.delete_task(task.id)
        assert success is True

        loaded = storage.load_task(task.id)
        assert loaded is None

    def test_list_all_tasks(self, temp_db):
        """Test listing all tasks."""
        db_path = temp_db / "test_storage.db"
        storage = TaskStorage(str(db_path))

        storage.save_task(Task(id="list-001", title="Task 1"))
        storage.save_task(Task(id="list-002", title="Task 2"))

        tasks = storage.list_all_tasks()

        assert len(tasks) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
