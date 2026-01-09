"""Anthropic SDK Integration for MetaAgent.

Provides Claude-powered capabilities for intelligent agent operations:
- Tool use with Claude's native tool calling
- Computer use capabilities
- Multi-turn conversations with context
- Streaming responses
- Intelligent code generation and analysis

Example:
    >>> cap = AnthropicCapability(config=AnthropicConfig(api_key="sk-..."))
    >>> await cap.initialize()
    >>>
    >>> # Simple completion
    >>> result = await cap.complete("Explain Python decorators")
    >>>
    >>> # With tools
    >>> result = await cap.complete_with_tools(
    ...     prompt="Search for Python best practices",
    ...     tools=[search_tool, read_file_tool]
    ... )
    >>>
    >>> # Code generation
    >>> result = await cap.generate_code(
    ...     description="Create a FastAPI endpoint for user registration",
    ...     language="python"
    ... )
"""

import asyncio
import os
import time
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class ClaudeModel(str, Enum):
    """Available Claude models."""

    OPUS = "claude-opus-4-20250514"
    SONNET = "claude-sonnet-4-20250514"
    HAIKU = "claude-3-5-haiku-20241022"
    # Legacy models
    OPUS_3 = "claude-3-opus-20240229"
    SONNET_35 = "claude-3-5-sonnet-20241022"
    SONNET_3 = "claude-3-sonnet-20240229"


class ToolDefinition(BaseModel):
    """Definition of a tool for Claude to use."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: dict[str, Any] = Field(..., description="JSON schema for input")

    def to_anthropic_format(self) -> dict[str, Any]:
        """Convert to Anthropic API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ToolCall(BaseModel):
    """A tool call made by Claude."""

    id: str
    name: str
    input: dict[str, Any]


class ToolResult(BaseModel):
    """Result of a tool execution."""

    tool_use_id: str
    content: str | list[dict[str, Any]]
    is_error: bool = False


class Message(BaseModel):
    """A message in a conversation."""

    role: str = Field(..., description="user or assistant")
    content: str | list[dict[str, Any]]

    def to_anthropic_format(self) -> dict[str, Any]:
        """Convert to Anthropic API format."""
        return {
            "role": self.role,
            "content": self.content,
        }


class AnthropicConfig(CapabilityConfig):
    """Configuration for Anthropic integration."""

    api_key: str | None = Field(
        default=None, description="Anthropic API key (or use ANTHROPIC_API_KEY env var)"
    )
    model: str = Field(
        default=ClaudeModel.SONNET.value, description="Default Claude model to use"
    )
    max_tokens: int = Field(
        default=4096, ge=1, le=200000, description="Maximum tokens in response"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Sampling temperature"
    )
    system_prompt: str | None = Field(
        default=None, description="System prompt for all requests"
    )
    enable_tool_use: bool = Field(
        default=True, description="Enable tool use capabilities"
    )
    enable_streaming: bool = Field(
        default=True, description="Enable streaming responses"
    )
    retry_on_overload: bool = Field(
        default=True, description="Retry on API overload errors"
    )


class ConversationContext(BaseModel):
    """Context for multi-turn conversations."""

    id: str = Field(default_factory=lambda: f"conv_{int(time.time() * 1000)}")
    messages: list[Message] = Field(default_factory=list)
    system_prompt: str | None = None
    model: str = ClaudeModel.SONNET.value
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_tokens: int = 0

    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str | list[dict[str, Any]]) -> None:
        """Add an assistant message."""
        self.messages.append(Message(role="assistant", content=content))

    def add_tool_result(
        self, tool_use_id: str, result: str, is_error: bool = False
    ) -> None:
        """Add a tool result message."""
        self.messages.append(
            Message(
                role="user",
                content=[
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": result,
                        "is_error": is_error,
                    }
                ],
            )
        )


