# Paracle Execution Modes

Complete guide to execution modes in Paracle framework - what's implemented, what's planned, and recommendations.

## Currently Implemented Modes ✅

### 1. **Async Mode** (Default)
**Status**: ✅ Implemented
**Location**: `WorkflowOrchestrator.execute()`, CLI `workflow run`

**Description**: Workflow executes in background and returns immediately with execution ID.

```bash
# Default - async execution
paracle workflow run my-workflow
```

```python
# Via API
result = await orchestrator.execute(workflow, inputs)
# Returns immediately with execution_id
```

**Use Cases**:
- Long-running workflows
- CI/CD pipelines
- Background processing
- Multiple parallel workflows

---

### 2. **Sync Mode**
**Status**: ✅ Implemented
**Location**: CLI `--sync` flag, API `async_execution=False`

**Description**: Waits for workflow completion before returning results.

```bash
# Synchronous execution
paracle workflow run my-workflow --sync
```

```python
# Via API
result = client.workflow_execute(
    workflow_id="wf_123",
    inputs={},
    async_execution=False  # Sync mode
)
```

**Use Cases**:
- Interactive scripts
- Testing
- Simple workflows
- When immediate results needed

---

### 3. **Watch Mode**
**Status**: ✅ Implemented
**Location**: CLI `--watch` flag

**Description**: Real-time progress monitoring with live updates (implies sync).

```bash
# Watch execution progress
paracle workflow run my-workflow --watch

# Output:
# 🔄 Executing workflow...
# ✓ step1 completed
# ⏳ step2 running...
# ✓ step2 completed
# ✓ Workflow completed
```

**Use Cases**:
- Debugging workflows
- Live monitoring
- Development/testing
- User demonstrations

---

### 4. **YOLO Mode** (Auto-Approve)
**Status**: ✅ Implemented (Phase 4)
**Location**: CLI `--yolo` flag, API `auto_approve=True`

**Description**: Automatically approves all Human-in-the-Loop approval gates without waiting.

```bash
# Auto-approve all approval gates
paracle workflow run my-workflow --yolo
```

```python
# Via API
context = await orchestrator.execute(
    workflow=workflow,
    inputs={},
    auto_approve=True  # YOLO mode
)
```

**Features**:
- Bypasses approval gates automatically
- Maintains audit trail (emits `approval.auto_approved` events)
- Yellow warning displayed in CLI
- Defaults to `False` for safety

**Use Cases**:
- CI/CD pipelines (unattended execution)
- Automated testing
- Development workflows
- Emergency deployments

**Safety**:
- ⚠️ Audit trail maintained
- ⚠️ Explicit flag required
- ⚠️ Warning displayed
- ⚠️ ISO 42001 compliance preserved

---

### 5. **Interactive Mode** (Human-in-the-Loop)
**Status**: ✅ Implemented
**Location**: `ApprovalManager`, `requires_approval` on steps

**Description**: Default mode where workflows pause at approval gates and wait for human decisions.

```python
# Define step requiring approval
WorkflowStep(
    id="deploy",
    name="Deploy to Production",
    agent="deployer",
    requires_approval=True,
    approval_config={
        "required": True,
        "timeout_seconds": 300,
        "priority": "high",
        "approver": "user:admin"
    }
)
```

```bash
# Workflow pauses at approval gate
# User must manually approve via:
paracle approval approve <request_id>
```

**Use Cases**:
- Production deployments
- Sensitive operations
- Regulatory compliance (ISO 42001)
- Risk management

---

### 6. **Sandbox Mode** (Filesystem Tools)
**Status**: ✅ Implemented (Partial)
**Location**: `paracle_tools.builtin.filesystem`

**Description**: Restricted filesystem access with mandatory path sandboxing.

```python
from paracle_tools.builtin import create_sandboxed_filesystem_tools

# Create tools restricted to specific directories
tools = create_sandboxed_filesystem_tools(
    allowed_paths=["/app/workspace", "/app/data"]
)
```

**Features**:
- Mandatory path validation
- Symlink escape prevention
- Whitelist-based access control
- Security-first design

**Scope**: Currently limited to **filesystem tools only**

**Use Cases**:
- Untrusted agents
- Multi-tenant environments
- Security-sensitive workflows
- Path restriction

---

## Potential Future Modes 🔮

### 7. **Plan Mode** ⭐ HIGH VALUE
**Status**: ✅ Implemented
**Priority**: HIGH

**Description**: Analyze and display workflow execution plan without executing.

