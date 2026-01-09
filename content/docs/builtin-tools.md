# Built-in Tools

Paracle provides 9 secure built-in tools for filesystem, HTTP, and shell operations.

## Overview

Built-in tools are native capabilities that agents can use for common operations. All tools are designed with security-first principles:

- **Mandatory sandboxing** - No unrestricted filesystem access
- **Explicit allowlists** - Shell commands require whitelisting
- **Path traversal protection** - Prevents directory escape attacks
- **Symlink attack prevention** - Detects malicious symlinks
- **Audit logging** - All operations are logged

```
┌─────────────────────────────────────────────────────────────────┐
│                    Built-in Tools                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Filesystem    │  │      HTTP       │  │     Shell       │ │
│  │                 │  │                 │  │                 │ │
│  │  read_file      │  │  http_get       │  │  run_command    │ │
│  │  write_file     │  │  http_post      │  │                 │ │
│  │  list_directory │  │  http_put       │  │                 │ │
│  │  delete_file    │  │  http_delete    │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Tool Registry

Tools are managed through the `BuiltinToolRegistry`:

```python
from paracle_tools.builtin.registry import BuiltinToolRegistry

# Initialize with security configuration (REQUIRED)
registry = BuiltinToolRegistry(
    filesystem_paths=["/app/data", "/app/config"],
    allowed_commands=["git", "ls", "cat", "grep"],
    http_timeout=30.0,
    command_timeout=30.0,
)

# Execute a tool
result = await registry.execute_tool(
    "read_file",
    path="/app/data/config.json",
)

# List available tools
tools = registry.list_tools()
```

### Security Requirements

The registry **requires** explicit configuration:

```python
# This will FAIL - no unrestricted access allowed
registry = BuiltinToolRegistry()  # ValueError!

# This is correct - explicit paths and commands
registry = BuiltinToolRegistry(
    filesystem_paths=["/app/data"],
    allowed_commands=["git"],
)
```

## Filesystem Tools

### read_file

Read contents of a file within allowed paths.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path to file to read |
| `encoding` | string | No | File encoding (default: utf-8) |

**Permissions:** `filesystem:read`

**Security:**
- Path must be within `allowed_paths`
- Maximum file size: 10 MB
- Symlink attacks are prevented
- Path traversal blocked

```python
result = await registry.execute_tool(
    "read_file",
    path="/app/data/config.json",
)

# Result
{
    "content": "{ ... }",
    "path": "/app/data/config.json",
    "size": 1024,
    "encoding": "utf-8"
}
```

**Errors:**

```python
# Path not allowed
PermissionError: "Access denied: path is not in allowed directories"

# File too large
ToolError: "File exceeds maximum size of 10485760 bytes"

# File not found
ToolError: "File not found: /path/to/file"
```

### write_file

Write content to a file within allowed paths.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path to file to write |
| `content` | string | Yes | Content to write |
| `encoding` | string | No | File encoding (default: utf-8) |
| `create_dirs` | boolean | No | Create parent directories (default: false) |

**Permissions:** `filesystem:write`

**Security:**
- Path must be within `allowed_paths`
- Parent directories validated
- Atomic writes where possible

```python
result = await registry.execute_tool(
    "write_file",
    path="/app/data/output.json",
    content='{"status": "success"}',
    create_dirs=True,
)

# Result
{
    "path": "/app/data/output.json",
    "size": 21,
    "created": true
}
```

### list_directory

List contents of a directory.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Directory path |
| `pattern` | string | No | Glob pattern filter |
| `recursive` | boolean | No | List recursively (default: false) |

**Permissions:** `filesystem:read`

**Security:**
- Maximum 10,000 entries returned
- Path must be within `allowed_paths`

```python
result = await registry.execute_tool(
    "list_directory",
    path="/app/data",
    pattern="*.json",
    recursive=True,
)

# Result
{
    "path": "/app/data",
    "entries": [
        {"name": "config.json", "type": "file", "size": 1024},
        {"name": "data.json", "type": "file", "size": 2048},
    ],
    "total": 2
}
```

### delete_file

Delete a file within allowed paths.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path to file to delete |

**Permissions:** `filesystem:delete`

**Security:**
- Path must be within `allowed_paths`
- Cannot delete directories (use `list_directory` + loop)
- Operation is logged

```python
result = await registry.execute_tool(
    "delete_file",
    path="/app/data/temp.json",
)