class AnthropicCapability(BaseCapability):
    """Anthropic Claude SDK integration capability.

    Provides powerful Claude-powered features:
    - Completions with tool use
    - Multi-turn conversations
    - Streaming responses
    - Code generation and analysis
    - Intelligent task decomposition

    Example:
        >>> cap = AnthropicCapability()
        >>> await cap.initialize()
        >>>
        >>> # Simple completion
        >>> result = await cap.complete("What is Python?")
        >>> print(result.output["content"])
        >>>
        >>> # Code generation
        >>> code = await cap.generate_code(
        ...     "Create a REST API endpoint",
        ...     language="python"
        ... )
    """

    name = "anthropic"
    description = "Claude SDK integration for intelligent AI capabilities"

    # Default system prompt for code generation
    CODE_GENERATION_PROMPT = """You are an expert software engineer.
Generate clean, well-documented, production-quality code.
Follow best practices and include type hints for Python.
Return ONLY the code without markdown code blocks unless asked."""

    # Default system prompt for analysis
    ANALYSIS_PROMPT = """You are an expert code reviewer and analyst.
Provide detailed, actionable analysis with specific suggestions.
Focus on code quality, security, performance, and maintainability."""

    def __init__(self, config: AnthropicConfig | None = None):
        """Initialize Anthropic capability.

        Args:
            config: Anthropic configuration
        """
        super().__init__(config or AnthropicConfig())
        self.config: AnthropicConfig = self.config
        self._client: Any = None
        self._async_client: Any = None
        self._conversations: dict[str, ConversationContext] = {}
        self._available = False

    async def initialize(self) -> None:
        """Initialize Anthropic client."""
        await super().initialize()

        try:
            # Try to import anthropic
            import anthropic

            # Get API key
            api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")

            if api_key:
                self._client = anthropic.Anthropic(api_key=api_key)
                self._async_client = anthropic.AsyncAnthropic(api_key=api_key)
                self._available = True
            else:
                # No API key - capability available but limited
                self._available = False

        except ImportError:
            # Anthropic not installed
            self._available = False

    async def shutdown(self) -> None:
        """Shutdown and cleanup."""
        self._client = None
        self._async_client = None
        self._conversations.clear()
        await super().shutdown()

    @property
    def is_available(self) -> bool:
        """Check if Anthropic SDK is available and configured."""
        return self._available and self._async_client is not None

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute Anthropic capability.

        Actions:
            - complete: Simple completion
            - complete_with_tools: Completion with tool use
            - generate_code: Generate code from description
            - analyze_code: Analyze code quality
            - start_conversation: Start multi-turn conversation
            - continue_conversation: Continue conversation
            - stream: Stream a completion
        """
        action = kwargs.get("action", "complete")
        start_time = time.time()

        try:
            if action == "complete":
                result = await self._complete(
                    prompt=kwargs.get("prompt", ""),
                    system=kwargs.get("system"),
                    model=kwargs.get("model"),
                    max_tokens=kwargs.get("max_tokens"),
                    temperature=kwargs.get("temperature"),
                )
            elif action == "complete_with_tools":
                result = await self._complete_with_tools(
                    prompt=kwargs.get("prompt", ""),
                    tools=kwargs.get("tools", []),
                    tool_choice=kwargs.get("tool_choice"),
                    system=kwargs.get("system"),
                )
            elif action == "generate_code":
                result = await self._generate_code(
                    description=kwargs.get("description", ""),
                    language=kwargs.get("language", "python"),
                    context=kwargs.get("context"),
                )
            elif action == "analyze_code":
                result = await self._analyze_code(
                    code=kwargs.get("code", ""),
                    analysis_type=kwargs.get("analysis_type", "general"),
                )
            elif action == "start_conversation":
                result = await self._start_conversation(
                    system_prompt=kwargs.get("system_prompt"),
                    model=kwargs.get("model"),
                )
            elif action == "continue_conversation":
                result = await self._continue_conversation(
                    conversation_id=kwargs.get("conversation_id", ""),
                    message=kwargs.get("message", ""),
                    tools=kwargs.get("tools"),
                )
            elif action == "decompose_task":
                result = await self._decompose_task(
                    task=kwargs.get("task", ""),
                    context=kwargs.get("context"),
                )
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

    async def _complete(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Simple completion."""
        if not self.is_available:
            return self._mock_completion(prompt)

        response = await self._async_client.messages.create(
            model=model or self.config.model,
            max_tokens=max_tokens or self.config.max_tokens,
            temperature=(
                temperature if temperature is not None else self.config.temperature
            ),
            system=system
            or self.config.system_prompt
            or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        )

        return {
            "content": response.content[0].text if response.content else "",
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "stop_reason": response.stop_reason,
        }

    async def _complete_with_tools(
        self,
        prompt: str,
        tools: list[ToolDefinition | dict[str, Any]],
        tool_choice: dict[str, Any] | None = None,
        system: str | None = None,
    ) -> dict[str, Any]:
        """Completion with tool use."""
        if not self.is_available:
            return self._mock_tool_completion(prompt, tools)

        # Convert tools to Anthropic format
        anthropic_tools = []
        for tool in tools:
            if isinstance(tool, ToolDefinition):
                anthropic_tools.append(tool.to_anthropic_format())
            else:
                anthropic_tools.append(tool)

        response = await self._async_client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=system
            or self.config.system_prompt
            or "You are a helpful assistant with access to tools.",
            messages=[{"role": "user", "content": prompt}],
            tools=anthropic_tools,
            tool_choice=tool_choice,
        )

        # Extract tool calls and text
        tool_calls = []
        text_content = ""

        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append(
                    {
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
            elif block.type == "text":
                text_content += block.text

        return {
            "content": text_content,
            "tool_calls": tool_calls,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "stop_reason": response.stop_reason,
        }

    async def _generate_code(
        self,
        description: str,
        language: str = "python",
        context: str | None = None,
    ) -> dict[str, Any]:
        """Generate code from description."""
        system = self.CODE_GENERATION_PROMPT

        prompt = f"""Generate {language} code for the following requirement:

{description}
"""
        if context:
            prompt += f"\nAdditional context:\n{context}"

        prompt += f"\n\nReturn clean, production-ready {language} code."

        result = await self._complete(prompt, system=system, temperature=0.3)

        # Extract code from response
        code = result.get("content", "")

        # Clean up markdown code blocks if present
        if f"```{language}" in code:
            code = code.split(f"```{language}")[-1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        return {
            "code": code,
            "language": language,
            "description": description,
            "model": result.get("model"),
            "usage": result.get("usage"),
        }

    async def _analyze_code(
        self,
        code: str,
        analysis_type: str = "general",
    ) -> dict[str, Any]:
        """Analyze code quality."""
        system = self.ANALYSIS_PROMPT

        analysis_prompts = {
            "general": "Provide a comprehensive code review including quality, readability, and suggestions.",
            "security": "Analyze for security vulnerabilities, injection risks, and security best practices.",
            "performance": "Analyze for performance issues, bottlenecks, and optimization opportunities.",
            "refactoring": "Suggest refactoring improvements and design pattern opportunities.",
        }

        analysis_instruction = analysis_prompts.get(
            analysis_type, analysis_prompts["general"]
        )

        prompt = f"""{analysis_instruction}

Code to analyze:
```
{code}
```

Provide your analysis in a structured format with:
1. Summary
2. Issues found (if any)
3. Specific recommendations
4. Code quality score (1-10)"""

        result = await self._complete(prompt, system=system, temperature=0.3)

        return {
            "analysis": result.get("content", ""),
            "analysis_type": analysis_type,
            "code_length": len(code),
            "model": result.get("model"),
            "usage": result.get("usage"),
        }

    async def _start_conversation(
        self,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Start a new multi-turn conversation."""
        context = ConversationContext(
            system_prompt=system_prompt or self.config.system_prompt,
            model=model or self.config.model,
        )
        self._conversations[context.id] = context

        return {
            "conversation_id": context.id,
            "model": context.model,
            "system_prompt": context.system_prompt,
        }

    async def _continue_conversation(
        self,
        conversation_id: str,
        message: str,
        tools: list[ToolDefinition | dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Continue an existing conversation."""
        context = self._conversations.get(conversation_id)
        if not context:
            raise ValueError(f"Conversation not found: {conversation_id}")

        # Add user message
        context.add_user_message(message)

        if not self.is_available:
            mock_response = f"[Mock response to: {message}]"
            context.add_assistant_message(mock_response)
            return {
                "conversation_id": conversation_id,
                "content": mock_response,
                "mock": True,
            }

        # Prepare messages for API
        messages = [m.to_anthropic_format() for m in context.messages]

        # Make API call
        kwargs = {
            "model": context.model,
            "max_tokens": self.config.max_tokens,
            "messages": messages,
        }

        if context.system_prompt:
            kwargs["system"] = context.system_prompt

        if tools:
            anthropic_tools = []
            for tool in tools:
                if isinstance(tool, ToolDefinition):
                    anthropic_tools.append(tool.to_anthropic_format())
                else:
                    anthropic_tools.append(tool)
            kwargs["tools"] = anthropic_tools

        response = await self._async_client.messages.create(**kwargs)

        # Extract response
        tool_calls = []
        text_content = ""

        for block in response.content:
            if hasattr(block, "type"):
                if block.type == "tool_use":
                    tool_calls.append(
                        {
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                    )
                elif block.type == "text":
                    text_content += block.text

        # Add assistant message to context
        context.add_assistant_message(response.content)
        context.total_tokens += (
            response.usage.input_tokens + response.usage.output_tokens
        )

        return {
            "conversation_id": conversation_id,
            "content": text_content,
            "tool_calls": tool_calls,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_conversation_tokens": context.total_tokens,
            },
            "stop_reason": response.stop_reason,
        }

    async def _decompose_task(
        self,
        task: str,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Decompose a complex task into subtasks."""
        system = """You are a task decomposition expert.
Break down complex tasks into clear, actionable subtasks.
Each subtask should be specific, measurable, and achievable.
Return a structured list of subtasks with dependencies."""

        prompt = f"""Decompose this task into subtasks:

Task: {task}
"""
        if context:
            prompt += f"\nContext: {context}"

        prompt += """

Return a JSON array of subtasks with this structure:
[
  {
    "id": "1",
    "name": "Subtask name",
    "description": "What to do",
    "dependencies": [],  // IDs of tasks this depends on
    "priority": "high|medium|low",
    "estimated_complexity": "simple|moderate|complex"
  }
]"""

        result = await self._complete(prompt, system=system, temperature=0.3)

        # Try to parse JSON from response
        content = result.get("content", "")
        subtasks = []

        try:
            import json

            # Find JSON in response
            if "[" in content:
                json_str = content[content.find("[") : content.rfind("]") + 1]
                subtasks = json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            # Return raw content if JSON parsing fails
            subtasks = [{"raw_response": content}]

        return {
            "task": task,
            "subtasks": subtasks,
            "count": len(subtasks),
            "model": result.get("model"),
        }

    async def stream_completion(
        self,
        prompt: str,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream a completion response.

        Yields:
            Text chunks as they arrive
        """
        if not self.is_available:
            # Mock streaming
            for word in f"[Mock streaming response for: {prompt}]".split():
                yield word + " "
                await asyncio.sleep(0.05)
            return

        async with self._async_client.messages.stream(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=system
            or self.config.system_prompt
            or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs,
    ) -> CapabilityResult:
        """Simple completion convenience method."""
        return await self.execute(
            action="complete",
            prompt=prompt,
            system=system,
            **kwargs,
        )

    async def complete_with_tools(
        self,
        prompt: str,
        tools: list[ToolDefinition | dict[str, Any]],
        **kwargs,
    ) -> CapabilityResult:
        """Completion with tools convenience method."""
        return await self.execute(
            action="complete_with_tools",
            prompt=prompt,
            tools=tools,
            **kwargs,
        )

    async def generate_code(
        self,
        description: str,
        language: str = "python",
        context: str | None = None,
    ) -> CapabilityResult:
        """Generate code convenience method."""
        return await self.execute(
            action="generate_code",
            description=description,
            language=language,
            context=context,
        )

    async def analyze_code(
        self,
        code: str,
        analysis_type: str = "general",
    ) -> CapabilityResult:
        """Analyze code convenience method."""
        return await self.execute(
            action="analyze_code",
            code=code,
            analysis_type=analysis_type,
        )

    async def decompose_task(
        self,
        task: str,
        context: str | None = None,
    ) -> CapabilityResult:
        """Decompose task convenience method."""
        return await self.execute(
            action="decompose_task",
            task=task,
            context=context,
        )

    # =========================================================================
    # Mock Methods (when SDK unavailable)
    # =========================================================================

    def _mock_completion(self, prompt: str) -> dict[str, Any]:
        """Mock completion when SDK unavailable."""
        return {
            "content": f"[Mock response - Anthropic SDK not available]\n\nPrompt was: {prompt[:100]}...",
            "model": "mock",
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "stop_reason": "mock",
            "mock": True,
        }

    def _mock_tool_completion(
        self,
        prompt: str,
        tools: list,
    ) -> dict[str, Any]:
        """Mock tool completion when SDK unavailable."""
        return {
            "content": "[Mock tool response - Anthropic SDK not available]",
            "tool_calls": [],
            "model": "mock",
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "stop_reason": "mock",
            "mock": True,
            "tools_provided": [
                t.get("name") if isinstance(t, dict) else t.name for t in tools
            ],
        }

    # =========================================================================
    # Built-in Tool Definitions
    # =========================================================================

    @staticmethod
    def create_tool(
        name: str,
        description: str,
        parameters: dict[str, Any],
    ) -> ToolDefinition:
        """Create a tool definition.

        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for parameters

        Example:
            >>> tool = AnthropicCapability.create_tool(
            ...     name="search",
            ...     description="Search the web",
            ...     parameters={
            ...         "type": "object",
            ...         "properties": {
            ...             "query": {"type": "string", "description": "Search query"}
            ...         },
            ...         "required": ["query"]
            ...     }
            ... )
        """
        return ToolDefinition(
            name=name,
            description=description,
            input_schema=parameters,
        )

    @classmethod
    def get_builtin_tools(cls) -> dict[str, ToolDefinition]:
        """Get built-in tool definitions."""
        return {
            "read_file": cls.create_tool(
                name="read_file",
                description="Read contents of a file",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to read"},
                    },
                    "required": ["path"],
                },
            ),
            "write_file": cls.create_tool(
                name="write_file",
                description="Write content to a file",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {
                            "type": "string",
                            "description": "Content to write",
                        },
                    },
                    "required": ["path", "content"],
                },
            ),
            "execute_code": cls.create_tool(
                name="execute_code",
                description="Execute Python code",
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute",
                        },
                    },
                    "required": ["code"],
                },
            ),
            "search_web": cls.create_tool(
                name="search_web",
                description="Search the web for information",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            ),
            "list_files": cls.create_tool(
                name="list_files",
                description="List files in a directory",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"},
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern",
                            "default": "*",
                        },
                    },
                    "required": ["path"],
                },
            ),
        }
