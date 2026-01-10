"""Test Demo 7 standalone."""

import sys
sys.path.insert(0, ".")

from paracle_kanban.task import Task, TaskPriority, TaskStatus, TaskType
from paracle_orchestration.context import ExecutionContext, ExecutionStatus
from paracle_orchestration.kanban_integration import (
    execute_workflow_for_tasks,
    get_workflow_progress,
)


# Create backlog
backlog_tasks = [
    Task(
        board_id="sprint_2",
        title="Design user authentication UI",
        description="Create mockups and wireframes",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        task_type=TaskType.FEATURE,
        assigned_to="designer",
    ),
    Task(
        board_id="sprint_2",
        title="Implement authentication backend",
        description="JWT tokens, OAuth2 integration",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        task_type=TaskType.FEATURE,
        assigned_to="backend_dev",
    ),
    Task(
        board_id="sprint_2",
        title="Write integration tests",
        description="Test auth flows end-to-end",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        task_type=TaskType.CHORE,
        assigned_to="qa_engineer",
    ),
    Task(
        board_id="sprint_2",
        title="Update API documentation",
        description="Document new auth endpoints",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        task_type=TaskType.CHORE,
        assigned_to="tech_writer",
    ),
    Task(
        board_id="sprint_2",
        title="Deploy to staging",
        description="Deploy auth feature to staging environment",
        status=TaskStatus.TODO,
        priority=TaskPriority.LOW,
        task_type=TaskType.CHORE,
        assigned_to="devops",
    ),
]

print("📋 Sprint Backlog created with 5 tasks:")
for i, task in enumerate(backlog_tasks, 1):
    print(f"   {i}. {task.title} ({task.task_type})")
    print(f"      Status: {task.status} | "
          f"Priority: {task.priority} | "
          f"Assigned: {task.assigned_to}")

# Create Sprint Workflow
sprint_context = ExecutionContext(
    workflow_id="sprint_2_execution",
    execution_id="exec_sprint_002",
    inputs={"sprint_name": "Sprint 2 - Authentication Feature"},
    status=ExecutionStatus.RUNNING,
    metadata={
        "workflow_name": "Sprint 2 Execution",
        "sprint_duration": "2 weeks",
    },
)

# Link all tasks to the sprint workflow
task_ids = [task.id for task in backlog_tasks]
progress_info = execute_workflow_for_tasks(
    workflow_id="sprint_2_execution",
    task_ids=task_ids,
    workflow_engine=None,  # Mock for demo
    context=sprint_context,
)

print(f"\n🚀 Sprint Workflow Started!")
print(f"   Workflow: {progress_info['workflow_id']}")
print(f"   Execution: {progress_info['execution_id']}")
print(f"   Managing: {progress_info['total_tasks']} tasks")

# Simulate task progression
print("\n📊 Sprint Progress Simulation:")

# Day 1-10: Complete all tasks
tasks_progress = [
    (1, 0, TaskStatus.IN_PROGRESS, "started"),
    (3, 0, TaskStatus.DONE, "completed"),
    (3, 1, TaskStatus.IN_PROGRESS, "started"),
    (5, 1, TaskStatus.DONE, "completed"),
    (5, 2, TaskStatus.IN_PROGRESS, "started"),
    (7, 2, TaskStatus.DONE, "completed"),
    (7, 3, TaskStatus.IN_PROGRESS, "started"),
    (9, 3, TaskStatus.DONE, "completed"),
    (9, 4, TaskStatus.IN_PROGRESS, "started"),
    (10, 4, TaskStatus.DONE, "completed"),
]

for day, task_idx, status, action in tasks_progress:
    backlog_tasks[task_idx].status = status
    print(f"   Day {day}: {backlog_tasks[task_idx].title} → {status}")

# Calculate final progress
class MockTaskManager:
    def __init__(self, tasks):
        self.tasks = {t.id: t for t in tasks}

    def get_task(self, task_id):
        return self.tasks[task_id]

mock_manager = MockTaskManager(backlog_tasks)
final_progress = get_workflow_progress(sprint_context, mock_manager)

print(f"\n✅ Sprint Completed!")
print(f"   Progress: {final_progress['completed']}/"
      f"{final_progress['total']} tasks "
      f"({final_progress['progress_percentage']}%)")
print(f"   Completed: {final_progress['completed']} tasks")
print(f"   In Progress: {final_progress['in_progress']} tasks")
print(f"   Blocked: {final_progress['blocked']} tasks")

print("\n💡 Use Case:")
print("   ✓ Manage entire sprints with workflow orchestration")
print("   ✓ Track progress across multiple tasks in one view")
print("   ✓ Automate sprint ceremonies (daily standup reports)")
print("   ✓ Calculate team velocity and metrics")
