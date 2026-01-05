# Built-in Tools Documentation

Paracle provides 9 native built-in tools that agents can use without requiring external MCP servers or dependencies.

## Quick Start

```python
from paracle_tools import read_file, write_file, http_get, run_command

# Use tools directly
result = await read_file.execute(path="/path/to/file.txt")
if result.success:
    content = result.output["content"]
    print(f"File has {result.output['lines']} lines")
else:
    print(f"Error: {result.error}")
```

## Tool Categories

### Filesystem Tools

#### `read_file`
Read the contents of a file.

**Parameters:**
- `path` (string, required): Path to the file to read
- `encoding` (string, optional): File encoding (default: "utf-8")

**Returns:**
```python
{
    "content": str,      # File contents
    "path": str,         # Absolute path
    "size": int,         # File size in bytes
    "lines": int         # Number of lines
}
```

**Example:**
```python
from paracle_tools import read_file

result = await read_file.execute(path="README.md")
if result.success:
    print(result.output["content"])
```

#### `write_file`
Write content to a file.

**Parameters:**
- `path` (string, required): Path to the file to write
- `content` (string, required): Content to write
- `encoding` (string, optional): File encoding (default: "utf-8")
- `create_dirs` (boolean, optional): Create parent directories (default: True)

**Returns:**
```python
{
    "path": str,    # Absolute path
    "size": int,    # File size in bytes
    "lines": int    # Number of lines written
}
```

**Example:**
```python
from paracle_tools import write_file

result = await write_file.execute(
    path="output.txt",
    content="Hello, World!"
)
```

#### `list_directory`
List contents of a directory.

**Parameters:**
- `path` (string, required): Path to the directory
- `recursive` (boolean, optional): List recursively (default: False)

**Returns:**
```python
{
    "path": str,          # Directory path
    "entries": [          # List of entries
        {
            "name": str,  # Entry name
            "type": str,  # "file" or "directory"
            "size": int   # Size in bytes (files only)
        }
    ],
    "count": int         # Total number of entries
}
```

**Example:**
```python
from paracle_tools import list_directory

result = await list_directory.execute(path="./src")
for entry in result.output["entries"]:
    print(f"{entry['type']}: {entry['name']}")
```

#### `delete_file`
Delete a file.

**Parameters:**
- `path` (string, required): Path to the file to delete

**Returns:**
```python
{
    "path": str,      # Deleted file path
    "deleted": bool   # True if successful
}
```

**Example:**
```python
from paracle_tools import delete_file

result = await delete_file.execute(path="temp.txt")
```

### HTTP Tools

#### `http_get`
Make an HTTP GET request.

**Parameters:**
- `url` (string, required): URL to request
- `headers` (object, optional): HTTP headers
- `params` (object, optional): Query parameters

**Returns:**
```python
{
    "status_code": int,      # HTTP status code
    "headers": dict,         # Response headers
    "body": str,             # Response body
    "json": dict | None,     # Parsed JSON (if content-type is JSON)
    "url": str               # Final URL (after redirects)
}
```

**Example:**
```python
from paracle_tools import http_get

result = await http_get.execute(
    url="https://api.github.com/repos/anthropics/paracle",
    headers={"Accept": "application/json"}
)

if result.success and result.output["json"]:
    repo = result.output["json"]
    print(f"Stars: {repo['stargazers_count']}")
```

#### `http_post`
Make an HTTP POST request.

**Parameters:**
- `url` (string, required): URL to request
- `headers` (object, optional): HTTP headers
- `json_data` (object, optional): JSON data for request body
- `form_data` (object, optional): Form data

**Returns:** Same as `http_get`

**Example:**
```python
from paracle_tools import http_post

result = await http_post.execute(
    url="https://api.example.com/items",
    json_data={"name": "New Item", "price": 99.99}
)
```

#### `http_put`
Make an HTTP PUT request.

**Parameters:**
- `url` (string, required): URL to request
- `headers` (object, optional): HTTP headers
- `json_data` (object, optional): JSON data for request body

**Returns:** Same as `http_get`

#### `http_delete`
Make an HTTP DELETE request.

**Parameters:**
- `url` (string, required): URL to request
- `headers` (object, optional): HTTP headers

**Returns:** Same as `http_get`

### Shell Tools

#### `run_command`
Execute a shell command safely.

**Parameters:**
- `command` (string, required): Shell command to execute
- `shell` (boolean, optional): Execute through shell (default: False for safety)

**Returns:**
```python
{
    "stdout": str,         # Standard output
    "stderr": str,         # Standard error
    "return_code": int,    # Exit code
    "success": bool,       # True if return_code == 0
    "command": str         # Command that was executed
}
```

**Allowed Commands (default whitelist):**
- Version control: `git`
- File viewing: `cat`, `head`, `tail`, `less`, `more`
- Directory listing: `ls`, `dir`, `tree`
- Search: `grep`, `find`, `which`, `whereis`
- System info: `pwd`, `whoami`, `hostname`, `uname`, `date`
- Python/packages: `python`, `python3`, `pip`, `uv`, `poetry`, `npm`, `node`
- Testing: `pytest`, `make`
- Text processing: `echo`, `printf`, `sed`, `awk`, `sort`, `uniq`, `cut`

