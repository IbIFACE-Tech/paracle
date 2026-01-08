# MCP Server Capability Coverage

This document provides a complete overview of Paracle's MCP (Model Context Protocol) server capabilities, showing how external AI applications can access ALL Paracle functionality.

## 📊 Coverage Summary

### Overall Statistics

- **Total Tools**: 56+ tools exposed
- **Tool Categories**: 9 comprehensive categories
- **Resources**: 21+ resource URIs
- **Prompts**: 12+ template prompts
- **Coverage**: 100% of Paracle platform capabilities

### Design Principle

> **The MCP server exposes the COMPLETE Paracle platform - not just core features.**

External AI applications (Claude Desktop, Cline, Continue, etc.) can:
- Execute agents and workflows
- Manage LLM providers and configurations
- Track costs and budgets
- Access governance and planning (roadmap, ADRs)
- Manage work sessions
- Integrate with IDEs
- Validate workspace integrity
- Analyze logs and detect issues
- Use templates and examples

---

## 🔧 Tool Categories

### 1. Core Execution (8 tools)

**Purpose**: Execute agents, workflows, and tools

| Tool                        | Description                      | Example Use Case                    |
| --------------------------- | -------------------------------- | ----------------------------------- |
| `paracle_run_agent`         | Execute any Paracle agent        | Run CoderAgent to implement feature |
| `paracle_run_workflow`      | Execute any Paracle workflow     | Run release workflow                |
| `paracle_list_agents`       | List all available agents        | Discover available agents           |
| `paracle_list_workflows`    | List all available workflows     | Browse workflow catalog             |
| `paracle_get_agent_spec`    | Get detailed agent specification | View agent capabilities             |
| `paracle_get_workflow_spec` | Get detailed workflow definition | Understand workflow steps           |
| `paracle_execute_tool`      | Call any Paracle built-in tool   | Execute filesystem operations       |
| `paracle_list_tools`        | List all tools (built-in + MCP)  | Discover available tools            |

**Example**:
```json
{
  "tool": "paracle_run_agent",
  "params": {
    "agent_id": "coder",
    "task": "Implement user authentication",
    "inputs": {
      "language": "python",
      "framework": "FastAPI"
    }
  }
}
```

---

### 2. Provider Management (5 tools)

**Purpose**: Manage LLM providers and configurations

| Tool                           | Description                     | Example Use Case                       |
| ------------------------------ | ------------------------------- | -------------------------------------- |
| `paracle_list_providers`       | List all LLM providers          | See available providers (OpenAI, etc.) |
| `paracle_test_provider`        | Test provider connection        | Verify API key validity                |
| `paracle_get_provider_config`  | Get provider configuration      | Check current provider settings        |
| `paracle_set_default_provider` | Set default provider for agents | Switch from OpenAI to Anthropic        |
| `paracle_get_provider_models`  | List available models           | Discover GPT-4, Claude models          |

**Example**:
```json
{
  "tool": "paracle_list_providers",
  "params": {}
}
```

**Response**:
```json
{
  "providers": [
    {"id": "openai", "name": "OpenAI", "status": "configured", "models": ["gpt-4", "gpt-3.5-turbo"]},
    {"id": "anthropic", "name": "Anthropic", "status": "configured", "models": ["claude-3-opus", "claude-3-sonnet"]},
    {"id": "groq", "name": "Groq", "status": "configured", "models": ["llama-3-70b"]}
  ]
}
```

---

### 3. Cost Tracking & Budgets (6 tools)

**Purpose**: Monitor and control API costs

| Tool                         | Description                            | Example Use Case                  |
| ---------------------------- | -------------------------------------- | --------------------------------- |
| `paracle_get_cost_report`    | Get cost report (daily/weekly/monthly) | Generate monthly cost report      |
| `paracle_get_usage_stats`    | View token usage statistics            | Analyze token consumption         |
| `paracle_get_budget_status`  | Check budget status and alerts         | Check if approaching budget limit |
| `paracle_estimate_cost`      | Estimate cost for execution            | Estimate workflow cost before run |
| `paracle_set_budget`         | Set cost budget limits                 | Set $100/month budget             |
| `paracle_get_cost_breakdown` | Detailed cost breakdown                | Cost by agent, provider, date     |

