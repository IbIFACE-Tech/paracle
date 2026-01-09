# MCP Integration

Paracle provides full support for the Model Context Protocol (MCP), enabling tool sharing between AI applications.

## Overview

The Model Context Protocol (MCP) is a standard protocol for sharing tools and context between AI applications. Paracle supports MCP in two ways:

1. **MCP Server** - Expose Paracle tools to IDEs and AI assistants
2. **MCP Client** - Discover and use tools from external MCP servers

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Integration                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Paracle MCP Server                      │   │
│  │                                                          │   │
│  │  Exposes:                                               │   │
│  │  - Built-in tools (filesystem, HTTP, shell)             │   │
│  │  - Agent tools (coder, reviewer, tester, etc.)          │   │
│  │  - Custom tools (.parac/tools/custom/)                  │   │
│  │  - Context tools (state, roadmap, policies)             │   │
│  │                                                          │   │
│  │  Transports: stdio, HTTP, WebSocket                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             ↕                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  MCP Client                              │   │
│  │                                                          │   │
│  │  Discovers tools from:                                  │   │
│  │  - External MCP servers                                 │   │
│  │  - Claude Desktop                                       │   │
│  │  - VS Code MCP extensions                               │   │
│  │  - Custom MCP providers                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## MCP Server

### Starting the Server

```bash
# Start MCP server (stdio transport - for IDE integration)
paracle mcp serve

# Start with HTTP transport
paracle mcp serve --transport http --port 3000

# Start with WebSocket transport
paracle mcp serve --transport websocket --port 3000

# With verbose logging
paracle mcp serve --verbose
```

### Exposed Tools

The MCP server exposes several categories of tools:

#### Context Tools

| Tool | Description |
|------|-------------|
| `context.current_state` | Get current project state from `.parac/memory/context/current_state.yaml` |
| `context.roadmap` | Get project roadmap from `.parac/roadmap/roadmap.yaml` |
| `context.policies` | Get project policies from `.parac/policies/` |
| `context.decisions` | Get architecture decisions from `.parac/roadmap/decisions.md` |

#### Workflow Tools

| Tool | Description |
|------|-------------|
| `workflow.list` | List available workflows |
| `workflow.run` | Execute a workflow |
| `workflow.status` | Get workflow execution status |

#### Memory Tools

| Tool | Description |
|------|-------------|
| `memory.log_action` | Log an action to `.parac/memory/logs/agent_actions.log` |
| `memory.log_decision` | Log a decision to `.parac/memory/logs/decisions.log` |

#### Agent Tools

All agent-specific tools are exposed with the agent prefix:

| Tool Pattern | Example |
|--------------|---------|
| `coder.*` | `coder.generate_code`, `coder.refactor` |
| `reviewer.*` | `reviewer.analyze`, `reviewer.suggest` |
| `tester.*` | `tester.generate_tests`, `tester.coverage` |
| `documenter.*` | `documenter.generate_docs` |

### Server Configuration

Configure the MCP server in `.parac/tools/mcp/`:

```yaml
# .parac/tools/mcp/mcp.yaml
server:
  name: paracle
  version: 1.0.0
  description: Paracle multi-agent framework tools

  # Transport configuration
  transports:
    stdio:
      enabled: true
    http:
      enabled: true
      port: 3000
      host: localhost
    websocket:
      enabled: false

  # Tool filtering
  expose_tools:
    - context.*
    - workflow.*
    - memory.*
    - coder.*
    - reviewer.*

  # Security
  security:
    require_auth: false
    allowed_origins:
      - "*"
```

### IDE Integration

#### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "paracle": {
      "command": "paracle",
      "args": ["mcp", "serve"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

#### VS Code

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "paracle": {
      "command": "paracle",
      "args": ["mcp", "serve"],
      "transport": "stdio"
    }
  }
}
```

#### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "paracle": {
      "command": "paracle",
      "args": ["mcp", "serve"],
      "env": {
        "PARACLE_PROJECT": "${workspaceFolder}"
      }
    }
  }
}
```

## MCP Client

### Connecting to External Servers

