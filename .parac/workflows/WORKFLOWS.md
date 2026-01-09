# Paracle Workflows - Complete Implementation Suite

This directory contains comprehensive workflows for implementing the Paracle framework and platform using multi-agent orchestration.

## 📋 Overview

Paracle workflows enable **automated, multi-agent execution** of complex development tasks following governance rules and best practices from `.parac/`.

### Workflow Philosophy

- **Dogfooding**: We use Paracle to build Paracle
- **Governance-First**: All workflows follow `.parac/GOVERNANCE.md`
- **Multi-Agent**: Orchestrates specialized agents (Architect, Coder, Tester, Reviewer, Documenter, PM, Release Manager)
- **Quality-Built-In**: Testing, review, and documentation are integral, not afterthoughts
- **Traceable**: All actions logged to `.parac/memory/logs/`

## 🚀 Available Workflows

### Development Workflows

#### 1. Feature Development (`feature_development.yaml`)
**Complete end-to-end feature implementation**

```bash
paracle workflow run feature_development \
  --feature_name "agent_skills" \
  --feature_description "Implement skill loading and injection system" \
  --target_package "paracle_orchestration" \
  --priority P0
```

**Steps**:
1. Pre-flight checklist (PM) - Validate alignment with roadmap
2. Architecture design (Architect) - Design modules, interfaces, models
3. Test design (Tester) - TDD approach, design tests first
4. Implementation (Coder) - Implement following design
5. Test implementation (Tester) - Create comprehensive test suite
6. Code review (Reviewer) - Quality, security, performance review
7. Documentation (Documenter) - API docs, guides, examples
8. Integration (Tester) - Validate integration, check regressions
9. Governance update (PM) - Update `.parac/` files

**Duration**: ~1 hour
**Outputs**: Implemented files, tests, documentation

---

#### 2. Bugfix (`bugfix.yaml`)
**Streamlined bug fixing with proper validation**

```bash
paracle workflow run bugfix \
  --bug_description "Memory leak in workflow orchestration" \
  --severity critical \
  --issue_number "#123"
```

**Steps**:
1. Bug analysis (Architect) - Identify root cause
2. Implement fix (Coder) - Apply fix
3. Regression testing (Tester) - Ensure fix works, no regressions
4. Quick review (Reviewer) - Verify fix quality
5. Document fix (Documenter) - Update changelog, docs

**Duration**: ~30 minutes
**Outputs**: Fixed files, changelog entry

---

#### 3. Refactoring (`refactoring.yaml`)
**Safe refactoring ensuring no behavioral changes**

```bash
paracle workflow run refactoring \
  --target_component "packages/paracle_orchestration/engine.py" \
  --refactoring_goal simplify \
  --scope medium
```

**Steps**:
1. Analyze (Architect) - Plan refactoring, assess risks
2. Baseline tests (Tester) - Run tests before refactoring
3. Refactor (Coder) - Apply changes
4. Validate (Tester) - Ensure behavior preserved
5. Review (Reviewer) - Check quality improvement
6. Document (Documenter) - Update docs

**Duration**: ~40 minutes
**Outputs**: Refactored files, quality improvement metrics
**Safety**: Automatic rollback on test failure

---

#### 4. Paracle Build (`paracle_build.yaml`)
**Complete dogfooding workflow for platform features**

The most comprehensive workflow - orchestrates all 7 agents following complete governance.

```bash
paracle workflow run paracle_build \
  --feature_name "workflow_execution_api" \
  --feature_description "Add async workflow execution endpoint" \
  --current_phase "phase_4"
```

**Special Features**:
- Mandatory Pre-Flight Checklist (ADR-016)
- ISO 42001 compliance checks
- Complete governance integration
- Multi-agent coordination

---

### Quality Assurance Workflows

#### 5. Code Review (`code_review.yaml`)
**Comprehensive automated code review**

```bash
paracle workflow run code_review \
  --changed_files ["packages/paracle_api/routes.py", "tests/test_routes.py"] \
  --pr_number "42" \
  --review_depth thorough
```

**Checks**:
- Static analysis (linting, type checking)
- Security vulnerabilities
- Code quality and best practices
- Test coverage
- Performance issues

**Duration**: ~15 minutes
**Outputs**: Review verdict, summary, blocking issues, action items

---

### Documentation Workflows

#### 6. Documentation (`documentation.yaml`)
**Create comprehensive documentation**