**Example**:
```json
{
  "tool": "paracle_get_cost_report",
  "params": {
    "period": "monthly",
    "year": 2026,
    "month": 1
  }
}
```

**Response**:
```json
{
  "period": "2026-01",
  "total_cost": 47.32,
  "by_provider": {
    "openai": 28.50,
    "anthropic": 18.82
  },
  "by_agent": {
    "coder": 15.20,
    "reviewer": 12.10,
    "architect": 10.50
  },
  "budget": {
    "limit": 100.00,
    "used": 47.32,
    "remaining": 52.68,
    "percent_used": 47.3
  }
}
```

---

### 4. Governance & Planning (7 tools)

**Purpose**: Access roadmap, decisions, and project state

| Tool                         | Description                          | Example Use Case                |
| ---------------------------- | ------------------------------------ | ------------------------------- |
| `paracle_query_roadmap`      | Query roadmap (phases, deliverables) | Check current phase priorities  |
| `paracle_get_current_phase`  | Get current project phase            | Know current phase and progress |
| `paracle_list_adrs`          | List Architecture Decision Records   | Browse all ADRs                 |
| `paracle_get_adr`            | Get specific ADR by ID               | Read ADR-003                    |
| `paracle_get_open_questions` | List open questions and blockers     | Check unresolved issues         |
| `paracle_get_project_state`  | Get current project state            | Read current_state.yaml         |
| `paracle_update_progress`    | Update phase progress and status     | Mark deliverable as completed   |

**Example**:
```json
{
  "tool": "paracle_get_current_phase",
  "params": {}
}
```

**Response**:
```json
{
  "id": "phase_5",
  "name": "Agent Skills & Discovery",
  "status": "in_progress",
  "progress": 60,
  "started_date": "2025-12-15",
  "deliverables": [
    {"name": "agent_skills", "status": "completed", "completion": 100},
    {"name": "skill_discovery", "status": "in_progress", "completion": 70},
    {"name": "skill_execution", "status": "in_progress", "completion": 50}
  ],
  "focus": "Progressive skill discovery and execution",
  "priorities": ["Complete skill execution", "Update documentation"]
}
```

---

### 5. Session Management (5 tools)

**Purpose**: Manage work sessions and checkpoints

| Tool                          | Description                | Example Use Case          |
| ----------------------------- | -------------------------- | ------------------------- |
| `paracle_session_start`       | Start new work session     | Begin feature development |
| `paracle_session_end`         | End session with summary   | Complete work session     |
| `paracle_session_status`      | Get current session status | Check active session      |
| `paracle_list_sessions`       | List recent work sessions  | View session history      |
| `paracle_get_session_summary` | Get session summary        | Review session actions    |

**Example**:
```json
{
  "tool": "paracle_session_start",
  "params": {
    "description": "Implement user authentication feature",
    "agent": "coder"
  }
}
```

**Response**:
```json
{
  "session_id": "session_01HJKF6Z8QXY7N3M9P4R5T6W8",
  "started_at": "2026-01-05T14:30:00Z",
  "description": "Implement user authentication feature",
  "agent": "coder",
  "status": "active"
}
```

---

### 6. IDE Integration (4 tools)

**Purpose**: Sync and configure IDE integrations

| Tool                       | Description                         | Example Use Case                   |
| -------------------------- | ----------------------------------- | ---------------------------------- |
| `paracle_sync_ide`         | Sync IDE instructions               | Update GitHub Copilot instructions |
| `paracle_list_ide_configs` | List IDE integration configurations | View all IDE integrations          |
| `paracle_get_ide_config`   | Get specific IDE configuration      | Get VS Code integration config     |
| `paracle_init_ide`         | Initialize IDE integration          | Setup new IDE integration          |

**Example**:
```json
{
  "tool": "paracle_sync_ide",
  "params": {
    "ide": "github_copilot",
    "mode": "full"
  }
}
```

**Response**:
```json
{
  "ide": "github_copilot",
  "config_file": ".github/copilot-instructions.md",
  "status": "synced",
  "timestamp": "2026-01-05T14:35:00Z",
  "changes": [
    "Updated agent roster",
    "Added new roadmap phase",
    "Synced current state"
  ]
}
```