```python
from paracle_mcp.client import MCPClient
from paracle_mcp.registry import MCPToolRegistry

# Create client
client = MCPClient(server_url="http://localhost:3000")

# Connect to server
async with client:
    # List available tools
    tools = await client.list_tools()
    for tool in tools:
        print(f"{tool['name']}: {tool['description']}")

    # Call a tool
    result = await client.call_tool(
        "search",
        query="paracle documentation",
    )
```

### Tool Registry

The `MCPToolRegistry` maintains a catalog of discovered tools:

```python
from paracle_mcp.client import MCPClient
from paracle_mcp.registry import MCPToolRegistry

# Create registry
registry = MCPToolRegistry()

# Discover tools from multiple servers
async with MCPClient("http://server1:3000") as client1:
    count1 = await registry.discover_from_server("server1", client1)
    print(f"Discovered {count1} tools from server1")

async with MCPClient("http://server2:3000") as client2:
    count2 = await registry.discover_from_server("server2", client2)
    print(f"Discovered {count2} tools from server2")

# List all discovered tools
all_tools = registry.list_tools()
print(f"Total tools: {len(all_tools)}")

# Get specific tool
tool = registry.get_tool("server1.search")
print(tool['description'])

# Call tool through registry
result = await registry.call_tool(
    "server1.search",
    query="example",
)
```

### Configuring External Servers

Define external MCP servers in `.parac/tools/mcp/`:

```yaml
# .parac/tools/mcp/external.yaml
external_servers:
  - id: github
    name: GitHub Tools
    description: GitHub API tools via MCP
    command: npx
    args: ["@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
    tools_prefix: github
    enabled: true

  - id: filesystem
    name: Filesystem Tools
    description: Extended filesystem tools
    command: npx
    args: ["@modelcontextprotocol/server-filesystem", "/app/data"]
    tools_prefix: fs
    enabled: true

  - id: memory
    name: Memory Tools
    description: Persistent memory via MCP
    command: npx
    args: ["@modelcontextprotocol/server-memory"]
    enabled: true
```

## Custom Tools

### Creating Custom MCP Tools

Create Python tools in `.parac/tools/custom/`:

```python
# .parac/tools/custom/my_tool.py

"""My custom MCP tool."""

# Tool metadata (required)
TOOL_NAME = "my_custom_tool"
TOOL_DESCRIPTION = "Performs custom operation"
TOOL_PARAMETERS = {
    "type": "object",
    "properties": {
        "input": {
            "type": "string",
            "description": "Input data",
        },
        "options": {
            "type": "object",
            "description": "Optional settings",
        },
    },
    "required": ["input"],
}


async def execute(input: str, options: dict = None) -> dict:
    """Execute the custom tool.

    Args:
        input: Input data
        options: Optional settings

    Returns:
        Result dictionary
    """
    # Your tool logic here
    result = process_input(input, options or {})

    return {
        "success": True,
        "result": result,
    }
```

### Registering Custom Tools

Register in `.parac/tools/registry.yaml`:

```yaml
# .parac/tools/registry.yaml
custom:
  - name: my_custom_tool
    description: Performs custom operation
    file: custom/my_tool.py
    parameters:
      type: object
      properties:
        input:
          type: string
        options:
          type: object
      required:
        - input

  - name: another_tool
    description: Another custom tool
    file: custom/another.py
```

## Protocol Implementation

### Request/Response Format

MCP uses JSON-RPC 2.0:

```json
// Request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {
      "query": "example"
    }
  }
}

// Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Search results..."
      }
    ]
  }
}
```

### Tool Annotations

Tools can include annotations for client hints:

```python
TOOL_ANNOTATIONS = {
    "readOnlyHint": True,      # Tool only reads data
    "destructiveHint": False,  # Tool doesn't modify data
    "idempotentHint": True,    # Repeated calls are safe
    "openWorldHint": False,    # Tool operates in closed system
}
```

### Error Handling

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "details": "Missing required parameter 'query'"
    }
  }
}
```

## Transports

### stdio Transport

Default transport for IDE integration:

```python
from paracle_mcp.transports.stdio import StdioTransport

transport = StdioTransport()
await transport.start()
```

Configuration:
- Input: stdin
- Output: stdout
- Errors: stderr (for debugging)

### HTTP Transport

REST-based transport:

```python
from paracle_mcp.transports.http import HTTPTransport

