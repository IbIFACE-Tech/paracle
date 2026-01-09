# Paracle Build Workflow - Dogfooding Strategy

## Overview

The `paracle_build.yaml` workflow is the **flagship dogfooding workflow** that demonstrates how Paracle uses itself to build itself. This workflow orchestrates all 6 agents to implement new features following strict governance and quality standards.

## What is Dogfooding?

**Dogfooding** means "eating your own dog food" - using the product you're building to build itself. For Paracle:

```
┌─────────────────────────────────────────────────────────────┐
│                    PARACLE FRAMEWORK                        │
│                      packages/                              │
│                                                             │
│   The PRODUCT we're building                               │
│   - paracle_core, paracle_domain, paracle_api, etc.        │
│   - Framework code that generates .parac/ for users        │
└─────────────────────────────────────────────────────────────┘
                          ↓ uses
┌─────────────────────────────────────────────────────────────┐
│              paracle_build.yaml WORKFLOW                    │
│                  (This workflow)                            │
│                                                             │
│   Using the framework to build the framework                │
│   - Orchestrates Architect, Coder, Tester, etc.           │
│   - Follows .parac/ governance                             │
│   - Demonstrates framework capabilities                     │
└─────────────────────────────────────────────────────────────┘
                          ↓ updates
┌─────────────────────────────────────────────────────────────┐
│                   .parac/ WORKSPACE                         │
│                  (Governance layer)                         │
│                                                             │
│   Our own .parac/ governance                                │
│   - Roadmap, current state, decisions                      │
│   - Agent specs, policies, memory                          │
└─────────────────────────────────────────────────────────────┘
```

## Workflow Architecture

### 8 Phases with 6 Agents

```
PHASE 0: Pre-Flight Checklist (PM)
   ↓
PHASE 1: Architecture Design (Architect)
   ↓
PHASE 2: Implementation (Coder)
   ↓
PHASE 3: Test Design (Tester)
   ↓
PHASE 4: Code Review (Reviewer)
   ↓
PHASE 5: Documentation (Documenter)
   ↓
PHASE 6: Governance Update (PM) ← MANDATORY
   ↓
PHASE 7: Integration Validation (Tester)
   ↓
PHASE 8: Final Summary (PM)
```

### Agent Responsibilities

| Phase | Agent      | Responsibility                                        |
| ----- | ---------- | ----------------------------------------------------- |
| 0     | PM         | Execute Pre-Flight Checklist, validate task alignment |
| 1     | Architect  | Design architecture, create ADR, define interfaces    |
| 2     | Coder      | Implement feature following architecture & code style |
| 3     | Tester     | Create unit & integration tests, validate coverage    |
| 4     | Reviewer   | Review code, security scan, quality validation        |
| 5     | Documenter | API docs, user guides, docstrings                     |
| 6     | PM         | **Update .parac/ governance (MANDATORY)**             |
| 7     | Tester     | Integration tests, validate no regressions            |
| 8     | PM         | Create summary, mark merge-ready                      |

## Usage

### Command Line (Future)

```bash
# Run the workflow with required inputs
paracle workflow run paracle_build \
  --input feature_name="workflow_execution_api" \
  --input feature_description="Add async workflow execution endpoint with status tracking" \
  --input current_phase="phase_4" \
  --input priority="P0"

# Skip tests (not recommended)
paracle workflow run paracle_build \
  --input feature_name="my_feature" \
  --input feature_description="..." \
  --input skip_tests=true

# Skip review (not recommended for production)
paracle workflow run paracle_build \
  --input feature_name="experimental_feature" \
  --input feature_description="..." \
  --input skip_review=true
```

### API (Current Phase 4)

```python
from paracle_api import WorkflowClient

client = WorkflowClient(base_url="http://localhost:8000")

# Execute workflow
execution = await client.execute_workflow(
    workflow_name="paracle_build",
    inputs={
        "feature_name": "workflow_execution_api",
        "feature_description": "Add async workflow execution endpoint",
        "current_phase": "phase_4",
        "priority": "P0"
    }
)

# Monitor execution
status = await client.get_execution_status(execution.id)
print(f"Status: {status.state}")
print(f"Progress: {status.current_step}/{status.total_steps}")

# Get results
results = await client.get_execution_results(execution.id)
print(f"Feature completed: {results.outputs['feature_completed']}")
print(f"Files changed: {results.outputs['files_changed']}")
```

### Python SDK

```python
from paracle_orchestration import WorkflowEngine
from paracle_domain.models import WorkflowSpec

# Load workflow
with open(".parac/workflows/definitions/paracle_build.yaml") as f:
    workflow_spec = WorkflowSpec.from_yaml(f.read())

# Execute
engine = WorkflowEngine()
result = await engine.execute(
    workflow=workflow_spec,
    inputs={
        "feature_name": "my_feature",
        "feature_description": "Description here",
        "current_phase": "phase_4",
        "priority": "P1"
    }
)

# Check results
if result.outputs["feature_completed"]:
    print("✅ Feature ready to merge!")
    print(f"Summary: {result.outputs['summary']}")
else:
    print("❌ Feature needs more work")
    print(f"Issues: {result.errors}")
```

