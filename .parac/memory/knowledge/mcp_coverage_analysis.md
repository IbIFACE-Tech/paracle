# MCP Coverage Analysis

> **Analysis of Paracle functions accessible through Model Context Protocol (MCP)**
>
> - **Date**: 2026-01-09
> - **Version**: 1.0.1
> - **Status**: ⚠️ Partial Coverage

## Summary

**Answer**: ❌ **NO** - Not all Paracle functions are accessible through MCP yet.

### Current MCP Coverage

The MCP server (`paracle_mcp`) exposes a **subset** of Paracle functionality:

| Category           | Exposed via MCP                               | Missing from MCP         |
| ------------------ | --------------------------------------------- | ------------------------ |
| **Agent Tools**    | ✅ All tools from `agent_tool_registry`        | -                        |
| **Context Tools**  | ✅ current_state, roadmap, decisions, policies | -                        |
| **Workflow Tools** | ✅ run, list                                   | -                        |
| **Memory Tools**   | ✅ log_action                                  | ❌ Full memory management |
| **Custom Tools**   | ✅ From `.parac/tools/custom/`                 | -                        |
| **External MCP**   | ✅ Can connect to other MCP servers            | -                        |
| **CLI Commands**   | ❌ Most CLI commands NOT exposed               | **35+ commands missing** |

---

## What's Accessible via MCP

### 1. ✅ Agent Tools (via agent_tool_registry)

The MCP server exposes all tools registered in `agent_tool_registry`:

```python
from paracle_orchestration.agent_tool_registry import agent_tool_registry

# All these tools are available via MCP
tools = agent_tool_registry.get_tools_for_agent(agent_id)
```

**Examples**:

- Filesystem operations
- Code analysis
- Test execution
- Git operations (if registered)

### 2. ✅ Context Tools

```python
# Available MCP tools for project context
- context_current_state    # .parac/memory/context/current_state.yaml
- context_roadmap          # .parac/roadmap/roadmap.yaml
- context_decisions        # .parac/roadmap/decisions.md
- context_policies         # .parac/policies/*
```

### 3. ✅ Workflow Tools

```python
# Available MCP tools for workflows
- workflow_run     # Execute a workflow (feature_development, bugfix, etc.)
- workflow_list    # List available workflows
```

### 4. ✅ Memory Tools

```python
# Available MCP tools for memory
- memory_log_action    # Log to agent_actions.log
```

### 5. ✅ Custom Tools

Tools in `.parac/tools/custom/*.py` are automatically exposed with `custom_` prefix:

```python
# Example: .parac/tools/custom/my_tool.py
# Becomes: custom_my_tool (in MCP)
```

### 6. ✅ External MCP Servers

Can connect to other MCP servers defined in `.parac/tools/mcp/mcp.yaml`:

```yaml
servers:
  - id: github
    name: GitHub MCP Server
    command: mcp-github
    args: []
    tools_prefix: github
```

### 7. ✅ Agent Router

```python
- set_active_agent    # Switch context to specific agent
```

---

## What's **NOT** Accessible via MCP

### ❌ CLI Commands Not Exposed

The following **35+ CLI commands** are NOT available through MCP:

#### Project Management

- ❌ `paracle init`
- ❌ `paracle status`
- ❌ `paracle sync`

- ❌ `paracle validate`
- ❌ `paracle session`

#### Board & Task Management

- ❌ `paracle board list`
- ❌ `paracle board create`

- ❌ `paracle board show`
- ❌ `paracle task list`
- ❌ `paracle task create`

- ❌ `paracle task move`

#### Error Management

- ❌ `paracle errors list`
- ❌ `paracle errors stats`

- ❌ `paracle errors patterns`
- ❌ `paracle errors clear`

#### Cost Tracking

- ❌ `paracle cost track`
- ❌ `paracle cost report`
- ❌ `paracle cost budget`

#### Providers

- ❌ `paracle providers list`

- ❌ `paracle providers configure`
- ❌ `paracle providers test`

#### Tools Management

- ❌ `paracle tools list`
- ❌ `paracle tools install`

- ❌ `paracle tools configure`

#### Cache Management

- ❌ `paracle cache clear`

