"""Chat session for interactive conversations.

This module provides an interactive chat session with tool use support.
The chat session maintains conversation history and can use capabilities
as tools during the conversation.

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
    ...     enabled_capabilities=["filesystem", "code_creation"],
    ... )
    >>>
    >>> async with ChatSession(provider, registry, config) as chat:
    ...     response = await chat.send("Read the main.py file")
    ...     print(response.content)
    ...
    ...     response = await chat.send("Add type hints to the functions")
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

When using tools:
- Be precise with file paths
- Explain what you're doing before taking actions
- Report results clearly
- Ask for clarification if needed

Be helpful, concise, and professional."""


@dataclass
class ChatConfig(SessionConfig):
    """Configuration for chat sessions.

    Attributes:
        enabled_capabilities: List of capabilities to enable as tools.
        auto_approve_reads: Whether to auto-approve read operations.
        auto_approve_writes: Whether to auto-approve write operations.
        show_tool_calls: Whether to show tool call details.
        max_tool_iterations: Maximum tool call iterations per turn.
    """

    enabled_capabilities: list[str] = field(
        default_factory=lambda: ["filesystem", "memory"]
    )
    auto_approve_reads: bool = True
    auto_approve_writes: bool = False
    show_tool_calls: bool = True
    max_tool_iterations: int = 10

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
}


class ChatSession(Session):
    """Interactive chat session with tool use.

    Provides a conversational interface with access to capabilities
    as tools. Maintains conversation history and handles tool execution.

    Attributes:
        config: Chat configuration.
        tools: Available tools based on enabled capabilities.
    """

    def __init__(
        self,
        provider: "CapabilityProvider",
        registry: "CapabilityRegistry",
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

    @property
    def tools(self) -> list[ToolDefinitionSchema]:
        """Available tools."""
        return self._tools

    async def initialize(self) -> None:
        """Initialize the chat session and load tools."""
        # Build tool list from enabled capabilities
        for cap_name in self.config.enabled_capabilities:
            if cap_name in CAPABILITY_TOOLS:
                for tool in CAPABILITY_TOOLS[cap_name]:
                    self._tools.append(tool)
                    self._tool_to_capability[tool.name] = cap_name

        self.status = SessionStatus.ACTIVE

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
            for tc, result in zip(response.tool_calls, tool_results):
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
