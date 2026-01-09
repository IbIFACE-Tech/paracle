"""Unit tests for paracle_meta.capabilities.anthropic_integration module."""

import pytest

from paracle_meta.capabilities.anthropic_integration import (
    AnthropicCapability,
    AnthropicConfig,
    ClaudeModel,
    ConversationContext,
    Message,
    ToolCall,
    ToolDefinition,
    ToolResult,
)


class TestClaudeModel:
    """Tests for ClaudeModel enum."""

    def test_model_values(self):
        """Test model enum values."""
        assert ClaudeModel.OPUS.value == "claude-opus-4-20250514"
        assert ClaudeModel.SONNET.value == "claude-sonnet-4-20250514"
        assert ClaudeModel.HAIKU.value == "claude-3-5-haiku-20241022"

    def test_legacy_models(self):
        """Test legacy model values."""
        assert ClaudeModel.OPUS_3.value == "claude-3-opus-20240229"
        assert ClaudeModel.SONNET_35.value == "claude-3-5-sonnet-20241022"


class TestToolDefinition:
    """Tests for ToolDefinition."""

    def test_create_tool(self):
        """Test creating a tool definition."""
        tool = ToolDefinition(
            name="search",
            description="Search the web",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"],
            },
        )

        assert tool.name == "search"
        assert tool.description == "Search the web"
        assert "query" in tool.input_schema["properties"]

    def test_to_anthropic_format(self):
        """Test conversion to Anthropic format."""
        tool = ToolDefinition(
            name="read_file",
            description="Read a file",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        )

        anthropic_format = tool.to_anthropic_format()

        assert anthropic_format["name"] == "read_file"
        assert anthropic_format["description"] == "Read a file"
        assert anthropic_format["input_schema"]["type"] == "object"


class TestToolCall:
    """Tests for ToolCall."""

    def test_create_tool_call(self):
        """Test creating a tool call."""
        call = ToolCall(
            id="call_123",
            name="search",
            input={"query": "Python tutorials"},
        )

        assert call.id == "call_123"
        assert call.name == "search"
        assert call.input["query"] == "Python tutorials"


class TestToolResult:
    """Tests for ToolResult."""

    def test_create_success_result(self):
        """Test creating successful tool result."""
        result = ToolResult(
            tool_use_id="call_123",
            content="Search results: ...",
            is_error=False,
        )

        assert result.tool_use_id == "call_123"
        assert result.content == "Search results: ..."
        assert result.is_error is False

    def test_create_error_result(self):
        """Test creating error tool result."""
        result = ToolResult(
            tool_use_id="call_456",
            content="Error: File not found",
            is_error=True,
        )

        assert result.is_error is True


class TestMessage:
    """Tests for Message."""

    def test_create_message(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_to_anthropic_format(self):
        """Test conversion to Anthropic format."""
        msg = Message(role="assistant", content="Hi there!")

        anthropic_format = msg.to_anthropic_format()

        assert anthropic_format["role"] == "assistant"
        assert anthropic_format["content"] == "Hi there!"


class TestConversationContext:
    """Tests for ConversationContext."""

    def test_create_context(self):
        """Test creating conversation context."""
        ctx = ConversationContext()

        assert ctx.id.startswith("conv_")
        assert ctx.messages == []
        assert ctx.total_tokens == 0

    def test_add_user_message(self):
        """Test adding user message."""
        ctx = ConversationContext()
        ctx.add_user_message("Hello, Claude!")

        assert len(ctx.messages) == 1
        assert ctx.messages[0].role == "user"
        assert ctx.messages[0].content == "Hello, Claude!"

    def test_add_assistant_message(self):
        """Test adding assistant message."""
        ctx = ConversationContext()
        ctx.add_assistant_message("Hello! How can I help?")

        assert len(ctx.messages) == 1
        assert ctx.messages[0].role == "assistant"

    def test_add_tool_result(self):
        """Test adding tool result."""
        ctx = ConversationContext()
        ctx.add_tool_result("call_123", "Result data", is_error=False)

        assert len(ctx.messages) == 1
        assert ctx.messages[0].role == "user"
        assert ctx.messages[0].content[0]["type"] == "tool_result"

    def test_multi_turn_conversation(self):
        """Test multi-turn conversation."""
        ctx = ConversationContext(system_prompt="You are helpful.")

        ctx.add_user_message("What is Python?")
        ctx.add_assistant_message("Python is a programming language.")
        ctx.add_user_message("Tell me more.")

        assert len(ctx.messages) == 3
        assert ctx.system_prompt == "You are helpful."


class TestAnthropicConfig:
    """Tests for AnthropicConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AnthropicConfig()
        assert config.api_key is None
        assert config.model == ClaudeModel.SONNET.value
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.enable_tool_use is True
        assert config.enable_streaming is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = AnthropicConfig(
            api_key="sk-test-key",
            model=ClaudeModel.OPUS.value,
            max_tokens=8192,
            temperature=0.5,
            system_prompt="You are a code expert.",
        )
        assert config.api_key == "sk-test-key"
        assert config.model == ClaudeModel.OPUS.value
        assert config.max_tokens == 8192
        assert config.temperature == 0.5
        assert config.system_prompt == "You are a code expert."


class TestAnthropicCapability:
    """Tests for AnthropicCapability."""

    @pytest.fixture
    def anthropic_capability(self):
        """Create Anthropic capability instance (no API key)."""
        return AnthropicCapability()

    @pytest.fixture
    def anthropic_capability_configured(self):
        """Create configured Anthropic capability."""
        config = AnthropicConfig(
            api_key="test-key",  # Won't work but tests mock path
            model=ClaudeModel.SONNET.value,
        )
        return AnthropicCapability(config=config)

    def test_initialization(self, anthropic_capability):
        """Test capability initialization."""
        assert anthropic_capability.name == "anthropic"
        assert (
            "Claude" in anthropic_capability.description
            or "AI" in anthropic_capability.description
        )

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, anthropic_capability):
        """Test initialize and shutdown lifecycle."""
        await anthropic_capability.initialize()
        assert anthropic_capability.is_initialized is True

        await anthropic_capability.shutdown()
        assert anthropic_capability.is_initialized is False
        assert anthropic_capability._client is None

    @pytest.mark.asyncio
    async def test_is_available_without_key(self, anthropic_capability):
        """Test availability without API key."""
        await anthropic_capability.initialize()

        # Without API key or anthropic installed, should use mock
        assert (
            anthropic_capability.is_available is False
            or anthropic_capability._available is False
        )

        await anthropic_capability.shutdown()

    @pytest.mark.asyncio
    async def test_complete_mock(self, anthropic_capability):
        """Test completion returns mock result when unavailable."""
        await anthropic_capability.initialize()

        result = await anthropic_capability.execute(
            action="complete",
            prompt="What is Python?",
        )

        # Should succeed with mock response
        assert result.success is True
        assert "content" in result.output
        assert result.output.get("mock") is True or "content" in result.output

        await anthropic_capability.shutdown()

    @pytest.mark.asyncio
    async def test_generate_code_mock(self, anthropic_capability):
        """Test code generation with mock."""
        await anthropic_capability.initialize()

        result = await anthropic_capability.execute(
            action="generate_code",
            description="Create a hello world function",
            language="python",
        )

        assert result.success is True
        assert "code" in result.output or "content" in result.output

        await anthropic_capability.shutdown()

    @pytest.mark.asyncio
    async def test_analyze_code_mock(self, anthropic_capability):
        """Test code analysis with mock."""
        await anthropic_capability.initialize()

        code = """
def add(a, b):
    return a + b
"""
        result = await anthropic_capability.execute(
            action="analyze_code",
            code=code,
            analysis_type="general",
        )

        assert result.success is True
        assert result.output is not None

        await anthropic_capability.shutdown()

    @pytest.mark.asyncio
    async def test_start_conversation(self, anthropic_capability):
        """Test starting a conversation."""
        await anthropic_capability.initialize()

        result = await anthropic_capability.execute(
            action="start_conversation",
            system_prompt="You are a Python tutor.",
        )

        assert result.success is True
        assert "conversation_id" in result.output

        await anthropic_capability.shutdown()

    @pytest.mark.asyncio
    async def test_continue_conversation(self, anthropic_capability):
        """Test continuing a conversation."""
        await anthropic_capability.initialize()

        # Start conversation
        start_result = await anthropic_capability.execute(
            action="start_conversation",
        )
        conv_id = start_result.output["conversation_id"]

        # Continue conversation
        result = await anthropic_capability.execute(
            action="continue_conversation",
            conversation_id=conv_id,
            message="Hello!",
        )

        assert result.success is True
        assert "content" in result.output or "response" in result.output

        await anthropic_capability.shutdown()

    @pytest.mark.asyncio
    async def test_decompose_task_mock(self, anthropic_capability):
        """Test task decomposition with mock."""
        await anthropic_capability.initialize()

        result = await anthropic_capability.execute(
            action="decompose_task",
            task="Build a REST API with user authentication",
        )

        assert result.success is True
        # Mock returns subtasks key
        has_expected_key = (
            "steps" in result.output
            or "tasks" in result.output
            or "subtasks" in result.output
            or "content" in result.output
        )
        assert has_expected_key

        await anthropic_capability.shutdown()

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, anthropic_capability):
        """Test execute with unknown action."""
        await anthropic_capability.initialize()

        result = await anthropic_capability.execute(action="unknown_action")

        assert result.success is False
        assert "Unknown action" in result.error

        await anthropic_capability.shutdown()


class TestAnthropicCapabilityConvenience:
    """Tests for convenience methods."""

    @pytest.fixture
    def capability(self):
        """Create capability for tests."""
        return AnthropicCapability()

    @pytest.mark.asyncio
    async def test_complete_convenience(self, capability):
        """Test complete convenience method."""
        await capability.initialize()

        result = await capability.complete("Hello")

        assert result.success is True

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_generate_code_convenience(self, capability):
        """Test generate_code convenience method."""
        await capability.initialize()

        result = await capability.generate_code(
            "Create a function that adds two numbers",
            language="python",
        )

        assert result.success is True

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_analyze_code_convenience(self, capability):
        """Test analyze_code convenience method."""
        await capability.initialize()

        result = await capability.analyze_code("def foo(): pass")

        assert result.success is True

        await capability.shutdown()


class TestBuiltInTools:
    """Tests for built-in tool definitions."""

    @pytest.fixture
    def capability(self):
        """Create capability for tests."""
        return AnthropicCapability()

    @pytest.mark.asyncio
    async def test_get_builtin_tools(self, capability):
        """Test getting built-in tools."""
        await capability.initialize()

        tools = capability.get_builtin_tools()

        # Returns a dict of tool name -> ToolDefinition
        assert isinstance(tools, dict)
        assert len(tools) > 0

        # Check that tools have required fields
        for name, tool in tools.items():
            assert isinstance(name, str)
            assert hasattr(tool, "name")

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_complete_with_tools_mock(self, capability):
        """Test completion with tools using mock."""
        await capability.initialize()

        tools = [
            ToolDefinition(
                name="search",
                description="Search the web",
                input_schema={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                },
            )
        ]

        result = await capability.complete_with_tools(
            prompt="Search for Python tutorials",
            tools=tools,
        )

        assert result.success is True

        await capability.shutdown()
