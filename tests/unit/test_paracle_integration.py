"""Tests for Paracle integration capability.

Tests the ParacleCapability which provides unified access to:
- Paracle REST API
- Paracle tools (git, code analysis, testing)
- MCP integration
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from paracle_meta.capabilities.paracle_integration import (
    ParacleCapability,
    ParacleConfig,
)


class TestParacleConfig:
    """Tests for ParacleConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ParacleConfig()

        assert config.api_base_url == "http://localhost:8000/v1"
        assert config.api_token is None
        assert config.enable_api is True
        assert config.enable_tools is True
        assert config.enable_mcp is True
        assert config.allowed_paths == ["."]

    def test_custom_config(self):
        """Test custom configuration."""
        config = ParacleConfig(
            api_base_url="http://api.example.com/v1",
            api_token="secret-token",
            enable_api=True,
            enable_tools=False,
            enable_mcp=False,
            allowed_paths=["/app", "/data"],
        )

        assert config.api_base_url == "http://api.example.com/v1"
        assert config.api_token == "secret-token"
        assert config.enable_tools is False
        assert config.enable_mcp is False
        assert config.allowed_paths == ["/app", "/data"]


class TestParacleCapability:
    """Tests for ParacleCapability."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ParacleConfig(
            api_base_url="http://localhost:8000/v1",
            enable_api=True,
            enable_tools=False,  # Disable for unit tests
            enable_mcp=False,  # Disable for unit tests
        )

    @pytest.fixture
    def capability(self, config):
        """Create capability instance."""
        return ParacleCapability(config)

    def test_init(self, capability):
        """Test capability initialization."""
        assert capability.name == "paracle"
        assert (
            capability.description
            == "Unified access to Paracle API, tools, and MCP integration"
        )
        assert capability._api_client is None
        assert capability._tool_registry is None
        assert capability._mcp is None

    @pytest.mark.asyncio
    async def test_initialize_api_client(self, capability):
        """Test API client initialization."""
        with patch(
            "paracle_meta.capabilities.paracle_integration.HTTPX_AVAILABLE", True
        ):
            with patch(
                "paracle_meta.capabilities.paracle_integration.httpx"
            ) as mock_httpx:
                mock_client = AsyncMock()
                mock_httpx.AsyncClient.return_value = mock_client

                await capability.initialize()

                assert capability._initialized is True
                mock_httpx.AsyncClient.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown(self, capability):
        """Test capability shutdown."""
        mock_client = AsyncMock()
        capability._api_client = mock_client
        capability._initialized = True

        await capability.shutdown()

        mock_client.aclose.assert_called_once()
        assert capability._api_client is None
        assert capability._initialized is False

    @pytest.mark.asyncio
    async def test_execute_list_tools(self, capability):
        """Test list_tools action."""
        capability._initialized = True
        capability._tool_registry = None
        capability._agent_tools = {
            "git_status": MagicMock(),
            "code_analysis": MagicMock(),
        }
        capability._mcp = None

        result = await capability.execute(action="list_tools")

        assert result.success is True
        assert "agent" in result.output
        assert "git_status" in result.output["agent"]
        assert "code_analysis" in result.output["agent"]

    @pytest.mark.asyncio
    async def test_execute_list_capabilities(self, capability):
        """Test list_capabilities action."""
        capability._initialized = True
        capability._api_client = MagicMock()
        capability._tool_registry = None
        capability._agent_tools = {}
        capability._mcp = None

        result = await capability.execute(action="list_capabilities")

        assert result.success is True
        assert result.output["api"] is True
        assert result.output["tools"] is False

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, capability):
        """Test unknown action error."""
        capability._initialized = True

        result = await capability.execute(action="unknown_action")

        assert result.success is False
        assert "Unknown action" in result.error

    @pytest.mark.asyncio
    async def test_api_list_agents(self, capability):
        """Test API list agents."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"agents": [{"id": "coder", "name": "Coder"}]}
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        capability._initialized = True
        capability._api_client = mock_client

        result = await capability.api_list_agents()

        assert result.success is True
        mock_client.get.assert_called_with("/agents")

    @pytest.mark.asyncio
    async def test_api_get_agent(self, capability):
        """Test API get agent by ID."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "coder", "name": "Coder Agent"}
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        capability._initialized = True
        capability._api_client = mock_client

        result = await capability.api_get_agent("coder")

        assert result.success is True
        mock_client.get.assert_called_with("/agents/coder")

    @pytest.mark.asyncio
    async def test_api_health(self, capability):
        """Test API health check."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        capability._initialized = True
        capability._api_client = mock_client

        result = await capability.api_health()

        assert result.success is True
        mock_client.get.assert_called_with("/health")

    @pytest.mark.asyncio
    async def test_execute_tool(self, capability):
        """Test tool execution."""
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {"status": "success", "output": "test result"}

        capability._initialized = True
        capability._agent_tools = {"test_tool": mock_tool}

        result = await capability.execute_tool("test_tool", arg1="value1")

        assert result.success is True
        mock_tool.execute.assert_called_with(arg1="value1")

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, capability):
        """Test tool not found error."""
        capability._initialized = True
        capability._agent_tools = {}
        capability._tool_registry = None

        result = await capability.execute_tool("nonexistent_tool")

        assert result.success is False
        assert "Tool not found" in result.error

    @pytest.mark.asyncio
    async def test_is_api_available(self, capability):
        """Test API availability check."""
        assert capability.is_api_available is False

        capability._api_client = MagicMock()
        assert capability.is_api_available is True

    @pytest.mark.asyncio
    async def test_is_tools_available(self, capability):
        """Test tools availability check."""
        assert capability.is_tools_available is False

        capability._agent_tools = {"git_status": MagicMock()}
        assert capability.is_tools_available is True

    @pytest.mark.asyncio
    async def test_available_tools(self, capability):
        """Test getting available tool names."""
        capability._agent_tools = {
            "git_status": MagicMock(),
            "code_analysis": MagicMock(),
        }
        capability._tool_registry = None

        tools = capability.available_tools

        assert "git_status" in tools
        assert "code_analysis" in tools


