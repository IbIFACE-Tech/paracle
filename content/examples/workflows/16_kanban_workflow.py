"""Example: Kanban workflow for task management.

This example demonstrates how to use the Kanban task management system
to organize and track work across agents.
"""

import sys

from paracle_kanban import Board, Task, TaskPriority, TaskStatus, TaskType
from paracle_kanban.board import BoardRepository

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    """Demonstrate Kanban workflow."""
    print("=== Paracle Kanban Example ===\n")

    # Initialize repository
    repo = BoardRepository()

    # Create a board
    print("1. Creating a board...")
    board = Board(
        name="Feature Development",
        description="Track feature implementation tasks",
    )
    board = repo.create_board(board)
    print(f"   [OK] Created board: {board.name} ({board.id})\n")

    # Create tasks
    print("2. Creating tasks...")
    tasks = [
        Task(
            board_id=board.id,
            title="Design API endpoints",
            description="Design REST API for user management",
            priority=TaskPriority.HIGH,
            task_type=TaskType.FEATURE,
            tags=["api", "design"],
        ),
        Task(
            board_id=board.id,
            title="Implement authentication",
            description="Add JWT authentication middleware",
            priority=TaskPriority.CRITICAL,
            task_type=TaskType.FEATURE,
            tags=["auth", "security"],
        ),
        Task(
            board_id=board.id,
            title="Write unit tests",
            description="Add test coverage for auth module",
            priority=TaskPriority.MEDIUM,
            task_type=TaskType.TEST,
            tags=["testing", "auth"],
        ),
        Task(
            board_id=board.id,
            title="Update API documentation",
            description="Document new endpoints",
            priority=TaskPriority.LOW,
            task_type=TaskType.DOCS,
            tags=["docs", "api"],
        ),
    ]

    for task in tasks:
        task = repo.create_task(task)
        print(f"   [OK] Created task: {task.title}")
    print()

    # Move tasks through workflow
    print("3. Moving tasks through workflow...")

    # Get first task and move to TODO
    task1 = tasks[0]
    task1.move_to(TaskStatus.TODO)
    repo.update_task(task1)
    print(f"   [OK] {task1.title} -> TODO")

    # Assign and start task
    task1.assign("architect_agent")
    task1.move_to(TaskStatus.IN_PROGRESS)
    repo.update_task(task1)
    print(f"   [OK] {task1.title} -> IN_PROGRESS (assigned to architect)")

    # Complete first task
    task1.move_to(TaskStatus.REVIEW)
    repo.update_task(task1)
    print(f"   [OK] {task1.title} -> REVIEW")

    task1.move_to(TaskStatus.DONE)
    repo.update_task(task1)
    print(f"   [OK] {task1.title} -> DONE")
    print()

    # Start second task
    task2 = tasks[1]
    task2.move_to(TaskStatus.TODO)
    task2.assign("coder_agent")
    task2.move_to(TaskStatus.IN_PROGRESS)
    repo.update_task(task2)
    print(f"   [OK] {task2.title} -> IN_PROGRESS (assigned to coder)")

    # Block task due to dependency
    task2.move_to(TaskStatus.BLOCKED, reason="Waiting for design review")
    repo.update_task(task2)
    print(f"   [OK] {task2.title} -> BLOCKED (waiting for design)\n")

    # List all tasks
    print("4. Current tasks:")
    all_tasks = repo.list_tasks(board_id=board.id)
    for task in all_tasks:
        status_icon = {
            TaskStatus.BACKLOG: "[BACKLOG]",
            TaskStatus.TODO: "[TODO]",
            TaskStatus.IN_PROGRESS: "[IN_PROGRESS]",
            TaskStatus.REVIEW: "[REVIEW]",
            TaskStatus.BLOCKED: "[BLOCKED]",
            TaskStatus.DONE: "[DONE]",
        }.get(task.status, "[?]")

        priority_icon = {
            TaskPriority.LOW: "[LOW]",
            TaskPriority.MEDIUM: "[MED]",
            TaskPriority.HIGH: "[HIGH]",
            TaskPriority.CRITICAL: "[CRIT]",
        }.get(task.priority, "[?]")

        assignee = f" (assigned: {task.assigned_to})" if task.assigned_to else ""
        print(f"   {status_icon} {priority_icon} {task.title}{assignee}")
        if task.blocked_by:
            print(f"      BLOCKED BY: {task.blocked_by}")
    print()

    # Get board statistics
    print("5. Board statistics:")
    stats = repo.get_board_stats(board.id)
    print(f"   Total tasks: {stats['total_tasks']}")
    print("   Status breakdown:")
    for status, count in stats["status_counts"].items():
        print(f"     {status}: {count}")
    print()

    # Show metrics for completed tasks
    print("6. Task metrics:")
    completed_tasks = repo.list_tasks(board_id=board.id, status=TaskStatus.DONE)
    for task in completed_tasks:
        if task.cycle_time():
            print(f"   [OK] {task.title}")
            print(f"     Cycle time: {task.cycle_time():.1f} hours")
            print(f"     Lead time: {task.lead_time():.1f} hours")
    print()

    # CLI Usage
    print("=== CLI Usage Examples ===\n")
    print("Create a board:")
    print('  paracle board create "My Board" ' '--description "Board description"\n')

    print("Create a task:")
    print('  paracle task create <board_id> "Task title" \\')
    print("    --priority HIGH --type FEATURE --tags api\n")

    print("List tasks:")
    print("  paracle task list --board <board_id>")
    print("  paracle task list --status IN_PROGRESS")
    print("  paracle task list --assignee coder_agent\n")

    print("Move task:")
    print("  paracle task move <task_id> IN_PROGRESS\n")

    print("Assign task:")
    print("  paracle task assign <task_id> coder_agent\n")

    print("Show board:")
    print("  paracle board show <board_id>  " "# Visual board with columns\n")

    print("Board stats:")
    print("  paracle board stats <board_id>  " "# Metrics and analytics\n")

    print("\nFor more help: paracle task --help, paracle board --help")


if __name__ == "__main__":
    main()