- ❌ `paracle cache stats`

#### Config Management

- ❌ `paracle config show`

- ❌ `paracle config set`
- ❌ `paracle config validate`

#### Git Operations

- ❌ `paracle git commit`
- ❌ `paracle git status`
- ❌ `paracle git push`

#### Release Management

- ❌ `paracle release prepare`
- ❌ `paracle release publish`
- ❌ `paracle release notes`

#### Governance

- ❌ `paracle governance list`

- ❌ `paracle governance check`
- ❌ `paracle audit log`

- ❌ `paracle compliance report`

#### Observability

- ❌ `paracle benchmark run`
- ❌ `paracle pool status`
- ❌ `paracle logs tail`

#### Remote Development

- ❌ `paracle remote connect`

- ❌ `paracle remote sync`

#### Retry Management

- ❌ `paracle retry list`

- ❌ `paracle retry execute`

#### Reviews & Approvals

- ❌ `paracle reviews list`
- ❌ `paracle approvals pending`

#### Conflicts

- ❌ `paracle conflicts detect`
- ❌ `paracle conflicts resolve`

#### Documentation

- ❌ `paracle adr create`
- ❌ `paracle roadmap show`

#### Services Inventory (NEW)

- ❌ `paracle inventory check`
- ❌ `paracle inventory update`

#### IDE Integration

- ❌ `paracle ide sync`
- ❌ `paracle ide build`

#### Groups

- ❌ `paracle groups list`
- ❌ `paracle groups create`

#### A2A Protocol

- ❌ `paracle a2a connect`
- ❌ `paracle a2a send`

---

## Architecture Gap

### Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     IDE / AI Assistant                      │
└──────────────────────┬──────────────────────────────────────┘
                       │ MCP Protocol
                       ↓
┌─────────────────────────────────────────────────────────────┐
│               ParacleMCPServer                              │
│                                                             │
│  ✅ Agent Tools (agent_tool_registry)                      │
│  ✅ Context Tools (current_state, roadmap, etc.)           │
│  ✅ Workflow Tools (run, list)                             │
│  ✅ Memory Tools (log_action)                              │
│  ✅ Custom Tools (.parac/tools/custom/)                    │
│                                                             │
│  ❌ CLI Commands (35+ commands NOT exposed)                │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Paracle Core + CLI                             │
│                                                             │
│  - paracle_orchestration (workflows, agent execution)      │
│  - paracle_kanban (boards, tasks)                          │
│  - paracle_observability (errors, metrics)                 │
│  - paracle_cli (35+ commands)                              │
│  - ... 37 total packages                                   │
└─────────────────────────────────────────────────────────────┘
```

### Gap: CLI Commands vs MCP Tools

The MCP server does NOT expose CLI commands directly. It only exposes:

1. **Agent tools** - Registered programmatically in code
2. **Custom tools** - User-defined Python functions
3. **Built-in MCP tools** - Context, workflow, memory

To access CLI functionality via MCP, you would need to:

```python
# Current workaround - use shell execution tool
tool_result = shell_execute("paracle board list")

# vs. Desired - native MCP tool
tool_result = call_tool("paracle_board_list", {})
```

---

## Recommendations

### ✅ Option 1: Add MCP Tool Wrappers (Recommended)

Create MCP tool wrappers for common CLI commands:

```python
# In paracle_mcp/server.py

def _get_kanban_tools(self) -> list[dict]:
    """Get Kanban board MCP tools."""
    return [
        {
            "name": "paracle_board_list",
            "description": "List all Kanban boards",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "paracle_board_create",
            "description": "Create a new Kanban board",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Board name"},
                    "description": {"type": "string", "description": "Board description"},
                },
                "required": ["name"],
            },
        },
        # ... more board tools
    ]

async def _handle_kanban_tool(self, name: str, arguments: dict) -> dict:
    """Handle Kanban tool calls."""
    from paracle_kanban import BoardRepository

    repo = BoardRepository()

    if name == "paracle_board_list":

        boards = repo.list_boards()
        return {"boards": [b.model_dump() for b in boards]}

    elif name == "paracle_board_create":
        board = repo.create_board(**arguments)
        return {"board": board.model_dump()}
    # ... more handlers
