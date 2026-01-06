# MCP Integration Guide

Guide to using Model Context Protocol (MCP) with Paracle.

## Overview

Paracle supports the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) for integrating external tools and resources. MCP provides a standardized way for AI applications to interact with tools, data sources, and services.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PARACLE FRAMEWORK                        │
│                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│   │   Agent     │───▶│ Tool Router │───▶│ MCP Client  │    │
│   │             │    │             │    │             │    │
│   └─────────────┘    └─────────────┘    └──────┬──────┘    │
│                                                │            │
└────────────────────────────────────────────────│────────────┘
                                                 │
                         HTTP/JSON-RPC           │
                                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                       MCP SERVER                             │
│                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│   │   Tools     │    │  Resources  │    │   Prompts   │    │
│   │             │    │             │    │             │    │
│   └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start Paracle MCP Server

Paracle includes a built-in MCP server that exposes all agent tools:

```bash
# For IDE integration (stdio transport)
paracle mcp serve --stdio

# For debugging (HTTP transport)
paracle mcp serve --port 3000
```

### 2. List Available Tools

```bash
paracle mcp list
paracle mcp list --category agent
paracle mcp list --json
```

### 3. Configure Your IDE

```bash
# Show configuration for your IDE
paracle mcp config --ide vscode
paracle mcp config --ide cursor
paracle mcp config --ide claude
```

---

## Using Paracle as MCP Client

### 1. Install Dependencies

```bash
pip install httpx
# MCP client is included in paracle_mcp
```

### 2. Connect to External MCP Server

```python
from paracle_mcp import MCPClient

# Create client
client = MCPClient(server_url="http://localhost:3000")

# Connect
await client.connect()

# List available tools
tools = await client.list_tools()
for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")

# Disconnect when done
await client.disconnect()
```

### 3. Use as Context Manager

```python
async with MCPClient(server_url="http://localhost:3000") as client:
    tools = await client.list_tools()
    result = await client.call_tool("search", {"query": "python"})
```

---

## MCPClient API

### Initialization

```python
from paracle_mcp import MCPClient

client = MCPClient(
    server_url="http://localhost:3000",  # MCP server URL
    timeout=30.0,                         # Request timeout
)
```

### Connection Management

```python
# Connect to server
connected = await client.connect()  # Returns True on success

# Check connection status
if client.is_connected:
    print("Connected!")

# Disconnect
await client.disconnect()
```

### Tool Operations

#### List Tools

```python
tools = await client.list_tools()

# Returns list of tool specifications:
# [
#     {
#         "name": "search",
#         "description": "Search the web",
#         "inputSchema": {
#             "type": "object",
#             "properties": {
#                 "query": {"type": "string"},
#                 "limit": {"type": "integer", "default": 10}
#             },
#             "required": ["query"]
#         }
#     }
# ]
```

#### Get Tool Details

```python
tool = await client.get_tool("search")

# Returns detailed tool specification:
# {
#     "name": "search",
#     "description": "Search the web for information",
#     "inputSchema": {...},
#     "metadata": {...}
# }
```

#### Call Tool

```python
result = await client.call_tool(
    tool_name="search",
    arguments={
        "query": "python tutorial",
        "limit": 5
    }
)

# Result is tool-specific, e.g.:
# {
#     "results": [
#         {"title": "Python Tutorial", "url": "..."},
#         ...
#     ]
# }
```

### Resource Operations

Resources provide read-only context to AI models.

#### List Resources

```python
resources = await client.list_resources()

# Returns list of available resources:
# [
#     {
#         "uri": "file:///docs/README.md",
#         "name": "README",
#         "mimeType": "text/markdown"
#     }
# ]
```

#### Read Resource

```python
content = await client.read_resource("file:///docs/README.md")
print(content)  # Markdown content of the file
```

---

## MCP Registry

The `MCPRegistry` manages multiple MCP servers:

```python
from paracle_mcp import MCPRegistry

# Create registry
registry = MCPRegistry()

# Register MCP servers
await registry.register(
    name="docs-server",
    server_url="http://localhost:3001",
    tools_prefix="docs_"  # Prefix for tool names
)

await registry.register(
    name="search-server",
    server_url="http://localhost:3002",
    tools_prefix="search_"
)

# List all tools from all servers
all_tools = await registry.list_all_tools()

# Call tool (automatically routes to correct server)
result = await registry.call_tool("docs_read_file", {"path": "README.md"})

# Disconnect all
await registry.disconnect_all()
```

---

## Integration with Agents

### Define Agent with MCP Tools

```python
from paracle_domain.models import AgentSpec

agent = AgentSpec(
    name="research-assistant",
    provider="openai",
    model="gpt-4",
    system_prompt="You are a research assistant with access to search tools.",
    tools=[
        # Built-in tools
        "read_file",
        "write_file",
        # MCP tools (prefixed with server name)
        "mcp:search:web_search",
        "mcp:docs:read_document",
    ],
    mcp_servers=[
        {
            "name": "search",
            "url": "http://localhost:3001"
        },
        {
            "name": "docs",
            "url": "http://localhost:3002"
        }
    ]
)
```

### Tool Resolution

When an agent needs to call a tool:

1. **Built-in tools** - Resolved from `BuiltinToolRegistry`
2. **MCP tools** - Resolved from configured MCP servers
3. **Custom tools** - Resolved from custom tool registry

