"""Tests for MCP tool registry."""

import pytest

from paracle_tools.mcp import MCPToolRegistry


class MockMCPClient:
    """Mock MCP client for testing."""

    def __init__(self, tools=None):
        self.is_connected = True
        self._tools = tools or [
            {
                "name": "search",
                "description": "Search the web",
                "schema": {"query": "string"},
            },
            {
                "name": "calculator",
                "description": "Perform calculations",
                "schema": {"expression": "string"},
            },
        ]
        self._call_results = {}

    async def list_tools(self):
        return self._tools

    async def call_tool(self, tool_name, arguments):
        # Return mock result
        return self._call_results.get(tool_name, {"result": f"Mock result for {tool_name}"})


class TestMCPToolRegistry:
    """Tests for MCPToolRegistry."""

    @pytest.mark.asyncio
    async def test_discover_from_server(self):
        """Test discovering tools from MCP server."""
        registry = MCPToolRegistry()
        client = MockMCPClient()

        count = await registry.discover_from_server("test_server", client)

        assert count == 2
        assert len(registry) == 2
        assert "test_server.search" in registry
        assert "test_server.calculator" in registry

    @pytest.mark.asyncio
    async def test_discover_raises_if_not_connected(self):
        """Test discovery fails if client not connected."""
        registry = MCPToolRegistry()
        client = MockMCPClient()
        client.is_connected = False

        with pytest.raises(RuntimeError, match="not connected"):
            await registry.discover_from_server("test_server", client)

    def test_get_tool(self):
        """Test retrieving tool by ID."""
        registry = MCPToolRegistry()
        registry._tools["server.tool"] = {
            "server": "server",
            "name": "tool",
            "description": "Test tool",
        }

        tool = registry.get_tool("server.tool")

        assert tool is not None
        assert tool["name"] == "tool"
        assert tool["description"] == "Test tool"

    def test_get_nonexistent_tool(self):
        """Test retrieving non-existent tool returns None."""
        registry = MCPToolRegistry()

        tool = registry.get_tool("nonexistent")

        assert tool is None

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing all tools."""
        registry = MCPToolRegistry()
        client = MockMCPClient()
        await registry.discover_from_server("test_server", client)

        tools = registry.list_tools()

        assert len(tools) == 2
        assert "test_server.search" in tools
        assert "test_server.calculator" in tools

    @pytest.mark.asyncio
    async def test_list_tools_filtered_by_server(self):
        """Test listing tools filtered by server."""
        registry = MCPToolRegistry()
        client1 = MockMCPClient([{"name": "tool1", "description": "Tool 1"}])
        client2 = MockMCPClient([{"name": "tool2", "description": "Tool 2"}])

        await registry.discover_from_server("server1", client1)
        await registry.discover_from_server("server2", client2)

        server1_tools = registry.list_tools("server1")
        server2_tools = registry.list_tools("server2")

        assert len(server1_tools) == 1
        assert "server1.tool1" in server1_tools
        assert len(server2_tools) == 1
        assert "server2.tool2" in server2_tools

    @pytest.mark.asyncio
    async def test_search_tools(self):
        """Test searching tools by query."""
        registry = MCPToolRegistry()
        client = MockMCPClient()
        await registry.discover_from_server("test_server", client)

        results = registry.search_tools("search")

        assert len(results) == 1
        assert "test_server.search" in results

    @pytest.mark.asyncio
    async def test_search_tools_case_insensitive(self):
        """Test search is case-insensitive."""
        registry = MCPToolRegistry()
        client = MockMCPClient()
        await registry.discover_from_server("test_server", client)

        results = registry.search_tools("CALCULATOR")

        assert len(results) == 1
        assert "test_server.calculator" in results

    @pytest.mark.asyncio
    async def test_call_tool(self):
        """Test calling a tool."""
        registry = MCPToolRegistry()
        client = MockMCPClient()
        await registry.discover_from_server("test_server", client)

        result = await registry.call_tool(
            "test_server.search",
            {"query": "python"}
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_call_nonexistent_tool_raises_error(self):
        """Test calling non-existent tool raises KeyError."""
        registry = MCPToolRegistry()

        with pytest.raises(KeyError, match="not found"):
            await registry.call_tool("nonexistent", {})

    @pytest.mark.asyncio
    async def test_create_callable(self):
        """Test creating callable function for tool."""
        registry = MCPToolRegistry()
        client = MockMCPClient()
        await registry.discover_from_server("test_server", client)

        search = registry.create_callable("test_server.search")

        assert callable(search)
        assert search.__name__ == "search"
        assert "Search" in search.__doc__

        # Test calling it
        result = await search(query="python")
        assert result is not None

    def test_create_callable_nonexistent_tool_raises_error(self):
        """Test creating callable for non-existent tool raises KeyError."""
        registry = MCPToolRegistry()

        with pytest.raises(KeyError, match="not found"):
            registry.create_callable("nonexistent")

    @pytest.mark.asyncio
    async def test_unregister_server(self):
        """Test unregistering all tools from a server."""
        registry = MCPToolRegistry()
        client = MockMCPClient()
        await registry.discover_from_server("test_server", client)

        assert len(registry) == 2

        count = registry.unregister_server("test_server")

        assert count == 2
        assert len(registry) == 0

    def test_clear(self):
        """Test clearing all tools."""
        registry = MCPToolRegistry()
        registry._tools = {"tool1": {}, "tool2": {}}

        assert len(registry) == 2

        registry.clear()

        assert len(registry) == 0

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """Test getting registry statistics."""
        registry = MCPToolRegistry()
        client = MockMCPClient()
        await registry.discover_from_server("test_server", client)

        stats = registry.get_statistics()

        assert stats["total_tools"] == 2
        assert stats["total_servers"] == 1
        assert "test_server" in stats["servers"]
        assert stats["tools_per_server"]["test_server"] == 2

    def test_len(self):
        """Test __len__ method."""
        registry = MCPToolRegistry()
        registry._tools = {"tool1": {}, "tool2": {}, "tool3": {}}

        assert len(registry) == 3

    def test_contains(self):
        """Test __contains__ method."""
        registry = MCPToolRegistry()
        registry._tools = {"server.tool": {}}

        assert "server.tool" in registry
        assert "nonexistent" not in registry

    def test_repr(self):
        """Test __repr__ method."""
        registry = MCPToolRegistry()
        registry._tools = {"tool1": {}, "tool2": {}}

        repr_str = repr(registry)

        assert "MCPToolRegistry" in repr_str
        assert "tools=2" in repr_str
