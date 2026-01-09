"""Registry for built-in tools.

Security Note:
    The registry now REQUIRES explicit configuration for filesystem and shell tools.
    This prevents accidental unrestricted access to the filesystem or shell.
"""

from __future__ import annotations

from typing import Any

from paracle_tools.builtin.base import Tool, ToolResult
from paracle_tools.builtin.filesystem import (
    DeleteFileTool,
    ListDirectoryTool,
    ReadFileTool,
    WriteFileTool,
)
from paracle_tools.builtin.http import (
    HTTPDeleteTool,
    HTTPGetTool,
    HTTPPostTool,
    HTTPPutTool,
)
from paracle_tools.builtin.shell import RunCommandTool


class BuiltinToolRegistry:
    """Registry for managing built-in tools.

    Provides centralized access to all built-in tools with:
    - Tool discovery and listing
    - Tool execution
    - Permission management
    - Configuration

    Security:
        Requires explicit configuration for filesystem and shell tools.
        No default unrestricted access is allowed.
    """

    def __init__(
        self,
        filesystem_paths: list[str],
        allowed_commands: list[str],
        http_timeout: float = 30.0,
        command_timeout: float = 30.0,
    ):
        """Initialize the tool registry.

        Args:
            filesystem_paths: Allowed paths for filesystem operations (REQUIRED)
            allowed_commands: Allowed shell commands (REQUIRED)
            http_timeout: Timeout for HTTP requests in seconds
            command_timeout: Timeout for shell commands in seconds

        Raises:
            ValueError: If filesystem_paths or allowed_commands is empty/None
        """
        if not filesystem_paths:
            raise ValueError(
                "filesystem_paths is required for security. "
                "Specify allowed directories for filesystem tools."
            )
        if not allowed_commands:
            raise ValueError(
                "allowed_commands is required for security. "
                "Specify allowed commands for shell tools."
            )

        self._tools: dict[str, Tool] = {}

        # Initialize filesystem tools (with mandatory sandboxing)
        self._tools["read_file"] = ReadFileTool(allowed_paths=filesystem_paths)
        self._tools["write_file"] = WriteFileTool(allowed_paths=filesystem_paths)
        self._tools["list_directory"] = ListDirectoryTool(
            allowed_paths=filesystem_paths
        )
        self._tools["delete_file"] = DeleteFileTool(allowed_paths=filesystem_paths)

        # Initialize HTTP tools
        self._tools["http_get"] = HTTPGetTool(timeout=http_timeout)
        self._tools["http_post"] = HTTPPostTool(timeout=http_timeout)
        self._tools["http_put"] = HTTPPutTool(timeout=http_timeout)
        self._tools["http_delete"] = HTTPDeleteTool(timeout=http_timeout)

        # Initialize shell tool (with mandatory command allowlist)
        self._tools["run_command"] = RunCommandTool(
            allowed_commands=allowed_commands,
            timeout=command_timeout,
        )

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools.

        Returns:
            List of tool metadata dictionaries
        """
        return [tool.to_dict() for tool in self._tools.values()]

    def list_tool_names(self) -> list[str]:
        """List all tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    async def execute_tool(self, name: str, **parameters) -> ToolResult:
        """Execute a tool by name.

        Args:
            name: Tool name
            **parameters: Tool parameters

        Returns:
            ToolResult with execution outcome

        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(name)
        if tool is None:
            return ToolResult.error_result(
                error=f"Tool '{name}' not found",
                available_tools=self.list_tool_names(),
            )

        return await tool.execute(**parameters)

    def has_tool(self, name: str) -> bool:
        """Check if a tool exists.

        Args:
            name: Tool name

        Returns:
            True if tool exists
        """
        return name in self._tools

    def get_tools_by_category(self) -> dict[str, list[str]]:
        """Get tools grouped by category.

        Returns:
            Dictionary mapping category to list of tool names
        """
        categories: dict[str, list[str]] = {
            "filesystem": [],
            "http": [],
            "shell": [],
        }

        for name, _tool in self._tools.items():
            if "file" in name or "directory" in name:
                categories["filesystem"].append(name)
            elif "http" in name:
                categories["http"].append(name)
            elif "command" in name or "shell" in name:
                categories["shell"].append(name)

        return categories

    def get_tool_permissions(self, name: str) -> list[str]:
        """Get required permissions for a tool.

        Args:
            name: Tool name

        Returns:
            List of required permissions, empty if tool not found
        """
        tool = self.get_tool(name)
        if tool is None:
            return []
        return tool.permissions

    def configure_filesystem_paths(self, allowed_paths: list[str]) -> None:
        """Reconfigure allowed filesystem paths.

        Args:
            allowed_paths: New list of allowed paths
        """
        # Recreate filesystem tools with new paths
        self._tools["read_file"] = ReadFileTool(allowed_paths=allowed_paths)
        self._tools["write_file"] = WriteFileTool(allowed_paths=allowed_paths)
        self._tools["list_directory"] = ListDirectoryTool(allowed_paths=allowed_paths)
        self._tools["delete_file"] = DeleteFileTool(allowed_paths=allowed_paths)

    def configure_allowed_commands(self, allowed_commands: list[str]) -> None:
        """Reconfigure allowed shell commands.

        Args:
            allowed_commands: New list of allowed commands
        """
        current_tool = self._tools.get("run_command")
        timeout = current_tool.timeout if current_tool else 30.0

        self._tools["run_command"] = RunCommandTool(
            allowed_commands=allowed_commands,
            timeout=timeout,
        )


# =============================================================================
# DEPRECATED: Default registry instance removed for security
# =============================================================================
# The default_registry has been REMOVED because it required unrestricted access.
#
# Migration:
#   # Old (insecure):
#   from paracle_tools.builtin.registry import default_registry
#   result = await default_registry.execute_tool("read_file", path="/etc/passwd")
#
#   # New (secure):
#   from paracle_tools.builtin.registry import BuiltinToolRegistry
#   registry = BuiltinToolRegistry(
#       filesystem_paths=["/app/data"],
#       allowed_commands=["git", "ls"],
#   )
#   result = await registry.execute_tool("read_file", path="/app/data/file.txt")
# =============================================================================