```python
from paracle_tools import ToolRouter

router = ToolRouter()

# Register built-in tools
router.register_builtin()

# Register MCP server
await router.register_mcp("search", "http://localhost:3001")

# Call tool (router handles dispatch)
result = await router.call("web_search", {"query": "python"})
```

---

## MCP Server Configuration

### In .parac/config.yaml

```yaml
mcp:
  servers:
    - name: search
      url: http://localhost:3001
      enabled: true
      tools_prefix: search_

    - name: docs
      url: http://localhost:3002
      enabled: true
      tools_prefix: docs_

    - name: code
      url: http://localhost:3003
      enabled: false  # Disabled

  defaults:
    timeout: 30
    retry_count: 3
```

### Environment Variables

```bash
# MCP server URL
MCP_SERVER_URL=http://localhost:3000

# Multiple servers
MCP_SEARCH_URL=http://localhost:3001
MCP_DOCS_URL=http://localhost:3002
```

---

## Running MCP Servers

### Example: File Server

```bash
# Using official MCP file server
npx @modelcontextprotocol/server-filesystem /path/to/files
```

### Example: Custom Server

```python
# Python MCP server example
from mcp import Server, Tool

server = Server(port=3000)

@server.tool("my_tool")
async def my_tool(query: str) -> str:
    """My custom tool."""
    return f"Result for: {query}"

server.run()
```

### Example: Docker

```dockerfile
# docker-compose.yml
version: "3"
services:
  mcp-server:
    image: mcp/file-server
    ports:
      - "3000:3000"
    volumes:
      - ./docs:/docs
```

---

## Security Considerations

### 1. Network Security

```python
# Use HTTPS in production
client = MCPClient(
    server_url="https://mcp.example.com",
    verify_ssl=True  # Verify TLS certificates
)
```

### 2. Authentication

```python
# API key authentication
client = MCPClient(
    server_url="https://mcp.example.com",
    headers={
        "Authorization": "Bearer your-api-key"
    }
)
```

### 3. Tool Restrictions

```python
# Restrict which MCP tools agents can use
agent = AgentSpec(
    name="restricted-agent",
    tools=[
        "mcp:search:web_search",  # Allowed
        # "mcp:code:execute" - Not allowed
    ],
    tool_permissions={
        "mcp:search:*": "allow",
        "mcp:code:*": "deny"
    }
)
```

### 4. Rate Limiting

```python
# Configure rate limits for MCP calls
client = MCPClient(
    server_url="http://localhost:3000",
    rate_limit=100,  # Max 100 calls per minute
)
```

---

## Error Handling

```python
from paracle_mcp import MCPClient, MCPError

try:
    async with MCPClient(server_url="http://localhost:3000") as client:
        result = await client.call_tool("search", {"query": "test"})

except ConnectionError as e:
    print(f"Failed to connect: {e}")

except RuntimeError as e:
    print(f"Tool execution failed: {e}")

except MCPError as e:
    print(f"MCP protocol error: {e}")
```

---

## Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("paracle_mcp").setLevel(logging.DEBUG)
```

### Inspect Tool Calls

```python
# Log all tool calls
client = MCPClient(
    server_url="http://localhost:3000",
    debug=True  # Enable request/response logging
)
```

---

## Best Practices

### 1. Use Connection Pooling

```python
# Reuse client for multiple operations
async with MCPClient(server_url="http://localhost:3000") as client:
    # All operations share the same connection
    await client.list_tools()
    await client.call_tool("tool1", {...})
    await client.call_tool("tool2", {...})
```

### 2. Handle Timeouts

```python
client = MCPClient(
    server_url="http://localhost:3000",
    timeout=60.0  # Longer timeout for slow tools
)
```

### 3. Validate Tool Inputs

```python
tool_spec = await client.get_tool("search")
schema = tool_spec["inputSchema"]

# Validate arguments against schema before calling
from jsonschema import validate
validate(arguments, schema)

result = await client.call_tool("search", arguments)
```

### 4. Cache Tool Specifications

```python
# Cache tool list to avoid repeated calls
tools = await client.list_tools()
tool_cache = {t["name"]: t for t in tools}
```

---

## IDE Configuration Examples

### VS Code

Add to `.vscode/mcp.json` or settings.json:

```json
{
  "mcp": {
    "servers": {
      "paracle": {
        "command": "paracle",
        "args": ["mcp", "serve", "--stdio"]
      }
    }
  }
}
```

### Cursor

In Settings > MCP, or `mcp_config.json`:

```json
{
  "mcpServers": {
    "paracle": {
      "command": "paracle",
      "args": ["mcp", "serve", "--stdio"]
    }
  }
}
```

### Claude Code

Add to `~/.claude/mcp_servers.json`:

```json
{
  "mcpServers": {
    "paracle": {
      "command": "paracle",
      "args": ["mcp", "serve", "--stdio"]
    }
  }
}
```

### Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "paracle": {
      "command": "paracle",
      "args": ["mcp", "serve", "--stdio"],
      "env": {}
    }
  }
}
```

---

## Related Documentation

- [CLI Reference](cli-reference.md) - Full CLI command reference
- [Built-in Tools](builtin-tools.md) - Paracle's native tools
- [Agents](getting-started.md) - Agent configuration
- [MCP Specification](https://modelcontextprotocol.io/) - Official MCP docs

---

**Last Updated:** 2026-01-06
**Version:** 0.0.1