```bash
paracle workflow run documentation \
  --doc_type user_guide \
  --topic "Agent Skills System" \
  --target_audience intermediate
```

**Supports**:
- API reference
- User guides
- Tutorials
- Quickstarts
- Architecture documentation

**Steps**: Research → Write → Review → Publish

**Duration**: ~30 minutes
**Outputs**: Published documentation, examples

---

### Release Management Workflows

#### 7. Release (`release.yaml`)
**Complete release process with semantic versioning**

```bash
# Minor version release
paracle workflow run release \
  --version_type minor \
  --release_notes "Added agent skills system"

# Dry run (test without publishing)
paracle workflow run release \
  --version_type patch \
  --dry_run true
```

**Steps**:
1. Pre-release validation - Tests, linting, typecheck
2. Version bump - Using `scripts/bump_version.py`
3. Changelog generation - From conventional commits
4. Git operations - Commit, tag, push
5. Build & package - Create sdist + wheel
6. PyPI publishing - Upload to PyPI (if not dry_run)
7. GitHub release - Create release with notes
8. Governance update - Update `.parac/` files
9. Notification - Notify stakeholders

**Duration**: ~30 minutes
**Outputs**: Release version, PyPI URL, GitHub release URL, changelog

**Security**: Requires `PYPI_TOKEN` environment variable

---

## 🏗️ Workflow Architecture

### Agent Roles

```
┌─────────────┐
│ PM Agent    │ → Planning, governance, coordination
└─────────────┘

┌─────────────┐
│ Architect   │ → Design, architecture, decisions
└─────────────┘

┌─────────────┐
│ Coder       │ → Implementation, code generation
└─────────────┘

┌─────────────┐
│ Tester      │ → Test design, test implementation, validation
└─────────────┘

┌─────────────┐
│ Reviewer    │ → Code review, quality assurance, security
└─────────────┘

┌─────────────┐
│ Documenter  │ → Documentation, guides, API references
└─────────────┘

┌───────────────────┐
│ Release Manager   │ → Versioning, publishing, deployment
└───────────────────┘
```

### Workflow Execution Flow

```
1. Input Validation
   ↓
2. Agent Selection (based on step.agent)
   ↓
3. Load Agent Spec (.parac/agents/specs/{agent}.md)
   ↓
4. Build Prompt (step config + inputs)
   ↓
5. LLM Execution (via provider)
   ↓
6. Tool Invocation (if needed)
   ↓
7. Output Validation
   ↓
8. Log Action (.parac/memory/logs/agent_actions.log)
   ↓
9. Next Step (based on dependencies)
```

### Dependency Management

Workflows support:
- **Sequential**: Steps execute in order
- **Parallel**: Independent steps execute concurrently
- **Conditional**: Steps execute based on conditions
- **Dependencies**: `depends_on` field specifies prerequisites

Example:
```yaml
steps:
  - id: design
    agent: architect

  - id: implement
    agent: coder
    depends_on: [design]  # Waits for design

  - id: test
    agent: tester
    depends_on: [implement]  # Waits for implementation
```

## 📊 Workflow Catalog

See [catalog.yaml](catalog.yaml) for complete workflow registry.

**Categories**:
- **Development**: feature_development, bugfix, refactoring, paracle_build
- **Quality**: code_review
- **Documentation**: documentation
- **Release**: release
- **Examples**: hello_world

## 🛠️ Usage

### Basic Execution

```bash
# List available workflows
paracle workflow list

# Get workflow info
paracle workflow info feature_development

# Run workflow
paracle workflow run feature_development \
  --feature_name "my_feature" \
  --feature_description "Feature description" \
  --target_package "paracle_core"

# Run with plan mode (dry run)
paracle workflow run feature_development \
  --feature_name "my_feature" \
  --mode plan
```

### Advanced Options

```bash
# Run with specific provider
paracle workflow run feature_development \
  --feature_name "my_feature" \
  --provider openai \
  --model gpt-4-turbo

# Run with cost tracking
paracle workflow run feature_development \
  --feature_name "my_feature" \
  --track-costs

# Run with custom timeout
paracle workflow run feature_development \
  --feature_name "my_feature" \
  --timeout 7200  # 2 hours
```

### Workflow Outputs

All workflows output to:
- **Console**: Real-time progress
- **Logs**: `.parac/memory/logs/{workflow}_workflow.log`
- **Governance**: `.parac/memory/logs/agent_actions.log`
- **Results**: JSON file with outputs

## 🔧 Creating Custom Workflows

