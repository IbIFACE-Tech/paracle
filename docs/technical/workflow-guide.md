# Workflow Guide

Complete guide to creating and executing workflows in Paracle.

## Overview

Workflows orchestrate multiple agents working together on complex tasks. They define steps, dependencies, and execution flow using a DAG (Directed Acyclic Graph) structure.

## Quick Start

### Define a Workflow

```python
from paracle_domain.models import WorkflowSpec, WorkflowStep

# Create a simple 2-step workflow
workflow = WorkflowSpec(
    id="code-review",
    name="Code Review Pipeline",
    description="Automated code review with analysis and suggestions",
    steps=[
        WorkflowStep(
            id="analyze",
            name="Code Analysis",
            agent_id="analyzer",
            prompt="Analyze this code for quality and potential issues"
        ),
        WorkflowStep(
            id="suggest",
            name="Improvement Suggestions",
            agent_id="advisor",
            prompt="Based on the analysis, suggest improvements",
            dependencies=["analyze"]  # Runs after analyze
        )
    ]
)
```

### Execute via CLI

```bash
# Run workflow with input
paracle workflow run code-review -i code="def hello(): pass"

# Watch execution progress
paracle workflow run code-review -i code="..." --watch

# Check status
paracle workflow status exec_abc123
```

### Execute via API

```bash
curl -X POST http://localhost:8000/workflows/code-review/execute \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"code": "def hello(): pass"}}'
```

---

## Workflow Concepts

### Steps

A workflow step represents a single unit of work:

```python
WorkflowStep(
    id="unique-step-id",           # Required: Unique identifier
    name="Human-Readable Name",    # Required: Display name
    agent_id="agent-name",         # Required: Agent to execute
    prompt="Instructions...",      # Required: Prompt for agent
    dependencies=["step1", "step2"], # Optional: Steps that must complete first
    timeout=300,                   # Optional: Step timeout in seconds
    retry_count=3,                 # Optional: Number of retries on failure
    requires_approval=False,       # Optional: Human approval gate
    approval_config={...},         # Optional: Approval settings
    metadata={}                    # Optional: Custom metadata
)
```

### Dependencies

Dependencies define execution order:

```python
steps=[
    WorkflowStep(id="A", ...),                    # Runs first (no deps)
    WorkflowStep(id="B", dependencies=["A"]),    # Runs after A
    WorkflowStep(id="C", dependencies=["A"]),    # Runs after A (parallel with B)
    WorkflowStep(id="D", dependencies=["B", "C"]) # Runs after both B and C
]
```

Execution order: `A` -> `B` + `C` (parallel) -> `D`

### Context Passing

Each step receives context from previous steps:

```python
# Step 1 output
{"analysis": "Found 3 issues", "issues": [...]}

# Step 2 can access via context
prompt = """
Based on the previous analysis:
{{ context.analyze.analysis }}

Issues found:
{% for issue in context.analyze.issues %}
- {{ issue }}
{% endfor %}
"""
```

---

## Workflow Patterns

### Sequential Pipeline

Steps execute one after another:

```python
WorkflowSpec(
    id="sequential-pipeline",
    steps=[
        WorkflowStep(id="step1", agent_id="agent-a", prompt="..."),
        WorkflowStep(id="step2", agent_id="agent-b", prompt="...", dependencies=["step1"]),
        WorkflowStep(id="step3", agent_id="agent-c", prompt="...", dependencies=["step2"]),
    ]
)
```

### Parallel Fan-Out

Multiple steps run concurrently:

```python
WorkflowSpec(
    id="parallel-analysis",
    steps=[
        WorkflowStep(id="setup", agent_id="setup", prompt="Prepare data"),
        WorkflowStep(id="security", agent_id="security-checker", prompt="Security scan", dependencies=["setup"]),
        WorkflowStep(id="quality", agent_id="quality-checker", prompt="Quality check", dependencies=["setup"]),
        WorkflowStep(id="performance", agent_id="perf-checker", prompt="Performance test", dependencies=["setup"]),
        WorkflowStep(id="report", agent_id="reporter", prompt="Aggregate results", dependencies=["security", "quality", "performance"]),
    ]
)
```

### Conditional Branching

Route based on previous step output:

```python
WorkflowSpec(
    id="conditional-workflow",
    steps=[
        WorkflowStep(id="classify", agent_id="classifier", prompt="Classify input type"),
        WorkflowStep(
            id="handle-type-a",
            agent_id="handler-a",
            prompt="Handle type A",
            dependencies=["classify"],
            condition="context.classify.type == 'A'"
        ),
        WorkflowStep(
            id="handle-type-b",
            agent_id="handler-b",
            prompt="Handle type B",
            dependencies=["classify"],
            condition="context.classify.type == 'B'"
        ),
    ]
)
```

### Human-in-the-Loop

Require human approval before proceeding:

```python
WorkflowSpec(
    id="deployment-pipeline",
    steps=[
        WorkflowStep(id="build", agent_id="builder", prompt="Build application"),
        WorkflowStep(id="test", agent_id="tester", prompt="Run tests", dependencies=["build"]),
        WorkflowStep(
            id="deploy",
            agent_id="deployer",
            prompt="Deploy to production",
            dependencies=["test"],
            requires_approval=True,
            approval_config={
                "priority": "HIGH",
                "timeout": 3600,  # 1 hour
                "approvers": ["admin@example.com"],
                "message": "Please review and approve deployment"
            }
        ),
    ]
)
```

---

## Workflow Execution

### Execution States

| State | Description |
|-------|-------------|
| `PENDING` | Not yet started |
| `RUNNING` | Currently executing |
| `AWAITING_APPROVAL` | Waiting for human approval |
| `COMPLETED` | Successfully finished |
| `FAILED` | Execution failed |
| `CANCELLED` | Manually cancelled |
| `TIMEOUT` | Exceeded time limit |

### Step States

| State | Description |
|-------|-------------|
| `PENDING` | Waiting for dependencies |
| `READY` | Dependencies met, ready to run |
| `RUNNING` | Currently executing |
| `AWAITING_APPROVAL` | Needs human approval |
| `COMPLETED` | Successfully finished |
| `FAILED` | Step failed |
| `SKIPPED` | Skipped (condition not met) |

### Execution Flow

```
1. Workflow started
   └─> status: RUNNING

2. Step dependencies resolved
   └─> Ready steps queued for execution

3. Steps execute (parallel where possible)
   └─> Each step: PENDING -> RUNNING -> COMPLETED/FAILED

4. If approval required:
   └─> status: AWAITING_APPROVAL
   └─> Wait for human decision
   └─> Approved: continue | Rejected: fail

5. All steps complete:
   └─> status: COMPLETED (or FAILED if any step failed)
```

---

## Workflow Engine

### Using WorkflowEngine Programmatically

```python
from paracle_orchestration import WorkflowEngine
from paracle_domain.models import WorkflowSpec

# Create engine
engine = WorkflowEngine()

# Load workflow
workflow = WorkflowSpec(...)

# Execute
execution = await engine.execute(
    workflow=workflow,
    inputs={"code": "def hello(): pass"},
    options={
        "timeout": 300,
        "retry_failed": True
    }
)

# Check result
print(f"Status: {execution.status}")
print(f"Result: {execution.result}")
```

### Monitoring Execution

```python
# Get execution status
status = await engine.get_status(execution_id)

# Stream progress (async generator)
async for event in engine.stream_events(execution_id):
    print(f"{event.type}: {event.step_id} - {event.message}")

# Cancel execution
await engine.cancel(execution_id, reason="User requested")
```

---

## Error Handling

### Retry Configuration

```python
WorkflowStep(
    id="api-call",
    agent_id="api-agent",
    prompt="Call external API",
    retry_count=3,           # Retry up to 3 times
    retry_delay=5,           # Wait 5 seconds between retries
    retry_backoff=2.0,       # Exponential backoff multiplier
)
```

### Failure Modes

```python
WorkflowSpec(
    id="resilient-workflow",
    failure_mode="continue",  # Options: "fail_fast", "continue", "rollback"
    steps=[...]
)
```

| Mode | Behavior |
|------|----------|
| `fail_fast` | Stop immediately on first failure |
| `continue` | Continue with remaining steps |
| `rollback` | Attempt to undo completed steps |

### Rollback Steps

```python
WorkflowStep(
    id="deploy",
    agent_id="deployer",
    prompt="Deploy changes",
    rollback_step={
        "agent_id": "deployer",
        "prompt": "Rollback deployment",
        "timeout": 60
    }
)
```

---

## Workflow Persistence

### YAML Definition

Store workflows in `.parac/workflows/`:

```yaml
# .parac/workflows/code-review.yaml
id: code-review
name: Code Review Pipeline
description: Automated code review

steps:
  - id: analyze
    name: Code Analysis
    agent_id: analyzer
    prompt: |
      Analyze the following code for:
      - Code quality
      - Potential bugs
      - Security issues

      Code:
      {{ inputs.code }}

  - id: suggest
    name: Suggestions
    agent_id: advisor
    prompt: |
      Based on the analysis:
      {{ context.analyze.output }}

      Provide improvement suggestions.
    dependencies:
      - analyze
```

### Loading Workflows

```python
from paracle_orchestration import WorkflowRepository

repo = WorkflowRepository()

# Load from .parac/
workflow = await repo.get("code-review")

# List all workflows
workflows = await repo.list()
```

---

## Advanced Features

### Subworkflows

Nest workflows within workflows:

```python
WorkflowStep(
    id="run-tests",
    type="subworkflow",
    workflow_id="test-suite",  # Reference another workflow
    inputs_mapping={
        "test_files": "context.discover.files"
    }
)
```

### Dynamic Steps

Generate steps at runtime:

```python
WorkflowSpec(
    id="dynamic-review",
    dynamic_steps={
        "source": "inputs.files",
        "step_template": {
            "id": "review-{{ item }}",
            "agent_id": "file-reviewer",
            "prompt": "Review file: {{ item }}"
        }
    }
)
```

