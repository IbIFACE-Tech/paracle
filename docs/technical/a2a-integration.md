# A2A Protocol Integration

> **Agent-to-Agent Protocol** - Open standard for AI agent interoperability.

Paracle implements the [A2A protocol](https://a2a-protocol.org/) enabling both:
1. **Server Mode**: Expose Paracle agents as A2A-compatible endpoints
2. **Client Mode**: Call external A2A agents from Paracle workflows

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL A2A AGENTS                         │
│           (Any A2A-compatible agent/service)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                    A2A Protocol (JSON-RPC 2.0)
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                        PARACLE                                   │
│  ┌─────────────────┐              ┌──────────────────────────┐  │
│  │   A2A Server    │              │      A2A Client          │  │
│  │ (paracle_a2a)   │              │   (ParacleA2AClient)     │  │
│  │                 │              │                          │  │
│  │ Expose agents   │              │  Call external agents    │  │
│  │ via Agent Cards │              │  from workflows          │  │
│  └────────┬────────┘              └────────────┬─────────────┘  │
│           │                                    │                 │
│           └────────────┬───────────────────────┘                 │
│                        │                                         │
│              ┌─────────┴─────────┐                              │
│              │  Paracle Agents   │                              │
│              │  (coder, tester,  │                              │
│              │   reviewer, etc.) │                              │
│              └───────────────────┘                              │
└──────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Expose Paracle Agents (Server Mode)

```bash
# Start A2A server exposing all agents
paracle a2a serve --port 8080

# Expose specific agents only
paracle a2a serve --agents coder,reviewer --port 8080

# With API key authentication
paracle a2a serve --auth apikey --api-key your-secret-key
```

### Discover and Call External Agents (Client Mode)

```bash
# Discover an A2A agent
paracle a2a agents discover http://example.com/a2a/agents/helper

# Invoke an external agent
paracle a2a invoke http://example.com/a2a/agents/coder "Write a hello world in Python"

# Stream responses
paracle a2a invoke http://example.com/a2a/agents/coder "Explain recursion" --stream
```

## A2A Protocol Concepts

### Agent Cards

Agent Cards are JSON metadata describing an agent's capabilities. They enable automatic discovery.

```json
{
  "name": "Paracle Coder",
  "description": "Code implementation agent",
  "url": "http://localhost:8080/a2a/agents/coder",
  "protocolVersion": "0.2.5",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false,
    "stateTransitionHistory": true
  },
  "skills": [
    {
      "id": "code-implementation",
      "name": "Code Implementation",
      "description": "Write production-quality code"
    }
  ]
}
```

Paracle generates Agent Cards automatically from `.parac/agents/specs/`.

### Task Lifecycle

```
SUBMITTED → WORKING → COMPLETED
              ↓
        INPUT_REQUIRED (user input needed)
              ↓
           WORKING
              ↓
   COMPLETED | FAILED | CANCELLED
```

### Messages and Artifacts

- **Messages**: User-agent conversation with Parts (text, file, data)
- **Artifacts**: Discrete outputs produced by the agent (code, documents, etc.)

## CLI Commands

### Server Commands

```bash
# Start A2A server
paracle a2a serve [OPTIONS]

Options:
  --host TEXT           Server host (default: 0.0.0.0)
  --port INTEGER        Server port (default: 8080)
  --agents TEXT         Agent IDs to expose (can repeat)
  --parac-root PATH     Path to .parac directory
  --no-streaming        Disable SSE streaming
  --auth [none|apikey|bearer]  Authentication mode
  --api-key TEXT        API key for authentication
```

### Agent Discovery

```bash
# List local agents
paracle a2a agents list --local

# List agents from remote server
paracle a2a agents list --url http://example.com/a2a

# Discover specific agent
paracle a2a agents discover http://example.com/a2a/agents/helper
```

### Invoking Agents

```bash
# Basic invocation (waits for completion)
paracle a2a invoke <URL> "message"

# With context for conversation continuity
paracle a2a invoke <URL> "continue" --context ctx123

# Streaming mode
paracle a2a invoke <URL> "message" --stream

# Check task status
paracle a2a status <TASK_ID> --url <URL>

# Watch task status
paracle a2a status <TASK_ID> --url <URL> --watch
```

## Programmatic Usage

### Server

```python
from pathlib import Path
from paracle_a2a.config import A2AServerConfig
from paracle_a2a.server.app import create_a2a_app, run_a2a_server

# Create FastAPI app
app = create_a2a_app(
    parac_root=Path(".parac"),
    config=A2AServerConfig(port=8080),
)

# Or run directly
run_a2a_server(
    parac_root=Path(".parac"),
    config=A2AServerConfig(
        port=8080,
        agent_ids=["coder", "reviewer"],
        enable_streaming=True,
    ),
)
```

### Client

```python
import asyncio
from paracle_a2a.client import ParacleA2AClient
from paracle_a2a.config import A2AClientConfig

async def main():
    # Create client
    client = ParacleA2AClient(
        url="http://example.com/a2a/agents/coder",
        config=A2AClientConfig(timeout_seconds=60),
    )

    # Discover agent capabilities
    card = await client.discover()
    print(f"Agent: {card.name}")
    print(f"Skills: {[s.name for s in card.skills]}")

    # Invoke agent (synchronous)
    task = await client.invoke(
        message="Write a hello world in Python",
        wait=True,
    )
    print(f"Status: {task.status.state}")

    # Invoke with streaming
    async for event in client.invoke_streaming(
        message="Explain recursion",
    ):
        print(f"Event: {event.type}")

asyncio.run(main())
```

### A2A Tool for Workflows

```python
from paracle_a2a.integration import A2ACallTool

# Create tool
tool = A2ACallTool()

# Use in workflow
result = await tool.execute({
    "url": "http://example.com/a2a/agents/analyzer",
    "message": "Analyze this code for security issues",
    "wait": True,
})

print(f"Task: {result.task_id}")
print(f"Status: {result.status}")
print(f"Result: {result.result}")
```

## Server Endpoints

When running `paracle a2a serve`, the following endpoints are available:

### Discovery

| Endpoint | Description |
|----------|-------------|
| `GET /.well-known/agent.json` | Root Agent Card |
| `GET /a2a/agents` | List available agents |
| `GET /a2a/agents/{id}/.well-known/agent.json` | Agent-specific Card |

### JSON-RPC 2.0

| Endpoint | Methods |
|----------|---------|
| `POST /a2a/agents/{id}` | `tasks/send`, `tasks/get`, `tasks/list`, `tasks/cancel` |

### Streaming

| Endpoint | Description |
|----------|-------------|
| `GET /a2a/agents/{id}/stream/{task_id}` | SSE stream for task updates |

## Configuration

### Server Configuration

```python
from paracle_a2a.config import A2AServerConfig

config = A2AServerConfig(
    # Server
    host="0.0.0.0",
    port=8080,
    base_path="/a2a",

    # Agents
    agent_ids=["coder", "reviewer"],  # Empty = all
    expose_all_agents=True,

    # Capabilities
    enable_streaming=True,
    enable_push_notifications=False,
    enable_state_transition_history=True,

    # Security
    require_authentication=False,
    api_keys=["secret-key"],
    cors_origins=["*"],

    # Rate limiting
    rate_limit_enabled=False,
    rate_limit_requests=100,
    rate_limit_window_seconds=60,

    # Tasks
    task_timeout_seconds=300.0,
    max_concurrent_tasks=10,
    task_history_limit=1000,
)
```

### Client Configuration

```python
from paracle_a2a.config import A2AClientConfig

config = A2AClientConfig(
    # Connection
    timeout_seconds=30.0,
    connect_timeout_seconds=10.0,
    max_retries=3,

    # Streaming
    enable_streaming=True,
    stream_timeout_seconds=300.0,

    # Authentication
    auth_type="bearer",  # or "apiKey"
    auth_token="your-token",

    # Discovery
    cache_agent_cards=True,
    card_cache_ttl_seconds=3600,
)
```

## Security

### Authentication Modes

1. **None** (default): No authentication required
2. **API Key**: `X-API-Key` header or query parameter
3. **Bearer**: `Authorization: Bearer <token>` header

```bash
# Start with API key auth
paracle a2a serve --auth apikey --api-key secret123

# Client uses
paracle a2a invoke <URL> "message" --api-key secret123
```

### CORS

By default, all origins are allowed. Configure in server config:

```python
config = A2AServerConfig(
    cors_origins=["https://your-domain.com"],
)
```

## Integration with Paracle Workflows

### Registering A2A Tool

```python
from paracle_a2a.integration import A2ACallTool
from paracle_orchestration import agent_tool_registry

# Register tool globally
agent_tool_registry.register_tool(
    "a2a_call",
    A2ACallTool(),
)

# Now any Paracle agent can use it
# In agent spec:
# tools:
#   - a2a_call
```

### Using in Workflows

```yaml
# .parac/workflows/analysis.yaml
name: code-analysis
steps:
  - id: analyze
    agent: coder
    task: "Analyze code"

  - id: external-review
    tool: a2a_call
    params:
      url: "http://external-service/a2a/agents/security"
      message: "Review for security issues"
    depends_on: [analyze]
```

## Task State Mapping

| A2A State | Paracle Status |
|-----------|----------------|
| `submitted` | `PENDING` |
| `working` | `RUNNING` |
| `input-required` | `AWAITING_APPROVAL` |
| `auth-required` | `AWAITING_APPROVAL` |
| `completed` | `COMPLETED` |
| `failed` | `FAILED` |
| `cancelled` | `CANCELLED` |
| `rejected` | `FAILED` |

## Error Handling

### Error Codes

| Code | Error | Description |
|------|-------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Invalid JSON-RPC |
| -32601 | Method not found | Unknown method |
| -32602 | Invalid params | Invalid parameters |
| -32603 | Internal error | Server error |
| -32001 | Task not found | Task ID not found |
| -32002 | Task cancelled | Task was cancelled |
| -32003 | Agent not found | Agent ID not found |
| -32004 | Content type not supported | Unsupported content |
| -32006 | Authentication required | Auth needed |
| -32008 | Task timeout | Task timed out |
| -32009 | Rate limit exceeded | Too many requests |

### Handling Errors

```python
from paracle_a2a.exceptions import TaskNotFoundError, AgentNotFoundError

try:
    task = await client.get_task("invalid-id")
except TaskNotFoundError as e:
    print(f"Task not found: {e.task_id}")
except AgentNotFoundError as e:
    print(f"Agent not found: {e.agent_id}")
```

## Remote Agents in Manifest

Define external A2A agents in your manifest to use them like local agents.

### Configuration

Add remote agents to `.parac/agents/manifest.yaml`:

```yaml
# Local agents
agents:
  - id: coder
    name: Coder Agent
    # ...

# Remote A2A agents
remote_agents:
  - id: external-coder
    name: External Code Assistant
    url: https://api.example.com/a2a/agents/coder
    description: Enterprise code generation service
    auth_type: bearer
    auth_token_env: EXTERNAL_CODER_TOKEN
    timeout_seconds: 120

  - id: security-scanner
    name: Security Analysis Agent
    url: https://security.example.com/a2a/agents/scanner
    description: Automated security vulnerability detection
    auth_type: apiKey
    auth_token_env: SECURITY_API_KEY
    timeout_seconds: 300
    tags:
      - security
      - compliance
```

### Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (use with `remote:` prefix) |
| `name` | string | Yes | Human-readable name |
| `url` | string | Yes | A2A endpoint URL |
| `description` | string | No | Agent description |
| `auth_type` | string | No | Authentication: `bearer` or `apiKey` |
| `auth_token_env` | string | No | Environment variable for auth token |
| `timeout_seconds` | float | No | Request timeout (default: 60) |
| `provider` | string | No | Provider/organization name |
| `version` | string | No | Agent version |
| `tags` | list | No | Tags for filtering |

### Usage

#### CLI Commands

```bash
# List all agents including remote
paracle agents list --remote

# List only remote agents
paracle agents list --remote-only

# Run a remote agent (use remote: prefix)
paracle agents run remote:external-coder --task "Write unit tests"

# Or by ID if unique
paracle agents run security-scanner --task "Scan for vulnerabilities"

# Dry run to validate remote agent
paracle agents run remote:external-coder --task "Test" --dry-run
```

#### In Workflows

```yaml
# .parac/workflows/full-review.yaml
name: full-code-review
steps:
  - id: local-review
    agent: reviewer
    task: "Review code changes"

  - id: security-scan
    agent: remote:security-scanner
    task: "Scan for security issues"
    depends_on: [local-review]

  - id: external-review
    agent: remote:external-coder
    task: "Suggest improvements"
    depends_on: [local-review]
```

#### Programmatic

```python
from paracle_a2a.registry import get_remote_registry

# Get registry
registry = get_remote_registry()

# List all remote agents
for agent in registry.list_all():
    print(f"{agent.id}: {agent.name} @ {agent.url}")

# Get specific agent
agent = registry.resolve("external-coder")
if agent:
    config = agent.get_client_config()
    # Use config with ParacleA2AClient
```

### Environment Variables

Authentication tokens should be stored in environment variables:

```bash
# .env (never commit!)
EXTERNAL_CODER_TOKEN=your-bearer-token
SECURITY_API_KEY=your-api-key
```

The `auth_token_env` field specifies which environment variable contains the token.

### Discovery

Remote agents can be auto-discovered to update capabilities:

```python
from paracle_a2a.registry import get_remote_registry

registry = get_remote_registry()

# Discover and update agent capabilities
agent = await registry.discover_and_update("external-coder")
if agent:
    print(f"Skills: {agent.skills}")
    print(f"Streaming: {agent.capabilities.get('streaming')}")
```

## Related Documentation

- [A2A Protocol Specification](https://a2a-protocol.org/latest/)
- [MCP Integration](./mcp-integration.md)
- [Agent Configuration](./agents.md)
- [Workflow Orchestration](./workflows.md)

## API Reference

### Models

- `AgentCard` - Agent discovery metadata
- `Task` - Task with lifecycle
- `Message` - Message with parts
- `Artifact` - Output artifact
- `TaskState` - Task state enum
- `Part` - TextPart, FilePart, DataPart

### Server Components

- `AgentCardGenerator` - Generate cards from specs
- `TaskManager` - Task lifecycle management
- `ParacleA2AExecutor` - Bridge to Paracle agents
- `EventQueue` - SSE event streaming

### Client Components

- `ParacleA2AClient` - Full-featured client
- `AgentDiscovery` - Agent Card discovery
- `StreamingHandler` - SSE handling

### Integration

- `A2ACallTool` - BaseTool for workflows
- `A2AParacleBridge` - State mapping utilities
