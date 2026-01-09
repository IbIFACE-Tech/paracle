"""MCP Tool Registry for managing discovered tools."""

from collections.abc import Callable
from typing import Any

from paracle_mcp.client import MCPClient


class MCPToolRegistry:
    """
    Registry for MCP-discovered tools.

    Maintains a catalog of tools discovered from MCP servers,
    making them available to Paracle agents.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._tools: dict[str, dict[str, Any]] = {}
        self._clients: dict[str, MCPClient] = {}

    async def discover_from_server(
        self,
        server_name: str,
        client: MCPClient,
    ) -> int:
        """
        Discover and register tools from an MCP server.

        Args:
            server_name: Identifier for this server
            client: Connected MCP client

        Returns:
            Number of tools discovered

        Example:
            >>> async with MCPClient("http://localhost:3000") as client:
            ...     count = await registry.discover_from_server("local", client)
            ...     print(f"Discovered {count} tools")
        """
        if not client.is_connected:
            raise RuntimeError(f"Client for '{server_name}' is not connected")

        # Store client reference
        self._clients[server_name] = client

        # Discover tools
        tools = await client.list_tools()

        # Register each tool
        for tool_spec in tools:
            tool_id = f"{server_name}.{tool_spec['name']}"
            self._tools[tool_id] = {
                "server": server_name,
                "name": tool_spec["name"],
                "description": tool_spec.get("description", ""),
                "schema": tool_spec.get("schema", {}),
                "metadata": tool_spec.get("metadata", {}),
                "client": client,
            }

        return len(tools)

    def get_tool(self, tool_id: str) -> dict[str, Any] | None:
        """
        Get tool specification by ID.

        Args:
            tool_id: Tool identifier (format: "server_name.tool_name")

        Returns:
            Tool specification or None if not found

        Example:
            >>> tool = registry.get_tool("local.search")
            >>> print(tool['description'])
        """
        return self._tools.get(tool_id)

    def list_tools(self, server_name: str | None = None) -> list[str]:
        """
        List all registered tool IDs.

        Args:
            server_name: Optional server filter

        Returns:
            List of tool IDs

        Example:
            >>> all_tools = registry.list_tools()
            >>> local_tools = registry.list_tools("local")
        """
        if server_name:
            return [
                tool_id
                for tool_id, tool in self._tools.items()
                if tool["server"] == server_name
            ]
        return list(self._tools.keys())

    def search_tools(self, query: str) -> list[str]:
        """
        Search tools by name or description.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching tool IDs

        Example:
            >>> search_tools = registry.search_tools("search")
        """
        query_lower = query.lower()
        matches = []

        for tool_id, tool in self._tools.items():
            if (
                query_lower in tool["name"].lower()
                or query_lower in tool["description"].lower()
            ):
                matches.append(tool_id)

        return matches

    async def call_tool(
        self,
        tool_id: str,
        arguments: dict[str, Any],
    ) -> Any:
        """
        Call a registered MCP tool.

        Args:
            tool_id: Tool identifier
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            KeyError: If tool not found
            RuntimeError: If tool execution fails

        Example:
            >>> result = await registry.call_tool(
            ...     "local.search",
            ...     {"query": "python", "limit": 5}
            ... )
        """
        tool = self._tools.get(tool_id)
        if not tool:
            raise KeyError(f"Tool '{tool_id}' not found in registry")

        client: MCPClient = tool["client"]
        tool_name = tool["name"]

        return await client.call_tool(tool_name, arguments)

    def create_callable(self, tool_id: str) -> Callable:
        """
        Create a callable Python function for a tool.

        Args:
            tool_id: Tool identifier

        Returns:
            Async callable function

        Example:
            >>> search = registry.create_callable("local.search")
            >>> result = await search(query="python", limit=5)
        """
        tool = self._tools.get(tool_id)
        if not tool:
            raise KeyError(f"Tool '{tool_id}' not found in registry")

        async def tool_callable(**kwargs):
            return await self.call_tool(tool_id, kwargs)

        # Add metadata to function
        tool_callable.__name__ = tool["name"]
        tool_callable.__doc__ = tool["description"]

        return tool_callable

    def unregister_server(self, server_name: str) -> int:
        """
        Unregister all tools from a server.

        Args:
            server_name: Server identifier

        Returns:
            Number of tools removed

        Example:
            >>> count = registry.unregister_server("local")
            >>> print(f"Removed {count} tools")
        """
        tools_to_remove = [
            tool_id
            for tool_id, tool in self._tools.items()
            if tool["server"] == server_name
        ]

        for tool_id in tools_to_remove:
            del self._tools[tool_id]

        if server_name in self._clients:
            del self._clients[server_name]

        return len(tools_to_remove)

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._clients.clear()

    def get_statistics(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Statistics dictionary

        Example:
            >>> stats = registry.get_statistics()
            >>> print(f"Total tools: {stats['total_tools']}")
        """
        servers = {tool["server"] for tool in self._tools.values()}

        return {
            "total_tools": len(self._tools),
            "total_servers": len(servers),
            "servers": list(servers),
            "tools_per_server": {
                server: len(self.list_tools(server)) for server in servers
            },
        }

    def __len__(self) -> int:
        """Return number of registered tools."""
        return len(self._tools)

    def __contains__(self, tool_id: str) -> bool:
        """Check if tool is registered."""
        return tool_id in self._tools

    def __repr__(self) -> str:
        return (
            f"MCPToolRegistry(tools={len(self._tools)}, servers={len(self._clients)})"
        )
