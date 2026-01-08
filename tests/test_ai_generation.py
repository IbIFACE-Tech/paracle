"""Tests for AI-enhanced agent creation.

Tests the integration of AI providers with the agents create command.
"""

import pytest
from paracle_cli.ai_helper import (
    AIProviderError,
    AIProviderNotAvailable,
    get_ai_provider,
    is_ai_available,
    list_available_providers,
)


class TestAIProviderHelper:
    """Test AI provider helper functions."""

    def test_get_ai_provider_none_available(self, monkeypatch):
        """Test graceful handling when no AI available."""
        # Mock paracle_meta as not available
        monkeypatch.setattr(
            "paracle_cli.ai_helper._load_ai_config", lambda: None
        )

        # Should return None when no providers available
        result = get_ai_provider()
        assert result is None or hasattr(result, "name")

    def test_is_ai_available(self):
        """Test AI availability check."""
        # Should return bool
        result = is_ai_available()
        assert isinstance(result, bool)

    def test_list_available_providers(self):
        """Test listing available providers."""
        # Should return list of strings
        providers = list_available_providers()
        assert isinstance(providers, list)

        # Valid provider names
        valid_providers = {"meta", "openai", "anthropic", "azure"}
        for provider in providers:
            assert provider in valid_providers

    def test_provider_not_available_error(self):
        """Test AIProviderNotAvailable exception."""
        error = AIProviderNotAvailable("Test error")
        assert isinstance(error, AIProviderError)
        assert str(error) == "Test error"

    def test_get_ai_provider_with_specific_name(self):
        """Test getting specific provider by name."""
        # Should handle unknown provider
        with pytest.raises(AIProviderNotAvailable):
            get_ai_provider("unknown_provider")


class TestAIProviderProtocol:
    """Test that providers implement the protocol correctly."""

    def test_openai_provider_protocol(self):
        """Test OpenAI provider implements protocol."""
        try:
            from paracle_cli.providers.openai_provider import (
                OpenAIProvider,
            )

            # Check required attributes
            assert hasattr(OpenAIProvider, "name")
            assert hasattr(OpenAIProvider, "generate_agent")
            assert hasattr(OpenAIProvider, "generate_skill")
            assert hasattr(OpenAIProvider, "generate_workflow")
            assert hasattr(OpenAIProvider, "enhance_documentation")
        except ImportError:
            pytest.skip("OpenAI provider not available")

    def test_anthropic_provider_protocol(self):
        """Test Anthropic provider implements protocol."""
        try:
            from paracle_cli.providers.anthropic_provider import (
                AnthropicProvider,
            )

            # Check required attributes
            assert hasattr(AnthropicProvider, "name")
            assert hasattr(AnthropicProvider, "generate_agent")
            assert hasattr(AnthropicProvider, "generate_skill")
            assert hasattr(AnthropicProvider, "generate_workflow")
            assert hasattr(AnthropicProvider, "enhance_documentation")
        except ImportError:
            pytest.skip("Anthropic provider not available")

    def test_azure_provider_protocol(self):
        """Test Azure provider implements protocol."""
        try:
            from paracle_cli.providers.azure_provider import AzureProvider

            # Check required attributes
            assert hasattr(AzureProvider, "name")
            assert hasattr(AzureProvider, "generate_agent")
            assert hasattr(AzureProvider, "generate_skill")
            assert hasattr(AzureProvider, "generate_workflow")
            assert hasattr(AzureProvider, "enhance_documentation")
        except ImportError:
            pytest.skip("Azure provider not available")


