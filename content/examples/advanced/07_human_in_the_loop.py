"""Example: Human-in-the-Loop Approval Workflow.

This example demonstrates Paracle's Human-in-the-Loop approval system
for AI governance and oversight (ISO 42001 compliance).

The workflow simulates a code deployment pipeline where:
1. Analyze step: AI analyzes the code changes
2. Security Review step: AI checks for security issues
3. Deploy step: REQUIRES HUMAN APPROVAL before executing

This pattern ensures human oversight of critical AI-driven decisions.
"""

import asyncio
from typing import Any

from paracle_domain.models import Workflow, WorkflowSpec, WorkflowStep
from paracle_events import EventBus
from paracle_orchestration import ApprovalManager, ExecutionStatus, WorkflowOrchestrator


def create_deployment_workflow() -> Workflow:
    """Create a deployment workflow with approval gates.

    This workflow has 3 steps:
    1. analyze - Analyze code changes (no approval needed)
    2. security - Security review (no approval needed)
    3. deploy - Production deployment (REQUIRES APPROVAL)
    """
    spec = WorkflowSpec(
        name="deployment-pipeline",
        description="CI/CD pipeline with human approval for production",
        steps=[
            # Step 1: Analyze changes (automatic)
            WorkflowStep(
                id="analyze",
                name="analyze",
                agent="code-analyzer",
                inputs={"scope": "changed_files"},
            ),
            # Step 2: Security review (automatic)
            WorkflowStep(
                id="security",
                name="security",
                agent="security-reviewer",
                depends_on=["analyze"],
            ),
            # Step 3: Deploy to production (REQUIRES HUMAN APPROVAL)
            WorkflowStep(
                id="deploy",
                name="deploy",
                agent="deployer",
                depends_on=["security"],
                requires_approval=True,  # <-- Key flag!
                approval_config={
                    "required": True,
                    "timeout_seconds": 120,  # 2 minutes for demo
                    "priority": "high",
                    "approvers": [],  # Empty = anyone can approve
                },
            ),
        ],
    )
    return Workflow(spec=spec)


async def mock_step_executor(
    step: WorkflowStep, inputs: dict[str, Any]
) -> dict[str, Any]:
    """Mock step executor that simulates AI agent execution.

    In a real application, this would call actual LLM providers
    and execute agent logic.
    """
    print(f"\n  [Agent: {step.agent}] Executing step '{step.name}'...")
    await asyncio.sleep(0.5)  # Simulate processing

    if step.name == "analyze":
        return {
            "files_changed": 5,
            "lines_added": 150,
            "lines_removed": 30,
            "complexity_delta": "+2",
            "recommendation": "Changes look reasonable",
        }

    if step.name == "security":
        return {
            "vulnerabilities_found": 0,
            "security_score": "A",
            "scan_completed": True,
            "recommendation": "No security issues detected",
        }

    if step.name == "deploy":
        return {
            "deployed_to": "production",
            "version": "v1.2.3",
            "timestamp": "2026-01-05T12:00:00Z",
            "status": "SUCCESS",
        }

    return {"status": "completed"}


async def simulate_human_approval(
    approval_manager: ApprovalManager,
    auto_approve: bool = True,
    delay: float = 2.0,
) -> None:
    """Simulate a human reviewing and approving/rejecting requests.

    In a real application, this would be:
    - A web UI where admins review pending approvals
    - A Slack integration that posts approval requests
    - An email notification system
    - The REST API (/approvals/pending, /approvals/{id}/approve)

    Args:
        approval_manager: The approval manager to monitor
        auto_approve: Whether to auto-approve (True) or reject (False)
        delay: Delay before making decision
    """
    print("\n[Human] Monitoring for approval requests...")

    # Wait for approval request to appear
    for _ in range(20):  # Max 10 seconds
        await asyncio.sleep(0.5)
        pending = approval_manager.list_pending()
        if pending:
            break

    if not pending:
        print("[Human] No approval requests found.")
        return

    request = pending[0]
    print("\n[Human] Received approval request:")
    print(f"        Step: {request.step_name}")
    print(f"        Agent: {request.agent_name}")
    print(f"        Priority: {request.priority.value}")
    print(f"        Context: {request.context.get('step_output', {})}")

    # Simulate review time
    print(f"\n[Human] Reviewing request (simulating {delay}s delay)...")
    await asyncio.sleep(delay)

    if auto_approve:
        print("[Human] APPROVED - Changes look safe to deploy.")
        await approval_manager.approve(
            request.id,
            approver="senior-engineer@example.com",
            reason="Reviewed and approved for production deployment",
        )
    else:
        print("[Human] REJECTED - Needs more testing.")
        await approval_manager.reject(
            request.id,
            approver="security-team@example.com",
            reason="Please add more unit tests before deploying",
        )


