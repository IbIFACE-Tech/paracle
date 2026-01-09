"""Built-in tools for Paracle agents.

This module provides native Python tools that agents can use without
requiring external MCP servers or dependencies.

SECURITY NOTE: Default tool instances have been REMOVED for security.
All tools now require explicit configuration (allowed_paths, allowed_commands).
Use the factory functions to create properly configured tools.

Available tool categories:
- Filesystem: ReadFileTool, WriteFileTool, ListDirectoryTool, DeleteFileTool
- HTTP: http_get, http_post, http_put, http_delete
- Shell: RunCommandTool (with mandatory command allowlist)
"""

__version__ = "1.0.1"

from paracle_tools.builtin.base import (
    BaseTool,
    PermissionError,
    Tool,
    ToolError,
    ToolResult,
)
from paracle_tools.builtin.filesystem import (
    DeleteFileTool,
    ListDirectoryTool,
    ReadFileTool,
    WriteFileTool,
    create_sandboxed_filesystem_tools,
)
from paracle_tools.builtin.http import http_delete, http_get, http_post, http_put
from paracle_tools.builtin.registry import BuiltinToolRegistry
from paracle_tools.builtin.shell import (
    DEVELOPMENT_COMMANDS,
    READONLY_COMMANDS,
    RunCommandTool,
    create_command_tool,
    create_development_command_tool,
    create_readonly_command_tool,
)

__all__ = [
    # Base classes
    "BaseTool",
    "Tool",
    "ToolResult",
    "ToolError",
    "PermissionError",
    # Filesystem tool classes (require allowed_paths)
    "ReadFileTool",
    "WriteFileTool",
    "ListDirectoryTool",
    "DeleteFileTool",
    "create_sandboxed_filesystem_tools",
    # HTTP tools
    "http_get",
    "http_post",
    "http_put",
    "http_delete",
    # Shell tool classes (require allowed_commands)
    "RunCommandTool",
    "create_command_tool",
    "create_readonly_command_tool",
    "create_development_command_tool",
    "READONLY_COMMANDS",
    "DEVELOPMENT_COMMANDS",
    # Registry
    "BuiltinToolRegistry",
]
