"""Tests for provider registry."""

from collections.abc import AsyncIterator
from typing import Any

import pytest
from paracle_providers.base import (
    ChatMessage,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    StreamChunk,
)
from paracle_providers.exceptions import ProviderNotFoundError
from paracle_providers.registry import ProviderRegistry


class MockProvider(LLMProvider):
    """Mock provider for testing."""

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> LLMResponse:
        return LLMResponse(content="mock response")

    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        yield StreamChunk(content="mock")

    def validate_config(self, config: dict[str, Any]) -> bool:
        return True

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def supported_models(self) -> list[str]:
        return ["mock-model"]


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        ProviderRegistry.clear()

    def test_register_provider(self):
        """Test registering a provider."""
        ProviderRegistry.register("mock", MockProvider)

        assert ProviderRegistry.is_registered("mock")
        assert "mock" in ProviderRegistry.list_providers()

    def test_register_invalid_provider(self):
        """Test registering a non-provider class raises TypeError."""

        class NotAProvider:
            pass

        with pytest.raises(TypeError):
            ProviderRegistry.register("invalid", NotAProvider)  # type: ignore

    def test_get_provider_class(self):
        """Test retrieving a provider class."""
        ProviderRegistry.register("mock", MockProvider)

        provider_class = ProviderRegistry.get_provider_class("mock")
        assert provider_class is MockProvider

    def test_get_nonexistent_provider(self):
        """Test retrieving a non-registered provider raises error."""
        with pytest.raises(ProviderNotFoundError) as exc_info:
            ProviderRegistry.get_provider_class("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_create_provider(self):
        """Test creating a provider instance."""
        ProviderRegistry.register("mock", MockProvider)

        provider = ProviderRegistry.create_provider("mock", api_key="test-key")

        assert isinstance(provider, MockProvider)
        assert provider.api_key == "test-key"

    def test_create_provider_with_kwargs(self):
        """Test creating a provider with custom kwargs."""
        ProviderRegistry.register("mock", MockProvider)

        provider = ProviderRegistry.create_provider(
            "mock", api_key="test", custom_param="value"
        )

        assert provider.api_key == "test"
        assert provider.config["custom_param"] == "value"

    def test_list_providers(self):
        """Test listing all providers."""
        ProviderRegistry.register("mock1", MockProvider)
        ProviderRegistry.register("mock2", MockProvider)

        providers = ProviderRegistry.list_providers()

        assert len(providers) == 2
        assert "mock1" in providers
        assert "mock2" in providers

    def test_list_providers_empty(self):
        """Test listing providers when none are registered."""
        providers = ProviderRegistry.list_providers()
        assert providers == []

    def test_is_registered(self):
        """Test checking if provider is registered."""
        assert not ProviderRegistry.is_registered("mock")

        ProviderRegistry.register("mock", MockProvider)

        assert ProviderRegistry.is_registered("mock")

    def test_unregister_provider(self):
        """Test unregistering a provider."""
        ProviderRegistry.register("mock", MockProvider)
        assert ProviderRegistry.is_registered("mock")

        ProviderRegistry.unregister("mock")

        assert not ProviderRegistry.is_registered("mock")

    def test_unregister_nonexistent_provider(self):
        """Test unregistering a non-existent provider raises error."""
        with pytest.raises(ProviderNotFoundError):
            ProviderRegistry.unregister("nonexistent")

    def test_clear_registry(self):
        """Test clearing all providers."""
        ProviderRegistry.register("mock1", MockProvider)
        ProviderRegistry.register("mock2", MockProvider)

        assert len(ProviderRegistry.list_providers()) == 2

        ProviderRegistry.clear()

        assert len(ProviderRegistry.list_providers()) == 0

    def test_multiple_registrations_same_name(self):
        """Test registering with same name replaces previous."""
        ProviderRegistry.register("mock", MockProvider)

        class AnotherMockProvider(MockProvider):
            pass

        ProviderRegistry.register("mock", AnotherMockProvider)

        provider_class = ProviderRegistry.get_provider_class("mock")
        assert provider_class is AnotherMockProvider