# Result
{
    "path": "/app/data/temp.json",
    "deleted": true
}
```

## HTTP Tools

### http_get

Make an HTTP GET request.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | Yes | URL to request |
| `headers` | object | No | HTTP headers |
| `params` | object | No | Query parameters |

**Permissions:** `http:request`

```python
result = await registry.execute_tool(
    "http_get",
    url="https://api.example.com/data",
    headers={"Authorization": "Bearer token"},
    params={"page": "1"},
)

# Result
{
    "status_code": 200,
    "headers": {"content-type": "application/json"},
    "body": '{"data": [...]}',
    "json": {"data": [...]},
    "url": "https://api.example.com/data?page=1"
}
```

**Errors:**

```python
# Timeout
ToolError: "Request timed out after 30.0s"

# Connection error
ToolError: "Connection failed: ..."
```

### http_post

Make an HTTP POST request.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | Yes | URL to request |
| `headers` | object | No | HTTP headers |
| `data` | string | No | Request body (raw) |
| `json` | object | No | JSON request body |

**Permissions:** `http:request`

```python
result = await registry.execute_tool(
    "http_post",
    url="https://api.example.com/items",
    json={"name": "New Item", "value": 42},
)

# Result
{
    "status_code": 201,
    "headers": {...},
    "body": '{"id": 123, "name": "New Item"}',
    "json": {"id": 123, "name": "New Item"}
}
```

### http_put

Make an HTTP PUT request.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | Yes | URL to request |
| `headers` | object | No | HTTP headers |
| `data` | string | No | Request body (raw) |
| `json` | object | No | JSON request body |

**Permissions:** `http:request`

```python
result = await registry.execute_tool(
    "http_put",
    url="https://api.example.com/items/123",
    json={"name": "Updated Item"},
)
```

### http_delete

Make an HTTP DELETE request.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | Yes | URL to request |
| `headers` | object | No | HTTP headers |

**Permissions:** `http:request`

```python
result = await registry.execute_tool(
    "http_delete",
    url="https://api.example.com/items/123",
)

# Result
{
    "status_code": 204,
    "headers": {...},
    "body": ""
}
```

## Shell Tool

### run_command

Execute a shell command from the allowed list.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `command` | string | Yes | Command to execute |

**Permissions:** `shell:execute`

**Security Features:**
- **Strict allowlist** - Only whitelisted commands can run
- **No shell=True** - Prevents command injection attacks
- **Timeout enforcement** - Maximum 5 minutes
- **Argument validation** - Commands parsed with shlex
- **Audit logging** - All executions logged

```python
# Initialize with allowed commands
registry = BuiltinToolRegistry(
    filesystem_paths=["/app"],
    allowed_commands=["git", "ls", "cat", "grep", "python"],
)

# Execute allowed command
result = await registry.execute_tool(
    "run_command",
    command="git status",
)

# Result
{
    "exit_code": 0,
    "stdout": "On branch main\nnothing to commit...",
    "stderr": "",
    "command": "git status",
    "timed_out": false
}
```

**What's Blocked:**

```python
# Command not in allowlist
result = await registry.execute_tool("run_command", command="rm -rf /")
# PermissionError: "Command 'rm' is not in allowed commands list"

# Command chaining (;) - blocked by design
result = await registry.execute_tool("run_command", command="ls; rm -rf /")
# Only "ls" is executed, "rm -rf /" is treated as argument

# Pipe injection (|) - blocked by design
result = await registry.execute_tool("run_command", command="cat file | rm -rf")
# Only "cat" is executed, rest is treated as arguments
```

**Why shell=True is Removed:**

The `shell=True` option allowed:
- Command chaining: `git status; rm -rf /`
- Command substitution: `git $(rm -rf /)`
- Pipe injection: `git status | malicious_script`
- Blocklist bypass: `/bin/rm`, `busybox rm`

All of these are now **impossible** because:
1. Commands are parsed with `shlex.split()`
2. Executed directly via `asyncio.create_subprocess_exec()`
3. No shell interpretation occurs

## Tool Permissions

Each tool requires specific permissions:

| Tool | Permissions |
|------|-------------|
| `read_file` | `filesystem:read` |
| `write_file` | `filesystem:write` |
| `list_directory` | `filesystem:read` |
| `delete_file` | `filesystem:delete` |
| `http_get` | `http:request` |
| `http_post` | `http:request` |
| `http_put` | `http:request` |
| `http_delete` | `http:request` |
| `run_command` | `shell:execute` |

### Checking Permissions

```python
# Get required permissions for a tool
perms = registry.get_tool_permissions("write_file")
# ["filesystem:write"]

