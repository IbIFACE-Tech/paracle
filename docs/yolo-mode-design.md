# YOLO Mode Design Document

## Overview

YOLO (You Only Live Once) mode allows Paracle workflows to execute with automatic approval of all Human-in-the-Loop gates. This enables:
- Unattended execution
- CI/CD automation
- Development/testing without manual intervention
- Production deployments with confidence

## Design Principles

1. **Safety First**: YOLO mode must be explicitly enabled
2. **Auditability**: All auto-approvals are logged with clear markers
3. **Flexibility**: Multiple activation methods (CLI, API, env var, code)
4. **Transparency**: Users know when YOLO mode is active

## Architecture

### 1. Core Changes

#### ApprovalManager Enhancement

```python
class ApprovalManager:
    """Manages approval requests with optional auto-approval."""

    def __init__(
        self,
        event_bus: EventBus,
        auto_approve: bool = False,  # NEW
        auto_approver: str = "system:auto",  # NEW
    ):
        self.auto_approve = auto_approve
        self.auto_approver = auto_approver
        # ... existing init

    async def create_request(self, ...) -> ApprovalRequest:
        """Create approval request with optional auto-approval."""
        request = # ... create request normally

        # Auto-approve if YOLO mode enabled
        if self.auto_approve:
            await self._auto_approve_request(request)

        return request

    async def _auto_approve_request(self, request: ApprovalRequest) -> None:
        """Automatically approve a request in YOLO mode."""
        await self.approve(
            request.id,
            approver=self.auto_approver,
            reason="Auto-approved: YOLO mode enabled",
        )

        # Emit special event for audit trail
        await self.event_bus.publish(Event(
            type="approval.auto_approved",
            data={
                "approval_id": request.id,
                "mode": "yolo",
                "workflow_id": request.workflow_id,
                "step_id": request.step_id,
            },
        ))
```

#### WorkflowOrchestrator Enhancement

```python
class WorkflowOrchestrator:
    """Orchestrator with YOLO mode support."""

    async def execute(
        self,
        workflow: Workflow,
        inputs: dict[str, Any],
        auto_approve: bool = False,  # NEW
        timeout_seconds: float | None = None,
    ) -> ExecutionContext:
        """Execute workflow with optional auto-approval.

        Args:
            auto_approve: If True, automatically approve all approval gates.
                         Useful for CI/CD, testing, or unattended execution.
        """
        # Create approval manager with YOLO setting
        if auto_approve:
            self.approval_manager = ApprovalManager(
                self.event_bus,
                auto_approve=True,
            )

        # ... rest of execution
```

### 2. CLI Integration

#### Commands

```bash
# Workflow execution with YOLO
paracle workflow run my-workflow --yolo
paracle workflow run my-workflow --auto-approve  # Alias

# Agent execution with YOLO
paracle agent run my-agent --yolo "Deploy the app"

# Global YOLO for all operations (dangerous!)
export PARACLE_AUTO_APPROVE=true
paracle workflow run my-workflow  # Auto-approves
```

#### CLI Code

```python
# In packages/paracle_cli/commands/workflow.py

@click.command()
@click.argument("workflow_name")
@click.option(
    "--yolo",
    "--auto-approve",
    is_flag=True,
    help="Automatically approve all approval gates (YOLO mode)",
)
@click.option(
    "--yolo-approver",
    default="system:cli",
    help="Approver name for auto-approvals",
)
async def run(workflow_name: str, yolo: bool, yolo_approver: str):
    """Execute a workflow with optional auto-approval."""

    if yolo:
        console.print("[yellow]⚠️  YOLO MODE ENABLED - Auto-approving all gates[/yellow]")

    # Pass to orchestrator
    result = await orchestrator.execute(
        workflow,
        inputs,
        auto_approve=yolo,
    )
```

### 3. API Integration

#### REST Endpoints

```python
# POST /api/v1/workflows/{workflow_id}/execute
{
    "inputs": {...},
    "auto_approve": true,  # NEW field
    "auto_approver": "api:user123"  # Optional
}

# POST /api/v1/agents/{agent_id}/execute
{
    "prompt": "Deploy the app",
    "auto_approve": true
}
```

#### API Code

```python
# In packages/paracle_api/routers/workflows.py

class WorkflowExecutionRequest(BaseModel):
    inputs: dict[str, Any]
    auto_approve: bool = Field(
        default=False,
        description="Auto-approve all approval gates (YOLO mode)",
    )
    auto_approver: str = Field(
        default="api:system",
        description="Approver name for auto-approvals",
    )

@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecutionRequest,
):
    """Execute workflow with optional auto-approval."""

    if request.auto_approve:
        logger.warning(f"YOLO mode enabled for workflow {workflow_id}")

    result = await orchestrator.execute(
        workflow,
        request.inputs,
        auto_approve=request.auto_approve,
    )

    return result
```

### 4. Environment Variable

```bash
# Enable globally (use with caution!)
export PARACLE_AUTO_APPROVE=true
export PARACLE_AUTO_APPROVER=system:env

# Disable explicitly
export PARACLE_AUTO_APPROVE=false
```

```python
# In packages/paracle_core/__init__.py
from pydantic_settings import BaseSettings

class ParacleSettings(BaseSettings):
    auto_approve: bool = Field(
        default=False,
        description="Global auto-approve flag (YOLO mode)",
    )
    auto_approver: str = Field(
        default="system:auto",
        description="Default approver for auto-approvals",
    )

    class Config:
        env_prefix = "PARACLE_"
```

### 5. Workflow YAML Configuration

