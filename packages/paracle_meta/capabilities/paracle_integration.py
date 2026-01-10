"""Paracle framework integration capability for MetaAgent.

Provides unified access to:
- Paracle REST API (agents, workflows, tools, observability)
- Paracle built-in tools (filesystem, git, terminal, etc.)
- MCP tools integration
- Tool registry management

This capability bridges paracle_meta with the core Paracle framework,
enabling the meta-agent to leverage all framework features.

Example:
    >>> from paracle_meta.capabilities.paracle_integration import (
    ...     ParacleCapability, ParacleConfig
    ... )
    >>>
    >>> # Create with API and tools enabled
    >>> config = ParacleConfig(
    ...     api_base_url="http://localhost:8000/v1",
    ...     enable_tools=True,
    ...     allowed_paths=["./project"],
    ... )
    >>> paracle = ParacleCapability(config)
    >>> await paracle.initialize()
    >>>
    >>> # Use the API
    >>> agents = await paracle.api_list_agents()
    >>> print(agents.output)
    >>>
    >>> # Use tools
    >>> result = await paracle.execute_tool("git_status")
    >>> print(result.output)
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)

if TYPE_CHECKING:
    from paracle_tools.builtin.base import ToolResult

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class ParacleConfig(CapabilityConfig):
    """Configuration for Paracle integration capability.

    Attributes:
        api_base_url: Base URL for Paracle REST API.
        api_token: JWT token for authentication (optional).
        enable_api: Whether to enable API access.
        enable_tools: Whether to enable tool access.
        enable_mcp: Whether to enable MCP integration.
        allowed_paths: Allowed filesystem paths for tools.
        allowed_commands: Allowed shell commands.
        mcp_server_url: MCP server URL (if enabled).
    """

    # API configuration
    api_base_url: str = Field(
        default="http://localhost:8000/v1",
        description="Base URL for Paracle REST API",
    )
    api_token: str | None = Field(
        default=None,
        description="JWT token for API authentication",
    )
    enable_api: bool = Field(
        default=True,
        description="Enable Paracle API access",
    )

    # Tools configuration
    enable_tools: bool = Field(
        default=True,
        description="Enable Paracle tools access",
    )
    allowed_paths: list[str] = Field(
        default_factory=lambda: ["."],
        description="Allowed filesystem paths for tools",
    )
    allowed_commands: list[str] = Field(
        default_factory=lambda: ["git", "ls", "cat", "grep", "find", "echo"],
        description="Allowed shell commands",
    )

    # MCP configuration
    enable_mcp: bool = Field(
        default=True,
        description="Enable MCP integration",
    )
    mcp_server_url: str = Field(
        default="http://localhost:3000",
        description="MCP server URL",
    )


class ParacleCapability(BaseCapability):
    """Unified Paracle framework integration capability.

    Provides access to:
    - REST API: agents, workflows, tools, observability endpoints
    - Built-in tools: filesystem, git, terminal, code analysis
    - MCP tools: external tool integration via Model Context Protocol

    This is the primary way for paracle_meta to interact with the
    broader Paracle ecosystem.

    Example:
        >>> paracle = ParacleCapability()
        >>> await paracle.initialize()
        >>>
        >>> # List agents via API
        >>> result = await paracle.execute(action="api_list_agents")
        >>>
        >>> # Execute a git status tool
        >>> result = await paracle.execute(action="tool", tool_name="git_status")
        >>>
        >>> # Call an MCP tool
        >>> result = await paracle.execute(
        ...     action="mcp_call",
        ...     tool_name="search",
        ...     arguments={"query": "Python"}
        ... )
    """

    name = "paracle"
    description = "Unified access to Paracle API, tools, and MCP integration"

    def __init__(self, config: ParacleConfig | None = None):
        """Initialize Paracle capability.

        Args:
            config: Paracle configuration
        """
        super().__init__(config or ParacleConfig())
        self.config: ParacleConfig = self.config

        # HTTP client for API
        self._api_client: httpx.AsyncClient | None = None

        # Tool registry
        self._tool_registry: Any = None  # BuiltinToolRegistry
        self._agent_tools: dict[str, Any] = {}  # Agent-specific tools

        # MCP capability (reuse existing)
        self._mcp: Any = None

    async def initialize(self) -> None:
        """Initialize all integrations."""
        # Initialize API client
        if self.config.enable_api:
            await self._init_api_client()

        # Initialize tools
        if self.config.enable_tools:
            await self._init_tools()

        # Initialize MCP
        if self.config.enable_mcp:
            await self._init_mcp()

        await super().initialize()

    async def _init_api_client(self) -> None:
        """Initialize HTTP client for API access."""
        if not HTTPX_AVAILABLE:
            return

        headers = {"Content-Type": "application/json"}
        if self.config.api_token:
            headers["Authorization"] = f"Bearer {self.config.api_token}"

        self._api_client = httpx.AsyncClient(
            base_url=self.config.api_base_url,
            timeout=self.config.timeout,
            headers=headers,
        )

    async def _init_tools(self) -> None:
        """Initialize Paracle tools."""
        try:
            from paracle_tools import BuiltinToolRegistry

            self._tool_registry = BuiltinToolRegistry(
                filesystem_paths=self.config.allowed_paths,
                allowed_commands=self.config.allowed_commands,
            )

            # Load agent-specific tools
            await self._load_agent_tools()

        except ImportError:
            # paracle_tools not available
            pass

    async def _load_agent_tools(self) -> None:
        """Load agent-specific tool instances."""
        try:
            from paracle_tools import (
                code_analysis,
                code_generation,
                code_review,
                coverage_analysis,
                diagram_generation,
                git_status,
                git_diff,
                git_log,
                git_add,
                git_commit,
                git_branch,
                git_checkout,
                markdown_generation,
                pattern_matching,
                refactoring,
                security_scan,
                static_analysis,
                task_tracking,
                terminal_execute,
                terminal_info,
                test_execution,
                test_generation,
                version_management,
                changelog_generation,
            )

            # Register tools by name
            self._agent_tools = {
                # Architect tools
                "code_analysis": code_analysis,
                "diagram_generation": diagram_generation,
                "pattern_matching": pattern_matching,
                # Coder tools
                "code_generation": code_generation,
                "refactoring": refactoring,
                # Reviewer tools
                "static_analysis": static_analysis,
                "security_scan": security_scan,
                "code_review": code_review,
                # Tester tools
                "test_generation": test_generation,
                "test_execution": test_execution,
                "coverage_analysis": coverage_analysis,
                # PM tools
                "task_tracking": task_tracking,
                # Documenter tools
                "markdown_generation": markdown_generation,
                # Git tools
                "git_status": git_status,
                "git_diff": git_diff,
                "git_log": git_log,
                "git_add": git_add,
                "git_commit": git_commit,
                "git_branch": git_branch,
                "git_checkout": git_checkout,
                # Terminal tools
                "terminal_execute": terminal_execute,
                "terminal_info": terminal_info,
                # Release tools
                "version_management": version_management,
                "changelog_generation": changelog_generation,
            }

        except ImportError:
            pass

    async def _init_mcp(self) -> None:
        """Initialize MCP integration."""
        try:
            from paracle_meta.capabilities.mcp_integration import (
                MCPCapability,
                MCPConfig,
            )

            mcp_config = MCPConfig(
                server_url=self.config.mcp_server_url,
                timeout=self.config.timeout,
            )
            self._mcp = MCPCapability(mcp_config)
            await self._mcp.initialize()

        except Exception:
            # MCP not available or failed to connect
            pass

    async def shutdown(self) -> None:
        """Cleanup all integrations."""
        if self._api_client:
            await self._api_client.aclose()
            self._api_client = None

        if self._mcp:
            await self._mcp.shutdown()
            self._mcp = None

        await super().shutdown()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute Paracle capability.

        Args:
            action: Action to perform. Options:
                - api_*: API actions (api_list_agents, api_get_agent, etc.)
                - tool: Execute a Paracle tool
                - mcp_*: MCP actions (mcp_list_tools, mcp_call, etc.)
                - list_tools: List all available tools
            **kwargs: Action-specific parameters

        Returns:
            CapabilityResult with execution outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "list_tools")
        start_time = time.time()

        try:
            # Route to appropriate handler
            if action.startswith("api_"):
                result = await self._handle_api_action(action, **kwargs)
            elif action == "tool":
                result = await self._handle_tool_action(**kwargs)
            elif action.startswith("mcp_"):
                result = await self._handle_mcp_action(action, **kwargs)
            elif action == "list_tools":
                result = await self._list_all_tools()
            elif action == "list_capabilities":
                result = self._list_capabilities()
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

    # =========================================================================
    # API Actions
    # =========================================================================

    async def _handle_api_action(self, action: str, **kwargs) -> Any:
        """Handle API actions."""
        if not self._api_client:
            raise RuntimeError("API client not initialized")

        # Map action names to API endpoints
        api_actions = {
            "api_list_agents": ("GET", "/agents"),
            "api_get_agent": ("GET", "/agents/{agent_id}"),
            "api_get_agent_spec": ("GET", "/agents/{agent_id}/spec"),
            "api_list_workflows": ("GET", "/workflows"),
            "api_get_workflow": ("GET", "/workflows/{workflow_id}"),
            "api_execute_workflow": ("POST", "/workflows/{workflow_id}/execute"),
            "api_list_tools": ("GET", "/tools"),
            "api_get_tool": ("GET", "/tools/{tool_id}"),
            "api_health": ("GET", "/health"),
            "api_metrics": ("GET", "/observability/metrics"),
            "api_traces": ("GET", "/observability/traces"),
            "api_kanban": ("GET", "/kanban/boards"),
            "api_approvals": ("GET", "/approvals/pending"),
        }

        if action not in api_actions:
            raise ValueError(f"Unknown API action: {action}")

        method, path_template = api_actions[action]

        # Substitute path parameters
        path = path_template.format(**kwargs)

        # Make request
        if method == "GET":
            response = await self._api_client.get(path)
        elif method == "POST":
            body = kwargs.get("body", {})
            response = await self._api_client.post(path, json=body)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Tool Actions
    # =========================================================================

    async def _handle_tool_action(self, **kwargs) -> Any:
        """Handle tool execution."""
        tool_name = kwargs.pop("tool_name", None)
        if not tool_name:
            raise ValueError("tool_name is required")

        # Try agent tools first
        if tool_name in self._agent_tools:
            tool = self._agent_tools[tool_name]
            return await tool.execute(**kwargs)

        # Then try builtin registry
        if self._tool_registry:
            return await self._tool_registry.execute_tool(tool_name, **kwargs)

        raise ValueError(f"Tool not found: {tool_name}")

    async def _list_all_tools(self) -> dict[str, Any]:
        """List all available tools."""
        tools: dict[str, list[str]] = {
            "builtin": [],
            "agent": [],
            "mcp": [],
        }

        # Builtin tools
        if self._tool_registry:
            tools["builtin"] = self._tool_registry.list_tool_names()

        # Agent tools
        tools["agent"] = list(self._agent_tools.keys())

        # MCP tools
        if self._mcp and self._mcp.is_connected:
            tools["mcp"] = self._mcp.available_tools

        return tools

    # =========================================================================
    # MCP Actions
    # =========================================================================

    async def _handle_mcp_action(self, action: str, **kwargs) -> Any:
        """Handle MCP actions."""
        if not self._mcp:
            raise RuntimeError("MCP not initialized")

        if action == "mcp_list_tools":
            result = await self._mcp.list_tools()
            return result.output if result.success else []

        elif action == "mcp_call":
            tool_name = kwargs.get("tool_name")
            arguments = kwargs.get("arguments", {})
            result = await self._mcp.call_tool(tool_name, arguments)
            if result.success:
                return result.output
            raise RuntimeError(result.error)

        elif action == "mcp_resources":
            result = await self._mcp.execute(action="get_resources")
            return result.output if result.success else []

        raise ValueError(f"Unknown MCP action: {action}")

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _list_capabilities(self) -> dict[str, bool]:
        """List available capabilities and their status."""
        return {
            "api": self._api_client is not None,
            "tools": self._tool_registry is not None,
            "agent_tools": bool(self._agent_tools),
            "mcp": self._mcp is not None and self._mcp.is_connected,
        }

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def api_list_agents(self) -> CapabilityResult:
        """List all agents via API."""
        return await self.execute(action="api_list_agents")

    async def api_get_agent(self, agent_id: str) -> CapabilityResult:
        """Get agent by ID via API."""
        return await self.execute(action="api_get_agent", agent_id=agent_id)

    async def api_list_workflows(self) -> CapabilityResult:
        """List all workflows via API."""
        return await self.execute(action="api_list_workflows")

    async def api_execute_workflow(
        self, workflow_id: str, inputs: dict[str, Any] | None = None
    ) -> CapabilityResult:
        """Execute a workflow via API."""
        return await self.execute(
            action="api_execute_workflow",
            workflow_id=workflow_id,
            body={"inputs": inputs or {}},
        )

    async def api_health(self) -> CapabilityResult:
        """Check API health."""
        return await self.execute(action="api_health")

    async def execute_tool(self, tool_name: str, **kwargs) -> CapabilityResult:
        """Execute a Paracle tool."""
        return await self.execute(action="tool", tool_name=tool_name, **kwargs)

    async def git_status(self, cwd: str = ".") -> CapabilityResult:
        """Get git status."""
        return await self.execute_tool("git_status", cwd=cwd)

    async def git_diff(self, cwd: str = ".") -> CapabilityResult:
        """Get git diff."""
        return await self.execute_tool("git_diff", cwd=cwd)

    async def analyze_code(self, path: str) -> CapabilityResult:
        """Analyze code structure."""
        return await self.execute_tool("code_analysis", path=path)

    async def run_tests(self, path: str | None = None) -> CapabilityResult:
        """Run tests."""
        return await self.execute_tool("test_execution", path=path)

    async def mcp_call(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> CapabilityResult:
        """Call an MCP tool."""
        return await self.execute(
            action="mcp_call", tool_name=tool_name, arguments=arguments
        )

    async def mcp_list_tools(self) -> CapabilityResult:
        """List available MCP tools."""
        return await self.execute(action="mcp_list_tools")

    @property
    def is_api_available(self) -> bool:
        """Check if API is available."""
        return self._api_client is not None

    @property
    def is_tools_available(self) -> bool:
        """Check if tools are available."""
        return self._tool_registry is not None or bool(self._agent_tools)

    @property
    def is_mcp_available(self) -> bool:
        """Check if MCP is available."""
        return self._mcp is not None and self._mcp.is_connected

    @property
    def available_tools(self) -> list[str]:
        """Get list of all available tool names."""
        tools = []
        if self._tool_registry:
            tools.extend(self._tool_registry.list_tool_names())
        tools.extend(self._agent_tools.keys())
        return tools