async def run_approval_workflow(auto_approve: bool = True) -> None:
    """Run the deployment workflow with human approval.

    Args:
        auto_approve: If True, simulates approval. If False, simulates rejection.
    """
    print("=" * 60)
    print("Paracle Human-in-the-Loop Demo")
    print("=" * 60)
    print(f"\nScenario: {'APPROVAL' if auto_approve else 'REJECTION'}")

    # Create components
    event_bus = EventBus()
    approval_manager = ApprovalManager(event_bus)
    orchestrator = WorkflowOrchestrator(
        event_bus=event_bus,
        step_executor=mock_step_executor,
        approval_manager=approval_manager,
    )
    workflow = create_deployment_workflow()

    # Define workflow inputs
    inputs = {
        "branch": "feature/new-feature",
        "commit": "abc123",
        "author": "developer@example.com",
    }

    print(f"\nStarting workflow: {workflow.spec.name}")
    print(f"Inputs: {inputs}")

    # Run workflow and human approval simulation concurrently
    async def run_workflow():
        return await orchestrator.execute(workflow, inputs)

    # Start both tasks
    workflow_task = asyncio.create_task(run_workflow())
    approval_task = asyncio.create_task(
        simulate_human_approval(approval_manager, auto_approve, delay=1.5)
    )

    # Wait for workflow to complete
    context = await workflow_task

    # Cancel approval task if still running
    approval_task.cancel()
    try:
        await approval_task
    except asyncio.CancelledError:
        pass

    # Print results
    print("\n" + "=" * 60)
    print("Workflow Results")
    print("=" * 60)
    print(f"\nStatus: {context.status.value}")
    print(f"Duration: {context.duration_seconds:.2f}s")

    if context.status == ExecutionStatus.COMPLETED:
        print("\nStep Results:")
        for step_name, result in context.step_results.items():
            print(f"  - {step_name}: {result}")
    else:
        print(f"\nErrors: {context.errors}")

    # Print approval statistics
    stats = approval_manager.get_stats()
    print("\nApproval Statistics:")
    print(f"  - Pending: {stats['pending_count']}")
    print(f"  - Approved: {stats['approved_count']}")
    print(f"  - Rejected: {stats['rejected_count']}")


async def demo_api_approval() -> None:
    """Demonstrate using the Approval API endpoints.

    This shows what would happen via REST API calls:
    - GET /approvals/pending - List pending approvals
    - GET /approvals/{id} - Get approval details
    - POST /approvals/{id}/approve - Approve request
    - POST /approvals/{id}/reject - Reject request
    """
    print("\n" + "=" * 60)
    print("API-Based Approval Demo")
    print("=" * 60)

    print(
        """
    In production, approvals are managed via the REST API:

    1. List pending approvals:
       GET /approvals/pending

    2. Get approval details:
       GET /approvals/{approval_id}

    3. Approve a request:
       POST /approvals/{approval_id}/approve
       Body: {"approver": "admin@example.com", "reason": "LGTM"}

    4. Reject a request:
       POST /approvals/{approval_id}/reject
       Body: {"approver": "admin@example.com", "reason": "Needs tests"}

    5. Get statistics:
       GET /approvals/stats

    Example curl commands:

    # Start the API server
    paracle serve

    # List pending approvals
    curl http://localhost:8000/approvals/pending

    # Approve a request
    curl -X POST http://localhost:8000/approvals/approval_xxx/approve \\
         -H "Content-Type: application/json" \\
         -d '{"approver": "admin@example.com", "reason": "Approved"}'
    """
    )


async def main() -> None:
    """Main entry point for the demo."""
    # Demo 1: Workflow with approval (approved)
    await run_approval_workflow(auto_approve=True)

    print("\n\n")

    # Demo 2: Workflow with approval (rejected)
    await run_approval_workflow(auto_approve=False)

    # Demo 3: Show API usage
    await demo_api_approval()


if __name__ == "__main__":
    asyncio.run(main())
