# Working with Workflows

Complete guide to creating and running workflows in Paracle.

## What is a Workflow?

A **workflow** orchestrates multiple agents to accomplish complex tasks. Workflows define a directed acyclic graph (DAG) of steps.

```yaml
# .parac/workflows/review-pipeline.yaml
name: review-pipeline
description: "Automated code review pipeline"

steps:
  - name: analyze
    agent: analyzer
    task: "Analyze code structure"

  - name: review
    agent: reviewer
    task: "Review code quality"
    depends_on: [analyze]

  - name: report
    agent: documenter
    task: "Generate review report"
    depends_on: [review]
```

## Creating Workflows

### Method 1: Manual YAML

Create a file in `.parac/workflows/`:

```yaml
# .parac/workflows/deploy-pipeline.yaml
name: deploy-pipeline
description: "Build, test, and deploy"

steps:
  - name: build
    agent: builder
    task: "Build the application"

  - name: test
    agent: tester
    task: "Run test suite"
    depends_on: [build]

  - name: deploy
    agent: deployer
    task: "Deploy to staging"
    depends_on: [test]
```

### Method 2: CLI Generation

```bash
# Interactive creation
paracle workflows create

# Generate with AI
paracle meta generate workflow \
  --name "ci-pipeline" \
  --description "CI/CD pipeline with build, test, deploy"
```

## Workflow Specification

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique workflow identifier |
| `steps` | list | List of workflow steps |

### Step Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Step identifier |
| `agent` | string | Yes | Agent to execute step |
| `task` | string | Yes | Task description |
| `depends_on` | list | No | Dependencies |
| `condition` | string | No | Conditional execution |
| `retry` | object | No | Retry configuration |
| `timeout` | int | No | Timeout in seconds |

### Full Example

```yaml
name: code-review-pipeline
description: "Comprehensive code review workflow"
version: "1.0"

# Input parameters
inputs:
  - name: file_path
    type: string
    required: true
    description: "Path to file to review"
  - name: review_type
    type: string
    default: "standard"
    description: "Type of review"

# Workflow steps
steps:
  - name: analyze
    agent: analyzer
    task: "Analyze code structure and complexity"
    inputs:
      file: "{{ inputs.file_path }}"
    outputs:
      - analysis_report

  - name: security-scan
    agent: security-auditor
    task: "Scan for security vulnerabilities"
    inputs:
      file: "{{ inputs.file_path }}"
    outputs:
      - security_report
    # Run in parallel with analyze (no depends_on)

  - name: review
    agent: reviewer
    task: "Review code quality based on analysis"
    depends_on: [analyze, security-scan]
    inputs:
      analysis: "{{ steps.analyze.outputs.analysis_report }}"
      security: "{{ steps.security-scan.outputs.security_report }}"
    outputs:
      - review_report

  - name: generate-report
    agent: documenter
    task: "Generate final review report"
    depends_on: [review]
    inputs:
      review: "{{ steps.review.outputs.review_report }}"
    condition: "{{ inputs.review_type == 'comprehensive' }}"

# Workflow outputs
outputs:
  - name: final_report
    from: "{{ steps.generate-report.outputs.report }}"
  - name: security_findings
    from: "{{ steps.security-scan.outputs.security_report }}"

# Error handling
on_error:
  - notify: slack
    message: "Workflow failed: {{ error.message }}"

# Metadata
metadata:
  team: platform
  sla: "30 minutes"
```

## Execution Flow

### Sequential Steps

```yaml
steps:
  - name: step1
    agent: agent1
    task: "First task"

  - name: step2
    agent: agent2
    task: "Second task"
    depends_on: [step1]  # Runs after step1

  - name: step3
    agent: agent3
    task: "Third task"
    depends_on: [step2]  # Runs after step2
```

```
step1 → step2 → step3
```

### Parallel Steps

```yaml
steps:
  - name: analyze
    agent: analyzer
    task: "Analyze code"

  - name: security
    agent: security
    task: "Security scan"
    # No depends_on - runs in parallel with analyze

  - name: report
    agent: reporter
    task: "Generate report"
    depends_on: [analyze, security]  # Waits for both
```

```
analyze ──┐
          ├→ report
security ─┘
```

### Complex DAG

```yaml
steps:
  - name: fetch
    agent: fetcher
    task: "Fetch data"

  - name: transform
    agent: transformer
    task: "Transform data"
    depends_on: [fetch]

  - name: validate
    agent: validator
    task: "Validate data"
    depends_on: [fetch]

  - name: enrich
    agent: enricher
    task: "Enrich data"
    depends_on: [transform, validate]

  - name: load
    agent: loader
    task: "Load data"
    depends_on: [enrich]
```

```
        ┌→ transform ─┐
fetch ──┤             ├→ enrich → load
        └→ validate  ─┘
```

## Running Workflows

### CLI Execution

```bash
# Run workflow
paracle workflow run review-pipeline

# With inputs
paracle workflow run review-pipeline --input file_path=src/main.py

# Dry run (show plan without executing)
paracle workflow run review-pipeline --dry-run

# Verbose output
paracle workflow run review-pipeline --verbose
```

### Execution Modes

```bash
# Safe mode (manual approvals)
paracle workflow run pipeline --mode safe

# YOLO mode (auto-approve)
paracle workflow run pipeline --mode yolo
```