## Required Inputs

### Mandatory

- **feature_name** (string): Name of feature (e.g., "workflow_execution_api")
- **feature_description** (string): Detailed requirements

### Optional

- **current_phase** (string): Phase from roadmap (default: "phase_4")
- **priority** (enum): P0/P1/P2 (default: P1)
- **skip_tests** (boolean): Skip test generation (default: false, NOT recommended)
- **skip_review** (boolean): Skip code review (default: false, NOT recommended)

## Outputs

The workflow provides comprehensive outputs:

```yaml
outputs:
  feature_completed: boolean  # Ready to merge?
  summary: string            # Complete summary
  files_changed: list        # All modified files
  test_coverage: float       # Coverage %
  documentation: list        # Doc files created
  governance_updates: list   # .parac/ files updated
  adr_number: string        # ADR number if created
```

## Key Features

### 1. Pre-Flight Checklist (MANDATORY)

Every execution starts with the Pre-Flight Checklist:

```
✅ Read .parac/GOVERNANCE.md
✅ Check .parac/memory/context/current_state.yaml
✅ Consult .parac/roadmap/roadmap.yaml
✅ Check .parac/memory/context/open_questions.md
✅ VALIDATE: Task alignment with roadmap
```

**If validation fails, workflow STOPS.**

### 2. Governance Updates (MANDATORY)

Phase 6 updates `.parac/` governance files:

```
✅ Log to .parac/memory/logs/agent_actions.log
✅ Update .parac/memory/context/current_state.yaml
✅ Update .parac/roadmap/roadmap.yaml (if deliverable)
✅ Document in .parac/roadmap/decisions.md (if ADR)
✅ Run `paracle sync --roadmap` to validate
```

**Ensures complete traceability and dogfooding compliance.**

### 3. Quality Gates

Multiple validation gates ensure quality:

- **Architecture Review**: Design must be sound
- **Code Review**: Must pass security & quality checks
- **Test Coverage**: Must exceed 80%
- **Integration Tests**: No regressions allowed
- **Governance Sync**: Must align with roadmap

### 4. ISO 42001 Compliance

Built-in compliance features:

- All steps audited and logged
- All decisions documented
- All approvals tracked
- Complete traceability
- Cost tracking

### 5. Failure Handling

Robust error handling:

- **Rollback**: Restore previous state
- **Retry**: Up to 3 retries on failure
- **Checkpoint**: Save state at each step
- **Logging**: All failures logged
- **Notification**: Alert on failure

## Example Execution

Here's what happens when you run the workflow:

```
🚀 Starting paracle_build workflow
   Feature: workflow_execution_api
   Phase: phase_4
   Priority: P0

⏳ PHASE 0: Pre-Flight Checklist (PM Agent)
   ✅ Read GOVERNANCE.md
   ✅ Current state: phase_4, 75% complete
   ✅ Roadmap: Task aligned with phase_4 priorities
   ✅ No blockers found
   ✅ VALIDATION PASSED

🏗️  PHASE 1: Architecture Design (Architect Agent)
   ✅ Hexagonal architecture design created
   ✅ Module structure: paracle_api/routers/workflows.py
   ✅ Interface contracts defined
   ✅ ADR-017 drafted
   ✅ Dependencies: FastAPI, asyncio

💻 PHASE 2: Implementation (Coder Agent)
   ✅ Created packages/paracle_api/routers/workflows.py
   ✅ Created packages/paracle_api/schemas/workflow.py
   ✅ Implementation follows CODE_STYLE.md
   ✅ Type hints added
   ✅ Google-style docstrings

🧪 PHASE 3: Test Design (Tester Agent)
   ✅ Created tests/integration/test_workflow_api.py
   ✅ 15 tests created
   ✅ Coverage: 92%
   ✅ All tests passing

👀 PHASE 4: Code Review (Reviewer Agent)
   ✅ Code quality: PASS
   ✅ Security scan: PASS (no vulnerabilities)
   ✅ Performance: PASS (no bottlenecks)
   ✅ Test coverage: PASS (92% > 80%)
   ✅ APPROVED

📚 PHASE 5: Documentation (Documenter Agent)
   ✅ Created docs/api/workflow-endpoints.md
   ✅ Updated README.md with usage examples
   ✅ Added inline docstrings
   ✅ API reference generated

📋 PHASE 6: Governance Update (PM Agent) [MANDATORY]
   ✅ Logged to agent_actions.log
   ✅ Updated current_state.yaml (added to completed)
   ✅ Updated roadmap.yaml (deliverable marked complete)
   ✅ Created ADR-017 in decisions.md
   ✅ Ran `paracle sync --roadmap` - ALIGNED

🔗 PHASE 7: Integration Validation (Tester Agent)
   ✅ Full test suite: 127 tests passing
   ✅ No regressions detected
   ✅ API endpoints validated
   ✅ Governance sync validated

📊 PHASE 8: Final Summary (PM Agent)
   ✅ Feature: workflow_execution_api
   ✅ Files changed: 8
   ✅ Test coverage: 92%
   ✅ Documentation: 3 files
   ✅ Governance: 4 files updated
   ✅ ADR: ADR-017 created
   ✅ MERGE READY: ✅ YES

🎉 Workflow completed successfully!
   Execution time: 12 minutes
   Token usage: 15,432 tokens
   Cost: $0.23
```