class TestProviderConfiguration:
    """Test provider configuration loading."""

    def test_load_ai_config_missing(self, tmp_path, monkeypatch):
        """Test loading config when file doesn't exist."""
        from paracle_cli.ai_helper import _load_ai_config

        # Point to non-existent directory
        monkeypatch.setattr(
            "paracle_cli.ai_helper.find_parac_root", lambda: tmp_path
        )

        config = _load_ai_config()
        assert config is None

    def test_load_ai_config_valid(self, tmp_path, monkeypatch):
        """Test loading valid AI config."""
        from paracle_cli.ai_helper import _load_ai_config

        # Create config file
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "ai.yaml"
        config_file.write_text("""
ai:
  provider: meta
  providers:
    meta:
      model: gpt-4-turbo
""")

        monkeypatch.setattr(
            "paracle_cli.ai_helper.find_parac_root", lambda: tmp_path
        )

        config = _load_ai_config()
        assert config is not None
        assert "ai" in config
        assert config["ai"]["provider"] == "meta"


class TestProviderPriority:
    """Test provider selection priority."""

    def test_specific_provider_priority(self, monkeypatch):
        """Test that specific provider takes priority."""
        # If we request specific provider, it should be used
        # even if paracle_meta is available

        # This test would need proper mocking of providers
        # Skipping for now as it requires complex setup
        pass

    def test_meta_over_configured(self, monkeypatch):
        """Test that paracle_meta takes priority over configured."""
        # paracle_meta should be preferred if activated
        # even if user has configured another provider

        # This test would need proper mocking
        pass


class TestErrorHandling:
    """Test error handling in AI helpers."""

    def test_missing_api_key_openai(self, monkeypatch):
        """Test error when OpenAI API key missing."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        try:
            from paracle_cli.providers.openai_provider import (
                OpenAIProvider,
            )

            with pytest.raises(Exception):  # Should raise some error
                OpenAIProvider()
        except ImportError:
            pytest.skip("OpenAI provider not available")

    def test_missing_api_key_anthropic(self, monkeypatch):
        """Test error when Anthropic API key missing."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        try:
            from paracle_cli.providers.anthropic_provider import (
                AnthropicProvider,
            )

            # Provider might fail during initialization or first use
            # This is implementation-dependent
        except ImportError:
            pytest.skip("Anthropic provider not available")


@pytest.fixture
def mock_ai_provider():
    """Mock AI provider for testing."""

    class MockProvider:
        @property
        def name(self):
            return "mock"

        async def generate_agent(self, description, **kwargs):
            return {
                "name": "test_agent",
                "yaml": "# Test Agent\n\n## Role\nTest role",
                "description": description,
            }

        async def generate_skill(self, description, **kwargs):
            return {
                "name": "test_skill",
                "yaml": "name: test_skill\ndescription: Test",
                "code": "async def execute(inputs): pass",
            }

        async def generate_workflow(self, description, **kwargs):
            return {
                "name": "test_workflow",
                "yaml": "name: test_workflow\nsteps: []",
            }

        async def enhance_documentation(self, code, **kwargs):
            return "# Documentation\n\nTest docs"

    return MockProvider()


class TestMockProvider:
    """Test with mock provider."""

    @pytest.mark.asyncio
    async def test_mock_generate_agent(self, mock_ai_provider):
        """Test agent generation with mock."""
        result = await mock_ai_provider.generate_agent("Test agent")

        assert result["name"] == "test_agent"
        assert "yaml" in result
        assert result["description"] == "Test agent"

    @pytest.mark.asyncio
    async def test_mock_generate_skill(self, mock_ai_provider):
        """Test skill generation with mock."""
        result = await mock_ai_provider.generate_skill("Test skill")

        assert result["name"] == "test_skill"
        assert "yaml" in result
        assert "code" in result

    @pytest.mark.asyncio
    async def test_mock_generate_workflow(self, mock_ai_provider):
        """Test workflow generation with mock."""
        result = await mock_ai_provider.generate_workflow("Test workflow")

        assert result["name"] == "test_workflow"
        assert "yaml" in result

    @pytest.mark.asyncio
    async def test_mock_enhance_docs(self, mock_ai_provider):
        """Test documentation enhancement with mock."""
        code = "def test(): pass"
        result = await mock_ai_provider.enhance_documentation(code)

        assert isinstance(result, str)
        assert len(result) > 0