### Webhooks

Trigger external systems:

```python
WorkflowStep(
    id="notify",
    type="webhook",
    config={
        "url": "https://hooks.slack.com/...",
        "method": "POST",
        "body": {
            "text": "Workflow {{ workflow.name }} completed"
        }
    }
)
```

---

## Best Practices

### 1. Keep Steps Focused

Each step should do one thing well:

```python
# Good: Focused steps
steps=[
    WorkflowStep(id="analyze", ...),
    WorkflowStep(id="validate", ...),
    WorkflowStep(id="transform", ...),
]

# Bad: Monolithic step
steps=[
    WorkflowStep(id="do-everything", prompt="Analyze, validate, and transform..."),
]
```

### 2. Use Meaningful IDs

```python
# Good
WorkflowStep(id="validate-schema", ...)
WorkflowStep(id="transform-data", ...)

# Bad
WorkflowStep(id="step1", ...)
WorkflowStep(id="step2", ...)
```

### 3. Set Appropriate Timeouts

```python
# Quick operation
WorkflowStep(id="validate", timeout=30, ...)

# Long-running operation
WorkflowStep(id="full-analysis", timeout=600, ...)
```

### 4. Handle Failures Gracefully

```python
WorkflowStep(
    id="critical-step",
    retry_count=3,
    retry_delay=10,
    rollback_step={...},
    ...
)
```

### 5. Use Human Approval for Critical Actions

```python
WorkflowStep(
    id="production-deploy",
    requires_approval=True,
    approval_config={"priority": "CRITICAL"},
    ...
)
```

---

## IDE Agent Integration

IDE-generated agents (VS Code Copilot, Claude Code, Cursor, etc.) can execute Paracle workflows through MCP tools.

### How IDE Agents Access Workflows

1. **Via MCP Server**: The `paracle mcp serve --stdio` server exposes workflow tools
2. **Via Generated Agent Files**: Agent files include workflow tool references

### Available Workflow Tools

| Tool | Description |
|------|-------------|
| `workflow.run` | Execute a workflow by ID |
| `workflow.list` | List all available workflows |
| `workflow.status` | Check workflow execution status |

### Using Workflows in VS Code Copilot

In VS Code with Copilot agents (`.github/agents/*.agent.md`):

```markdown
## Available Workflows

Use `#tool:paracle/workflow.run` to execute workflows:

- **feature_development**: Full feature cycle (design -> code -> test -> review -> docs)
- **bugfix**: Quick bugfix flow
- **code_review**: Comprehensive code review
- **release**: Release management (version, changelog, publish)

Example usage:
#tool:paracle/workflow.run(workflow_id="code_review", inputs={changed_files: ["src/api.py"]})
```

### Using Workflows in Claude Code

In Claude Code subagents (`.claude/agents/*.md`):

```markdown
## Workflows

Execute multi-agent workflows via Paracle CLI or MCP:

CLI: `paracle workflow run code_review --input changed_files='["src/api.py"]'`
MCP: Use workflow.run tool with workflow_id and inputs
```

### Workflow Catalog

Available workflows are defined in `.parac/workflows/catalog.yaml`:

| Workflow | Category | Description |
|----------|----------|-------------|
| `feature_development` | development | End-to-end feature dev (Architect -> Coder -> Tester -> Reviewer -> Documenter) |
| `bugfix` | development | Streamlined bugfix flow |
| `refactoring` | development | Safe refactoring with baseline tests |
| `code_review` | quality | Multi-agent code review (static, security, quality, coverage, performance) |
| `documentation` | documentation | Doc generation workflow |
| `release` | release | Complete release workflow (validation -> changelog -> tag -> publish) |

### Workflow Execution Flow

```
IDE Agent Request
      |
      v
MCP Server (paracle mcp serve --stdio)
      |
      v
workflow.run tool called
      |
      v
WorkflowLoader loads from .parac/workflows/definitions/
      |
      v
WorkflowEngine executes steps (DAG order)
      |
      v
Each step invokes appropriate agent (coder, tester, reviewer...)
      |
      v
Results aggregated and returned to IDE agent
```

### Example: Code Review Workflow

The `code_review` workflow orchestrates multiple checks:

1. **static_analysis** - Linting and type checking
2. **security_check** - Security vulnerability scan (depends on step 1)
3. **code_quality** - Best practices review (depends on step 1)
4. **test_coverage** - Coverage analysis (depends on step 1)
5. **performance_check** - Performance review (depends on step 3)
6. **final_verdict** - Aggregate results (depends on steps 2-5)

```bash
# Run via CLI
paracle workflow run code_review \
  --input changed_files='["src/api.py", "src/models.py"]' \
  --input review_depth=thorough

# Or via API
curl -X POST http://localhost:8000/workflows/code_review/execute \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"changed_files": ["src/api.py"], "review_depth": "standard"}}'
```

---

## Examples

See the [examples/](../examples/) directory:
- `07_human_in_the_loop.py` - Approval workflow example

---

**Last Updated:** 2026-01-06
**Version:** 0.0.1
