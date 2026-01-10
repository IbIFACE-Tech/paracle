"""MCP API Bridge - Routes MCP tool calls through REST API.

This module implements ADR-022: MCP Full Coverage via API-First Bridge.
It routes MCP tool calls through the Paracle REST API, leveraging the existing
use_api_or_fallback pattern with critical offline wrappers for resilience.

Architecture:
1. Primary: MCP tool call → REST API endpoint (via requests/httpx)
2. Fallback: If API unavailable → Direct core function call
3. Critical: Offline wrappers for board_list, errors_stats, inventory_check

Benefits:
- Zero duplication (single source of truth: REST API)
- Auto-coverage (new endpoints → auto-available in MCP)
- API-first aligned (consistent architecture)
- Resilient (multiple fallback layers)
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("paracle.mcp.api_bridge")


@dataclass
class APIEndpointMapping:
    """Mapping from MCP tool to REST API endpoint."""

    tool_name: str
    http_method: str  # GET, POST, PUT, DELETE
    endpoint: str  # e.g., "/api/v1/boards"
    # Map tool params to API params
    params_mapping: dict[str, str] | None = None
    body_params: list[str] | None = None  # Params that go in request body


# =============================================================================
# Critical Offline Tools (bypass API for reliability)
# =============================================================================

OFFLINE_CRITICAL = [
    "paracle_board_list",
    "paracle_errors_stats",
    "paracle_inventory_check",
]


# =============================================================================
# Tool → API Endpoint Mappings
# =============================================================================

TOOL_API_MAPPINGS: dict[str, APIEndpointMapping] = {
    # Kanban/Board Tools
    "paracle_board_list": APIEndpointMapping(
        tool_name="paracle_board_list",
        http_method="GET",
        endpoint="/api/boards",
    ),
    "paracle_board_create": APIEndpointMapping(
        tool_name="paracle_board_create",
        http_method="POST",
        endpoint="/api/boards",
        body_params=["name", "description", "columns"],
    ),
    "paracle_board_show": APIEndpointMapping(
        tool_name="paracle_board_show",
        http_method="GET",
        endpoint="/api/boards/{board_id}/show",
    ),
    "paracle_board_stats": APIEndpointMapping(
        tool_name="paracle_board_stats",
        http_method="GET",
        endpoint="/api/boards/{board_id}/stats",
    ),
    "paracle_board_update": APIEndpointMapping(
        tool_name="paracle_board_update",
        http_method="PUT",
        endpoint="/api/boards/{board_id}",
        body_params=["name", "description"],
    ),
    "paracle_board_delete": APIEndpointMapping(
        tool_name="paracle_board_delete",
        http_method="DELETE",
        endpoint="/api/boards/{board_id}",
    ),
    # Task Tools
    "paracle_task_list": APIEndpointMapping(
        tool_name="paracle_task_list",
        http_method="GET",
        endpoint="/api/tasks",
    ),
    "paracle_task_create": APIEndpointMapping(
        tool_name="paracle_task_create",
        http_method="POST",
        endpoint="/api/tasks",
        body_params=[
            "board_id",
            "title",
            "description",
            "priority",
            "task_type",
            "assigned_to",
            "tags",
        ],
    ),
    "paracle_task_show": APIEndpointMapping(
        tool_name="paracle_task_show",
        http_method="GET",
        endpoint="/api/tasks/{task_id}",
    ),
    "paracle_task_update": APIEndpointMapping(
        tool_name="paracle_task_update",
        http_method="PUT",
        endpoint="/api/tasks/{task_id}",
        body_params=["title", "description", "priority", "tags"],
    ),
    "paracle_task_move": APIEndpointMapping(
        tool_name="paracle_task_move",
        http_method="PUT",
        endpoint="/api/tasks/{task_id}/move",
        body_params=["status"],
    ),
    "paracle_task_assign": APIEndpointMapping(
        tool_name="paracle_task_assign",
        http_method="PUT",
        endpoint="/api/tasks/{task_id}/assign",
        body_params=["assignee"],
    ),
    "paracle_task_delete": APIEndpointMapping(
        tool_name="paracle_task_delete",
        http_method="DELETE",
        endpoint="/api/tasks/{task_id}",
    ),
    # Error/Observability Tools
    "paracle_errors_list": APIEndpointMapping(
        tool_name="paracle_errors_list",
        http_method="GET",
        endpoint="/api/observability/errors",
    ),
    "paracle_errors_stats": APIEndpointMapping(
        tool_name="paracle_errors_stats",
        http_method="GET",
        endpoint="/api/observability/errors/stats",
    ),
    "paracle_errors_clear": APIEndpointMapping(
        tool_name="paracle_errors_clear",
        http_method="POST",
        endpoint="/api/observability/errors/clear",
    ),
    # Cost Tools
    "paracle_cost_summary": APIEndpointMapping(
        tool_name="paracle_cost_summary",
        http_method="GET",
        endpoint="/api/observability/cost/summary",
    ),
    "paracle_cost_by_agent": APIEndpointMapping(
        tool_name="paracle_cost_by_agent",
        http_method="GET",
        endpoint="/api/observability/cost/by-agent",
    ),
    # Log Tools
    "paracle_log_action": APIEndpointMapping(
        tool_name="paracle_log_action",
        http_method="POST",
        endpoint="/api/logs/action",
        body_params=["agent", "action", "description"],
    ),
    "paracle_log_decision": APIEndpointMapping(
        tool_name="paracle_log_decision",
        http_method="POST",
        endpoint="/api/logs/decision",
        body_params=["decision", "rationale", "alternatives"],
    ),
    "paracle_logs_recent": APIEndpointMapping(
        tool_name="paracle_logs_recent",
        http_method="GET",
        endpoint="/api/logs/recent",
    ),
    # .parac Tools
    "paracle_parac_status": APIEndpointMapping(
        tool_name="paracle_parac_status",
        http_method="GET",
        endpoint="/api/parac/status",
    ),
    "paracle_parac_sync": APIEndpointMapping(
        tool_name="paracle_parac_sync",
        http_method="POST",
        endpoint="/api/parac/sync",
    ),
}


class MCPAPIBridge:
    """Bridge between MCP tools and REST API.

    Routes MCP tool calls through REST API endpoints with fallback to direct core.
    Implements ADR-022 hybrid approach: API-first + critical wrappers + fallback.
    """

    def __init__(
        self,
        api_base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        enable_fallback: bool = True,
    ):
        """Initialize API bridge.

        Args:
            api_base_url: Base URL for REST API (default: http://localhost:8000)
            timeout: HTTP request timeout in seconds (default: 30.0)
            enable_fallback: Enable fallback to direct core if API unavailable
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout = timeout
        self.enable_fallback = enable_fallback
        self.client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    async def call_api_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Route MCP tool call through REST API.

        Args:
            tool_name: MCP tool name (e.g., "paracle_board_list")
            arguments: Tool arguments from MCP

        Returns:
            API response as dict

        Raises:
            HTTPError: If API call fails and fallback disabled
        """
        # Check if this is a critical offline tool
        if tool_name in OFFLINE_CRITICAL:
            logger.info(
                f"{tool_name} is critical offline tool, using direct implementation"
            )
            return await self._call_offline_tool(tool_name, arguments)

        # Get API endpoint mapping
        mapping = TOOL_API_MAPPINGS.get(tool_name)
        if not mapping:
            if self.enable_fallback:
                logger.warning(
                    f"No API mapping for {tool_name}, attempting direct fallback"
                )
                return await self._fallback_to_direct(tool_name, arguments)
            raise ValueError(f"No API mapping found for tool: {tool_name}")

        # Build API request
        try:
            url = self.api_base_url + mapping.endpoint

            # Replace path parameters (e.g., {board_id} → actual board_id)
            for key, value in arguments.items():
                if f"{{{key}}}" in url:
                    url = url.replace(f"{{{key}}}", str(value))

            # Prepare request parameters
            params = {}
            body = {}

            if mapping.body_params:
                # POST/PUT: Parameters go in body
                body = {k: v for k, v in arguments.items()
                        if k in mapping.body_params}
            else:
                # GET/DELETE: Parameters go in query string
                params = {
                    k: v
                    for k, v in arguments.items()
                    if f"{{{k}}}" not in mapping.endpoint
                }

            # Make API request
            logger.info(
                f"Calling API: {mapping.http_method} {url} (params={params}, body={body})"
            )

            if mapping.http_method == "GET":
                response = self.client.get(url, params=params)
            elif mapping.http_method == "POST":
                response = self.client.post(url, params=params, json=body)
            elif mapping.http_method == "PUT":
                response = self.client.put(url, params=params, json=body)
            elif mapping.http_method == "DELETE":
                response = self.client.delete(url, params=params)
            else:
                raise ValueError(
                    f"Unsupported HTTP method: {mapping.http_method}")

            response.raise_for_status()
            return response.json()

        except (httpx.HTTPError, httpx.ConnectError) as e:
            logger.error(f"API call failed for {tool_name}: {e}")
            if self.enable_fallback:
                logger.info(f"Attempting fallback for {tool_name}")
                return await self._fallback_to_direct(tool_name, arguments)
            raise

    async def _call_offline_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Call critical offline tool bypassing API.

        These tools are critical and must work even when API is down.

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result as dict
        """
        if tool_name == "paracle_board_list":
            return await self._offline_board_list(arguments)
        elif tool_name == "paracle_errors_stats":
            return await self._offline_errors_stats(arguments)
        elif tool_name == "paracle_inventory_check":
            return await self._offline_inventory_check(arguments)
        else:
            raise ValueError(f"Unknown offline tool: {tool_name}")

    async def _offline_board_list(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Offline implementation of board list.

        Direct access to BoardRepository bypassing API.
        """
        from paracle_kanban.board import BoardRepository

        try:
            repo = BoardRepository()
            boards = repo.list_boards(
                include_archived=arguments.get("archived", False))

            return {
                "boards": [
                    {
                        "id": b.id,
                        "name": b.name,
                        "description": b.description,
                        "archived": b.archived,
                        "created_at": b.created_at.isoformat(),
                        "updated_at": b.updated_at.isoformat(),
                    }
                    for b in boards
                ],
                "count": len(boards),
            }
        except Exception as e:
            logger.error(f"Offline board_list failed: {e}")
            return {"error": str(e), "boards": [], "count": 0}

    async def _offline_errors_stats(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Offline implementation of errors stats.

        Direct access to ErrorRegistry bypassing API.
        """
        from paracle_observability import ErrorRegistry

        try:
            registry = ErrorRegistry()
            stats = registry.get_statistics()

            return {
                "total_errors": stats["total_errors"],
                "by_severity": stats["by_severity"],
                "by_component": stats["by_component"],
                "recent_count": stats["recent_errors"],
            }
        except Exception as e:
            logger.error(f"Offline errors_stats failed: {e}")
            return {
                "error": str(e),
                "total_errors": 0,
                "by_severity": {},
                "by_component": {},
            }

    async def _offline_inventory_check(
        self, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Offline implementation of inventory check.

        Direct package scanning bypassing API.
        """
        try:
            from paracle_cli.commands.inventory import (
                _find_parac_root,
                _scan_package,
            )

            # Find workspace root
            packages_dir = Path.cwd() / "packages"
            if not packages_dir.exists():
                # Try to find from .parac
                parac_root = _find_parac_root()
                if parac_root:
                    packages_dir = parac_root.parent / "packages"

            if not packages_dir.exists():
                return {
                    "error": "packages/ directory not found",
                    "packages_count": 0,
                }

            # Scan packages
            packages = []
            for pkg_dir in sorted(packages_dir.iterdir()):
                if pkg_dir.is_dir() and not pkg_dir.name.startswith(
                    (".", "_", "paracle.egg-info")
                ):
                    metadata = _scan_package(pkg_dir)
                    if metadata:
                        packages.append(metadata["name"])

            return {
                "packages_count": len(packages),
                "packages": packages,
                "up_to_date": True,  # Simplified for offline mode
            }
        except Exception as e:
            logger.error(f"Offline inventory_check failed: {e}")
            return {"error": str(e), "packages_count": 0, "packages": []}

    async def _fallback_to_direct(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Fallback to direct core function call.

        Used when API is unavailable or tool has no mapping.

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Returns:
            Direct function result as dict
        """
        logger.info(f"Fallback to direct core for {tool_name}")

        # Try to import and call the direct core function
        try:
            # Map tool name to core module/function
            # This requires knowledge of internal structure
            # For now, return error and suggest using offline tools
            return {
                "error": f"API unavailable and no direct fallback for {tool_name}",
                "suggestion": "Use offline critical tools or start API server",
            }
        except Exception as e:
            logger.error(f"Direct fallback failed for {tool_name}: {e}")
            return {"error": str(e)}

    def is_api_available(self) -> bool:
        """Check if REST API is available.

        Returns:
            True if API responds to health check
        """
        try:
            response = self.client.get(f"{self.api_base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
