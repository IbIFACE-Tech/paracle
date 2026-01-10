"""Example: Bidirectional Workflow ↔ Kanban Integration.

This example demonstrates how workflows and Kanban tasks can be linked
and synchronized bidirectionally:

1. Workflow → Kanban: Track workflow execution in Kanban board
2. Kanban → Workflow: Trigger workflow when task starts
3. State Sync: Automatic status synchronization
4. Multiple Links: One task can have multiple workflow executions
"""


from paracle_kanban.task import Task, TaskPriority, TaskStatus, TaskType
from paracle_orchestration.context import ExecutionContext, ExecutionStatus
from paracle_orchestration.kanban_integration import (
    TaskWorkflowSync,
)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_1_workflow_to_kanban():
    """Demo 1: Create a Kanban task to track workflow execution."""
    print_section("Demo 1: Workflow → Kanban (Track execution)")

    # Create a workflow execution context
    context = ExecutionContext(
        workflow_id="feature_development",
        execution_id="exec_001",
        inputs={"feature": "user_auth"},
        status=ExecutionStatus.RUNNING,
        metadata={"workflow_name": "Feature Development",
                  "requested_by": "coder"},
    )

    print(f"📋 Workflow started: {context.workflow_id}")
    print(f"   Execution ID: {context.execution_id}")
    print(f"   Status: {context.status.value}")

    # Create a Kanban task to track this workflow
    task = TaskWorkflowSync.create_task_from_workflow(
        workflow_id=context.workflow_id,
        execution_id=context.execution_id,
        context=context,
        board_id="sprint_1",
    )

    print(f"\n✅ Created tracking task: {task.id}")
    print(f"   Title: {task.title}")
    print(f"   Status: {task.status.value}")
    print(f"   Linked workflow: {task.metadata.get('primary_workflow_id')}")

    # Simulate workflow progress
    print("\n🔄 Simulating workflow progress...")

    # Step 1: Workflow awaits approval
    context.status = ExecutionStatus.AWAITING_APPROVAL
    updated = TaskWorkflowSync.sync_workflow_to_task(task, context)
    print("   Workflow → AWAITING_APPROVAL")
    print(f"   Task status updated: {updated} → {task.status.value}")

    # Step 2: Workflow completes
    context.status = ExecutionStatus.COMPLETED
    updated = TaskWorkflowSync.sync_workflow_to_task(task, context)
    print("   Workflow → COMPLETED")
    print(f"   Task status updated: {updated} → {task.status.value}")

    # Show sync metadata
    workflow_info = TaskWorkflowSync.get_workflow_info_from_task(task)
    print("\n📊 Sync metadata:")
    print(f"   Last synced: {workflow_info['last_sync_at']}")
    print(f"   Synced from: {workflow_info['last_sync_from']}")


def demo_2_kanban_to_workflow():
    """Demo 2: Trigger workflow execution from Kanban task."""
    print_section("Demo 2: Kanban → Workflow (Trigger execution)")

    # Create a Kanban task for a feature
    task = Task(
        board_id="backlog",
        title="Implement payment gateway",
        description="Integrate Stripe payment processing",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        task_type=TaskType.FEATURE,
        assigned_to="coder",
    )

    # Link a workflow to this task
    workflow_id = "payment_integration"
    TaskWorkflowSync.link_workflow_to_task(task, workflow_id)

    print(f"📝 Created task: {task.id}")
    print(f"   Title: {task.title}")
    print(f"   Linked workflow: {task.metadata['primary_workflow_id']}")

    # User moves task to IN_PROGRESS → trigger workflow
    print("\n👤 User moves task to IN_PROGRESS...")
    task.move_to(TaskStatus.IN_PROGRESS)

    # Create a mock workflow execution
    context = ExecutionContext(
        workflow_id=workflow_id,
        execution_id="exec_002",
        inputs={"task_id": task.id, "payment_provider": "stripe"},
        status=ExecutionStatus.RUNNING,
    )

    # Link task to workflow execution
    TaskWorkflowSync.link_task_to_workflow(context, task.id)

    print(f"✅ Workflow execution started: {context.execution_id}")
    print(f"   Linked to task: {context.metadata['primary_task_id']}")

    # Simulate workflow completion
    context.complete({"integration_url": "https://api.stripe.com"})
    TaskWorkflowSync.sync_workflow_to_task(task, context)

    print("\n🎉 Workflow completed!")
    print(f"   Task status: {task.status.value}")
    print(f"   Output: {context.outputs}")


