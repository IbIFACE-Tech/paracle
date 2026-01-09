"""Tests for LLM provider base models and protocol."""

import pytest
from datetime import datetime

from paracle_providers.base import (
    ChatMessage,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    StreamChunk,
    TokenUsage,
)


class TestChatMessage:
    """Tests for ChatMessage model."""

    def test_create_user_message(self):
        """Test creating a user message."""
        msg = ChatMessage(role="user", content="Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.name is None
        assert msg.tool_call_id is None

    def test_create_system_message_with_name(self):
        """Test creating a system message with name."""
        msg = ChatMessage(role="system", content="You are helpful", name="context")

        assert msg.role == "system"
        assert msg.content == "You are helpful"
        assert msg.name == "context"

    def test_message_is_frozen(self):
        """Test that messages are immutable."""
        msg = ChatMessage(role="user", content="Hello")

        with pytest.raises(Exception):  # Pydantic ValidationError
            msg.content = "Changed"


class TestLLMConfig:
    """Tests for LLMConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LLMConfig()

        assert config.temperature == 0.7
        assert config.max_tokens is None
        assert config.timeout == 30.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = LLMConfig(
            temperature=0.5,
            max_tokens=1000,
            top_p=0.9,
            timeout=60.0,
        )

        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        assert config.top_p == 0.9
        assert config.timeout == 60.0

    def test_temperature_validation_min(self):
        """Test temperature minimum bound."""
        with pytest.raises(ValueError):
            LLMConfig(temperature=-0.1)

    def test_temperature_validation_max(self):
        """Test temperature maximum bound."""
        with pytest.raises(ValueError):
            LLMConfig(temperature=2.1)

    def test_max_tokens_validation(self):
        """Test max_tokens must be positive."""
        with pytest.raises(ValueError):
            LLMConfig(max_tokens=0)


class TestTokenUsage:
    """Tests for TokenUsage model."""

    def test_create_usage(self):
        """Test creating token usage."""
        usage = TokenUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )

        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30

    def test_default_usage(self):
        """Test default usage values."""
        usage = TokenUsage()

        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0


class TestLLMResponse:
    """Tests for LLMResponse model."""

    def test_create_response(self):
        """Test creating a response."""
        response = LLMResponse(
            content="Hello there!",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
            model="gpt-4",
        )

        assert response.content == "Hello there!"
        assert response.finish_reason == "stop"
        assert response.usage.total_tokens == 8
        assert response.model == "gpt-4"
        assert isinstance(response.created_at, datetime)

    def test_response_with_metadata(self):
        """Test response with custom metadata."""
        response = LLMResponse(
            content="Test",
            metadata={"custom_field": "value"},
        )

        assert response.metadata["custom_field"] == "value"

    def test_response_is_frozen(self):
        """Test that responses are immutable."""
        response = LLMResponse(content="Test")

        with pytest.raises(Exception):
            response.content = "Changed"


class TestStreamChunk:
    """Tests for StreamChunk model."""

    def test_create_chunk(self):
        """Test creating a stream chunk."""
        chunk = StreamChunk(content="partial")

        assert chunk.content == "partial"
        assert chunk.finish_reason is None

    def test_final_chunk(self):
        """Test final chunk with finish reason."""
        chunk = StreamChunk(content="", finish_reason="stop")

        assert chunk.content == ""
        assert chunk.finish_reason == "stop"


class TestLLMProviderProtocol:
    """Tests for LLMProvider protocol."""

    def test_provider_is_abstract(self):
        """Test that LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider(api_key="test")  # type: ignore

    def test_provider_requires_implementation(self):
        """Test that concrete providers must implement abstract methods."""

        class IncompleteProvider(LLMProvider):
            """Provider missing implementations."""

            @property
            def provider_name(self) -> str:
                return "incomplete"

            @property
            def supported_models(self) -> list[str]:
                return []

        # This should fail because abstract methods aren't implemented
        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore
