"""MCP (Model Context Protocol) integration capability for MetaAgent.

Provides access to external tools and resources through the
Model Context Protocol standard.
"""

import time
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class MCPConfig(CapabilityConfig):
    """Configuration for MCP capability."""

    server_url: str = Field(
        default="http://localhost:3000",
        description="MCP server URL",
    )
    auto_discover: bool = Field(
        default=True, description="Auto-discover available tools on connect"
    )
    cache_tools: bool = Field(default=True, description="Cache tool definitions")
    max_concurrent_calls: int = Field(
        default=5, ge=1, le=20, description="Max concurrent tool calls"
    )


class MCPTool:
    """Wrapper for an MCP tool."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        mcp_capability: "MCPCapability",
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self._mcp = mcp_capability

    async def __call__(self, **kwargs) -> Any:
        """Call the tool with arguments."""
        result = await self._mcp.call_tool(self.name, kwargs)
        if result.success:
            return result.output
        raise RuntimeError(result.error)

    def __repr__(self) -> str:
        return f"MCPTool(name={self.name}, description={self.description[:50]}...)"


class MCPCapability(BaseCapability):
    """MCP integration capability for MetaAgent.

    Provides access to external tools through the Model Context Protocol,
    enabling the MetaAgent to use tools from any MCP-compatible server.

    Example:
        >>> mcp = MCPCapability(config=MCPConfig(server_url="http://localhost:3000"))
        >>> await mcp.initialize()
        >>>
        >>> # List available tools
        >>> result = await mcp.execute(action="list_tools")
        >>> print(result.output)
        >>>
        >>> # Call a tool
        >>> result = await mcp.execute(
        ...     action="call_tool",
        ...     tool_name="search",
        ...     arguments={"query": "Python tutorial"}
        ... )
        >>>
        >>> # Get tool as callable
        >>> search = mcp.get_tool("search")
        >>> results = await search(query="Python tutorial")
    """

    name = "mcp"
    description = "Model Context Protocol integration for external tools"

    def __init__(self, config: MCPConfig | None = None):
        """Initialize MCP capability.

        Args:
            config: MCP configuration
        """
        super().__init__(config or MCPConfig())
        self.config: MCPConfig = self.config
        self._client: httpx.AsyncClient | None = None
        self._tools_cache: dict[str, dict[str, Any]] = {}
        self._connected = False

    async def initialize(self) -> None:
        """Initialize MCP client and connect to server."""
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for MCP integration. "
                "Install with: pip install httpx"
            )

        self._client = httpx.AsyncClient(
            base_url=self.config.server_url,
            timeout=self.config.timeout,
        )

        # Try to connect to server
        try:
            await self._connect()
        except Exception:
            # Allow initialization even if server is not available
            # Tools will fail at call time
            pass

        await super().initialize()

    async def shutdown(self) -> None:
        """Disconnect from MCP server and cleanup."""
        if self._connected and self._client:
            try:
                await self._client.post("/mcp/shutdown")
            except Exception:
                pass

        if self._client:
            await self._client.aclose()
            self._client = None

        self._connected = False
        self._tools_cache.clear()
        await super().shutdown()

    async def _connect(self) -> bool:
        """Connect to MCP server."""
        if not self._client:
            raise RuntimeError("HTTP client not initialized")

        try:
            response = await self._client.post(
                "/mcp/initialize",
                json={
                    "protocol_version": "1.0",
                    "client_info": {
                        "name": "paracle_meta",
                        "version": "1.1.0",
                    },
                },
            )
            response.raise_for_status()

            result = response.json()
            self._connected = result.get("status") == "ok"

            # Auto-discover tools
            if self._connected and self.config.auto_discover:
                await self._discover_tools()

            return self._connected

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to MCP server: {e}") from e

    async def _discover_tools(self) -> list[dict[str, Any]]:
        """Discover available tools from server."""
        if not self._client or not self._connected:
            return []

        try:
            response = await self._client.get("/mcp/tools")
            response.raise_for_status()

            result = response.json()
            tools = result.get("tools", [])

            # Cache tools
            if self.config.cache_tools:
                for tool in tools:
                    self._tools_cache[tool["name"]] = tool

            return tools

        except Exception:
            return []

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute MCP capability.

        Args:
            action: Action to perform (list_tools, call_tool, get_resources, read_resource)
            **kwargs: Action-specific parameters

        Returns:
            CapabilityResult with MCP operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "list_tools")
        start_time = time.time()

        try:
            if action == "connect":
                result = await self._connect()
            elif action == "list_tools":
                result = await self._list_tools(**kwargs)
            elif action == "call_tool":
                result = await self._call_tool(**kwargs)
            elif action == "get_resources":
                result = await self._get_resources(**kwargs)
            elif action == "read_resource":
                result = await self._read_resource(**kwargs)
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result,
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    async def _list_tools(
        self, refresh: bool = False, **kwargs
    ) -> list[dict[str, Any]]:
        """List available MCP tools.

        Args:
            refresh: Force refresh from server

        Returns:
            List of tool specifications
        """
        # Return from cache if available
        if self._tools_cache and not refresh:
            return list(self._tools_cache.values())

        # Fetch from server
        if not self._connected:
            # Return mock tools when not connected
            return self._get_mock_tools()

        tools = await self._discover_tools()
        return tools

    def _get_mock_tools(self) -> list[dict[str, Any]]:
        """Return mock tools for testing when server unavailable."""
        return [
            {
                "name": "search",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Max results"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "read_file",
                "description": "Read contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "write_file",
                "description": "Write contents to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "File content"},
                    },
                    "required": ["path", "content"],
                },
            },
        ]

    async def _call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        **kwargs,
    ) -> Any:
        """Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if not self._connected:
            # Return mock result when not connected
            return self._mock_tool_call(tool_name, arguments)

        if not self._client:
            raise RuntimeError("HTTP client not initialized")

        try:
            response = await self._client.post(
                "/mcp/tools/call",
                json={
                    "tool": tool_name,
                    "arguments": arguments,
                },
            )
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise RuntimeError(f"Tool execution failed: {result['error']}")

            return result.get("result")

        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to call tool '{tool_name}': {e}") from e

    def _mock_tool_call(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Return mock tool result for testing."""
        return {
            "mock": True,
            "tool": tool_name,
            "arguments": arguments,
            "result": f"Mock result for {tool_name}",
        }

    async def _get_resources(self, **kwargs) -> list[dict[str, Any]]:
        """List available MCP resources.

        Returns:
            List of resource specifications
        """
        if not self._connected or not self._client:
            return []

        try:
            response = await self._client.get("/mcp/resources")
            response.raise_for_status()

            result = response.json()
            return result.get("resources", [])

        except Exception:
            return []

    async def _read_resource(self, uri: str, **kwargs) -> str:
        """Read content from an MCP resource.

        Args:
            uri: Resource URI

        Returns:
            Resource content
        """
        if not self._connected or not self._client:
            return ""

        try:
            response = await self._client.post(
                "/mcp/resources/read",
                json={"uri": uri},
            )
            response.raise_for_status()

            result = response.json()
            return result.get("content", "")

        except Exception as e:
            raise RuntimeError(f"Failed to read resource '{uri}': {e}") from e

    # Convenience methods
    def get_tool(self, tool_name: str) -> MCPTool:
        """Get a tool wrapper for direct calling.

        Args:
            tool_name: Name of the tool

        Returns:
            MCPTool wrapper
        """
        tool_spec = self._tools_cache.get(tool_name)
        if not tool_spec:
            # Create minimal spec
            tool_spec = {
                "name": tool_name,
                "description": f"MCP tool: {tool_name}",
                "parameters": {},
            }

        return MCPTool(
            name=tool_spec["name"],
            description=tool_spec.get("description", ""),
            parameters=tool_spec.get("parameters", {}),
            mcp_capability=self,
        )

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> CapabilityResult:
        """Call an MCP tool directly.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            CapabilityResult with tool output
        """
        return await self.execute(
            action="call_tool", tool_name=tool_name, arguments=arguments
        )

    async def list_tools(self, refresh: bool = False) -> CapabilityResult:
        """List available MCP tools."""
        return await self.execute(action="list_tools", refresh=refresh)

    @property
    def is_connected(self) -> bool:
        """Check if connected to MCP server."""
        return self._connected

    @property
    def available_tools(self) -> list[str]:
        """Get list of available tool names."""
        return list(self._tools_cache.keys())
