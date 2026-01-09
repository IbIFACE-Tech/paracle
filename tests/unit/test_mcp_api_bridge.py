"""Tests for MCP API Bridge (ADR-022).

Tests the hybrid API-first + critical wrappers approach for MCP full coverage.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add packages to path for imports BEFORE importing paracle modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages"))

from paracle_mcp.api_bridge import (  # noqa: E402
    OFFLINE_CRITICAL,
    TOOL_API_MAPPINGS,
    APIEndpointMapping,
    MCPAPIBridge,
)


@pytest.fixture
def api_bridge():
    """Create API bridge instance for testing."""
    bridge = MCPAPIBridge(
        api_base_url="http://localhost:8000",
        timeout=10.0,
        enable_fallback=True
    )
    yield bridge
    bridge.close()


@pytest.fixture
def mock_http_client():
    """Mock httpx Client."""
    with patch("paracle_mcp.api_bridge.httpx.Client") as mock_client:
        yield mock_client


class TestAPIEndpointMapping:
    """Test API endpoint mapping structure."""

    def test_tool_mappings_exist(self):
        """Verify core tool mappings are defined."""
        assert "paracle_board_list" in TOOL_API_MAPPINGS
        assert "paracle_task_create" in TOOL_API_MAPPINGS
        assert "paracle_errors_stats" in TOOL_API_MAPPINGS
        assert "paracle_log_action" in TOOL_API_MAPPINGS

    def test_mapping_structure(self):
        """Verify mapping structure is correct."""
        mapping = TOOL_API_MAPPINGS["paracle_board_list"]
        assert isinstance(mapping, APIEndpointMapping)
        assert mapping.tool_name == "paracle_board_list"
        assert mapping.http_method == "GET"
        assert mapping.endpoint == "/api/boards"

    def test_post_mapping_has_body_params(self):
        """Verify POST mappings define body parameters."""
        mapping = TOOL_API_MAPPINGS["paracle_task_create"]
        assert mapping.http_method == "POST"
        assert mapping.body_params is not None
        assert "title" in mapping.body_params
        assert "board_id" in mapping.body_params


class TestOfflineCriticalTools:
    """Test critical offline tools."""

    def test_critical_tools_defined(self):
        """Verify critical tools are marked offline."""
        assert "paracle_board_list" in OFFLINE_CRITICAL
        assert "paracle_errors_stats" in OFFLINE_CRITICAL
        assert "paracle_inventory_check" in OFFLINE_CRITICAL

    @pytest.mark.asyncio
    async def test_offline_board_list(self, api_bridge):
        """Test offline board list bypasses API."""
        with patch("paracle_mcp.api_bridge.BoardRepository") as mock_repo:
            # Mock repository response
            mock_board = Mock()
            mock_board.id = "test-board-1"
            mock_board.name = "Test Board"
            mock_board.description = "Test description"
            mock_board.archived = False
            mock_board.created_at = "2026-01-10T10:00:00"
            mock_board.updated_at = "2026-01-10T10:00:00"

            mock_repo.return_value.list_boards.return_value = [mock_board]

            # Call offline tool
            result = await api_bridge.call_api_tool(
                "paracle_board_list",
                {"archived": False}
            )

            assert "boards" in result
            assert result["count"] == 1
            assert result["boards"][0]["name"] == "Test Board"

    @pytest.mark.asyncio
    async def test_offline_errors_stats(self, api_bridge):
        """Test offline errors stats bypasses API."""
        with patch("paracle_mcp.api_bridge.ErrorRegistry") as mock_registry:
            # Mock registry response
            mock_registry.return_value.get_statistics.return_value = {
                "total_errors": 5,
                "by_severity": {"ERROR": 3, "WARNING": 2},
                "by_component": {"api": 2, "cli": 3},
                "recent_errors": 2
            }

            result = await api_bridge.call_api_tool(
                "paracle_errors_stats",
                {}
            )

            assert result["total_errors"] == 5
            assert result["by_severity"]["ERROR"] == 3
            assert result["recent_count"] == 2


class TestAPIBridge:
    """Test API bridge routing and fallback."""

    def test_initialization(self, api_bridge):
        """Test bridge initializes correctly."""
        assert api_bridge.api_base_url == "http://localhost:8000"
        assert api_bridge.timeout == 10.0
        assert api_bridge.enable_fallback is True
        assert api_bridge.client is not None

    def test_is_api_available(self, api_bridge):
        """Test API availability check."""
        with patch.object(api_bridge.client, "get") as mock_get:
            mock_get.return_value.status_code = 200
            assert api_bridge.is_api_available() is True

            mock_get.side_effect = Exception("Connection refused")
            assert api_bridge.is_api_available() is False

    @pytest.mark.asyncio
    async def test_call_api_tool_success(self, api_bridge):
        """Test successful API tool call."""
        with patch.object(api_bridge.client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "boards": [],
                "count": 0
            }
            mock_get.return_value = mock_response

            # Call non-critical tool (should use API)
            with patch("paracle_mcp.api_bridge.OFFLINE_CRITICAL", []):
                result = await api_bridge.call_api_tool(
                    "paracle_board_list",
                    {"archived": False}
                )

            assert "boards" in result
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_api_tool_with_path_params(self, api_bridge):
        """Test API call with path parameters."""
        with patch.object(api_bridge.client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "board-123", "name": "Test"}
            mock_get.return_value = mock_response

            with patch("paracle_mcp.api_bridge.OFFLINE_CRITICAL", []):
                result = await api_bridge.call_api_tool(
                    "paracle_board_show",
                    {"board_id": "board-123"}
                )

            # Verify path parameter was substituted
            call_args = mock_get.call_args
            assert "board-123" in str(call_args)

    @pytest.mark.asyncio
    async def test_call_api_tool_post_with_body(self, api_bridge):
        """Test POST API call with body parameters."""
        with patch.object(api_bridge.client, "post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "task-1", "title": "New Task"}
            mock_post.return_value = mock_response

            with patch("paracle_mcp.api_bridge.OFFLINE_CRITICAL", []):
                result = await api_bridge.call_api_tool(
                    "paracle_task_create",
                    {
                        "board_id": "board-1",
                        "title": "New Task",
                        "description": "Test task",
                        "priority": "high"
                    }
                )

            assert result["title"] == "New Task"
            # Verify body was sent
            call_kwargs = mock_post.call_args.kwargs
            assert "json" in call_kwargs

    @pytest.mark.asyncio
    async def test_fallback_on_api_failure(self, api_bridge):
        """Test fallback to direct core when API fails."""
        with patch.object(api_bridge.client, "get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            with patch("paracle_mcp.api_bridge.OFFLINE_CRITICAL", []):
                result = await api_bridge.call_api_tool(
                    "paracle_board_list",
                    {}
                )

            # Should return fallback error message
            assert "error" in result or "suggestion" in result

    @pytest.mark.asyncio
    async def test_no_fallback_when_disabled(self, api_bridge):
        """Test that fallback can be disabled."""
        api_bridge.enable_fallback = False

        with patch.object(api_bridge.client, "get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            with pytest.raises(Exception):
                await api_bridge.call_api_tool(
                    "paracle_task_list",
                    {}
                )


class TestMappingCoverage:
    """Test that all expected endpoints have mappings."""

    def test_kanban_endpoints_covered(self):
        """Verify all Kanban endpoints are mapped."""
        expected_tools = [
            "paracle_board_list",
            "paracle_board_create",
            "paracle_board_show",
            "paracle_board_stats",
            "paracle_board_update",
            "paracle_board_delete",
            "paracle_task_list",
            "paracle_task_create",
            "paracle_task_show",
            "paracle_task_update",
            "paracle_task_move",
            "paracle_task_assign",
            "paracle_task_delete",
        ]

        for tool in expected_tools:
            assert tool in TOOL_API_MAPPINGS, f"Missing mapping: {tool}"

    def test_observability_endpoints_covered(self):
        """Verify observability endpoints are mapped."""
        expected_tools = [
            "paracle_errors_list",
            "paracle_errors_stats",
            "paracle_errors_clear",
            "paracle_cost_summary",
            "paracle_cost_by_agent",
        ]

        for tool in expected_tools:
            assert tool in TOOL_API_MAPPINGS, f"Missing mapping: {tool}"

    def test_log_endpoints_covered(self):
        """Verify log endpoints are mapped."""
        expected_tools = [
            "paracle_log_action",
            "paracle_log_decision",
            "paracle_logs_recent",
        ]

        for tool in expected_tools:
            assert tool in TOOL_API_MAPPINGS, f"Missing mapping: {tool}"


class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_api_call_respects_timeout(self, api_bridge):
        """Verify timeout is enforced."""
        api_bridge.timeout = 0.1  # Very short timeout

        with patch.object(api_bridge.client, "get") as mock_get:
            import time

            def slow_response(*args, **kwargs):
                time.sleep(1)  # Longer than timeout
                return Mock(status_code=200, json=lambda: {})

            mock_get.side_effect = slow_response

            # Should timeout and fallback
            with patch("paracle_mcp.api_bridge.OFFLINE_CRITICAL", []):
                result = await api_bridge.call_api_tool(
                    "paracle_board_list",
                    {}
                )

            # Should have fallback error
            assert "error" in result or "suggestion" in result


@pytest.mark.integration
class TestAPIBridgeIntegration:
    """Integration tests (require running API server)."""

    @pytest.mark.skipif(
        True,  # Skip by default - requires API server
        reason="Requires running Paracle API server"
    )
    @pytest.mark.asyncio
    async def test_real_api_call(self):
        """Test real API call (requires API server running)."""
        bridge = MCPAPIBridge(api_base_url="http://localhost:8000")

        try:
            if not bridge.is_api_available():
                pytest.skip("API server not available")

            result = await bridge.call_api_tool(
                "paracle_parac_status",
                {}
            )

            assert "status" in result or "error" in result
        finally:
            bridge.close()