**Blocked Commands (always):**
`rm`, `rmdir`, `del`, `format`, `mkfs`, `dd`, `fdisk`, `sudo`, `su`, `chmod`, `chown`, `shutdown`, `reboot`

**Example:**
```python
from paracle_tools import run_command

# Safe command execution
result = await run_command.execute(command="git status")
if result.success and result.output["success"]:
    print(result.output["stdout"])
```

## Using the Tool Registry

The `BuiltinToolRegistry` provides centralized management:

```python
from paracle_tools import BuiltinToolRegistry

# Create registry with custom configuration
registry = BuiltinToolRegistry(
    filesystem_paths=["/allowed/path"],  # Restrict filesystem access
    allowed_commands=["git", "ls"],      # Whitelist specific commands
    http_timeout=10.0,                   # HTTP request timeout
    command_timeout=5.0                  # Shell command timeout
)

# List all tools
tools = registry.list_tool_names()
# ['read_file', 'write_file', 'list_directory', 'delete_file',
#  'http_get', 'http_post', 'http_put', 'http_delete', 'run_command']

# Get tools by category
categories = registry.get_tools_by_category()
# {'filesystem': [...], 'http': [...], 'shell': [...]}

# Execute a tool by name
result = await registry.execute_tool(
    "read_file",
    path="config.yaml"
)

# Check tool permissions
perms = registry.get_tool_permissions("read_file")
# ['filesystem:read']
```

## Permission System

### Filesystem Path Restrictions

Restrict filesystem tools to specific directories:

```python
from paracle_tools.builtin.filesystem import ReadFileTool

# Only allow reading from specific paths
tool = ReadFileTool(allowed_paths=["/home/user/data", "/var/log"])

# This will succeed
result = await tool.execute(path="/home/user/data/file.txt")

# This will fail with PermissionError
result = await tool.execute(path="/etc/passwd")
# result.success == False
# result.error == "Access denied: /etc/passwd is not in allowed paths"
```

### Shell Command Whitelist

Control which commands can be executed:

```python
from paracle_tools.builtin.shell import RunCommandTool

# Only allow specific commands
tool = RunCommandTool(allowed_commands=["git", "ls", "echo"])

# This will succeed
result = await tool.execute(command="git status")

# This will fail with PermissionError
result = await tool.execute(command="python script.py")
# result.success == False
# result.error == "Command 'python' is not in allowed commands"
```

## Error Handling

All tools return a `ToolResult` object:

```python
class ToolResult:
    success: bool              # True if executed successfully
    output: Any               # Tool output (dict, str, etc.)
    error: str | None         # Error message if failed
    metadata: dict            # Additional metadata

# Always check success before using output
result = await read_file.execute(path="file.txt")
if result.success:
    content = result.output["content"]
    print(f"Read {result.output['size']} bytes")
else:
    print(f"Failed: {result.error}")
    # Additional error details in metadata
    if "path" in result.metadata:
        print(f"Path: {result.metadata['path']}")
```

## Timeouts

HTTP and shell tools support timeout configuration:

```python
from paracle_tools.builtin.http import HTTPGetTool
from paracle_tools.builtin.shell import RunCommandTool

# HTTP with 5-second timeout
http_tool = HTTPGetTool(timeout=5.0)
result = await http_tool.execute(url="https://slow-api.example.com")
# Will timeout after 5 seconds

# Shell with 10-second timeout
shell_tool = RunCommandTool(timeout=10.0)
result = await shell_tool.execute(command="long-running-process")
# Will timeout after 10 seconds
```

## Integration with Agents

Tools can be attached to agents via `AgentSpec`:

```python
from paracle_domain.models import AgentSpec, Agent

spec = AgentSpec(
    name="file-processor",
    provider="openai",
    model="gpt-4",
    tools=["read_file", "write_file", "list_directory"],
    system_prompt="You are a file processing assistant."
)

agent = Agent(spec=spec)
```

## Dependencies

- **Filesystem tools**: No dependencies (uses Python stdlib)
- **HTTP tools**: Requires `httpx` (`pip install httpx`)
- **Shell tools**: No dependencies (uses Python stdlib `asyncio`)

## Security Best Practices

1. **Always use path restrictions** in production:
   ```python
   registry = BuiltinToolRegistry(
       filesystem_paths=["/app/data", "/app/output"]
   )
   ```

2. **Use command whitelists**, not blocklists:
   ```python
   registry = BuiltinToolRegistry(
       allowed_commands=["git", "ls", "cat"]  # Explicit whitelist
   )
   ```

3. **Set reasonable timeouts**:
   ```python
   registry = BuiltinToolRegistry(
       http_timeout=30.0,
       command_timeout=60.0
   )
   ```

4. **Validate tool outputs** before using them in critical operations

5. **Monitor tool usage** in production environments

## Examples

See the [examples/](../examples/) directory for complete working examples:

- `examples/filesystem_tools.py` - File operations
- `examples/http_tools.py` - API interactions
- `examples/shell_tools.py` - Command execution
- `examples/agent_with_tools.py` - Agent using multiple tools
