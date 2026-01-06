"""
Tool management and Model Context Protocol (MCP) integration.

This package provides:
- Built-in tools: filesystem, HTTP, shell operations (with security controls)
- MCP client for discovering and calling MCP-compatible tools
- Tool registry for managing available tools
- Tool integration with Paracle agents

SECURITY NOTE: Default tool instances have been REMOVED for security.
All filesystem/shell tools now require explicit configuration.
Use factory functions to create properly configured tools.
"""

__version__ = "0.0.1"

# MCP tools
# Built-in tools
from paracle_tools.builtin import (
    DEVELOPMENT_COMMANDS,
    READONLY_COMMANDS,
    # Base classes
    BaseTool,
    BuiltinToolRegistry,
    DeleteFileTool,
    ListDirectoryTool,
    PermissionError,
    # Filesystem tool classes (require allowed_paths)
    ReadFileTool,
    # Shell tool classes (require allowed_commands)
    RunCommandTool,
    Tool,
    ToolError,
    ToolResult,
    WriteFileTool,
    create_command_tool,
    create_development_command_tool,
    create_readonly_command_tool,
    create_sandboxed_filesystem_tools,
    http_delete,
    # HTTP tools
    http_get,
    http_post,
    http_put,
)
from paracle_tools.git_tools import (
    GitAddTool,
    GitCommitTool,
    GitPushTool,
    GitStatusTool,
    GitTagTool,
    git_add,
    git_commit,
    git_push,
    git_status,
    git_tag,
)
from paracle_tools.mcp import MCPClient, MCPToolRegistry

__all__ = [
    # MCP
    "MCPClient",
    "MCPToolRegistry",
    # Built-in base
    "BaseTool",
    "Tool",
    "ToolResult",
    "ToolError",
    "PermissionError",
    "BuiltinToolRegistry",
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
    # Git tools
    "GitAddTool",
    "GitCommitTool",
    "GitPushTool",
    "GitStatusTool",
    "GitTagTool",
    "git_add",
    "git_commit",
    "git_push",
    "git_status",
    "git_tag",
]