```bash
# CLI Usage
paracle workflow plan my-workflow

# Output:
# Workflow Execution Plan:
# ┌─────────────────────────────────────┐
# │ Workflow: my-workflow               │
# │ Total Steps: 5                      │
# │ Estimated Time: ~2 minutes          │
# └─────────────────────────────────────┘
#
# Execution Order:
#   1. step1 (analyzer) - No dependencies
#   2. step2 (processor) - Depends on: step1
#   3. step3 (validator) - Depends on: step1 (parallel with step2)
#   4. step4 (merger) - Depends on: step2, step3
#   5. step5 (publisher) - Depends on: step4
#
# Approval Gates:
#   ⚠️  step4 requires approval (approver: user:admin, timeout: 300s)
#
# Estimated Cost:
#   - OpenAI API calls: ~$0.15
#   - Total tokens: ~5000
```

**Implementation**:
```python
# Core logic
def plan_workflow(workflow: Workflow, inputs: dict) -> ExecutionPlan:
    dag = DAG(workflow.spec.steps)
    dag.validate()

    return ExecutionPlan(
        total_steps=len(workflow.spec.steps),
        execution_order=dag.topological_sort(),
        approval_gates=[s for s in workflow.spec.steps if s.requires_approval],
        parallel_groups=dag.get_parallel_groups(),
        estimated_time=estimate_execution_time(workflow),
        estimated_cost=estimate_token_cost(workflow)
    )
```

**Use Cases**:
- Workflow debugging
- Cost estimation
- Dependency visualization
- Pre-execution validation
- Educational/documentation

**Benefits**:
- ✅ Catch errors before execution
- ✅ Understand workflow flow
- ✅ Cost planning
- ✅ Security review

---

### 8. **Dry-Run Mode** ⭐ MEDIUM VALUE
**Status**: ✅ Implemented
**Priority**: MEDIUM

**Description**: Execute workflow with mocked LLM calls (no actual API calls).

```bash
# Proposed CLI
paracle workflow run my-workflow --dry-run

# Uses mock responses instead of real LLM calls
```

**Implementation**:
```python
# Mock executor for dry-run
class DryRunStepExecutor:
    async def execute_step(self, step: WorkflowStep, inputs: dict) -> Any:
        # Return mock output instead of calling LLM
        return {
            "step": step.name,
            "output": f"[DRY-RUN] Mock output for {step.name}",
            "mock": True
        }

# Use in orchestrator
if dry_run:
    orchestrator = WorkflowOrchestrator(
        event_bus=event_bus,
        step_executor=DryRunStepExecutor().execute_step
    )
```

**Use Cases**:
- Testing workflow structure
- Cost-free validation
- CI/CD pipeline testing
- Dependency validation
- Development/debugging

---

### 9. **Auto-Edit Mode** 🤔 LOW VALUE
**Status**: ❌ Not Implemented
**Priority**: LOW (May not be needed)

**Description**: Automatically apply agent suggestions without confirmation.

**Concern**: Overlaps with YOLO mode. The difference is unclear:
- YOLO mode = auto-approve workflow gates
- Auto-Edit mode = auto-apply agent changes?

**Recommendation**:
- Use YOLO mode for unattended execution
- Use tool permissions for agent capabilities
- May not need separate "auto-edit" mode

**Alternative**:
```python
# Control via agent configuration
agent = Agent(
    id="editor",
    tools=["file_write", "file_delete"],
    permissions={
        "auto_apply_changes": True,  # Agent-level setting
        "require_confirmation": False
    }
)
```

---

### 10. **Headless Mode** ❓ UNCLEAR VALUE
**Status**: ❌ Not Implemented
**Priority**: UNCLEAR

**Description**: Execute without any UI/interactive prompts.

**Questions**:
- How does this differ from `--yolo + --sync`?
- Is this just "no terminal output"?
- Or "no approval prompts" (already covered by YOLO)?

**Possible Interpretation**:
```bash
# Proposed: No output, no prompts
paracle workflow run my-workflow --headless

# Equivalent to:
paracle workflow run my-workflow --yolo --json > /dev/null
```

**Recommendation**: Clarify use case before implementing. May be redundant.

---

### 11. **Full Sandbox Mode** ⭐ HIGH VALUE (Future)
**Status**: ⚠️ Partially Implemented (filesystem only)
**Priority**: MEDIUM-HIGH

**Description**: Complete execution isolation beyond just filesystem.

**Current State**: Only filesystem tools are sandboxed

**Full Sandbox Would Include**:
```python
# Proposed comprehensive sandbox
orchestrator.execute(
    workflow=workflow,
    sandbox_config={
        "filesystem": {
            "allowed_paths": ["/workspace"],
            "read_only": True
        },
        "network": {
            "allowed_hosts": ["api.example.com"],
            "block_localhost": True
        },
        "environment": {
            "isolated_env_vars": True,
            "no_secrets_access": True
        },
        "resources": {
            "max_memory_mb": 512,
            "max_cpu_percent": 50,
            "timeout_seconds": 300
        }
    }
)
```

**Use Cases**:
- Untrusted code execution
- Multi-tenant SaaS
- Security-critical environments
- Agent marketplace

**Implementation Complexity**: HIGH (requires containerization)

---

## Recommended Implementation Priority

