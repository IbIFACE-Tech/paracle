"""Example: YOLO Mode - Auto-Approve Workflow Execution.

This example demonstrates Paracle's YOLO (You Only Live Once) mode,
which automatically approves all Human-in-the-Loop approval gates.

Use cases:
- CI/CD pipelines that need to run unattended
- Development/testing without manual intervention
- Trusted automation workflows
- Non-critical operations

⚠️ WARNING: Use YOLO mode responsibly! In production, ensure:
   - Workflows are thoroughly tested
   - Approval policies are configured
   - Audit logs are monitored
   - Compliance requirements are met
"""

import asyncio
from typing import Any

from paracle_domain.models import Workflow, WorkflowSpec, WorkflowStep
from paracle_events import EventBus
from paracle_orchestration import ApprovalManager, WorkflowOrchestrator


def create_ci_cd_workflow() -> Workflow:
    """Create a CI/CD workflow with multiple approval gates.

    This workflow simulates a deployment pipeline:
    1. test - Run test suite (no approval)
    2. build - Build Docker image (no approval)
    3. deploy_staging - Deploy to staging (APPROVAL GATE)
    4. smoke_test - Run smoke tests (no approval)
    5. deploy_prod - Deploy to production (APPROVAL GATE)

    Without YOLO mode, this would require 2 manual approvals.
    With YOLO mode, all gates are auto-approved.
    """
    spec = WorkflowSpec(
        name="cicd-pipeline",
        description="Automated CI/CD with approval gates",
        steps=[
            # Step 1: Test (automatic)
            WorkflowStep(
                id="test",
                name="test",
                agent="test-runner",
                inputs={"scope": "all"},
            ),
            # Step 2: Build (automatic)
            WorkflowStep(
                id="build",
                name="build",
                agent="docker-builder",
                depends_on=["test"],
            ),
            # Step 3: Deploy to Staging (APPROVAL GATE #1)
            WorkflowStep(
                id="deploy_staging",
                name="deploy_staging",
                agent="deployer",
                depends_on=["build"],
                requires_approval=True,
                approval_config={
                    "required": True,
                    "timeout_seconds": 300,
                    "priority": "medium",
                },
            ),
            # Step 4: Smoke Test (automatic)
            WorkflowStep(
                id="smoke_test",
                name="smoke_test",
                agent="test-runner",
                depends_on=["deploy_staging"],
            ),
            # Step 5: Deploy to Production (APPROVAL GATE #2)
            WorkflowStep(
                id="deploy_prod",
                name="deploy_prod",
                agent="deployer",
                depends_on=["smoke_test"],
                requires_approval=True,
                approval_config={
                    "required": True,
                    "timeout_seconds": 600,
                    "priority": "high",
                },
            ),
        ],
    )
    return Workflow(spec=spec)


async def mock_step_executor(
    step: WorkflowStep, inputs: dict[str, Any]
) -> dict[str, Any]:
    """Mock step executor (simulates real work)."""
    print(f"  [Agent: {step.agent}] Executing '{step.name}'...")
    await asyncio.sleep(0.3)

    # Simulate different outputs per step
    outputs = {
        "test": {
            "tests_passed": 150,
            "tests_failed": 0,
            "coverage": "92%",
            "status": "SUCCESS",
        },
        "build": {
            "image": "myapp:v1.2.3",
            "size_mb": 450,
            "status": "SUCCESS",
        },
        "deploy_staging": {
            "environment": "staging",
            "url": "https://staging.example.com",
            "status": "DEPLOYED",
        },
        "smoke_test": {
            "tests_passed": 10,
            "tests_failed": 0,
            "status": "SUCCESS",
        },
        "deploy_prod": {
            "environment": "production",
            "url": "https://example.com",
            "status": "DEPLOYED",
        },
    }

    return outputs.get(step.name, {"status": "completed"})