### Workflow Structure

```yaml
name: my_workflow
version: 1.0.0
description: Workflow description

metadata:
  category: development
  tags: [tag1, tag2]
  governance: true

inputs:
  param1:
    type: string
    required: true
    description: Parameter description

steps:
  - id: step1
    name: step_name
    description: Step description
    agent: coder
    depends_on: []
    config:
      model: gpt-4
      temperature: 0.5
      system_prompt: |
        Agent instructions
    inputs:
      input1: "{{ inputs.param1 }}"
    outputs:
      - output1
      - output2
    tools:
      - name: tool_name
        description: Tool purpose
    validation:
      must_pass: true
      on_fail: abort

outputs:
  result:
    description: Result description
    value: "{{ steps.step1.outputs.output1 }}"

config:
  timeout: 1800
  retry:
    max_attempts: 2
  logging:
    level: INFO
```

### Best Practices

1. **Governance First**: Always start with pre-flight checklist
2. **Test Early**: Design tests before implementation (TDD)
3. **Validate Steps**: Use `validation.must_pass` for critical steps
4. **Log Everything**: All agent actions are logged automatically
5. **Handle Failures**: Define `on_fail` strategies (abort, retry, rollback)
6. **Clear Dependencies**: Explicit `depends_on` relationships
7. **Descriptive Prompts**: Clear `system_prompt` for agents
8. **Type Inputs**: Use proper input types and validation
9. **Document Outputs**: Describe what each step produces

## 📈 Monitoring & Debugging

### Workflow Logs

```bash
# View workflow execution log
cat .parac/memory/logs/feature_workflow.log

# View agent actions log
cat .parac/memory/logs/agent_actions.log

# View real-time progress
paracle workflow run feature_development ... --follow
```

### Debugging Failed Workflows

```bash
# Get workflow execution status
paracle workflow status <execution_id>

# View step outputs
paracle workflow outputs <execution_id>

# Replay failed step
paracle workflow replay <execution_id> --step step_id
```

## 💰 Cost Management

Workflows track costs for LLM calls:

```bash
# Run with cost tracking
paracle workflow run feature_development ... --track-costs

# View costs after execution
paracle workflow costs <execution_id>

# Set budget limit
paracle workflow run feature_development ... --max-cost 5.00
```

## 🔒 Security

### Secrets Management

Workflows can use secrets (e.g., `PYPI_TOKEN`):

```yaml
steps:
  - id: publish
    secrets:
      - PYPI_TOKEN  # Loaded from environment
```

**Never commit secrets to git!** Use:
- Environment variables
- `.env` file (gitignored)
- Secret management tools (Vault, etc.)

### Execution Isolation

- Workflows run in isolated contexts
- File system access controlled
- Network access limited (if sandbox enabled)

## 📚 References

- **Agent Specs**: `.parac/agents/specs/`
- **Skills**: `.parac/agents/skills/`
- **Governance**: `.parac/GOVERNANCE.md`
- **Pre-Flight Checklist**: `.parac/PRE_FLIGHT_CHECKLIST.md`
- **Roadmap**: `.parac/roadmap/roadmap.yaml`
- **Policies**: `.parac/policies/`

## 🚦 Status

| Workflow            | Status | Priority | Tests | Documentation |
| ------------------- | ------ | -------- | ----- | ------------- |
| feature_development | ✅      | P0       | ✅     | ✅             |
| bugfix              | ✅      | P0       | ✅     | ✅             |
| refactoring         | ✅      | P1       | ✅     | ✅             |
| paracle_build       | ✅      | P0       | ✅     | ✅             |
| code_review         | ✅      | P0       | ✅     | ✅             |
| documentation       | ✅      | P1       | ✅     | ✅             |
| release             | ✅      | P0       | ✅     | ✅             |

## 🎯 Roadmap

### Phase 6 (Q1 2026) - Current
- ✅ Core workflows implemented
- ✅ Multi-agent orchestration
- ✅ Governance integration
- ⏳ CLI commands enhancement
- ⏳ Web UI for workflow management

### Phase 7 (Q2 2026) - Community
- Workflow marketplace
- Community workflows
- Workflow templates
- Workflow sharing

### Phase 8 (Q3 2026) - Performance
- Parallel workflow execution
- Distributed workflows
- Workflow optimization
- Caching and memoization

---

**Version**: 2.0
**Last Updated**: 2026-01-06
**Maintained By**: Paracle Team

