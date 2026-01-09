"""Model Context Protocol (MCP) client implementation."""

from typing import Any

try:
    import httpx
except ImportError:
    raise ImportError(
        "httpx is required for MCP client. " "Install with: pip install httpx"
    )


class MCPClient:
    """
    Client for Model Context Protocol.

    MCP is a standard protocol for tools and context to be shared
    between AI applications. This client enables Paracle to discover
    and call MCP-compatible tools.

    Specification: https://modelcontextprotocol.io/
    """

    def __init__(self, server_url: str | None = None, **config: Any):
        """
        Initialize MCP client.

        Args:
            server_url: MCP server base URL
            **config: Additional configuration
        """
        self.server_url = server_url or config.get(
            "server_url", "http://localhost:3000"
        )
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=self.server_url,
            timeout=config.get("timeout", 30.0),
        )
        self._connected = False

    async def connect(self) -> bool:
        """
        Connect to MCP server and initialize session.

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Send initialize request
            response = await self.client.post(
                "/mcp/initialize",
                json={
                    "protocol_version": "1.0",
                    "client_info": {
                        "name": "paracle",
                        "version": "0.0.1",
                    },
                },
            )
            response.raise_for_status()

            init_result = response.json()
            self._connected = True

            return init_result.get("status") == "ok"

        except httpx.HTTPError as e:
            raise ConnectionError(f"Failed to connect to MCP server: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from MCP server and cleanup."""
        if self._connected:
            try:
                await self.client.post("/mcp/shutdown")
            except Exception:
                pass  # Best effort
            finally:
                self._connected = False
                await self.client.aclose()

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        List all available tools from MCP server.

        Returns:
            List of tool specifications

        Example:
            >>> tools = await client.list_tools()
            >>> for tool in tools:
            ...     print(tool['name'], tool['description'])

        Raises:
            RuntimeError: If not connected
            httpx.HTTPError: On API errors
        """
        if not self._connected:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        try:
            response = await self.client.get("/mcp/tools")
            response.raise_for_status()

            result = response.json()
            return result.get("tools", [])

        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to list tools: {e}") from e

    async def get_tool(self, tool_name: str) -> dict[str, Any]:
        """
        Get detailed information about a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool specification including schema and metadata

        Raises:
            RuntimeError: If not connected or tool not found
        """
        if not self._connected:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        try:
            response = await self.client.get(f"/mcp/tools/{tool_name}")
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise RuntimeError(f"Tool '{tool_name}' not found") from e
            raise

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        """
        Call a tool via MCP.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as dictionary
            **kwargs: Additional call parameters

        Returns:
            Tool execution result

        Example:
            >>> result = await client.call_tool(
            ...     "search",
            ...     {"query": "python tutorial", "limit": 5}
            ... )

        Raises:
            RuntimeError: If not connected or tool execution fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        try:
            response = await self.client.post(
                "/mcp/tools/call",
                json={
                    "tool": tool_name,
                    "arguments": arguments,
                    **kwargs,
                },
            )
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise RuntimeError(f"Tool execution failed: {result['error']}")

            return result.get("result")

        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to call tool '{tool_name}': {e}") from e

    async def list_resources(self) -> list[dict[str, Any]]:
        """
        List available MCP resources (context, files, etc.).

        Returns:
            List of resource specifications

        Note:
            Resources are read-only context that can be provided to models.
        """
        if not self._connected:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        try:
            response = await self.client.get("/mcp/resources")
            response.raise_for_status()

            result = response.json()
            return result.get("resources", [])

        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to list resources: {e}") from e

    async def read_resource(self, resource_uri: str) -> str:
        """
        Read content from an MCP resource.

        Args:
            resource_uri: URI of the resource to read

        Returns:
            Resource content as string

        Example:
            >>> content = await client.read_resource("file:///docs/README.md")
        """
        if not self._connected:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        try:
            response = await self.client.post(
                "/mcp/resources/read",
                json={"uri": resource_uri},
            )
            response.raise_for_status()

            result = response.json()
            return result.get("content", "")

        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to read resource '{resource_uri}': {e}") from e

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to server."""
        return self._connected

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"MCPClient(server_url={self.server_url}, status={status})"
