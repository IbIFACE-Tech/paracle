"""Chat session for interactive conversations.

This module provides an interactive chat session with tool use support.
The chat session maintains conversation history and can use capabilities
as tools during the conversation.

NEW in v1.5.0: Plan and Edit modes are now accessible from Chat mode:
- Use create_plan tool to decompose complex tasks into steps
- Use execute_plan tool to run a plan step by step
- Use edit_file tool for structured code editing with diff preview
- Use apply_edits tool to apply pending edits

NEW in v1.6.0: Paracle integration for API, tools, and MCP:
- Use paracle_* tools to access Paracle REST API
- Use git_*, code_*, test_* tools for development workflows
- Use mcp_* tools for Model Context Protocol integration

Example:
    >>> from paracle_meta.sessions import ChatSession, ChatConfig
    >>> from paracle_meta.capabilities.providers import AnthropicProvider
    >>> from paracle_meta.registry import CapabilityRegistry
    >>>
    >>> provider = AnthropicProvider()
    >>> registry = CapabilityRegistry()
    >>> await registry.initialize()
    >>>
    >>> config = ChatConfig(
    ...     system_prompt="You are a helpful coding assistant.",
    ...     enabled_capabilities=["filesystem", "code_creation", "planning", "editing"],
    ... )
    >>>
    >>> async with ChatSession(provider, registry, config) as chat:
    ...     response = await chat.send("Read the main.py file")
    ...     print(response.content)
    ...
    ...     # Use planning mode
    ...     response = await chat.send("Create a plan to build a REST API")
    ...     print(response.content)
    ...
    ...     # Use editing mode
    ...     response = await chat.send("Edit main.py to add type hints")
    ...     print(response.content)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from paracle_meta.capabilities.provider_protocol import (
    LLMMessage,
    LLMRequest,
    ToolCallResult,
    ToolDefinitionSchema,
)
from paracle_meta.sessions.base import (
    Session,
    SessionConfig,
    SessionMessage,
    SessionStatus,
)
from paracle_meta.sessions.edit import (
    EditConfig,
    EditOperation,
    EditSession,
    EditStatus,
)
from paracle_meta.sessions.plan import (
    Plan,
    PlanConfig,
    PlanSession,
    PlanStep,
    StepStatus,
)

if TYPE_CHECKING:
    from paracle_meta.capabilities.provider_protocol import CapabilityProvider
    from paracle_meta.registry import CapabilityRegistry


# Default system prompt for chat mode
DEFAULT_CHAT_SYSTEM_PROMPT = """You are an intelligent coding assistant with access to various tools.

You can:
- Read and write files
- Execute shell commands (with user approval)
- Create code (functions, classes, modules)
- Search and analyze codebases
- Remember context across the conversation

**Planning Mode** (for complex tasks):
- Use `create_plan` to decompose complex goals into actionable steps
- Use `execute_plan` to run plans step by step
- Use `get_plan_status` to check progress
- Plans track dependencies, complexity, and validation criteria

**Editing Mode** (for code changes):
- Use `edit_file` for structured code modifications with diff preview
- Use `search_replace` for find-and-replace across files
- Use `apply_edits` to apply pending edits after review
- Use `revert_edit` to undo applied changes
- All edits show a diff preview before application

When using tools:
- Be precise with file paths
- Explain what you're doing before taking actions
- Report results clearly
- Ask for clarification if needed
- For complex tasks, consider creating a plan first

**Paracle Integration** (API, tools, MCP):
- Use `paracle_list_agents` to list agents from the API
- Use `paracle_list_workflows` to list workflows
- Use `git_status`, `git_diff`, `git_log` for git operations
- Use `code_analysis` to analyze code structure
- Use `run_tests` to execute tests
- Use `mcp_list_tools` and `mcp_call` for MCP tools