```yaml
# workflows/deploy.yaml
name: production-deployment
description: Deploy to production with YOLO mode

# Global YOLO for this workflow
auto_approve: true  # NEW field
auto_approver: workflow:deploy

steps:
  - id: build
    name: build
    agent: builder

  - id: deploy
    name: deploy
    agent: deployer
    requires_approval: true  # Will be auto-approved in YOLO mode
    approval_config:
      timeout_seconds: 300
      priority: high
```

## Safety Mechanisms

### 1. Audit Trail

All auto-approvals are logged with clear markers:

```python
# Event emitted
{
    "type": "approval.auto_approved",
    "timestamp": "2026-01-05T12:00:00Z",
    "data": {
        "approval_id": "appr_123",
        "mode": "yolo",
        "source": "cli",  # or "api", "env", "workflow"
        "approver": "system:auto",
        "workflow_id": "wf_456",
        "step_id": "deploy"
    }
}
```

### 2. Warnings

CLI/API warnings when YOLO mode is active:

```
⚠️  YOLO MODE ENABLED
    All approval gates will be automatically approved.
    Approver: system:cli
    Source: CLI flag

    Continue? [y/N]
```

### 3. Policy Overrides

Respect `.parac/policies/approvals.yaml`:

```yaml
# Some approvals cannot be auto-approved
approval_matrix:
  security:
    auto_approve: false  # Never auto-approve security steps
    force_human: true

  production_deploy:
    auto_approve: false  # Require human for prod
```

### 4. RBAC Integration

```python
# Only certain users can enable YOLO mode
if not user.has_permission("workflows:auto_approve"):
    raise PermissionError("User cannot enable YOLO mode")
```

## Testing Strategy

### Unit Tests

```python
async def test_yolo_mode_auto_approves():
    """YOLO mode should auto-approve all requests."""
    manager = ApprovalManager(event_bus, auto_approve=True)

    request = await manager.create_request(...)

    # Should be immediately approved
    assert request.status == ApprovalStatus.APPROVED
    assert request.approver == "system:auto"

async def test_yolo_mode_disabled_by_default():
    """YOLO mode should be disabled by default."""
    manager = ApprovalManager(event_bus)

    request = await manager.create_request(...)

    # Should be pending
    assert request.status == ApprovalStatus.PENDING
```

### Integration Tests

```python
async def test_workflow_execution_with_yolo():
    """Workflow should complete without manual approval in YOLO mode."""
    workflow = create_workflow_with_approval_gate()

    # Execute with YOLO
    result = await orchestrator.execute(
        workflow,
        inputs={},
        auto_approve=True,
    )

    # Should complete successfully
    assert result.status == ExecutionStatus.COMPLETED
    assert "deploy" in result.step_results
```

### E2E Tests

```bash
# Test CLI YOLO mode
paracle workflow run test-workflow --yolo

# Test API YOLO mode
curl -X POST /api/v1/workflows/test/execute \
  -d '{"auto_approve": true}'
```

## Documentation

### User Guide

Create `docs/yolo-mode.md`:

```markdown
# YOLO Mode: Auto-Approve Workflows

## What is YOLO Mode?

YOLO (You Only Live Once) mode automatically approves all Human-in-the-Loop
approval gates in workflows, enabling unattended execution.

## When to Use

✅ CI/CD pipelines
✅ Development/testing
✅ Trusted automation
✅ Non-critical workflows

❌ Production deployments (without testing)
❌ Security-sensitive operations
❌ Financial transactions
❌ When compliance requires human oversight

## Usage

### CLI
paracle workflow run my-workflow --yolo

### API
POST /api/v1/workflows/my-workflow/execute
{"auto_approve": true}

### Environment
export PARACLE_AUTO_APPROVE=true

### Code
result = await orchestrator.execute(workflow, inputs, auto_approve=True)
```

## Migration Path

### Phase 1: Core Implementation (Week 1)
- [ ] Update `ApprovalManager` with `auto_approve` parameter
- [ ] Add auto-approval logic
- [ ] Add audit events
- [ ] Unit tests

### Phase 2: Integration (Week 2)
- [ ] Update `WorkflowOrchestrator`
- [ ] Add CLI `--yolo` flag
- [ ] Add API parameter
- [ ] Integration tests

### Phase 3: Safety & Docs (Week 3)
- [ ] Environment variable support
- [ ] Policy override support
- [ ] Warning messages
- [ ] Documentation
- [ ] E2E tests

### Phase 4: Polish (Week 4)
- [ ] RBAC integration
- [ ] Dashboard indicators
- [ ] Monitoring/metrics
- [ ] Examples

## Metrics

Track YOLO mode usage:

```python
# Metrics to collect
- yolo_mode_activations (counter)
- yolo_approvals_count (counter by workflow)
- yolo_mode_duration (histogram)
- yolo_failures_count (counter)
```

## Security Considerations

1. **Logging**: All auto-approvals logged with unique approver ID
2. **Audit Trail**: Events published to event bus
3. **Rate Limiting**: Limit YOLO executions per user/hour
4. **Policy Enforcement**: Respect approval policies
5. **RBAC**: Require permission to enable YOLO mode

## Compliance

- ISO 42001: Document YOLO mode in AI governance
- SOC 2: Audit trail for all auto-approvals
- GDPR: Log data processing in YOLO mode
- Industry-specific: Check regulatory requirements

## FAQ

**Q: Is YOLO mode safe?**
A: Yes, when used appropriately. Always test first, use policy overrides.

**Q: Can I disable YOLO for specific steps?**
A: Yes, set `approval_config.force_human = true` in workflow YAML.

**Q: How do I audit YOLO approvals?**
A: Check event logs for `approval.auto_approved` events.

**Q: Can I use YOLO in production?**
A: Yes, but test thoroughly and consider compliance requirements.