---

### 7. Validation & Sync (5 tools)

**Purpose**: Validate workspace integrity and sync state

| Tool                         | Description                | Example Use Case                 |
| ---------------------------- | -------------------------- | -------------------------------- |
| `paracle_validate_workspace` | Validate .parac/ integrity | Check workspace health           |
| `paracle_sync_workspace`     | Sync workspace state       | Regenerate manifest.yaml         |
| `paracle_check_governance`   | Check governance alignment | Verify roadmap/state consistency |
| `paracle_validate_yaml`      | Validate YAML syntax       | Check YAML file validity         |
| `paracle_fix_issues`         | Auto-fix common issues     | Fix common workspace problems    |

**Example**:
```json
{
  "tool": "paracle_validate_workspace",
  "params": {
    "path": ".parac"
  }
}
```

**Response**:
```json
{
  "status": "valid",
  "checks": [
    {"check": "required_files", "status": "passed", "message": "All required files present"},
    {"check": "yaml_syntax", "status": "passed", "message": "All YAML files valid"},
    {"check": "roadmap_alignment", "status": "passed", "message": "Roadmap and state aligned"},
    {"check": "agent_specs", "status": "passed", "message": "All agent specs valid"}
  ],
  "warnings": [],
  "errors": []
}
```

---

### 8. Log Management (6 tools)

**Purpose**: Search, analyze, and aggregate logs

| Tool                         | Description                  | Example Use Case                |
| ---------------------------- | ---------------------------- | ------------------------------- |
| `paracle_search_logs`        | Search logs with filters     | Find error logs from CoderAgent |
| `paracle_aggregate_logs`     | Aggregate log metrics        | Daily error count trends        |
| `paracle_get_log_stats`      | Get log statistics           | Error/warning/info counts       |
| `paracle_detect_anomalies`   | Detect log anomalies         | Identify unusual patterns       |
| `paracle_get_agent_actions`  | Get agent action log entries | View CoderAgent actions         |
| `paracle_get_execution_logs` | Get logs for execution       | Logs for workflow execution     |

**Example**:
```json
{
  "tool": "paracle_search_logs",
  "params": {
    "level": "error",
    "agent": "coder",
    "start_date": "2026-01-01",
    "end_date": "2026-01-05"
  }
}
```

**Response**:
```json
{
  "total": 12,
  "logs": [
    {
      "timestamp": "2026-01-03T10:15:30Z",
      "level": "error",
      "agent": "coder",
      "message": "Failed to parse response from OpenAI",
      "context": {"execution_id": "exec_01HJ..."}
    },
    // ... more logs
  ]
}
```

---

### 9. Templates & Examples (5 tools)

**Purpose**: Access templates and examples

| Tool                           | Description                      | Example Use Case               |
| ------------------------------ | -------------------------------- | ------------------------------ |
| `paracle_list_templates`       | List available project templates | Browse templates               |
| `paracle_get_template`         | Get template details             | View FastAPI template          |
| `paracle_create_from_template` | Create project from template     | Scaffold new project           |
| `paracle_list_examples`        | List available examples          | Browse example projects        |
| `paracle_get_example`          | Get example code                 | View agent inheritance example |

**Example**:
```json
{
  "tool": "paracle_list_templates",
  "params": {}
}
```

**Response**:
```json
{
  "templates": [
    {
      "id": "python_cli",
      "name": "Python CLI Application",
      "description": "Python CLI app with Click, agents, and workflows",
      "tags": ["python", "cli", "starter"]
    },
    {
      "id": "fastapi_rest",
      "name": "FastAPI REST API",
      "description": "REST API with FastAPI, agents, and database",
      "tags": ["python", "api", "rest"]
    }
  ]
}
```

---

## 📂 Resource URIs

Resources provide read access to Paracle workspace files and state.

### Configuration & Specs (5 resources)

| URI                               | Description             | Example                       |
| --------------------------------- | ----------------------- | ----------------------------- |
| `parac://agents/{agent_id}`       | Agent specifications    | `parac://agents/coder`        |
| `parac://workflows/{workflow_id}` | Workflow definitions    | `parac://workflows/release`   |
| `parac://tools/{tool_id}`         | Tool configurations     | `parac://tools/filesystem`    |
| `parac://providers/{provider_id}` | Provider configurations | `parac://providers/openai`    |
| `parac://policies/{policy_name}`  | Policy files            | `parac://policies/CODE_STYLE` |