class TestParacleCapabilityWithMCP:
    """Tests for ParacleCapability MCP integration."""

    @pytest.fixture
    def config(self):
        """Create test configuration with MCP enabled."""
        return ParacleConfig(
            enable_api=False,
            enable_tools=False,
            enable_mcp=True,
            mcp_server_url="http://localhost:3000",
        )

    @pytest.fixture
    def capability(self, config):
        """Create capability instance."""
        return ParacleCapability(config)

    @pytest.mark.asyncio
    async def test_mcp_list_tools(self, capability):
        """Test MCP list tools."""
        mock_mcp = AsyncMock()
        mock_mcp.list_tools.return_value = MagicMock(
            success=True,
            output=[{"name": "search", "description": "Search tool"}],
        )

        capability._initialized = True
        capability._mcp = mock_mcp

        result = await capability.mcp_list_tools()

        assert result.success is True

    @pytest.mark.asyncio
    async def test_mcp_call(self, capability):
        """Test MCP tool call."""
        mock_mcp = AsyncMock()
        mock_mcp.call_tool.return_value = MagicMock(
            success=True,
            output={"result": "search results"},
        )

        capability._initialized = True
        capability._mcp = mock_mcp

        result = await capability.mcp_call("search", {"query": "test"})

        assert result.success is True
        mock_mcp.call_tool.assert_called_with("search", {"query": "test"})

    @pytest.mark.asyncio
    async def test_is_mcp_available(self, capability):
        """Test MCP availability check."""
        assert capability.is_mcp_available is False

        mock_mcp = MagicMock()
        mock_mcp.is_connected = True
        capability._mcp = mock_mcp

        assert capability.is_mcp_available is True


class TestParacleCapabilityConvenienceMethods:
    """Tests for convenience methods."""

    @pytest.fixture
    def capability(self):
        """Create capability instance."""
        config = ParacleConfig(enable_tools=False, enable_mcp=False)
        return ParacleCapability(config)

    @pytest.mark.asyncio
    async def test_git_status(self, capability):
        """Test git_status convenience method."""
        mock_result = MagicMock(success=True, output={"branch": "main"})

        capability._initialized = True
        capability._agent_tools = {
            "git_status": AsyncMock(execute=AsyncMock(return_value=mock_result.output))
        }

        # The method routes through execute_tool
        result = await capability.execute_tool("git_status", cwd=".")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_git_diff(self, capability):
        """Test git_diff convenience method."""
        mock_result = MagicMock(success=True, output="diff content")

        capability._initialized = True
        capability._agent_tools = {
            "git_diff": AsyncMock(execute=AsyncMock(return_value=mock_result.output))
        }

        result = await capability.execute_tool("git_diff", cwd=".")

        assert result.success is True
