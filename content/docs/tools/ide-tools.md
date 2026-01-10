# IDE Tools - MCP Integration

## Overview

Paracle provides MCP tools for interacting with VS Code-compatible IDEs through their native CLI commands. This enables agents to control the IDE programmatically.

## Supported IDEs

| IDE | Command | Priority | Features |
|-----|---------|----------|----------|
| **Cursor** | `cursor` | 1 (highest) | diff, extensions |
| **VS Code** | `code` | 2 | diff, merge, extensions |
| **Windsurf** | `windsurf` | 3 | diff, extensions |
| **VSCodium** | `codium` | 4 | diff, merge, extensions |

Detection priority favors AI-focused IDEs (Cursor first), then falls back to VS Code and alternatives.

---

## Available Tools (10)

### Information

#### `ide_info`
Get information about available IDEs.

```python
tool_call("ide_info", {})
# Result:
# {
#   "detected_ide": "cursor",
#   "detected_display_name": "Cursor",
#   "supported_ides": {
#     "vscode": {"available": true, "supports_diff": true, ...},
#     "cursor": {"available": true, "supports_diff": true, ...},
#     ...
#   }
# }
```

#### `ide_version`
Get IDE version information.

```python
tool_call("ide_version", {"ide": "vscode"})
# Result: Version info lines
```

---

### File Operations

#### `ide_open_file`
Open a file in the IDE, optionally at a specific line and column.

**Parameters:**
- `path` (required): File path to open
- `line` (optional): Line number to navigate to
- `column` (optional): Column number
- `reuse_window` (optional, default: true): Reuse existing window
- `ide` (optional): Specific IDE to use

```python
# Open file
tool_call("ide_open_file", {"path": "/project/src/main.py"})

# Open at specific line
tool_call("ide_open_file", {
    "path": "/project/src/main.py",
    "line": 42
})

# Open at specific line and column
tool_call("ide_open_file", {
    "path": "/project/src/main.py",
    "line": 42,
    "column": 10
})
```

#### `ide_open_folder`
Open a folder in the IDE.

**Parameters:**
- `path` (required): Folder path to open
- `new_window` (optional): Open in new window
- `add_to_workspace` (optional): Add to current workspace

```python
# Open folder
tool_call("ide_open_folder", {"path": "/project"})

# Open in new window
tool_call("ide_open_folder", {
    "path": "/project",
    "new_window": True
})

# Add to workspace
tool_call("ide_open_folder", {
    "path": "/another-project",
    "add_to_workspace": True
})
```

#### `ide_new_window`
Open a new IDE window.

**Parameters:**
- `path` (optional): Folder to open in new window
- `ide` (optional): Specific IDE to use

```python
# New empty window
tool_call("ide_new_window", {})

# New window with folder
tool_call("ide_new_window", {"path": "/project"})
```

---

### Diff & Merge

#### `ide_diff`
Show diff between two files in the IDE.

**Parameters:**
- `file1` (required): First file path
- `file2` (required): Second file path
- `wait` (optional): Wait for diff window to close
- `ide` (optional): Specific IDE to use

```python
tool_call("ide_diff", {
    "file1": "/project/old.py",
    "file2": "/project/new.py"
})

# Wait for user to close diff
tool_call("ide_diff", {
    "file1": "/project/old.py",
    "file2": "/project/new.py",
    "wait": True
})
```

#### `ide_merge`
Open 3-way merge editor (VS Code and VSCodium only).

**Parameters:**
- `base` (required): Base file path
- `local` (required): Local file path
- `remote` (required): Remote file path
- `result_path` (required): Output file path
- `wait` (optional, default: true): Wait for merge to complete
- `ide` (optional): Specific IDE to use

```python
tool_call("ide_merge", {
    "base": "/project/base.py",
    "local": "/project/local.py",
    "remote": "/project/remote.py",
    "result_path": "/project/merged.py"
})
```

> **Note**: Merge is only supported by VS Code and VSCodium. Cursor and Windsurf do not support this feature.

---

### Extension Management

#### `ide_list_extensions`
List installed IDE extensions.

```python
tool_call("ide_list_extensions", {})
# Result:
# {
#   "success": true,
#   "extensions": ["ms-python.python", "ms-vscode.go", ...],
#   "count": 42
# }
```

#### `ide_install_extension`
Install an IDE extension.

**Parameters:**
- `extension_id` (required): Extension ID (e.g., 'ms-python.python')
- `ide` (optional): Specific IDE to use