### Runtime & State (4 resources)

| URI                             | Description           | Example                            |
| ------------------------------- | --------------------- | ---------------------------------- |
| `parac://executions/{exec_id}`  | Execution results     | `parac://executions/exec_01HJ...`  |
| `parac://logs/{session_id}`     | Session logs          | `parac://logs/session_01HJ...`     |
| `parac://state/current`         | Current project state | `parac://state/current`            |
| `parac://sessions/{session_id}` | Session data          | `parac://sessions/session_01HJ...` |

### Governance & Planning (5 resources)

| URI                       | Description                   | Example                   |
| ------------------------- | ----------------------------- | ------------------------- |
| `parac://roadmap/phases`  | Roadmap phases                | `parac://roadmap/phases`  |
| `parac://roadmap/current` | Current phase information     | `parac://roadmap/current` |
| `parac://adrs/{adr_id}`   | Architecture Decision Records | `parac://adrs/003`        |
| `parac://questions/open`  | Open questions                | `parac://questions/open`  |
| `parac://decisions/log`   | Decision log entries          | `parac://decisions/log`   |

### Knowledge & Memory (3 resources)

| URI                         | Description             | Example                          |
| --------------------------- | ----------------------- | -------------------------------- |
| `parac://knowledge/{topic}` | Knowledge base articles | `parac://knowledge/architecture` |
| `parac://memory/context`    | Context files           | `parac://memory/context`         |
| `parac://memory/summaries`  | Session/phase summaries | `parac://memory/summaries`       |

### Templates & Skills (3 resources)

| URI                               | Description       | Example                          |
| --------------------------------- | ----------------- | -------------------------------- |
| `parac://templates/{template_id}` | Project templates | `parac://templates/python_cli`   |
| `parac://skills/{skill_id}`       | Agent skills      | `parac://skills/api-development` |
| `parac://examples/{example_id}`   | Example projects  | `parac://examples/inheritance`   |

**Example Usage**:
```json
{
  "method": "resources/read",
  "params": {
    "uri": "parac://agents/coder"
  }
}
```

**Response**:
```yaml
id: coder
name: CoderAgent
description: Implementation of features, production-quality code
role: implementation
capabilities:
  - code_implementation
  - code_quality
  - integration
inherits_from: base_agent
...
```

---

## 💬 Prompt Templates

Prompts provide contextual guidance and generation templates.

### Generation Templates (4 prompts)

| Prompt              | Description                     | Use Case            |
| ------------------- | ------------------------------- | ------------------- |
| `agent_template`    | Generate agent specification    | Create new agent    |
| `workflow_template` | Generate workflow definition    | Create new workflow |
| `tool_template`     | Generate custom tool            | Create custom tool  |
| `skill_template`    | Generate agent skill definition | Create agent skill  |

### Guidance Templates (4 prompts)

| Prompt              | Description                | Use Case                 |
| ------------------- | -------------------------- | ------------------------ |
| `debugging_guide`   | Debug Paracle issues       | Troubleshoot problems    |
| `best_practices`    | Paracle best practices     | Learn conventions        |
| `governance_guide`  | Governance workflow        | Manage .parac/ workspace |
| `inheritance_guide` | Agent inheritance patterns | Understand inheritance   |

### Task-Specific Templates (4 prompts)

| Prompt              | Description                     | Use Case               |
| ------------------- | ------------------------------- | ---------------------- |
| `feature_workflow`  | Generate feature workflow       | Implement new feature  |
| `bugfix_workflow`   | Generate bugfix workflow        | Fix bug systematically |
| `deployment_guide`  | Deployment and production setup | Deploy to production   |
| `cost_optimization` | Cost optimization strategies    | Reduce API costs       |

**Example Usage**:
```json
{
  "method": "prompts/get",
  "params": {
    "name": "agent_template",
    "arguments": {
      "agent_type": "code_reviewer",
      "capabilities": ["code_review", "security_audit"]
    }
  }
}
```