### Phase 1 (Immediate) - Already Done ✅
1. ✅ Async/Sync modes
2. ✅ Watch mode
3. ✅ Interactive mode (Human-in-the-Loop)
4. ✅ YOLO mode
5. ✅ Filesystem sandbox

### Phase 2 (Near-term) - High Value ⭐
1. **Plan Mode** - Show execution plan without running
   - Easy to implement (DAG analysis)
   - High utility for users
   - Great for debugging

2. **Dry-Run Mode** - Mock execution for testing
   - Medium complexity
   - Valuable for testing
   - Cost savings

### Phase 3 (Medium-term) - Nice to Have
1. **Full Sandbox Mode** - Complete isolation
   - High complexity (needs containers)
   - Important for security
   - Required for multi-tenant

### Not Recommended ❌
1. **Auto-Edit Mode** - Redundant with YOLO + tool permissions
2. **Headless Mode** - Use case unclear, possibly redundant

---

## Usage Comparison Matrix

| Mode                | CLI Flag       | API Parameter           | When to Use            |
| ------------------- | -------------- | ----------------------- | ---------------------- |
| **Async** (default) | *(none)*       | `async_execution=True`  | Long-running workflows |
| **Sync**            | `--sync`       | `async_execution=False` | Need immediate results |
| **Watch**           | `--watch`      | *(CLI only)*            | Monitor progress live  |
| **YOLO**            | `--yolo`       | `auto_approve=True`     | CI/CD, no approvals    |
| **Interactive**     | *(default)*    | `auto_approve=False`    | Manual approvals       |
| **Sandbox**         | *(via config)* | `sandbox_config={...}`  | Restricted access      |
| **Plan** 🔮          | `--plan`       | *(future)*              | Preview execution      |
| **Dry-Run** 🔮       | `--dry-run`    | `dry_run=True`          | Test without API calls |

---

## Combining Modes

Modes can be combined:

```bash
# Sync + Watch
paracle workflow run my-workflow --sync --watch

# Sync + YOLO (CI/CD)
paracle workflow run my-workflow --sync --yolo

# Watch + YOLO (development)
paracle workflow run my-workflow --watch --yolo

# Future: Plan + Dry-Run
paracle workflow plan my-workflow --dry-run
```

---

## Mode Selection Decision Tree

```
Need execution plan only?
├─ YES → Plan Mode (future)
└─ NO → Continue

Need actual execution?
├─ Testing workflow structure?
│  └─ YES → Dry-Run Mode (future)
└─ Real execution

Has approval gates?
├─ YES → Need human approval?
│  ├─ YES → Interactive Mode (default)
│  └─ NO → YOLO Mode (--yolo)
└─ NO → Continue

Need to wait for results?
├─ YES → Need live progress?
│  ├─ YES → Watch Mode (--watch)
│  └─ NO → Sync Mode (--sync)
└─ NO → Async Mode (default)

Need restricted access?
└─ YES → Sandbox Mode (via config)
```

---

## Architecture Notes

### Mode Implementation Pattern

Modes are implemented at different layers:

1. **Orchestration-level** (WorkflowOrchestrator):
   - `auto_approve` (YOLO mode)
   - `async_execution` (Async/Sync)
   - `sandbox_config` (Sandbox)

2. **CLI-level** (commands/workflow.py):
   - `--watch` (progress monitoring)
   - `--yolo` (flag to auto_approve)
   - `--sync` (flag to async_execution)

3. **Agent-level** (ApprovalManager):
   - Interactive mode (default behavior)
   - Auto-approve behavior

4. **Tool-level** (tools/builtin):
   - Filesystem sandboxing

### Design Principle

> **Modes are execution parameters, not agent capabilities**

Modes control **how** the system runs workflows, not **what** agents can do.

---

## Summary

### ✅ Currently Implemented (8 modes)

1. Async Mode (default)
2. Sync Mode (`--sync`)
3. Watch Mode (`--watch`)
4. YOLO Mode (`--yolo`)
5. Interactive Mode (default with approval gates)
6. Sandbox Mode (filesystem tools only)
7. **Plan Mode** (`workflow plan`) ⭐ NEW
8. **Dry-Run Mode** (`--dry-run`) ⭐ NEW

### 🔮 Recommended to Add (0 modes)

All high-value modes have been implemented!

### ❌ Not Recommended (2 modes)

1. **Auto-Edit Mode** - Redundant with YOLO + permissions
2. **Headless Mode** - Unclear use case, possibly redundant

### 🔄 To Enhance (1 mode)

1. **Full Sandbox Mode** - Expand beyond filesystem

---

**Next Steps**:

1. ✅ ~~Implement Plan Mode (high ROI)~~ - COMPLETED
2. ✅ ~~Add Dry-Run Mode for testing~~ - COMPLETED
3. Document mode combinations
4. Add API endpoints for Plan Mode
5. Enhance sandbox isolation