```python
tool_call("ide_install_extension", {
    "extension_id": "ms-python.python"
})
```

#### `ide_uninstall_extension`
Uninstall an IDE extension.

**Parameters:**
- `extension_id` (required): Extension ID
- `ide` (optional): Specific IDE to use

```python
tool_call("ide_uninstall_extension", {
    "extension_id": "ms-python.python"
})
```

---

## Use Cases

### 1. Code Review Workflow

```python
# Agent reviewing changes
await tool_call("ide_diff", {
    "file1": "src/auth.py.bak",
    "file2": "src/auth.py",
    "wait": True
})
```

### 2. Navigate to Error

```python
# Agent found an error at line 42
await tool_call("ide_open_file", {
    "path": "src/main.py",
    "line": 42,
    "column": 15
})
```

### 3. Project Setup

```python
# Install recommended extensions
extensions = ["ms-python.python", "charliermarsh.ruff", "ms-python.black-formatter"]
for ext in extensions:
    await tool_call("ide_install_extension", {"extension_id": ext})

# Open project
await tool_call("ide_open_folder", {"path": "/new-project"})
```

### 4. Multi-Project Workflow

```python
# Open main project
await tool_call("ide_open_folder", {"path": "/main-project"})

# Add related project to workspace
await tool_call("ide_open_folder", {
    "path": "/shared-libs",
    "add_to_workspace": True
})
```

### 5. Conflict Resolution

```python
# Open 3-way merge for git conflict
await tool_call("ide_merge", {
    "base": ".git/MERGE_BASE",
    "local": "src/config.py",
    "remote": ".git/MERGE_HEAD",
    "result_path": "src/config.py.merged",
    "wait": True
})
```

---

## Configuration

### VS Code Settings

```json
// .vscode/settings.json
{
  "mcp.servers": {
    "paracle": {
      "command": "uv",
      "args": ["run", "paracle", "mcp", "serve", "--stdio"]
    }
  }
}
```

### Claude Desktop

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "paracle": {
      "command": "uv",
      "args": ["run", "paracle", "mcp", "serve", "--stdio"]
    }
  }
}
```

---

## Limitations

### What IDE Tools Can Do

✅ Open files and folders
✅ Navigate to specific lines/columns
✅ Show diffs between files
✅ 3-way merge (VS Code/Codium only)
✅ Manage extensions
✅ Open new windows

### What IDE Tools Cannot Do

❌ Read terminal output
❌ Access extension output panels
❌ Interact with IDE UI
❌ Read debug console
❌ Execute commands in integrated terminal

> **Note**: These limitations are due to CLI commands being designed to *launch* the IDE, not *interact* with a running instance. For advanced integration, a dedicated VS Code extension would be required.

---

## Error Handling

### IDENotFoundError

Raised when no supported IDE CLI is found in PATH.

```python
# Solution: Ensure IDE CLI is installed
# VS Code: Install and run "Shell Command: Install 'code' command in PATH"
# Cursor: Install from cursor.sh
```

### IDECommandError

Raised when IDE command execution fails.

```python
# Common causes:
# - File not found
# - Permission denied
# - Command timeout (30s default)
```

---

## API Reference

### Python API

```python
from paracle_tools.ide_tools import (
    detect_ide,
    get_ide_command,
    ide_info,
    ide_open_file,
    ide_open_folder,
    ide_diff,
    ide_merge,
    ide_new_window,
    ide_list_extensions,
    ide_install_extension,
    ide_uninstall_extension,
    ide_version,
    IDENotFoundError,
    IDECommandError,
    SUPPORTED_IDES,
)

# Detect available IDE
detected = detect_ide()  # Returns: "cursor", "vscode", etc. or None

# Get IDE command
cmd = get_ide_command("vscode")  # Returns: "code"

# Direct function calls
result = ide_open_file("/path/to/file.py", line=42)
```

---

## Testing

Run IDE tools tests:

```bash
pytest tests/unit/test_ide_tools.py -v
```

All 31 tests cover:
- IDE detection
- File/folder opening
- Diff functionality
- Extension management
- Error handling

---

## Related Documentation

- [MCP Quick Reference](../mcp-quick-reference.md)
- [MCP Full Coverage](../mcp-full-coverage.md)
- [GitHub CLI Tool](github-cli-tool.md)

---

**Last Updated**: 2026-01-10