**Response**:
```yaml
# Generated Agent Template

id: code_reviewer
name: Code Reviewer Agent
description: Reviews code for quality, security, and best practices

role: code_review
capabilities:
  - code_review
  - security_audit
  - static_analysis

inherits_from: base_agent

instructions: |
  You are a meticulous code reviewer focused on:
  - Code quality and maintainability
  - Security vulnerabilities
  - Best practices adherence
  - Performance considerations
  ...
```

---

## 🎯 Use Case Examples

### 1. Complete Development Workflow

**Scenario**: AI application manages entire feature development

```
1. paracle_session_start("Implement user auth")
2. paracle_get_current_phase() → Check project phase
3. paracle_query_roadmap() → Verify feature in roadmap
4. paracle_run_agent("architect", "Design auth system")
5. paracle_run_agent("coder", "Implement auth endpoints")
6. paracle_run_agent("tester", "Create test suite")
7. paracle_get_cost_report() → Check costs
8. paracle_session_end() → Complete session
```

### 2. Cost-Aware Agent Execution

**Scenario**: Execute agent with budget constraints

```
1. paracle_estimate_cost("coder", task) → $2.30
2. paracle_get_budget_status() → $47.32 used of $100
3. paracle_run_agent("coder", task, cost_limit=3.00)
4. paracle_get_cost_breakdown() → Review actual cost
```

### 3. Multi-Provider Strategy

**Scenario**: Test and switch providers for cost optimization

```
1. paracle_list_providers() → OpenAI, Anthropic, Groq
2. paracle_get_provider_models("groq") → llama-3-70b
3. paracle_test_provider("groq") → OK
4. paracle_estimate_cost(provider="groq") → $0.50 vs $2.30
5. paracle_set_default_provider("groq")
6. paracle_run_agent("coder", task)
```

### 4. Governance-Driven Development

**Scenario**: AI follows project governance

```
1. paracle_get_project_state() → Phase 5, 60% complete
2. paracle_query_roadmap(phase=5) → Current deliverables
3. paracle_get_open_questions() → Check blockers
4. paracle_list_adrs() → Review decisions
5. paracle_get_adr(3) → Read specific ADR
6. paracle_run_workflow("feature_development")
7. paracle_update_progress(deliverable="skill_execution", 70%)
```

### 5. Log Analysis & Troubleshooting

**Scenario**: Analyze and debug issues

```
1. paracle_search_logs(level="error", days=7)
2. paracle_aggregate_logs(group_by="agent") → Error counts by agent
3. paracle_detect_anomalies() → Spike in API timeouts
4. paracle_get_execution_logs(exec_id) → Detailed logs
5. paracle_run_agent("reviewer", "Analyze error patterns")
```

### 6. Template-Based Project Creation

**Scenario**: Create new project from template

```
1. paracle_list_templates() → Browse templates
2. paracle_get_template("fastapi_rest") → View details
3. paracle_create_from_template("fastapi_rest", name="my-api")
4. paracle_init_ide("github_copilot") → Setup IDE
5. paracle_sync_ide() → Sync instructions
```

---

## 🔗 Integration Examples

### Claude Desktop

**Config**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "paracle": {
      "command": "paracle",
      "args": ["mcp-server", "start", "--mode", "stdio"]
    }
  }
}
```

**Usage in Claude**:
```
User: "Show me the current project phase"
Claude: [Uses paracle_get_current_phase tool]
"The project is in Phase 5 (Agent Skills & Discovery), currently at 60% completion..."