## Best Practices

### 1. Always Use Pre-Flight Checklist

Never skip Phase 0. It ensures:
- Task alignment with roadmap
- No duplicate work
- Correct phase and priority
- No blockers

### 2. Never Skip Tests

Tests are critical for quality:
- Catch bugs early
- Prevent regressions
- Document behavior
- Enable refactoring

### 3. Never Skip Review

Code review ensures:
- Security vulnerabilities caught
- Performance issues identified
- Quality standards maintained
- Knowledge transfer

### 4. Always Update Governance

Phase 6 is **MANDATORY** for dogfooding:
- Maintains traceability
- Updates project state
- Documents decisions
- Validates roadmap alignment

### 5. Run Full Integration Tests

Phase 7 validates:
- No regressions
- Proper integration
- API correctness
- CLI functionality

## Extending the Workflow

You can customize the workflow for your needs:

### Add Custom Steps

```yaml
steps:
  # ... existing steps ...

  - id: custom_validation
    name: custom_check
    agent: reviewer
    depends_on: [integration_validation]
    config:
      # Your custom config
    inputs:
      # Your inputs
    outputs:
      # Your outputs
```

### Change Agent Models

```yaml
steps:
  - id: code_implementation
    config:
      model: gpt-4-turbo  # Use faster model
      temperature: 0.1     # Adjust temperature
```

### Add Parallel Steps

```yaml
settings:
  parallel_execution:
    enabled: true
    max_concurrent: 3  # Run 3 steps in parallel
```

### Custom Failure Handling

```yaml
on_failure:
  rollback:
    enabled: true
  notify:
    - type: slack
      webhook: "https://..."
    - type: email
      to: "team@example.com"
```

## Troubleshooting

### Workflow Fails at Pre-Flight

**Problem**: Task not in roadmap or wrong phase

**Solution**:
1. Check `.parac/roadmap/roadmap.yaml`
2. Verify current phase in `.parac/memory/context/current_state.yaml`
3. Add task to roadmap or adjust phase

### Code Review Fails

**Problem**: Code doesn't meet quality standards

**Solution**:
1. Review `.parac/policies/CODE_STYLE.md`
2. Fix issues reported
3. Re-run from `code_implementation` step

### Tests Fail

**Problem**: Test coverage < 80%

**Solution**:
1. Add more tests
2. Review `.parac/policies/TESTING.md`
3. Ensure all paths covered

### Governance Update Fails

**Problem**: `paracle sync --roadmap` shows misalignment

**Solution**:
1. Manually fix `.parac/roadmap/roadmap.yaml`
2. Update `.parac/memory/context/current_state.yaml`
3. Run `paracle sync --roadmap` again

## Metrics & Monitoring

The workflow tracks:

- **Execution time**: Total workflow duration
- **Token usage**: LLM API tokens consumed
- **Cost**: Estimated API cost
- **Files changed**: Number of files modified
- **Test coverage**: Percentage of code covered
- **Security findings**: Vulnerabilities detected
- **Quality score**: Overall code quality

## Related Documentation

- [Pre-Flight Checklist](../../PRE_FLIGHT_CHECKLIST.md) - Mandatory validation
- [Governance](../../GOVERNANCE.md) - Governance rules
- [Roadmap](../../roadmap/roadmap.yaml) - Project roadmap
- [Agent Specs](../../agents/specs/) - Agent specifications
- [Policies](../../policies/) - Project policies

## Future Enhancements

Planned improvements:

- **v1.1**: Add human-in-the-loop approvals
- **v1.2**: Support for parallel feature development
- **v1.3**: Automated PR creation
- **v1.4**: Cost optimization recommendations
- **v1.5**: Multi-repo support
- **v2.0**: Self-improvement loop (workflow improves itself)

---

**Version**: 1.0.0
**Created**: 2026-01-05
**Status**: Active
**Category**: Dogfooding

**Remember**: This workflow demonstrates Paracle building Paracle. Every feature we add to the framework is built using this workflow, proving the framework works! 🎯