def demo_3_multiple_workflows_per_task():
    """Demo 3: One task can trigger multiple workflow executions."""
    print_section("Demo 3: Multiple Workflows per Task")

    # Create a complex task
    task = Task(
        board_id="sprint_1",
        title="Release v1.0.0",
        description="Complete release process",
        status=TaskStatus.TODO,
        priority=TaskPriority.CRITICAL,
        task_type=TaskType.FEATURE,
    )

    print(f"📝 Created release task: {task.id}")

    # Link multiple workflows
    workflows = [
        ("version_bump", "exec_v1"),
        ("changelog_generation", "exec_v2"),
        ("build_release", "exec_v3"),
        ("deploy_production", "exec_v4"),
    ]

    print(f"\n🔗 Linking {len(workflows)} workflows:")
    for wf_id, exec_id in workflows:
        TaskWorkflowSync.link_workflow_to_task(task, wf_id, exec_id)
        print(f"   ✓ {wf_id} (exec: {exec_id})")

    # Show all linked workflows
    workflow_info = TaskWorkflowSync.get_workflow_info_from_task(task)
    print(f"\n📊 Task has {len(workflow_info['workflows'])} linked workflows:")
    for wf in workflow_info["workflows"]:
        print(f"   • {wf['workflow_id']} → {wf['execution_id']}")


def demo_4_status_sync_edge_cases():
    """Demo 4: Handle edge cases in status synchronization."""
    print_section("Demo 4: Status Sync Edge Cases")

    # Create task in DONE status
    task = Task(
        board_id="sprint_1",
        title="Completed feature",
        description="Already done",
        status=TaskStatus.DONE,
        priority=TaskPriority.LOW,
        task_type=TaskType.FEATURE,
    )

    print(f"📝 Task status: {task.status.value} (already completed)")

    # Try to sync with RUNNING workflow (invalid transition)
    context = ExecutionContext(
        workflow_id="test_workflow",
        execution_id="exec_test",
        inputs={},
        status=ExecutionStatus.RUNNING,
    )

    print("\n🔄 Attempting to sync RUNNING workflow to DONE task...")
    updated = TaskWorkflowSync.sync_workflow_to_task(task, context)

    print(f"   Updated: {updated}")
    print(f"   Task status: {task.status.value} (unchanged)")

    if "pending_status" in task.metadata:
        print(
            f"   ⚠️ Pending status transition: {task.metadata['pending_status']}")
        print(
            f"   Status sync blocked: {task.metadata['status_sync_blocked']}")


def demo_5_bidirectional_sync():
    """Demo 5: Complete bidirectional synchronization."""
    print_section("Demo 5: Complete Bidirectional Sync")

    # Create task and workflow
    task = Task(
        board_id="sprint_2",
        title="Deploy microservice",
        description="Deploy user service to production",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        task_type=TaskType.FEATURE,
    )

    context = ExecutionContext(
        workflow_id="deployment",
        execution_id="exec_deploy",
        inputs={"service": "user_service", "environment": "production"},
        status=ExecutionStatus.PENDING,
    )

    print("📝 Initial state:")
    print(f"   Task: {task.id} → {task.status.value}")
    print(f"   Workflow: {context.execution_id} → {context.status.value}")

    # Link bidirectionally
    TaskWorkflowSync.link_workflow_to_task(
        task, context.workflow_id, context.execution_id)
    TaskWorkflowSync.link_task_to_workflow(context, task.id)

    print("\n🔗 Bidirectional linking established")
    print(f"   Task → Workflow: {task.metadata['primary_workflow_id']}")
    print(f"   Workflow → Task: {context.metadata['primary_task_id']}")

    # Simulate execution flow
    steps = [
        (ExecutionStatus.RUNNING, "Starting deployment..."),
        (ExecutionStatus.AWAITING_APPROVAL, "Awaiting production approval..."),
        (ExecutionStatus.RUNNING, "Approved, continuing deployment..."),
        (ExecutionStatus.COMPLETED, "Deployment successful!"),
    ]

    print("\n🔄 Synchronization flow:")
    for status, message in steps:
        context.status = status
        TaskWorkflowSync.sync_workflow_to_task(task, context)
        print(f"   {message}")
        print(
            f"   → Workflow: {context.status.value} | Task: {task.status.value}")

    # Final state
    print("\n✅ Final state:")
    print(f"   Task: {task.status.value}")
    print(f"   Workflow: {context.status.value}")
    print(
        f"   Both systems synchronized: {task.status.value == 'done' and context.status == ExecutionStatus.COMPLETED}")