User: "Run the CoderAgent to implement user authentication"
Claude: [Uses paracle_run_agent tool]
"I'll execute the CoderAgent with that task..."
```

### Cline (VS Code)

**Config**: `.vscode/settings.json`

```json
{
  "cline.mcpServers": [
    {
      "name": "paracle",
      "url": "http://localhost:3100"
    }
  ]
}
```

### Continue.dev

**Config**: `~/.continue/config.json`

```json
{
  "mcpServers": [
    {
      "name": "paracle",
      "url": "http://localhost:3100"
    }
  ]
}
```

---

## 📈 Coverage Matrix

| Capability Category   | Tools  | Resources | Prompts | Coverage   |
| --------------------- | ------ | --------- | ------- | ---------- |
| Core Execution        | 8      | 3         | 2       | ✅ 100%     |
| Provider Management   | 5      | 1         | 0       | ✅ 100%     |
| Cost Tracking         | 6      | 0         | 1       | ✅ 100%     |
| Governance & Planning | 7      | 5         | 1       | ✅ 100%     |
| Session Management    | 5      | 1         | 0       | ✅ 100%     |
| IDE Integration       | 4      | 0         | 0       | ✅ 100%     |
| Validation & Sync     | 5      | 0         | 0       | ✅ 100%     |
| Log Management        | 6      | 1         | 0       | ✅ 100%     |
| Templates & Examples  | 5      | 3         | 4       | ✅ 100%     |
| **TOTAL**             | **56** | **21**    | **12**  | **✅ 100%** |

---

## 🚀 Implementation Phases

### Phase 1: Core Capabilities (Week 1)

- MCP server implementation (Python MCP SDK)
- Core execution tools (8)
- Basic resources (6)
- Stdio transport

### Phase 2: Advanced Tools (Week 2)

- Provider management tools (5)
- Cost tracking tools (6)
- Governance tools (7)
- Session management tools (5)

### Phase 3: Platform Integration (Week 3)

- IDE integration tools (4)
- Validation tools (5)
- Log management tools (6)
- Template tools (5)

### Phase 4: Resources & Prompts (Week 4)

- Complete resource URIs (21)
- Prompt templates (12)
- Resource providers
- Prompt handlers

### Phase 5: Testing & Documentation (Week 5)

- Integration tests for all tools
- Integration examples (Claude, Cline, Continue)
- Comprehensive documentation
- Capability coverage validation

---

## 📚 Documentation Structure

### Core Documentation

- **docs/mcp-server.md** - Overview and architecture
- **docs/mcp-server-setup.md** - Installation and setup
- **docs/mcp-server-api.md** - Complete API reference
- **docs/mcp-capability-coverage.md** - This document

### Category Documentation

- **docs/mcp-server-tools.md** - Tool reference by category
- **docs/mcp-server-resources.md** - Resource URI reference
- **docs/mcp-server-prompts.md** - Prompt template reference

### Integration Documentation

- **docs/mcp-integrations.md** - Integration guides
- **docs/mcp-claude-integration.md** - Claude Desktop setup
- **docs/mcp-cline-integration.md** - Cline VS Code setup
- **docs/mcp-continue-integration.md** - Continue.dev setup

### Examples

- **examples/mcp_server_demo.py** - Demo script
- **examples/mcp_custom_integration.py** - Custom integration example
- **examples/mcp_cost_tracking.py** - Cost tracking example
- **examples/mcp_governance.py** - Governance workflow example

---

## 🎓 Key Takeaways

### For AI Application Developers

1. **Complete Platform Access**: MCP server exposes 100% of Paracle functionality
2. **9 Capability Categories**: Execution, providers, costs, governance, sessions, IDE, validation, logs, templates
3. **56+ Tools**: Comprehensive toolset for AI agent management
4. **21+ Resources**: Read access to all workspace state
5. **12+ Prompts**: Contextual guidance and generation

### For Paracle Users

1. **External AI Control**: Use Claude, Cline, or Continue to manage Paracle
2. **Cost Awareness**: Track and control API costs through MCP
3. **Governance Integration**: AI applications follow project governance
4. **Full Observability**: Logs, metrics, and analytics via MCP
5. **Template Access**: Create projects from templates via AI

### For Contributors

1. **Extensible Design**: Easy to add new tools/resources/prompts
2. **Category Organization**: Tools grouped by capability
3. **Test Coverage**: All tools must have integration tests
4. **Documentation**: Each tool/resource/prompt documented
5. **Version Compatibility**: MCP protocol v1.0 compliance

---

## 📞 Support

- **Documentation**: See `docs/mcp-*.md` files
- **Examples**: Check `examples/mcp_*.py` scripts
- **Issues**: https://github.com/IbIFACE-Tech/paracle-lite/issues
- **Discussions**: https://github.com/IbIFACE-Tech/paracle-lite/discussions

---

**Last Updated**: 2026-01-05
**Version**: 1.0
**Status**: Specification (Phase 7 implementation pending)