Be helpful, concise, and professional."""


@dataclass
class ChatConfig(SessionConfig):
    """Configuration for chat sessions.

    Attributes:
        enabled_capabilities: List of capabilities to enable as tools.
            Available: filesystem, memory, shell, code_creation, planning, editing, paracle
        auto_approve_reads: Whether to auto-approve read operations.
        auto_approve_writes: Whether to auto-approve write operations.
        show_tool_calls: Whether to show tool call details.
        max_tool_iterations: Maximum tool call iterations per turn.
        plan_auto_execute: Whether to auto-execute plan steps (default: False).
        plan_require_approval: Whether to require approval for each plan step.
        edit_auto_apply: Whether to auto-apply edits (default: False for review).
        edit_create_backups: Whether to create backup files before editing.
        paracle_api_url: Base URL for Paracle REST API.
        paracle_api_token: JWT token for API authentication.
        paracle_allowed_paths: Allowed filesystem paths for Paracle tools.
        paracle_enable_mcp: Whether to enable MCP integration.
    """

    enabled_capabilities: list[str] = field(
        default_factory=lambda: ["filesystem", "memory", "planning", "editing", "paracle"]
    )
    auto_approve_reads: bool = True
    auto_approve_writes: bool = False
    show_tool_calls: bool = True
    max_tool_iterations: int = 10
    # Planning options
    plan_auto_execute: bool = False
    plan_require_approval: bool = True
    # Editing options
    edit_auto_apply: bool = False
    edit_create_backups: bool = True
    # Paracle integration options
    paracle_api_url: str = "http://localhost:8000/v1"
    paracle_api_token: str | None = None
    paracle_allowed_paths: list[str] = field(default_factory=lambda: ["."])
    paracle_enable_mcp: bool = True

    def __post_init__(self) -> None:
        """Set default system prompt if not provided."""
        if self.system_prompt is None:
            self.system_prompt = DEFAULT_CHAT_SYSTEM_PROMPT


# Tool definitions for capabilities
CAPABILITY_TOOLS: dict[str, list[ToolDefinitionSchema]] = {
    "filesystem": [
        ToolDefinitionSchema(
            name="read_file",
            description="Read contents of a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                        "default": "utf-8",
                    },
                },
                "required": ["path"],
            },
        ),
        ToolDefinitionSchema(
            name="write_file",
            description="Write content to a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write",
                    },
                },
                "required": ["path", "content"],
            },
        ),
        ToolDefinitionSchema(
            name="list_directory",
            description="List contents of a directory",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path",
                        "default": ".",
                    },
                },
            },
        ),
        ToolDefinitionSchema(
            name="glob_files",
            description="Find files matching a pattern",
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (e.g., '**/*.py')",
                    },
                },
                "required": ["pattern"],
            },
        ),
    ],
    "memory": [
        ToolDefinitionSchema(
            name="remember",
            description="Store information for later recall",
            input_schema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key to store under",
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to store",
                    },
                },
                "required": ["key", "value"],
            },
        ),
        ToolDefinitionSchema(
            name="recall",
            description="Retrieve stored information",
            input_schema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key to retrieve",
                    },
                },
                "required": ["key"],
            },
        ),
        ToolDefinitionSchema(
            name="search_memory",
            description="Search stored information",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                },
                "required": ["query"],
            },
        ),
    ],
    "shell": [
        ToolDefinitionSchema(
            name="run_command",
            description="Run a shell command (requires approval)",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to run",
                    },
                    "working_dir": {
                        "type": "string",
                        "description": "Working directory",
                    },
                },
                "required": ["command"],
            },
        ),
    ],
    "code_creation": [
        ToolDefinitionSchema(
            name="create_function",
            description="Generate a function from description",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Function name",
                    },
                    "description": {
                        "type": "string",
                        "description": "What the function should do",
                    },
                    "parameters": {
                        "type": "string",
                        "description": "Parameter signature (e.g., 'x: int, y: int')",
                    },
                },
                "required": ["name", "description"],
            },
        ),
        ToolDefinitionSchema(
            name="create_class",
            description="Generate a class from description",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Class name",
                    },
                    "description": {
                        "type": "string",
                        "description": "What the class should do",
                    },
                },
                "required": ["name", "description"],
            },
        ),
        ToolDefinitionSchema(
            name="refactor_code",
            description="Refactor existing code",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to refactor",
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Refactoring instructions",
                    },
                },
                "required": ["code", "instructions"],
            },
        ),
    ],
    # Planning tools - decompose complex tasks into actionable steps
    "planning": [
        ToolDefinitionSchema(
            name="create_plan",
            description="Create a structured plan to achieve a goal. Decomposes complex tasks into actionable steps with dependencies and validation criteria.",
            input_schema={
                "type": "object",
                "properties": {
                    "goal": {
                        "type": "string",
                        "description": "The goal to achieve (e.g., 'Build a REST API with authentication')",
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context about requirements or constraints",
                    },
                },
                "required": ["goal"],
            },
        ),
        ToolDefinitionSchema(
            name="execute_plan",
            description="Execute a plan step by step. Runs all pending steps in order, respecting dependencies.",
            input_schema={
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "string",
                        "description": "ID of the plan to execute (from create_plan result). If not provided, executes the current plan.",
                    },
                },
            },
        ),
        ToolDefinitionSchema(
            name="execute_step",
            description="Execute a single step from a plan.",
            input_schema={
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "string",
                        "description": "ID of the plan",
                    },
                    "step_id": {
                        "type": "string",
                        "description": "ID of the step to execute",
                    },
                },
                "required": ["step_id"],
            },
        ),
        ToolDefinitionSchema(
            name="get_plan_status",
            description="Get the current status of a plan including progress and step details.",
            input_schema={
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "string",
                        "description": "ID of the plan. If not provided, returns status of current plan.",
                    },
                },
            },
        ),
        ToolDefinitionSchema(
            name="list_plans",
            description="List all plans created in this session.",
            input_schema={
                "type": "object",
                "properties": {},
            },
        ),
    ],
    # Editing tools - structured code editing with diff preview
    "editing": [
        ToolDefinitionSchema(
            name="edit_file",
            description="Edit a file with instructions. Returns a diff preview before applying changes.",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to edit",
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Edit instructions (e.g., 'Add type hints to all functions')",
                    },
                    "line_start": {
                        "type": "integer",
                        "description": "Start line for partial edit (optional)",
                    },
                    "line_end": {
                        "type": "integer",
                        "description": "End line for partial edit (optional)",
                    },
                },
                "required": ["file_path", "instructions"],
            },
        ),
        ToolDefinitionSchema(
            name="search_replace",
            description="Search and replace text across files.",
            input_schema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Text to search for",
                    },
                    "replace": {
                        "type": "string",
                        "description": "Replacement text",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Specific file to modify (optional)",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern for files (e.g., '**/*.py')",
                    },
                    "regex": {
                        "type": "boolean",
                        "description": "Whether search is a regex pattern",
                    },
                },
                "required": ["search", "replace"],
            },
        ),
        ToolDefinitionSchema(
            name="insert_code",
            description="Insert code at a specific location in a file.",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file",
                    },
                    "content": {
                        "type": "string",
                        "description": "Code to insert",
                    },
                    "after_line": {
                        "type": "integer",
                        "description": "Insert after this line number",
                    },
                    "before_line": {
                        "type": "integer",
                        "description": "Insert before this line number",
                    },
                },
                "required": ["file_path", "content"],
            },
        ),
        ToolDefinitionSchema(
            name="delete_lines",
            description="Delete lines from a file.",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "First line to delete",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Last line to delete (inclusive)",
                    },
                },
                "required": ["file_path", "start_line"],
            },
        ),
        ToolDefinitionSchema(
            name="apply_edits",
            description="Apply all pending edits. Use after reviewing diff previews.",
            input_schema={
                "type": "object",
                "properties": {
                    "edit_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific edit IDs to apply. If empty, applies all pending edits.",
                    },
                },
            },
        ),
        ToolDefinitionSchema(
            name="revert_edit",
            description="Revert an applied edit to restore original content.",
            input_schema={
                "type": "object",
                "properties": {
                    "edit_id": {
                        "type": "string",
                        "description": "ID of the edit to revert",
                    },
                },
                "required": ["edit_id"],
            },
        ),
        ToolDefinitionSchema(
            name="get_pending_edits",
            description="Get list of pending edits with their diffs.",
            input_schema={
                "type": "object",
                "properties": {},
            },
        ),
        ToolDefinitionSchema(
            name="get_edit_summary",
            description="Get summary of all edits in this session.",
            input_schema={
                "type": "object",
                "properties": {},
            },
        ),
    ],
    # Paracle integration tools - API, tools, and MCP
    "paracle": [
        # API tools
        ToolDefinitionSchema(
            name="paracle_list_agents",
            description="List all agents from Paracle API.",
            input_schema={
                "type": "object",
                "properties": {},
            },
        ),
        ToolDefinitionSchema(
            name="paracle_get_agent",
            description="Get agent details by ID from Paracle API.",
            input_schema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent ID",
                    },
                },
                "required": ["agent_id"],
            },
        ),
        ToolDefinitionSchema(
            name="paracle_list_workflows",
            description="List all workflows from Paracle API.",
            input_schema={
                "type": "object",
                "properties": {},
            },
        ),
        ToolDefinitionSchema(
            name="paracle_execute_workflow",
            description="Execute a workflow via Paracle API.",
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID to execute",
                    },
                    "inputs": {
                        "type": "object",
                        "description": "Workflow input parameters",
                    },
                },
                "required": ["workflow_id"],
            },
        ),
        ToolDefinitionSchema(
            name="paracle_health",
            description="Check Paracle API health status.",
            input_schema={
                "type": "object",
                "properties": {},
            },
        ),
        # Git tools
        ToolDefinitionSchema(
            name="git_status",
            description="Get git repository status.",
            input_schema={
                "type": "object",
                "properties": {
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (default: current)",
                    },
                },
            },
        ),
        ToolDefinitionSchema(
            name="git_diff",
            description="Show git diff of changes.",
            input_schema={
                "type": "object",
                "properties": {
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                    },
                    "staged": {
                        "type": "boolean",
                        "description": "Show staged changes only",
                    },
                },
            },
        ),
        ToolDefinitionSchema(
            name="git_log",
            description="Show git commit history.",
            input_schema={
                "type": "object",
                "properties": {
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of commits to show",
                    },
                },
            },
        ),
        # Code analysis tools
        ToolDefinitionSchema(
            name="code_analysis",
            description="Analyze code structure, dependencies, and complexity.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File or directory path to analyze",
                    },
                },
                "required": ["path"],
            },
        ),
        ToolDefinitionSchema(
            name="static_analysis",
            description="Run static analysis with ruff, mypy, or pylint.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File or directory to analyze",
                    },
                    "tool": {
                        "type": "string",
                        "enum": ["ruff", "mypy", "pylint"],
                        "description": "Analysis tool to use",
                    },
                },
                "required": ["path"],
            },
        ),
        # Testing tools
        ToolDefinitionSchema(
            name="run_tests",
            description="Run pytest tests.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to test file or directory",
                    },
                    "markers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Test markers to filter",
                    },
                },
            },
        ),
        ToolDefinitionSchema(
            name="coverage_analysis",
            description="Analyze test coverage.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to analyze",
                    },
                },
            },
        ),
        # MCP tools
        ToolDefinitionSchema(
            name="mcp_list_tools",
            description="List available MCP tools from connected server.",
            input_schema={
                "type": "object",
                "properties": {},
            },
        ),
        ToolDefinitionSchema(
            name="mcp_call",
            description="Call an MCP tool with arguments.",
            input_schema={
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the MCP tool to call",
                    },
                    "arguments": {
                        "type": "object",
                        "description": "Tool arguments",
                    },
                },
                "required": ["tool_name"],
            },
        ),
        # Utility tools
        ToolDefinitionSchema(
            name="paracle_list_tools",
            description="List all available Paracle tools (builtin, agent, MCP).",
            input_schema={
                "type": "object",
                "properties": {},
            },
        ),
    ],
}


class ChatSession(Session):
    """Interactive chat session with tool use.

    Provides a conversational interface with access to capabilities
    as tools. Maintains conversation history and handles tool execution.

    NEW in v1.5.0: Integrates PlanSession and EditSession for seamless
    access to planning and editing capabilities from within chat mode.

    NEW in v1.6.0: Integrates ParacleCapability for unified access to
    Paracle API, tools, and MCP integration.

    Attributes:
        config: Chat configuration.
        tools: Available tools based on enabled capabilities.
        plan_session: Embedded planning session for task decomposition.
        edit_session: Embedded editing session for structured code changes.
        paracle: Paracle integration capability.
    """

    def __init__(
        self,
        provider: CapabilityProvider,
        registry: CapabilityRegistry,
        config: ChatConfig | None = None,
    ):
        """Initialize chat session.

        Args:
            provider: LLM provider.
            registry: Capability registry.
            config: Chat configuration.
        """
        super().__init__(provider, registry, config or ChatConfig())
        self.config: ChatConfig = self.config  # type: ignore
        self._tools: list[ToolDefinitionSchema] = []
        self._tool_to_capability: dict[str, str] = {}

        # Embedded sessions for planning and editing (initialized lazily)
        self._plan_session: PlanSession | None = None
        self._edit_session: EditSession | None = None

        # Paracle integration capability (initialized lazily)
        self._paracle: Any = None  # ParacleCapability

    @property
    def tools(self) -> list[ToolDefinitionSchema]:
        """Available tools."""
        return self._tools

    @property
    def plan_session(self) -> PlanSession:
        """Get the embedded planning session."""
        if self._plan_session is None:
            raise RuntimeError("Planning session not initialized. Call initialize() first.")
        return self._plan_session

    @property
    def edit_session(self) -> EditSession:
        """Get the embedded editing session."""
        if self._edit_session is None:
            raise RuntimeError("Editing session not initialized. Call initialize() first.")
        return self._edit_session

    @property
    def current_plan(self) -> Plan | None:
        """Get the current plan from the planning session."""
        if self._plan_session:
            return self._plan_session.current_plan
        return None

    @property
    def pending_edits(self) -> list[EditOperation]:
        """Get pending edits from the editing session."""
        if self._edit_session:
            return self._edit_session.pending_edits
        return []

    @property
    def paracle(self) -> Any:
        """Get the Paracle integration capability."""
        return self._paracle

    async def initialize(self) -> None:
        """Initialize the chat session and load tools."""
        # Build tool list from enabled capabilities
        for cap_name in self.config.enabled_capabilities:
            if cap_name in CAPABILITY_TOOLS:
                for tool in CAPABILITY_TOOLS[cap_name]:
                    self._tools.append(tool)
                    self._tool_to_capability[tool.name] = cap_name

        # Initialize embedded planning session if enabled
        if "planning" in self.config.enabled_capabilities:
            plan_config = PlanConfig(
                auto_execute=self.config.plan_auto_execute,
                require_approval=self.config.plan_require_approval,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
            self._plan_session = PlanSession(self.provider, self.registry, plan_config)
            await self._plan_session.initialize()

        # Initialize embedded editing session if enabled
        if "editing" in self.config.enabled_capabilities:
            edit_config = EditConfig(
                auto_apply=self.config.edit_auto_apply,
                create_backups=self.config.edit_create_backups,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
            self._edit_session = EditSession(self.provider, self.registry, edit_config)
            await self._edit_session.initialize()

        # Initialize Paracle integration if enabled
        if "paracle" in self.config.enabled_capabilities:
            await self._init_paracle()

        self.status = SessionStatus.ACTIVE

    async def _init_paracle(self) -> None:
        """Initialize Paracle integration capability."""
        try:
            from paracle_meta.capabilities.paracle_integration import (
                ParacleCapability,
                ParacleConfig,
            )

            paracle_config = ParacleConfig(
                api_base_url=self.config.paracle_api_url,
                api_token=self.config.paracle_api_token,
                enable_api=True,
                enable_tools=True,
                allowed_paths=self.config.paracle_allowed_paths,
                enable_mcp=self.config.paracle_enable_mcp,
            )
            self._paracle = ParacleCapability(paracle_config)
            await self._paracle.initialize()

        except ImportError:
            # Paracle integration not available
            pass
        except Exception:
            # Failed to initialize, continue without Paracle
            pass

    async def send(self, message: str) -> SessionMessage:
        """Send a message and get response.

        Args:
            message: User message.

        Returns:
            Assistant response message.

        Raises:
            RuntimeError: If session is not active.
        """
        if self.status != SessionStatus.ACTIVE:
            raise RuntimeError(f"Session is not active: {self.status}")

        if self.turn_count >= self.config.max_turns:
            raise RuntimeError(f"Maximum turns ({self.config.max_turns}) reached")

        # Add user message
        await self.add_message("user", message)

        # Build LLM request
        request = self._build_request()

        # Get response (may involve tool calls)
        response = await self._get_response_with_tools(request)

        # Add assistant message
        assistant_msg = await self.add_message(
            "assistant",
            response.content,
            tool_calls=(
                [
                    {"id": tc.id, "name": tc.name, "input": tc.input}
                    for tc in (response.tool_calls or [])
                ]
                if response.tool_calls
                else None
            ),
        )

        return assistant_msg

    def _build_request(self) -> LLMRequest:
        """Build LLM request from conversation history."""
        messages = [LLMMessage(role=m.role, content=m.content) for m in self.messages]

        return LLMRequest(
            messages=messages,
            system_prompt=self.config.system_prompt,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            tools=self._tools if self.config.enable_tools else None,
        )

    async def _get_response_with_tools(
        self,
        request: LLMRequest,
    ) -> Any:
        """Get response, handling tool calls iteratively."""
        from paracle_meta.capabilities.provider_protocol import LLMResponse

        iteration = 0
        accumulated_content = ""

        while iteration < self.config.max_tool_iterations:
            response = await self.provider.complete(request)

            if not response.tool_calls:
                # No tool calls, return final response
                response.content = accumulated_content + response.content
                return response

            # Execute tool calls
            tool_results = await self._execute_tool_calls(response.tool_calls)

            # Add tool results to messages
            for tc, result in zip(response.tool_calls, tool_results, strict=False):
                # Add assistant's tool call
                self.messages.append(
                    SessionMessage(
                        role="assistant",
                        content="",
                        tool_calls=[{"id": tc.id, "name": tc.name, "input": tc.input}],
                    )
                )
                # Add tool result
                self.messages.append(
                    SessionMessage(
                        role="user",
                        content="",
                        tool_results=[
                            {
                                "tool_use_id": result.tool_use_id,
                                "content": result.content,
                                "is_error": result.is_error,
                            }
                        ],
                    )
                )

            # Accumulate any content
            if response.content:
                accumulated_content += response.content + "\n"

            # Rebuild request with tool results
            request = self._build_request()
            iteration += 1

        # Max iterations reached
        return LLMResponse(
            content=accumulated_content + "[Max tool iterations reached]",
            provider=self.provider.name,
        )

    async def _execute_tool_calls(
        self,
        tool_calls: list[Any],
    ) -> list[ToolCallResult]:
        """Execute tool calls and return results."""
        results = []

        for tc in tool_calls:
            try:
                result = await self._execute_single_tool(tc.name, tc.input)
                results.append(
                    ToolCallResult(
                        tool_use_id=tc.id,
                        content=result,
                        is_error=False,
                    )
                )
            except Exception as e:
                results.append(
                    ToolCallResult(
                        tool_use_id=tc.id,
                        content=f"Error: {str(e)}",
                        is_error=True,
                    )
                )

        return results

    async def _execute_single_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> str:
        """Execute a single tool call.

        Args:
            tool_name: Name of the tool.
            tool_input: Tool input parameters.

        Returns:
            Tool result as string.
        """
        cap_name = self._tool_to_capability.get(tool_name)
        if not cap_name:
            return f"Unknown tool: {tool_name}"

        # Handle planning tools
        if cap_name == "planning":
            return await self._execute_planning_tool(tool_name, tool_input)

        # Handle editing tools
        if cap_name == "editing":
            return await self._execute_editing_tool(tool_name, tool_input)

        # Handle Paracle integration tools
        if cap_name == "paracle":
            return await self._execute_paracle_tool(tool_name, tool_input)

        # Handle other capabilities
        capability = await self.registry.get(cap_name)

        # Map tool names to capability methods
        if tool_name == "read_file":
            result = await capability.read_file(
                tool_input["path"],
                encoding=tool_input.get("encoding", "utf-8"),
            )
        elif tool_name == "write_file":
            result = await capability.write_file(
                tool_input["path"],
                tool_input["content"],
            )
        elif tool_name == "list_directory":
            result = await capability.list_directory(tool_input.get("path", "."))
        elif tool_name == "glob_files":
            result = await capability.glob_files(tool_input["pattern"])
        elif tool_name == "remember":
            result = await capability.store(tool_input["key"], tool_input["value"])
        elif tool_name == "recall":
            result = await capability.retrieve(tool_input["key"])
        elif tool_name == "search_memory":
            result = await capability.search(tool_input["query"])
        elif tool_name == "run_command":
            result = await capability.execute(
                command=tool_input["command"],
                working_dir=tool_input.get("working_dir"),
            )
        elif tool_name == "create_function":
            result = await capability.create_function(
                name=tool_input["name"],
                description=tool_input["description"],
                parameters=tool_input.get("parameters", ""),
            )
        elif tool_name == "create_class":
            result = await capability.create_class(
                name=tool_input["name"],
                description=tool_input["description"],
            )
        elif tool_name == "refactor_code":
            result = await capability.refactor(
                code=tool_input["code"],
                instructions=tool_input["instructions"],
            )
        else:
            return f"Tool not implemented: {tool_name}"

        # Format result
        if hasattr(result, "output"):
            return str(result.output)
        return str(result)

    # =========================================================================
    # Planning Tools Implementation
    # =========================================================================

    async def _execute_planning_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> str:
        """Execute a planning tool.

        Args:
            tool_name: Name of the planning tool.
            tool_input: Tool input parameters.

        Returns:
            Tool result as string.
        """
        if self._plan_session is None:
            return "Planning not enabled. Add 'planning' to enabled_capabilities."

        if tool_name == "create_plan":
            goal = tool_input["goal"]
            context = tool_input.get("context", "")
            if context:
                goal = f"{goal}\n\nContext: {context}"

            plan = await self._plan_session.create_plan(goal)
            return self._format_plan(plan)

        elif tool_name == "execute_plan":
            plan_id = tool_input.get("plan_id")
            if plan_id:
                plan = self._plan_session.get_plan(plan_id)
                if not plan:
                    return f"Plan not found: {plan_id}"
            else:
                plan = self._plan_session.current_plan
                if not plan:
                    return "No current plan. Use create_plan first."

            executed_plan = await self._plan_session.execute_plan(plan)
            return self._format_plan_execution_result(executed_plan)

        elif tool_name == "execute_step":
            step_id = tool_input["step_id"]
            plan_id = tool_input.get("plan_id")

            if plan_id:
                plan = self._plan_session.get_plan(plan_id)
            else:
                plan = self._plan_session.current_plan

            if not plan:
                return "No plan available. Use create_plan first."

            step = plan.get_step(step_id)
            if not step:
                return f"Step not found: {step_id}"

            executed_step = await self._plan_session.execute_step(step)
            return self._format_step_result(executed_step)

        elif tool_name == "get_plan_status":
            plan_id = tool_input.get("plan_id")
            if plan_id:
                plan = self._plan_session.get_plan(plan_id)
            else:
                plan = self._plan_session.current_plan

            if not plan:
                return "No plan available."

            return self._format_plan_status(plan)

        elif tool_name == "list_plans":
            plans = self._plan_session.list_plans()
            if not plans:
                return "No plans created in this session."

            lines = ["## Plans in this session:", ""]
            for plan in plans:
                status_icon = "●" if plan.is_complete else "○"
                lines.append(
                    f"- {status_icon} **{plan.id}**: {plan.goal[:50]}... "
                    f"({plan.progress:.0f}% complete)"
                )
            return "\n".join(lines)

        return f"Unknown planning tool: {tool_name}"

    def _format_plan(self, plan: Plan) -> str:
        """Format a plan for display."""
        lines = [
            f"## Plan Created: {plan.id}",
            "",
            f"**Goal**: {plan.goal}",
            f"**Summary**: {plan.summary}",
            "",
            f"**Steps** ({len(plan.steps)} total):",
        ]

        for i, step in enumerate(plan.steps, 1):
            complexity_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
                step.complexity, "⚪"
            )
            lines.append(f"{i}. {step.description}")
            lines.append(f"   └─ Complexity: {complexity_icon} {step.complexity}")
            if step.capability != "none":
                lines.append(f"   └─ Capability: {step.capability}")
            if step.depends_on:
                lines.append(f"   └─ Depends on: {', '.join(step.depends_on)}")

        if plan.risks:
            lines.extend(["", "**Risks**:"])
            for risk in plan.risks:
                lines.append(f"- ⚠️ {risk}")

        if plan.success_criteria:
            lines.extend(["", f"**Success Criteria**: {plan.success_criteria}"])

        lines.extend([
            "",
            "Use `execute_plan` to run this plan, or `execute_step` for "
            "individual steps.",
        ])

        return "\n".join(lines)

    def _format_plan_status(self, plan: Plan) -> str:
        """Format plan status for display."""
        lines = [
            f"## Plan Status: {plan.id}",
            "",
            f"**Goal**: {plan.goal}",
            f"**Progress**: {plan.progress:.0f}% "
            f"({plan.completed_steps}/{len(plan.steps)} steps)",
            f"**Status**: {plan.status.value}",
            "",
            "**Steps**:",
        ]

        for i, step in enumerate(plan.steps, 1):
            status_icon = {
                StepStatus.PENDING: "○",
                StepStatus.IN_PROGRESS: "◐",
                StepStatus.COMPLETED: "●",
                StepStatus.FAILED: "✗",
                StepStatus.SKIPPED: "○",
                StepStatus.BLOCKED: "◌",
            }.get(step.status, "○")

            lines.append(f"{i}. {status_icon} {step.description}")
            if step.result:
                lines.append(f"   └─ Result: {step.result[:100]}...")
            if step.error:
                lines.append(f"   └─ Error: {step.error}")

        return "\n".join(lines)

    def _format_plan_execution_result(self, plan: Plan) -> str:
        """Format plan execution result."""
        completed = sum(1 for s in plan.steps if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in plan.steps if s.status == StepStatus.FAILED)

        lines = [
            f"## Plan Execution Complete: {plan.id}",
            "",
            f"**Status**: {plan.status.value}",
            f"**Completed**: {completed}/{len(plan.steps)} steps",
        ]

        if failed > 0:
            lines.append(f"**Failed**: {failed} steps")

        lines.extend(["", "**Results**:"])

        for i, step in enumerate(plan.steps, 1):
            status_icon = "✓" if step.status == StepStatus.COMPLETED else "✗"
            lines.append(f"{i}. {status_icon} {step.description}")
            if step.result:
                lines.append(f"   └─ {step.result[:150]}")
            if step.error:
                lines.append(f"   └─ Error: {step.error}")

        return "\n".join(lines)

    def _format_step_result(self, step: PlanStep) -> str:
        """Format step execution result."""
        status_icon = "✓" if step.status == StepStatus.COMPLETED else "✗"
        lines = [
            f"## Step {status_icon}: {step.id}",
            "",
            f"**Description**: {step.description}",
            f"**Status**: {step.status.value}",
        ]

        if step.result:
            lines.extend(["", "**Result**:", step.result])

        if step.error:
            lines.extend(["", f"**Error**: {step.error}"])

        return "\n".join(lines)

    # =========================================================================
    # Editing Tools Implementation
    # =========================================================================

    async def _execute_editing_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> str:
        """Execute an editing tool.

        Args:
            tool_name: Name of the editing tool.
            tool_input: Tool input parameters.

        Returns:
            Tool result as string.
        """
        if self._edit_session is None:
            return "Editing not enabled. Add 'editing' to enabled_capabilities."

        if tool_name == "edit_file":
            edit = await self._edit_session.edit_file(
                file_path=tool_input["file_path"],
                instructions=tool_input["instructions"],
                line_start=tool_input.get("line_start"),
                line_end=tool_input.get("line_end"),
            )
            return self._format_edit_preview(edit)

        elif tool_name == "search_replace":
            edits = await self._edit_session.search_replace(
                search=tool_input["search"],
                replace=tool_input["replace"],
                file_path=tool_input.get("file_path"),
                pattern=tool_input.get("pattern"),
                regex=tool_input.get("regex", False),
            )
            return self._format_edits_preview(edits)

        elif tool_name == "insert_code":
            edit = await self._edit_session.insert_code(
                file_path=tool_input["file_path"],
                content=tool_input["content"],
                after_line=tool_input.get("after_line"),
                before_line=tool_input.get("before_line"),
            )
            return self._format_edit_preview(edit)

        elif tool_name == "delete_lines":
            edit = await self._edit_session.delete_lines(
                file_path=tool_input["file_path"],
                start_line=tool_input["start_line"],
                end_line=tool_input.get("end_line"),
            )
            return self._format_edit_preview(edit)

        elif tool_name == "apply_edits":
            edit_ids = tool_input.get("edit_ids", [])
            if edit_ids:
                # Apply specific edits
                edits = [
                    e for e in self._edit_session.pending_edits
                    if e.id in edit_ids
                ]
            else:
                edits = None  # Apply all pending

            stats = await self._edit_session.apply_all(edits)
            return self._format_apply_result(stats)

        elif tool_name == "revert_edit":
            edit_id = tool_input["edit_id"]
            edit = next(
                (e for e in self._edit_session.applied_edits if e.id == edit_id),
                None
            )
            if not edit:
                return f"Edit not found or not applied: {edit_id}"

            success = await self._edit_session.revert(edit)
            if success:
                return f"✓ Reverted edit {edit_id} for {edit.file_path}"
            return f"✗ Failed to revert edit {edit_id}"

        elif tool_name == "get_pending_edits":
            edits = self._edit_session.pending_edits
            if not edits:
                return "No pending edits."
            return self._format_edits_preview(edits)

        elif tool_name == "get_edit_summary":
            summary = self._edit_session.get_summary()
            return self._format_edit_summary(summary)

        return f"Unknown editing tool: {tool_name}"

    # =========================================================================
    # Paracle Integration Tools Implementation
    # =========================================================================

    async def _execute_paracle_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> str:
        """Execute a Paracle integration tool.

        Args:
            tool_name: Name of the Paracle tool.
            tool_input: Tool input parameters.

        Returns:
            Tool result as string.
        """
        if self._paracle is None:
            return "Paracle integration not enabled. Add 'paracle' to enabled_capabilities."

        # API tools
        if tool_name == "paracle_list_agents":
            result = await self._paracle.api_list_agents()
            return self._format_paracle_result(result, "Agents")

        elif tool_name == "paracle_get_agent":
            agent_id = tool_input["agent_id"]
            result = await self._paracle.api_get_agent(agent_id)
            return self._format_paracle_result(result, f"Agent: {agent_id}")

        elif tool_name == "paracle_list_workflows":
            result = await self._paracle.api_list_workflows()
            return self._format_paracle_result(result, "Workflows")

        elif tool_name == "paracle_execute_workflow":
            workflow_id = tool_input["workflow_id"]
            inputs = tool_input.get("inputs", {})
            result = await self._paracle.api_execute_workflow(workflow_id, inputs)
            return self._format_paracle_result(result, f"Workflow Execution: {workflow_id}")

        elif tool_name == "paracle_health":
            result = await self._paracle.api_health()
            return self._format_paracle_result(result, "API Health")

        # Git tools
        elif tool_name == "git_status":
            cwd = tool_input.get("cwd", ".")
            result = await self._paracle.git_status(cwd)
            return self._format_paracle_result(result, "Git Status")

        elif tool_name == "git_diff":
            cwd = tool_input.get("cwd", ".")
            result = await self._paracle.git_diff(cwd)
            return self._format_paracle_result(result, "Git Diff")

        elif tool_name == "git_log":
            cwd = tool_input.get("cwd", ".")
            result = await self._paracle.execute_tool(
                "git_log",
                cwd=cwd,
                count=tool_input.get("count", 10),
            )
            return self._format_paracle_result(result, "Git Log")

        # Code analysis tools
        elif tool_name == "code_analysis":
            path = tool_input["path"]
            result = await self._paracle.analyze_code(path)
            return self._format_paracle_result(result, f"Code Analysis: {path}")

        elif tool_name == "static_analysis":
            path = tool_input["path"]
            tool = tool_input.get("tool", "ruff")
            result = await self._paracle.execute_tool(
                "static_analysis",
                path=path,
                tool=tool,
            )
            return self._format_paracle_result(result, f"Static Analysis ({tool}): {path}")

        # Testing tools
        elif tool_name == "run_tests":
            path = tool_input.get("path")
            result = await self._paracle.run_tests(path)
            return self._format_paracle_result(result, "Test Results")

        elif tool_name == "coverage_analysis":
            path = tool_input.get("path")
            result = await self._paracle.execute_tool(
                "coverage_analysis",
                path=path,
            )
            return self._format_paracle_result(result, "Coverage Analysis")

        # MCP tools
        elif tool_name == "mcp_list_tools":
            result = await self._paracle.mcp_list_tools()
            return self._format_paracle_result(result, "MCP Tools")

        elif tool_name == "mcp_call":
            mcp_tool_name = tool_input["tool_name"]
            arguments = tool_input.get("arguments", {})
            result = await self._paracle.mcp_call(mcp_tool_name, arguments)
            return self._format_paracle_result(result, f"MCP Tool: {mcp_tool_name}")

        # Utility tools
        elif tool_name == "paracle_list_tools":
            result = await self._paracle.execute(action="list_tools")
            return self._format_paracle_result(result, "Available Tools")

        return f"Unknown Paracle tool: {tool_name}"

    def _format_paracle_result(self, result: Any, title: str) -> str:
        """Format a Paracle capability result for display."""
        if hasattr(result, "success"):
            if result.success:
                output = result.output
                if isinstance(output, dict):
                    lines = [f"## {title}", ""]
                    for key, value in output.items():
                        if isinstance(value, list):
                            lines.append(f"**{key}** ({len(value)} items):")
                            for item in value[:10]:  # Limit to 10 items
                                if isinstance(item, dict):
                                    item_str = ", ".join(
                                        f"{k}: {v}" for k, v in list(item.items())[:3]
                                    )
                                    lines.append(f"  - {item_str}")
                                else:
                                    lines.append(f"  - {item}")
                            if len(value) > 10:
                                lines.append(f"  ... and {len(value) - 10} more")
                        else:
                            lines.append(f"**{key}**: {value}")
                    return "\n".join(lines)
                elif isinstance(output, list):
                    lines = [f"## {title}", ""]
                    for item in output[:20]:
                        lines.append(f"- {item}")
                    if len(output) > 20:
                        lines.append(f"... and {len(output) - 20} more")
                    return "\n".join(lines)
                else:
                    return f"## {title}\n\n{output}"
            else:
                return f"## {title} - Error\n\n{result.error}"
        else:
            return f"## {title}\n\n{result}"

    def _format_edit_preview(self, edit: EditOperation) -> str:
        """Format a single edit preview."""
        status_icon = {
            EditStatus.PENDING: "○",
            EditStatus.PREVIEWED: "◐",
            EditStatus.APPLIED: "●",
            EditStatus.FAILED: "✗",
            EditStatus.SKIPPED: "○",
            EditStatus.REVERTED: "↩",
        }.get(edit.status, "○")

        lines = [
            f"## Edit Preview: {edit.id}",
            "",
            f"**File**: {edit.file_path}",
            f"**Status**: {status_icon} {edit.status.value}",
            f"**Type**: {edit.edit_type.value}",
        ]

        if edit.has_changes:
            lines.append(
                f"**Changes**: +{edit.lines_added} -{edit.lines_removed} lines"
            )
            if edit.diff:
                lines.extend(["", "```diff", edit.diff[:2000], "```"])
        else:
            lines.append("**No changes needed.**")

        if edit.error:
            lines.append(f"**Error**: {edit.error}")

        if edit.status == EditStatus.PREVIEWED:
            lines.extend([
                "",
                f"Use `apply_edits` with edit_id='{edit.id}' to apply, "
                "or call without arguments to apply all pending edits.",
            ])

        return "\n".join(lines)

    def _format_edits_preview(self, edits: list[EditOperation]) -> str:
        """Format multiple edit previews."""
        if not edits:
            return "No edits to show."

        lines = [f"## Edit Preview ({len(edits)} file(s))", ""]

        for edit in edits:
            status_icon = "◐" if edit.status == EditStatus.PREVIEWED else "○"
            lines.append(f"### {status_icon} {edit.file_path} ({edit.id})")

            if edit.has_changes:
                lines.append(
                    f"+{edit.lines_added} -{edit.lines_removed} lines"
                )
                if edit.diff:
                    # Truncate each diff to keep output manageable
                    diff_preview = edit.diff[:500]
                    if len(edit.diff) > 500:
                        diff_preview += "\n... (truncated)"
                    lines.extend(["```diff", diff_preview, "```"])
            else:
                lines.append("No changes needed.")
            lines.append("")

        lines.append("Use `apply_edits` to apply all pending edits.")

        return "\n".join(lines)

    def _format_apply_result(self, stats: dict[str, int]) -> str:
        """Format apply edits result."""
        lines = [
            "## Edits Applied",
            "",
            f"**Applied**: {stats['applied']} file(s)",
            f"**Skipped**: {stats['skipped']} file(s)",
            f"**Failed**: {stats['failed']} file(s)",
        ]

        if stats["failed"] > 0:
            lines.append(
                "\nSome edits failed. Use `get_pending_edits` to see details."
            )

        return "\n".join(lines)

    def _format_edit_summary(self, summary: dict[str, Any]) -> str:
        """Format edit session summary."""
        return "\n".join([
            "## Edit Session Summary",
            "",
            f"**Pending edits**: {summary['pending_edits']}",
            f"**Applied edits**: {summary['applied_edits']}",
            f"**Batches**: {summary['batches']}",
            f"**Total lines added**: +{summary['total_lines_added']}",
            f"**Total lines removed**: -{summary['total_lines_removed']}",
            f"**Files modified**: {summary['files_modified']}",
        ])

    async def stream_send(self, message: str):
        """Send a message and stream the response.

        Args:
            message: User message.

        Yields:
            Response chunks.
        """
        if self.status != SessionStatus.ACTIVE:
            raise RuntimeError(f"Session is not active: {self.status}")

        await self.add_message("user", message)
        request = self._build_request()

        accumulated = ""
        async for chunk in self.provider.stream(request):
            accumulated += chunk.content
            yield chunk.content

        await self.add_message("assistant", accumulated)
