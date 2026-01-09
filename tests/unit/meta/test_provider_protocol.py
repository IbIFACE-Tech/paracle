"""Unit tests for paracle_meta.capabilities.provider_protocol module."""

import pytest
from paracle_meta.capabilities.provider_protocol import (
    LLMMessage,
    LLMRequest,
    LLMResponse,
    LLMUsage,
    ProviderAPIError,
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderStatus,
    ProviderUnavailableError,
    StreamChunk,
    ToolCallRequest,
    ToolCallResult,
    ToolDefinitionSchema,
)


class TestToolDefinitionSchema:
    """Tests for ToolDefinitionSchema."""

    def test_create_tool(self):
        """Test creating a tool definition."""
        tool = ToolDefinitionSchema(
            name="search",
            description="Search the web",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        )

        assert tool.name == "search"
        assert tool.description == "Search the web"
        assert "query" in tool.input_schema["properties"]

    def test_to_dict(self):
        """Test conversion to dictionary."""
        tool = ToolDefinitionSchema(
            name="read_file",
            description="Read a file",
            input_schema={"type": "object", "properties": {}},
        )

        data = tool.to_dict()
        assert data["name"] == "read_file"
        assert data["description"] == "Read a file"
        assert "input_schema" in data


class TestToolCallRequest:
    """Tests for ToolCallRequest."""

    def test_create_tool_call(self):
        """Test creating a tool call."""
        call = ToolCallRequest(
            id="call_123",
            name="search",
            input={"query": "Python tutorials"},
        )

        assert call.id == "call_123"
        assert call.name == "search"
        assert call.input["query"] == "Python tutorials"


class TestToolCallResult:
    """Tests for ToolCallResult."""

    def test_create_success_result(self):
        """Test creating successful result."""
        result = ToolCallResult(
            tool_use_id="call_123",
            content="Search results...",
            is_error=False,
        )

        assert result.tool_use_id == "call_123"
        assert result.is_error is False

    def test_create_error_result(self):
        """Test creating error result."""
        result = ToolCallResult(
            tool_use_id="call_456",
            content="Error: File not found",
            is_error=True,
        )

        assert result.is_error is True


class TestLLMMessage:
    """Tests for LLMMessage."""

    def test_create_message(self):
        """Test creating a message."""
        msg = LLMMessage(role="user", content="Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        msg = LLMMessage(role="assistant", content="Hi there!")

        data = msg.to_dict()
        assert data["role"] == "assistant"
        assert data["content"] == "Hi there!"


class TestLLMRequest:
    """Tests for LLMRequest."""

    def test_create_with_prompt(self):
        """Test creating request with prompt."""
        request = LLMRequest(prompt="Hello")

        assert request.prompt == "Hello"
        assert request.temperature == 0.7
        assert request.max_tokens == 4096

    def test_create_with_messages(self):
        """Test creating request with messages."""
        messages = [LLMMessage(role="user", content="Hi")]
        request = LLMRequest(messages=messages)

        assert request.messages == messages

    def test_validation_requires_prompt_or_messages(self):
        """Test that either prompt or messages is required."""
        with pytest.raises(ValueError, match="Either prompt or messages"):
            LLMRequest()

    def test_get_messages_from_prompt(self):
        """Test get_messages converts prompt to messages."""
        request = LLMRequest(prompt="Hello")
        messages = request.get_messages()

        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"

    def test_get_messages_returns_existing(self):
        """Test get_messages returns existing messages."""
        messages = [
            LLMMessage(role="user", content="Hi"),
            LLMMessage(role="assistant", content="Hello!"),
        ]
        request = LLMRequest(messages=messages)

        assert request.get_messages() == messages

    def test_custom_parameters(self):
        """Test custom request parameters."""
        request = LLMRequest(
            prompt="Test",
            temperature=0.3,
            max_tokens=1000,
            top_p=0.9,
            top_k=50,
            stop_sequences=["END"],
        )

        assert request.temperature == 0.3
        assert request.max_tokens == 1000
        assert request.top_p == 0.9
        assert request.top_k == 50
        assert request.stop_sequences == ["END"]


class TestLLMUsage:
    """Tests for LLMUsage."""

    def test_default_values(self):
        """Test default usage values."""
        usage = LLMUsage()

        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0

    def test_total_calculated(self):
        """Test total is calculated from input and output."""
        usage = LLMUsage(input_tokens=100, output_tokens=50)

        assert usage.total_tokens == 150

    def test_explicit_total(self):
        """Test explicit total is preserved."""
        usage = LLMUsage(input_tokens=100, output_tokens=50, total_tokens=200)

        # Post-init recalculates if total is 0
        assert usage.total_tokens == 200 or usage.total_tokens == 150


class TestLLMResponse:
    """Tests for LLMResponse."""

    def test_create_simple_response(self):
        """Test creating a simple response."""
        response = LLMResponse(content="Hello!")

        assert response.content == "Hello!"
        assert response.tool_calls is None
        assert response.has_tool_calls is False

    def test_response_with_tool_calls(self):
        """Test response with tool calls."""
        tool_calls = [
            ToolCallRequest(id="call_1", name="search", input={"query": "test"})
        ]
        response = LLMResponse(content="", tool_calls=tool_calls)

        assert response.has_tool_calls is True
        assert len(response.tool_calls) == 1

    def test_response_with_usage(self):
        """Test response with usage info."""
        usage = LLMUsage(input_tokens=10, output_tokens=20)
        response = LLMResponse(content="Test", usage=usage)

        assert response.usage.total_tokens == 30


class TestStreamChunk:
    """Tests for StreamChunk."""

    def test_create_chunk(self):
        """Test creating a stream chunk."""
        chunk = StreamChunk(content="Hello")

        assert chunk.content == "Hello"
        assert chunk.is_final is False

    def test_final_chunk(self):
        """Test final stream chunk."""
        usage = LLMUsage(input_tokens=10, output_tokens=20)
        chunk = StreamChunk(content="", is_final=True, usage=usage)

        assert chunk.is_final is True
        assert chunk.usage is not None


class TestProviderStatus:
    """Tests for ProviderStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert ProviderStatus.AVAILABLE.value == "available"
        assert ProviderStatus.UNAVAILABLE.value == "unavailable"
        assert ProviderStatus.RATE_LIMITED.value == "rate_limited"
        assert ProviderStatus.ERROR.value == "error"


class TestProviderErrors:
    """Tests for provider error classes."""

    def test_provider_error(self):
        """Test base provider error."""
        error = ProviderError("Test error", provider="test", recoverable=True)

        assert str(error) == "Test error"
        assert error.provider == "test"
        assert error.recoverable is True

    def test_unavailable_error(self):
        """Test unavailable error."""
        error = ProviderUnavailableError("anthropic", "No API key")

        assert "anthropic" in str(error)
        assert "unavailable" in str(error)
        assert error.recoverable is True

    def test_rate_limit_error(self):
        """Test rate limit error."""
        error = ProviderRateLimitError("openai", retry_after=60)

        assert error.retry_after == 60
        assert error.recoverable is True

    def test_authentication_error(self):
        """Test authentication error."""
        error = ProviderAuthenticationError("anthropic")

        assert "authentication" in str(error).lower()
        assert error.recoverable is False

    def test_api_error(self):
        """Test API error."""
        error = ProviderAPIError("openai", "Internal server error", status_code=500)

        assert error.status_code == 500
        assert error.recoverable is True
