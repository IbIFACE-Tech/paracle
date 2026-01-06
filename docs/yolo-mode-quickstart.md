# YOLO Mode Implementation Guide

## Quick Start

**YOLO (You Only Live Once) mode** allows Paracle workflows to execute with automatic approval of all Human-in-the-Loop gates. This enables unattended execution for CI/CD, testing, and trusted automation.

## Current Status

✅ **Infrastructure Ready**: Paracle already has `ApprovalManager` with Human-in-the-Loop support
📝 **Implementation Needed**: Add `auto_approve` parameter and logic

## 5-Minute Implementation

### Step 1: Update ApprovalManager

**File**: `packages/paracle_orchestration/approval.py`

Add `auto_approve` parameter to `__init__`:

```python
class ApprovalManager:
    def __init__(
        self,
        event_bus: EventBus,
        auto_approve: bool = False,  # NEW
        auto_approver: str = "system:auto",  # NEW
    ) -> None:
        self.event_bus = event_bus
        self.auto_approve = auto_approve  # NEW
        self.auto_approver = auto_approver  # NEW
        # ... rest of init
```

Update `create_request` method:

```python
async def create_request(
    self,
    workflow_id: str,
    execution_id: str,
    step_id: str,
    step_name: str,
    agent_name: str,
    context: dict[str, Any],
    config: ApprovalConfig,
    priority: ApprovalPriority = ApprovalPriority.MEDIUM,
    metadata: dict[str, Any] | None = None,
) -> ApprovalRequest:
    """Create approval request with optional auto-approval."""

    # ... existing create logic ...

    # NEW: Auto-approve if YOLO mode enabled
    if self.auto_approve:
        await self.approve(
            request.id,
            approver=self.auto_approver,
            reason="Auto-approved: YOLO mode enabled",
        )

        # Emit audit event
        await self.event_bus.publish(Event(
            type="approval.auto_approved",
            data={
                "approval_id": request.id,
                "mode": "yolo",
                "workflow_id": workflow_id,
                "step_id": step_id,
                "approver": self.auto_approver,
            },
            source="approval_manager",
        ))

    return request
```

### Step 2: Update WorkflowOrchestrator

**File**: `packages/paracle_orchestration/engine.py`

Add `auto_approve` parameter to `execute`:

```python
async def execute(
    self,
    workflow: Workflow,
    inputs: dict[str, Any],
    timeout_seconds: float | None = None,
    execution_id: str | None = None,
    auto_approve: bool = False,  # NEW
) -> ExecutionContext:
    """Execute workflow with optional auto-approval.

    Args:
        workflow: Workflow to execute
        inputs: Input data
        timeout_seconds: Optional timeout
        execution_id: Optional execution ID
        auto_approve: If True, auto-approve all approval gates (YOLO mode)
    """

    # NEW: Create approval manager with YOLO setting
    if auto_approve:
        self.approval_manager = ApprovalManager(
            self.event_bus,
            auto_approve=True,
            auto_approver="system:orchestrator",
        )

    # ... rest of execution ...
```

### Step 3: Add CLI Support

**File**: `packages/paracle_cli/commands/workflow.py`

Add `--yolo` flag to `run` command:

```python
@click.command()
@click.argument("workflow_name")
@click.option("--inputs", "-i", help="JSON inputs")
@click.option(
    "--yolo",
    "--auto-approve",
    is_flag=True,
    help="Automatically approve all approval gates (YOLO mode)",
)
async def run(workflow_name: str, inputs: str | None, yolo: bool):
    """Execute a workflow.

    Use --yolo to auto-approve all approval gates.
    """
    if yolo:
        console.print(
            "[yellow]⚠️  YOLO MODE ENABLED - Auto-approving all approval gates[/yellow]"
        )

    # Parse inputs
    workflow_inputs = json.loads(inputs) if inputs else {}

    # Execute workflow with auto_approve flag
    result = await orchestrator.execute(
        workflow,
        workflow_inputs,
        auto_approve=yolo,  # NEW
    )

    console.print(f"✅ Workflow completed: {result.status}")
```

### Step 4: Add API Support

**File**: `packages/paracle_api/schemas/workflow.py`

Add `auto_approve` field to request schema:

```python
class WorkflowExecutionRequest(BaseModel):
    """Request to execute a workflow."""

    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow inputs"
    )
    auto_approve: bool = Field(
        default=False,
        description="Auto-approve all approval gates (YOLO mode)"
    )
    auto_approver: str = Field(
        default="api:system",
        description="Approver name for auto-approvals"
    )
```

**File**: `packages/paracle_api/routers/workflows.py`

Update execute endpoint:

```python
@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecutionRequest,
):
    """Execute a workflow with optional auto-approval."""

    if request.auto_approve:
        logger.warning(
            f"YOLO mode enabled for workflow {workflow_id} "
            f"by {request.auto_approver}"
        )

    result = await orchestrator.execute(
        workflow,
        request.inputs,
        auto_approve=request.auto_approve,  # NEW
    )

    return {
        "execution_id": result.execution_id,
        "status": result.status.value,
        "auto_approved": request.auto_approve,  # NEW
    }
```

## Usage Examples

### CLI