```

### ✅ Option 2: Auto-Generate MCP Tools from CLI

Automatically generate MCP tool schemas from Click commands:

```python
def _generate_mcp_tools_from_cli(self):
    """Auto-generate MCP tools from CLI commands."""
    from paracle_cli.main import cli

    for command in cli.commands.values():
        # Extract command metadata
        name = f"paracle_{command.name}"
        description = command.help or ""


        # Extract parameters from Click decorators
        params = self._extract_click_params(command)

1       # Generate MCP tool schema
2       tool_schema = {
3           "name": name,
4           "description": description,
            "inputSchema": params,
        }
        yield tool_schema
1`

### ✅ Option 3: Use API-First Pattern

Expose CLI functionality through REST API, then wrap in MCP:

```

CLI Command → REST API → MCP Tool

```

Example:

```python
# MCP tool calls REST API
async def _handle_api_tool(self, name: str, arguments: dict):
    async with httpx.AsyncClient() as client:
1       response = await client.post(
2           f"http://localhost:8000/api/v1/{name}",
3           json=arguments
4       )
        return response.json()
```

1-

## Implementation Priority

### Phase 1: High-Value MCP Tools (Immediate)

Expose these CLI commands as MCP tools first:

1. ✅ **Kanban Management** (`board`, `task`)
2. ✅ **Error Monitoring** (`errors list`, `errors stats`)
3. ✅ **Cost Tracking** (`cost report`)
4. ✅ **Config Management** (`config show`, `config set`)
5. ✅ **Services Inventory** (`inventory check`, `inventory update`)

### Phase 2: Extended Coverage (Soon)

1. ✅ **Provider Management** (`providers list`, `providers test`)
2. ✅ **Tools Management** (`tools list`, `tools install`)
3. ✅ **Git Operations** (`git status`, `git commit`)
4. ✅ **Release Management** (`release prepare`, `release notes`)

### Phase 3: Full Coverage (Later)

1. All remaining CLI commands

---

## Current Limitations

### 1. No Direct CLI Access

MCP cannot directly invoke CLI commands. Workarounds:

```python
# ❌ Not available
result = mcp_tool("paracle_board_list")

# ✅ Current workaround
result = shell_tool("paracle board list")
```

### 2. No Streaming Support

CLI commands with progress bars/streaming output don't work well in MCP.

### 3. No Interactive Prompts

CLI commands requiring user input won't work through MCP.

### 4. Authentication

MCP tools don't inherit CLI authentication/API keys automatically.

---

## Testing MCP Coverage

```bash
# 1. Start MCP server
paracle mcp serve --stdio

# 2. In another terminal - list available tools
echo '{"method": "tools/list"}' | paracle mcp serve --stdio

# 3. Count exposed tools
# Expected: ~50-100 tools (agent tools + context + workflow + memory + custom)
# Actual: Check output
```

---

## Conclusion

### Current State

- ✅ **Agent tools**: Fully accessible via MCP
- ✅ **Context/Workflow/Memory**: Core operations available
- ✅ **Custom tools**: Extensible via `.parac/tools/custom/`
- ✅ **External MCP**: Can federate with other MCP servers
- ❌ **CLI commands**: 35+ commands NOT accessible via MCP

### Recommendation

**Implement Option 1** (MCP Tool Wrappers) for high-priority commands in Phase 1, starting with Kanban, Errors, and Cost tracking.

This provides native MCP integration without requiring REST API overhead, while maintaining type safety and better error handling than shell execution workarounds.

---

## Related Files

- **MCP Server**: [`packages/paracle_mcp/server.py`](../../packages/paracle_mcp/server.py)
- **MCP Client**: [`packages/paracle_mcp/client.py`](../../packages/paracle_mcp/client.py)
- **Tool Registry**: [`packages/paracle_orchestration/agent_tool_registry.py`](../../packages/paracle_orchestration/agent_tool_registry.py)
- **CLI Main**: [`packages/paracle_cli/main.py`](../../packages/paracle_cli/main.py)

---

**Status**: ⚠️ Partial Coverage (needs enhancement)
**Version**: 1.0.1
**Last Updated**: 2026-01-09