transport = HTTPTransport(host="0.0.0.0", port=3000)
await transport.start()
```

Endpoints:
- `POST /mcp/initialize` - Initialize session
- `POST /mcp/tools/list` - List tools
- `POST /mcp/tools/call` - Call tool
- `POST /mcp/shutdown` - End session

### WebSocket Transport

Bidirectional communication:

```python
from paracle_mcp.transports.websocket import WebSocketTransport

transport = WebSocketTransport(host="0.0.0.0", port=3000)
await transport.start()
```

Connection: `ws://localhost:3000/mcp`

## CLI Commands

### Server Commands

```bash
# Start MCP server
paracle mcp serve [OPTIONS]

Options:
  --transport [stdio|http|websocket]  Transport type (default: stdio)
  --host TEXT                         Host for HTTP/WS (default: localhost)
  --port INTEGER                      Port for HTTP/WS (default: 3000)
  --verbose                           Enable verbose logging
```

### Client Commands

```bash
# List tools from MCP server
paracle mcp list-tools --server http://localhost:3000

# Call a tool
paracle mcp call <tool_name> --server <url> [ARGS...]

# Test connection
paracle mcp test --server http://localhost:3000
```

### Configuration Commands

```bash
# Initialize MCP configuration
paracle mcp init

# Add external server
paracle mcp add-server --name github --command "npx @modelcontextprotocol/server-github"

# Remove external server
paracle mcp remove-server github

# List configured servers
paracle mcp servers
```

## Security Considerations

### Authentication

For production deployments:

```yaml
# .parac/tools/mcp/mcp.yaml
server:
  security:
    require_auth: true
    auth_method: bearer
    token_env: MCP_AUTH_TOKEN
```

### Tool Permissions

Control which tools are exposed:

```yaml
server:
  expose_tools:
    - context.*      # All context tools
    - workflow.list  # Only workflow listing
    - memory.*       # All memory tools
    # coder.* - Not exposed

  block_tools:
    - "*:delete"     # No delete operations
    - shell.*        # No shell tools via MCP
```

### Rate Limiting

```yaml
server:
  security:
    rate_limit:
      requests_per_minute: 100
      concurrent_connections: 10
```

## Best Practices

### 1. Use stdio for IDE Integration

```bash
# Best for Claude Desktop, VS Code, Cursor
paracle mcp serve  # Uses stdio by default
```

### 2. Secure HTTP Endpoints

```yaml
server:
  security:
    require_auth: true
    allowed_origins:
      - "https://your-app.com"
```

### 3. Prefix External Tools

```yaml
external_servers:
  - id: github
    tools_prefix: github  # Tools become github.search, github.create_issue
```

### 4. Handle Errors Gracefully

```python
try:
    result = await client.call_tool("search", query=query)
except MCPError as e:
    logger.error(f"MCP error: {e.code} - {e.message}")
    return fallback_search(query)
```

### 5. Monitor Tool Usage

```python
from paracle_core.logging import get_logger

logger = get_logger("mcp")

@mcp_server.before_tool_call
async def log_tool_call(tool_name, args):
    logger.info(f"MCP tool call: {tool_name}", extra={"args": args})
```

## Troubleshooting

### Connection Issues

```bash
# Test MCP server
paracle mcp test --server http://localhost:3000

# Check server logs
paracle mcp serve --verbose

# Verify transport
curl -X POST http://localhost:3000/mcp/initialize
```

### Tool Not Found

```bash
# List available tools
paracle mcp list-tools

# Check tool registration
cat .parac/tools/registry.yaml
```

### Permission Denied

```bash
# Check exposed tools
grep expose_tools .parac/tools/mcp/mcp.yaml

# Verify authentication
export MCP_AUTH_TOKEN=your-token
paracle mcp call tool_name
```

## Related Documentation

- [Built-in Tools](builtin-tools.md) - Native Paracle tools
- [Skills System](skills.md) - Skills with MCP export
- [Architecture Overview](architecture.md) - System design
- [Security Audit Report](security-audit-report.md) - Security assessment

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP GitHub](https://github.com/modelcontextprotocol)
- [Claude Desktop MCP](https://claude.ai/docs/mcp)
