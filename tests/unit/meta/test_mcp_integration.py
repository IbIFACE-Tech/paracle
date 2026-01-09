"""Unit tests for paracle_meta.capabilities.mcp_integration module."""

import pytest
from paracle_meta.capabilities.mcp_integration import MCPCapability, MCPConfig, MCPTool


class TestMCPConfig:
    """Tests for MCPConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = MCPConfig()
        assert config.server_url == "http://localhost:3000"
        assert config.auto_discover is True
        assert config.cache_tools is True
        assert config.max_concurrent_calls == 5

    def test_custom_values(self):
        """Test custom configuration values."""
        config = MCPConfig(
            server_url="http://custom-server:8080",
            auto_discover=False,
            max_concurrent_calls=10,
        )
        assert config.server_url == "http://custom-server:8080"
        assert config.auto_discover is False
        assert config.max_concurrent_calls == 10


class TestMCPCapability:
    """Tests for MCPCapability."""

    @pytest.fixture
    def mcp_capability(self):
        """Create MCP capability instance."""
        return MCPCapability()

    @pytest.fixture
    def mcp_capability_custom(self):
        """Create MCP capability with custom config."""
        config = MCPConfig(
            server_url="http://test-server:3000",
            auto_discover=False,
        )
        return MCPCapability(config=config)

    def test_initialization(self, mcp_capability):
        """Test capability initialization."""
        assert mcp_capability.name == "mcp"
        assert (
            "MCP" in mcp_capability.description
            or "Model Context Protocol" in mcp_capability.description
        )
        assert mcp_capability.is_connected is False

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, mcp_capability):
        """Test initialize and shutdown lifecycle."""
        await mcp_capability.initialize()
        assert mcp_capability.is_initialized is True
        assert mcp_capability._client is not None
        # Connection may fail if no server, but initialization should succeed

        await mcp_capability.shutdown()
        assert mcp_capability.is_initialized is False
        assert mcp_capability._client is None

    @pytest.mark.asyncio
    async def test_list_tools_mock(self, mcp_capability):
        """Test listing tools returns mock tools when disconnected."""
        await mcp_capability.initialize()

        result = await mcp_capability.list_tools()

        assert result.success is True
        assert isinstance(result.output, list)
        # Should return mock tools
        if result.output:
            assert any("name" in tool for tool in result.output)

        await mcp_capability.shutdown()

    @pytest.mark.asyncio
    async def test_call_tool_mock(self, mcp_capability):
        """Test calling tool returns mock result when disconnected."""
        await mcp_capability.initialize()

        result = await mcp_capability.call_tool(
            tool_name="search",
            arguments={"query": "test"},
        )

        assert result.success is True
        # Mock result should be returned
        assert result.output is not None

        await mcp_capability.shutdown()

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, mcp_capability):
        """Test execute with unknown action."""
        await mcp_capability.initialize()

        result = await mcp_capability.execute(action="unknown_action")

        assert result.success is False
        assert "Unknown action" in result.error

        await mcp_capability.shutdown()

    def test_get_tool_wrapper(self, mcp_capability):
        """Test getting tool wrapper."""
        tool = mcp_capability.get_tool("test_tool")

        assert isinstance(tool, MCPTool)
        assert tool.name == "test_tool"

    def test_get_mock_tools(self, mcp_capability):
        """Test _get_mock_tools returns valid tools."""
        tools = mcp_capability._get_mock_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool

    def test_mock_tool_call(self, mcp_capability):
        """Test _mock_tool_call returns valid result."""
        result = mcp_capability._mock_tool_call(
            tool_name="search",
            arguments={"query": "test"},
        )

        assert result["mock"] is True
        assert result["tool"] == "search"
        assert result["arguments"]["query"] == "test"
        assert "result" in result

    @pytest.mark.asyncio
    async def test_available_tools_property(self, mcp_capability):
        """Test available_tools property."""
        await mcp_capability.initialize()

        # Before listing, cache is empty
        tools = mcp_capability.available_tools
        assert isinstance(tools, list)

        await mcp_capability.shutdown()


class TestMCPTool:
    """Tests for MCPTool wrapper."""

    @pytest.fixture
    def mcp_capability(self):
        """Create MCP capability for tool testing."""
        return MCPCapability()

    def test_tool_creation(self, mcp_capability):
        """Test creating MCPTool."""
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"},
            mcp_capability=mcp_capability,
        )

        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.parameters == {"type": "object"}

    def test_tool_repr(self, mcp_capability):
        """Test tool string representation."""
        tool = MCPTool(
            name="test_tool",
            description="A test tool for testing purposes",
            parameters={},
            mcp_capability=mcp_capability,
        )

        repr_str = repr(tool)
        assert "MCPTool" in repr_str
        assert "test_tool" in repr_str

    @pytest.mark.asyncio
    async def test_tool_call(self, mcp_capability):
        """Test calling tool via wrapper."""
        await mcp_capability.initialize()

        tool = mcp_capability.get_tool("search")
        result = await tool(query="test query")

        # Should return mock result
        assert result is not None

        await mcp_capability.shutdown()


class TestMCPCapabilityIntegration:
    """Integration-style tests for MCPCapability."""

    @pytest.fixture
    def capability(self):
        """Create capability for tests."""
        return MCPCapability(config=MCPConfig(timeout=5.0))

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, capability):
        """Test full capability lifecycle."""
        # Initialize
        await capability.initialize()
        assert capability.is_initialized

        # List tools
        list_result = await capability.list_tools()
        assert list_result.success is True

        # Call a tool
        call_result = await capability.call_tool("search", {"query": "test"})
        assert call_result.success is True

        # Shutdown
        await capability.shutdown()
        assert not capability.is_initialized

    @pytest.mark.asyncio
    async def test_convenience_methods(self, capability):
        """Test convenience method wrappers."""
        await capability.initialize()

        # Test list_tools convenience method
        result = await capability.list_tools()
        assert result.capability == "mcp"

        # Test call_tool convenience method
        result = await capability.call_tool("test", {})
        assert result.capability == "mcp"

        await capability.shutdown()