# Get tools by category
categories = registry.get_tools_by_category()
# {
#     "filesystem": ["read_file", "write_file", "list_directory", "delete_file"],
#     "http": ["http_get", "http_post", "http_put", "http_delete"],
#     "shell": ["run_command"]
# }
```

## Configuration

### Filesystem Paths

Configure allowed paths for filesystem operations:

```python
# Initial configuration
registry = BuiltinToolRegistry(
    filesystem_paths=["/app/data", "/app/config"],
    allowed_commands=["git"],
)

# Reconfigure at runtime
registry.configure_filesystem_paths([
    "/app/data",
    "/app/config",
    "/app/uploads",  # Add new path
])
```

### Allowed Commands

Configure allowed shell commands:

```python
# Initial configuration
registry = BuiltinToolRegistry(
    filesystem_paths=["/app"],
    allowed_commands=["git", "ls", "cat"],
)

# Reconfigure at runtime
registry.configure_allowed_commands([
    "git",
    "ls",
    "cat",
    "python",  # Add new command
    "pytest",
])
```

### Timeouts

Configure operation timeouts:

```python
registry = BuiltinToolRegistry(
    filesystem_paths=["/app"],
    allowed_commands=["git"],
    http_timeout=60.0,      # HTTP request timeout
    command_timeout=120.0,  # Shell command timeout (max 300s)
)
```

## Tool Results

All tools return a `ToolResult` object:

```python
@dataclass
class ToolResult:
    success: bool           # Whether operation succeeded
    data: dict[str, Any]   # Result data
    error: str | None      # Error message if failed
    metadata: dict         # Additional metadata

# Success result
ToolResult(
    success=True,
    data={"content": "file contents..."},
    error=None,
    metadata={"duration_ms": 12}
)

# Error result
ToolResult(
    success=False,
    data={},
    error="File not found: /path/to/file",
    metadata={"error_code": "FILE_NOT_FOUND"}
)
```

## Error Handling

### ToolError

General tool execution error:

```python
from paracle_tools.builtin.base import ToolError

try:
    result = await registry.execute_tool("read_file", path="/missing")
except ToolError as e:
    print(f"Tool error: {e.message}")
    print(f"Context: {e.context}")
```

### PermissionError

Security-related access denial:

```python
from paracle_tools.builtin.base import PermissionError

try:
    result = await registry.execute_tool("read_file", path="/etc/passwd")
except PermissionError as e:
    print(f"Access denied: {e.message}")
    print(f"Tool: {e.tool_name}")
```

## Agent-Specific Tools

Beyond built-in tools, Paracle provides specialized tools for each agent type:

| Module | Purpose |
|--------|---------|
| `paracle_tools.coder_tools` | Code generation, refactoring |
| `paracle_tools.reviewer_tools` | Code review, analysis |
| `paracle_tools.tester_tools` | Test generation, coverage |
| `paracle_tools.documenter_tools` | Documentation generation |
| `paracle_tools.architect_tools` | Architecture design |
| `paracle_tools.pm_tools` | Project management |
| `paracle_tools.git_tools` | Git operations |
| `paracle_tools.release_tools` | Release management |
| `paracle_tools.terminal_tools` | Terminal operations |

## Best Practices

### 1. Principle of Least Privilege

Only allow what's necessary:

```python
# Good - minimal permissions
registry = BuiltinToolRegistry(
    filesystem_paths=["/app/data"],  # Only data directory
    allowed_commands=["git", "ls"],  # Only git and ls
)

# Avoid - overly permissive
registry = BuiltinToolRegistry(
    filesystem_paths=["/"],           # Entire filesystem
    allowed_commands=["bash", "sh"],  # Full shell access
)
```

### 2. Use Absolute Paths

Always use absolute paths for clarity:

```python
# Good
result = await registry.execute_tool(
    "read_file",
    path="/app/data/config.json",
)

# Avoid - relative paths
result = await registry.execute_tool(
    "read_file",
    path="../../../etc/passwd",  # Path traversal attempt
)
```

### 3. Handle Errors Gracefully

```python
result = await registry.execute_tool("read_file", path=file_path)

if not result.success:
    logger.error(f"Failed to read file: {result.error}")
    return handle_error(result.error)

content = result.data["content"]
```

### 4. Log Operations

All tool operations are logged automatically, but you can add context:

```python
from paracle_core.logging import get_logger

logger = get_logger(__name__)

logger.info(f"Reading config file: {file_path}")
result = await registry.execute_tool("read_file", path=file_path)
logger.info(f"Config loaded: {result.success}")
```

## Related Documentation

- [Skills System](skills.md) - Skills with tools
- [MCP Integration](mcp-integration.md) - MCP tool protocol
- [Security Audit Report](security-audit-report.md) - Security assessment
- [Architecture Overview](architecture.md) - System design