def demo_6_production_pattern():
    """Demo 6: Production-ready pattern with basic integration."""
    print_section("Demo 6: Production Pattern")

    print("📋 Board concept: Q1 2026 Sprint")

    # Create task for a feature (without board for now)
    task = Task(
        board_id="sprint_q1",
        title="Implement user dashboard",
        description="Build analytics dashboard for users",
        priority=TaskPriority.HIGH,
        task_type=TaskType.FEATURE,
        assigned_to="coder",
        status=TaskStatus.TODO,
    )

    print(f"📝 Created task: {task.id}")

    # Link workflow
    workflow_id = "dashboard_development"
    TaskWorkflowSync.link_workflow_to_task(task, workflow_id)

    # Move to IN_PROGRESS (triggers workflow in real system)
    task.move_to(TaskStatus.IN_PROGRESS)

    print("\n👤 Task moved to IN_PROGRESS")
    print(f"   → This would trigger workflow: {workflow_id}")

    # Create execution context (mocked)
    context = ExecutionContext(
        workflow_id=workflow_id,
        execution_id="exec_dashboard",
        inputs={"task_id": task.id},
        status=ExecutionStatus.RUNNING,
        metadata={"triggered_by": "task_status_change", "task_id": task.id},
    )

    TaskWorkflowSync.link_task_to_workflow(context, task.id)

    # Simulate workflow steps
    print("\n🔄 Workflow execution:")
    steps_info = [
        ("design", "Generating UI mockups..."),
        ("implement", "Implementing dashboard components..."),
        ("test", "Running unit tests..."),
        ("review", "Code review in progress..."),
    ]

    for step_id, description in steps_info:
        print(f"   ⚙️ Step {step_id}: {description}")
        context.step_results[step_id] = {"completed": True}

    # Workflow completes
    context.complete({"dashboard_url": "https://app.example.com/dashboard"})
    TaskWorkflowSync.sync_workflow_to_task(task, context)

    print("\n✅ Workflow completed successfully!")
    print(f"   Task status: {task.status.value}")
    print(f"   Output: {context.outputs['dashboard_url']}")


def demo_7_workflow_orchestrates_backlog():
    """Demo 7: Workflow orchestrates multiple Kanban tasks from backlog."""
    print_section("Demo 7: Workflow Orchestrates Backlog (Sprint Pattern)")

    # Scenario: You have a backlog with 5 tasks for a sprint
    print("📋 Sprint Backlog:")
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

    for i, task in enumerate(backlog_tasks, 1):
        print(f"   {i}. {task.title} ({task.task_type.value})")
        print(f"      Status: {task.status.value} | "
              f"Priority: {task.priority.value} | "
              f"Assigned: {task.assigned_to}")

    # Create a Sprint Workflow that manages these tasks
    from paracle_orchestration.kanban_integration import (
        execute_workflow_for_tasks,
        get_workflow_progress,
    )

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

    print(f"\n🚀 Sprint Workflow Started:")
    print(f"   Workflow: {progress_info['workflow_id']}")
    print(f"   Execution: {progress_info['execution_id']}")
    print(f"   Managing: {progress_info['total_tasks']} tasks")
    print(f"   Linked at: {progress_info['linked_at']}")

    # Simulate task progression over time
    print("\n📊 Sprint Progress Simulation:")

    # Day 1: Start design task
    backlog_tasks[0].status = TaskStatus.IN_PROGRESS
    print(f"   Day 1: {backlog_tasks[0].title} → IN_PROGRESS")

    # Day 3: Design done, backend starts
    backlog_tasks[0].status = TaskStatus.DONE
    backlog_tasks[1].status = TaskStatus.IN_PROGRESS
    print(f"   Day 3: {backlog_tasks[0].title} → DONE")
    print(f"          {backlog_tasks[1].title} → IN_PROGRESS")

    # Day 5: Backend done, tests start
    backlog_tasks[1].status = TaskStatus.DONE
    backlog_tasks[2].status = TaskStatus.IN_PROGRESS
    print(f"   Day 5: {backlog_tasks[1].title} → DONE")
    print(f"          {backlog_tasks[2].title} → IN_PROGRESS")

    # Day 7: Tests done, docs in progress
    backlog_tasks[2].status = TaskStatus.DONE
    backlog_tasks[3].status = TaskStatus.IN_PROGRESS
    print(f"   Day 7: {backlog_tasks[2].title} → DONE")
    print(f"          {backlog_tasks[3].title} → IN_PROGRESS")

    # Day 9: Docs done, deployment starts
    backlog_tasks[3].status = TaskStatus.DONE
    backlog_tasks[4].status = TaskStatus.IN_PROGRESS
    print(f"   Day 9: {backlog_tasks[3].title} → DONE")
    print(f"          {backlog_tasks[4].title} → IN_PROGRESS")

    # Day 10: All done!
    backlog_tasks[4].status = TaskStatus.DONE
    print(f"   Day 10: {backlog_tasks[4].title} → DONE")

    # Calculate final progress
    # Mock a simple task manager for demo
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

    # Mark sprint workflow as complete
    sprint_context.complete({"sprint_velocity": 5, "tasks_completed": 5})

    print("\n💡 Use Case:")
    print("   - Manage entire sprints with workflow orchestration")
    print("   - Track progress across multiple tasks in one view")
    print("   - Automate sprint ceremonies (daily standup reports)")
    print("   - Calculate team velocity and metrics")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  WORKFLOW ↔ KANBAN BIDIRECTIONAL INTEGRATION")
    print("=" * 60)

    demos = [
        demo_1_workflow_to_kanban,
        demo_2_kanban_to_workflow,
        demo_3_multiple_workflows_per_task,
        demo_4_status_sync_edge_cases,
        demo_5_bidirectional_sync,
        demo_6_production_pattern,
        demo_7_workflow_orchestrates_backlog,
    ]

    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\n❌ Error in {demo.__name__}: {e}")

    print(f"\n{'='*60}")
    print("  ✅ All demos completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