### Monitor Execution

```bash
# Watch workflow progress
paracle workflow status <workflow-run-id>

# List running workflows
paracle workflow list --status running

# Cancel workflow
paracle workflow cancel <workflow-run-id>
```

## Conditional Execution

### Step Conditions

```yaml
steps:
  - name: deploy-staging
    agent: deployer
    task: "Deploy to staging"
    condition: "{{ inputs.environment == 'staging' }}"

  - name: deploy-prod
    agent: deployer
    task: "Deploy to production"
    condition: "{{ inputs.environment == 'production' }}"
    depends_on: [deploy-staging]
```

### Skip on Failure

```yaml
steps:
  - name: tests
    agent: tester
    task: "Run tests"

  - name: deploy
    agent: deployer
    task: "Deploy"
    depends_on: [tests]
    on_failure: skip  # Skip if tests fail
```

## Error Handling

### Retry Configuration

```yaml
steps:
  - name: flaky-step
    agent: agent
    task: "Flaky operation"
    retry:
      max_attempts: 3
      delay: 10  # seconds
      backoff: exponential
```

### Timeout

```yaml
steps:
  - name: long-step
    agent: agent
    task: "Long running task"
    timeout: 300  # 5 minutes
```

### On Error Actions

```yaml
on_error:
  - type: notify
    channel: slack
    message: "Workflow {{ workflow.name }} failed"

  - type: rollback
    steps: [deploy]

  - type: retry
    max_attempts: 2
```

## Input/Output Passing

### Step Outputs

```yaml
steps:
  - name: analyze
    agent: analyzer
    task: "Analyze code"
    outputs:
      - complexity_score
      - issues_found

  - name: report
    agent: reporter
    task: "Create report for score {{ steps.analyze.outputs.complexity_score }}"
    depends_on: [analyze]
```

### Workflow Inputs

```yaml
inputs:
  - name: repo_url
    type: string
    required: true
  - name: branch
    type: string
    default: "main"

steps:
  - name: clone
    agent: git-agent
    task: "Clone {{ inputs.repo_url }} branch {{ inputs.branch }}"
```

## Listing Workflows

```bash
# List all workflows
paracle workflows list

# Show workflow details
paracle workflows show review-pipeline

# Show workflow runs
paracle workflow runs review-pipeline
```

## Best Practices

### 1. Single Responsibility Steps

```yaml
# Good - each step does one thing
steps:
  - name: analyze
    task: "Analyze code"
  - name: review
    task: "Review code"

# Bad - too much in one step
steps:
  - name: do-everything
    task: "Analyze, review, and deploy"
```

### 2. Clear Dependencies

```yaml
# Good - explicit dependencies
steps:
  - name: build
    task: "Build"
  - name: test
    depends_on: [build]
  - name: deploy
    depends_on: [test]

# Bad - implicit ordering
steps:
  - name: build
  - name: test
  - name: deploy
```

### 3. Meaningful Names

```yaml
# Good
name: security-audit-pipeline
steps:
  - name: static-analysis
  - name: dependency-scan
  - name: generate-report

# Bad
name: pipeline1
steps:
  - name: step1
  - name: step2
```

### 4. Use Timeouts

```yaml
steps:
  - name: external-api
    timeout: 60  # Prevent hanging
    retry:
      max_attempts: 3
```

## Examples

### CI/CD Pipeline

```yaml
name: cicd-pipeline
description: "Build, test, and deploy"

inputs:
  - name: branch
    default: "main"

steps:
  - name: checkout
    agent: git-agent
    task: "Checkout {{ inputs.branch }}"

  - name: build
    agent: builder
    task: "Build application"
    depends_on: [checkout]

  - name: unit-tests
    agent: tester
    task: "Run unit tests"
    depends_on: [build]

  - name: integration-tests
    agent: tester
    task: "Run integration tests"
    depends_on: [build]

  - name: security-scan
    agent: security
    task: "Security scan"
    depends_on: [build]

  - name: deploy-staging
    agent: deployer
    task: "Deploy to staging"
    depends_on: [unit-tests, integration-tests, security-scan]

  - name: smoke-tests
    agent: tester
    task: "Run smoke tests"
    depends_on: [deploy-staging]

  - name: deploy-prod
    agent: deployer
    task: "Deploy to production"
    depends_on: [smoke-tests]
    condition: "{{ inputs.branch == 'main' }}"
```

### Document Generation

```yaml
name: doc-generation
description: "Generate project documentation"

steps:
  - name: analyze-code
    agent: analyzer
    task: "Analyze codebase structure"
    outputs:
      - code_structure

  - name: extract-docstrings
    agent: extractor
    task: "Extract docstrings"
    outputs:
      - docstrings

  - name: generate-api-docs
    agent: documenter
    task: "Generate API documentation"
    depends_on: [analyze-code, extract-docstrings]

  - name: generate-user-guide
    agent: documenter
    task: "Generate user guide"
    depends_on: [analyze-code]

  - name: combine-docs
    agent: documenter
    task: "Combine all documentation"
    depends_on: [generate-api-docs, generate-user-guide]
```

## Next Steps

- [Agents Guide](agents.md) - Create and configure agents
- [Skills Guide](skills.md) - Reusable capabilities
- [CLI Reference](../../technical/cli-reference.md) - Full command reference