async def run_without_yolo() -> None:
    """Run workflow WITHOUT YOLO mode (requires manual approval).

    This will create approval requests and wait for human decision.
    In a real application, you would approve via:
    - REST API: POST /api/v1/approvals/{id}/approve
    - CLI: paracle approval approve {id}
    - Web UI: Click "Approve" button
    """
    print("\n" + "=" * 60)
    print("SCENARIO 1: WITHOUT YOLO MODE (Manual Approval Required)")
    print("=" * 60)

    event_bus = EventBus()
    approval_manager = ApprovalManager(event_bus)
    orchestrator = WorkflowOrchestrator(
        event_bus=event_bus,
        step_executor=mock_step_executor,
        approval_manager=approval_manager,
    )

    workflow = create_ci_cd_workflow()

    print("\n🚀 Starting workflow execution...")
    print("   (This will pause at approval gates)")

    try:
        # Execute WITHOUT auto_approve (default behavior)
        result = await orchestrator.execute(
            workflow,
            inputs={"version": "v1.2.3"},
            timeout_seconds=5,  # Will timeout waiting for approval
        )
        print(f"\n✅ Workflow completed: {result.status}")

    except Exception as e:
        print(f"\n⏱️  Workflow timed out (expected!): {e}")
        print("   In real usage, you would approve via API/CLI")

    # Show pending approvals
    pending = approval_manager.list_pending()
    if pending:
        print(f"\n📋 Pending approvals: {len(pending)}")
        for req in pending:
            print(f"   - {req.step_name} (ID: {req.id})")


async def run_with_yolo() -> None:
    """Run workflow WITH YOLO mode (auto-approve all gates).

    This demonstrates how YOLO mode enables unattended execution
    by automatically approving all approval gates.
    """
    print("\n" + "=" * 60)
    print("SCENARIO 2: WITH YOLO MODE (Auto-Approve Enabled)")
    print("=" * 60)

    event_bus = EventBus()

    # Create ApprovalManager with YOLO mode enabled
    approval_manager = ApprovalManager(
        event_bus,
        auto_approve=True,  # 🎯 YOLO MODE!
        auto_approver="system:yolo",
    )

    orchestrator = WorkflowOrchestrator(
        event_bus=event_bus,
        step_executor=mock_step_executor,
        approval_manager=approval_manager,
    )

    workflow = create_ci_cd_workflow()

    print("\n⚠️  YOLO MODE ENABLED - Auto-approving all gates")
    print("🚀 Starting workflow execution...")

    # Execute - will complete without manual intervention
    result = await orchestrator.execute(
        workflow,
        inputs={"version": "v1.2.3"},
    )

    print(f"\n✅ Workflow completed: {result.status}")
    print(f"📊 Steps completed: {len(result.step_results)}")

    # Show results
    print("\n📋 Step Results:")
    for step_name, step_result in result.step_results.items():
        print(f"   {step_name}: {step_result.get('status', 'N/A')}")

    # Show that approvals were auto-approved
    print("\n🤖 Auto-Approvals:")
    # In real implementation, query approval history
    print("   - deploy_staging: Auto-approved by system:yolo")
    print("   - deploy_prod: Auto-approved by system:yolo")


async def run_with_yolo_selective() -> None:
    """Demonstrate selective YOLO mode (some steps require human approval).

    This shows how to use approval policies to override YOLO mode
    for critical steps.
    """
    print("\n" + "=" * 60)
    print("SCENARIO 3: SELECTIVE YOLO (Policy Overrides)")
    print("=" * 60)

    print("\n💡 In this scenario:")
    print("   - Staging deployment: Auto-approved (YOLO)")
    print("   - Production deployment: Requires human (policy override)")
    print("   (Not implemented in this example - see docs/yolo-mode-design.md)")


async def main() -> None:
    """Run all examples."""
    print("=" * 60)
    print("YOLO MODE EXAMPLES")
    print("=" * 60)

    # Example 1: Normal mode (requires manual approval)
    await run_without_yolo()

    await asyncio.sleep(1)

    # Example 2: YOLO mode (auto-approve)
    await run_with_yolo()

    await asyncio.sleep(1)

    # Example 3: Selective YOLO
    await run_with_yolo_selective()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\n✅ YOLO mode is useful for:")
    print("   - CI/CD pipelines")
    print("   - Development/testing")
    print("   - Trusted automation")
    print("   - Non-critical workflows")
    print("\n⚠️  Use with caution for:")
    print("   - Production deployments")
    print("   - Security-sensitive operations")
    print("   - Financial transactions")
    print("   - Compliance-required approvals")
    print("\n📖 For more info, see: docs/yolo-mode-design.md")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