```bash
# Normal execution (requires manual approval)
paracle workflow run deploy-pipeline

# YOLO mode (auto-approve)
paracle workflow run deploy-pipeline --yolo

# Alias
paracle workflow run deploy-pipeline --auto-approve
```

### API

```bash
# Normal execution
curl -X POST http://localhost:8000/api/v1/workflows/wf_123/execute \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"version": "v1.2.3"}
  }'

# YOLO mode
curl -X POST http://localhost:8000/api/v1/workflows/wf_123/execute \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"version": "v1.2.3"},
    "auto_approve": true,
    "auto_approver": "api:deploy-bot"
  }'
```

### Python

```python
from paracle_orchestration import ApprovalManager, WorkflowOrchestrator
from paracle_events import EventBus

# Option 1: YOLO at ApprovalManager level
approval_manager = ApprovalManager(
    event_bus,
    auto_approve=True,
    auto_approver="system:my-app",
)
orchestrator = WorkflowOrchestrator(event_bus, step_executor, approval_manager)
result = await orchestrator.execute(workflow, inputs)

# Option 2: YOLO at execution level
orchestrator = WorkflowOrchestrator(event_bus, step_executor)
result = await orchestrator.execute(
    workflow,
    inputs,
    auto_approve=True,  # YOLO!
)
```

### Environment Variable

```bash
# Enable globally (use with caution!)
export PARACLE_AUTO_APPROVE=true
export PARACLE_AUTO_APPROVER=system:env

# Then all executions auto-approve
paracle workflow run deploy-pipeline
```

Add to `packages/paracle_core/config.py`:

```python
from pydantic_settings import BaseSettings

class ParacleSettings(BaseSettings):
    auto_approve: bool = Field(
        default=False,
        description="Global auto-approve (YOLO mode)",
    )
    auto_approver: str = Field(
        default="system:auto",
        description="Approver for auto-approvals",
    )

    class Config:
        env_prefix = "PARACLE_"
```

## Testing

### Unit Test

```python
# tests/unit/test_yolo_mode.py

async def test_approval_manager_yolo_mode():
    """YOLO mode should auto-approve all requests."""
    event_bus = EventBus()
    manager = ApprovalManager(event_bus, auto_approve=True)

    request = await manager.create_request(
        workflow_id="wf_123",
        execution_id="exec_456",
        step_id="deploy",
        step_name="deploy",
        agent_name="deployer",
        context={},
        config=ApprovalConfig(),
    )

    # Should be auto-approved
    assert request.status == ApprovalStatus.APPROVED
    assert request.approver == "system:auto"
    assert "Auto-approved" in request.decision_reason


async def test_workflow_execution_with_yolo():
    """Workflow should complete without manual approval in YOLO mode."""
    event_bus = EventBus()
    orchestrator = WorkflowOrchestrator(event_bus, mock_step_executor)

    workflow = create_workflow_with_approval_gate()

    result = await orchestrator.execute(
        workflow,
        inputs={},
        auto_approve=True,  # YOLO!
    )

    assert result.status == ExecutionStatus.COMPLETED
    assert len(result.step_results) == 3  # All steps completed
```

### Integration Test

```bash
# Run example
python examples/08_yolo_mode.py

# Output should show:
# - Without YOLO: Timeout waiting for approval
# - With YOLO: Completes successfully
```

## Audit & Compliance

All auto-approvals are auditable:

### Event Log

```json
{
  "type": "approval.auto_approved",
  "timestamp": "2026-01-05T12:00:00Z",
  "data": {
    "approval_id": "appr_123abc",
    "mode": "yolo",
    "workflow_id": "wf_456def",
    "step_id": "deploy",
    "approver": "system:auto"
  },
  "source": "approval_manager"
}
```

### Database

Approval records show auto-approval:

```sql
SELECT * FROM approvals WHERE approver LIKE 'system:%';
```

### Logs

```
2026-01-05 12:00:00 [INFO] YOLO mode enabled for workflow wf_456def
2026-01-05 12:00:01 [INFO] Auto-approved step 'deploy' (appr_123abc)
```

## Safety Checklist

Before enabling YOLO mode in production:

- [ ] Workflow thoroughly tested in staging
- [ ] Approval policies configured (if needed)
- [ ] Audit logging verified
- [ ] Monitoring/alerting set up
- [ ] Team trained on YOLO mode
- [ ] Compliance requirements checked
- [ ] Rollback plan documented

## Next Steps

1. **Implement core changes** (Steps 1-2 above)
2. **Add CLI support** (Step 3)
3. **Add API support** (Step 4)
4. **Write tests**
5. **Update documentation**
6. **Try example**: `python examples/08_yolo_mode.py`

## Resources

- **Design Doc**: `docs/yolo-mode-design.md` (comprehensive design)
- **Example**: `examples/08_yolo_mode.py` (runnable example)
- **Human-in-the-Loop**: `examples/07_human_in_the_loop.py` (approval basics)
- **Approval Manager**: `packages/paracle_orchestration/approval.py`

## Questions?

See the full design document at `docs/yolo-mode-design.md` or the example at `examples/08_yolo_mode.py`.

---

**Time to implement**: 30-60 minutes
**Complexity**: Low
**Risk**: Low (additive feature, backward compatible)
**Value**: High (enables CI/CD and automation)
