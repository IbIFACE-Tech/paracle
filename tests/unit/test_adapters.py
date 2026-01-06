"""Comprehensive tests for framework adapters.

Tests the adapter base class, registry, and all framework adapters
with mock implementations to avoid requiring external dependencies.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Any

from paracle_domain.models import AgentSpec, WorkflowSpec, WorkflowStep
from paracle_adapters import (
    FrameworkAdapter,
    AdapterRegistry,
    AdapterError,
    AdapterNotFoundError,
    AdapterConfigurationError,
    AdapterExecutionError,
    FeatureNotSupportedError,
    get_adapter_class,
    list_available_adapters,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_agent_spec():
    """Create a sample agent specification."""
    return AgentSpec(
        name="test-agent",
        model="gpt-4",
        provider="openai",
        system_prompt="You are a helpful assistant.",
        temperature=0.7,
        config={
            "tools": ["search", "calculator"],
            "role": "Assistant",
            "goal": "Help users with tasks",
        },
    )


@pytest.fixture
def sample_workflow_spec():
    """Create a sample workflow specification."""
    return WorkflowSpec(
        name="test-workflow",
        description="A test workflow",
        steps=[
            WorkflowStep(
                id="step1",
                name="First Step",
                agent="agent1",
                inputs={"task": "Do something"},
            ),
            WorkflowStep(
                id="step2",
                name="Second Step",
                agent="agent2",
                depends_on=["step1"],
                inputs={"task": "Do something else"},
            ),
        ],
    )


class MockAdapter(FrameworkAdapter):
    """Mock adapter for testing."""

    async def create_agent(self, agent_spec: AgentSpec) -> Any:
        return {"type": "mock", "spec": agent_spec}

    async def execute_agent(
        self, agent_instance: Any, input_data: dict, **kwargs
    ) -> dict:
        return {
            "response": f"Mock response to: {input_data.get('input', '')}",
            "metadata": {"framework": "mock"},
        }

    async def create_workflow(self, workflow_spec: WorkflowSpec) -> Any:
        return {"type": "mock_workflow", "spec": workflow_spec}

    async def execute_workflow(
        self, workflow_instance: Any, inputs: dict, **kwargs
    ) -> dict:
        return {
            "response": {"result": "Mock workflow result"},
            "metadata": {"framework": "mock"},
        }

    @property
    def framework_name(self) -> str:
        return "mock"

    @property
    def supported_features(self) -> list[str]:
        return ["agents", "workflows", "tools"]

    def validate_config(self, config: dict) -> bool:
        return True


# ============================================================================
# Base Adapter Tests
# ============================================================================

class TestFrameworkAdapter:
    """Tests for the FrameworkAdapter base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that FrameworkAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            FrameworkAdapter()

    def test_mock_adapter_instantiation(self):
        """Test that concrete adapters can be instantiated."""
        adapter = MockAdapter()
        assert adapter.framework_name == "mock"

    def test_supports_feature(self):
        """Test feature support checking."""
        adapter = MockAdapter()
        assert adapter.supports_feature("agents") is True
        assert adapter.supports_feature("workflows") is True
        assert adapter.supports_feature("unknown") is False

    def test_config_storage(self):
        """Test configuration is stored correctly."""
        adapter = MockAdapter(verbose=True, max_iterations=10)
        assert adapter.config["verbose"] is True
        assert adapter.config["max_iterations"] == 10

    def test_repr(self):
        """Test string representation."""
        adapter = MockAdapter()
        assert "MockAdapter" in repr(adapter)
        assert "mock" in repr(adapter)

    @pytest.mark.asyncio
    async def test_create_agent(self, sample_agent_spec):
        """Test agent creation."""
        adapter = MockAdapter()
        agent = await adapter.create_agent(sample_agent_spec)
        assert agent["type"] == "mock"
        assert agent["spec"] == sample_agent_spec

    @pytest.mark.asyncio
    async def test_execute_agent(self, sample_agent_spec):
        """Test agent execution."""
        adapter = MockAdapter()
        agent = await adapter.create_agent(sample_agent_spec)
        result = await adapter.execute_agent(agent, {"input": "Hello"})
        assert "response" in result
        assert "Mock response" in result["response"]

    @pytest.mark.asyncio
    async def test_create_workflow(self, sample_workflow_spec):
        """Test workflow creation."""
        adapter = MockAdapter()
        workflow = await adapter.create_workflow(sample_workflow_spec)
        assert workflow["type"] == "mock_workflow"

    @pytest.mark.asyncio
    async def test_execute_workflow(self, sample_workflow_spec):
        """Test workflow execution."""
        adapter = MockAdapter()
        workflow = await adapter.create_workflow(sample_workflow_spec)
        result = await adapter.execute_workflow(workflow, {"input": "test"})
        assert "response" in result


# ============================================================================
# Registry Tests
# ============================================================================

class TestAdapterRegistry:
    """Tests for the AdapterRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        AdapterRegistry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        AdapterRegistry.clear()

    def test_register_adapter(self):
        """Test adapter registration."""
        AdapterRegistry.register("mock", MockAdapter)
        assert AdapterRegistry.is_registered("mock")

    def test_unregister_adapter(self):
        """Test adapter unregistration."""
        AdapterRegistry.register("mock", MockAdapter)
        AdapterRegistry.unregister("mock")
        assert not AdapterRegistry.is_registered("mock")

    def test_get_adapter_class(self):
        """Test retrieving adapter class."""
        AdapterRegistry.register("mock", MockAdapter)
        cls = AdapterRegistry.get_adapter_class("mock")
        assert cls == MockAdapter

    def test_get_nonexistent_raises(self):
        """Test that getting non-existent adapter raises error."""
        with pytest.raises(AdapterNotFoundError):
            AdapterRegistry.get_adapter_class("nonexistent")

    def test_create_adapter_instance(self):
        """Test creating adapter instance."""
        AdapterRegistry.register("mock", MockAdapter)
        adapter = AdapterRegistry.create_adapter("mock", verbose=True)
        assert isinstance(adapter, MockAdapter)
        assert adapter.config["verbose"] is True

    def test_list_adapters(self):
        """Test listing registered adapters."""
        AdapterRegistry.register("mock1", MockAdapter)
        AdapterRegistry.register("mock2", MockAdapter)
        adapters = AdapterRegistry.list_adapters()
        assert "mock1" in adapters
        assert "mock2" in adapters


# ============================================================================
# Exception Tests
# ============================================================================

class TestAdapterExceptions:
    """Tests for adapter exceptions."""

    def test_adapter_error(self):
        """Test base AdapterError."""
        error = AdapterError("Test error")
        assert str(error) == "Test error"

    def test_adapter_not_found_error(self):
        """Test AdapterNotFoundError."""
        error = AdapterNotFoundError("unknown")
        assert "unknown" in str(error)
        assert error.adapter_name == "unknown"

    def test_adapter_configuration_error(self):
        """Test AdapterConfigurationError."""
        error = AdapterConfigurationError(
            "Invalid config",
            framework="langchain",
        )
        assert "Invalid config" in str(error)

    def test_adapter_execution_error(self):
        """Test AdapterExecutionError."""
        original = ValueError("Original error")
        error = AdapterExecutionError(
            "Execution failed",
            framework="langchain",
            original_error=original,
        )
        assert "Execution failed" in str(error)
        assert error.original_error == original

    def test_feature_not_supported_error(self):
        """Test FeatureNotSupportedError."""
        error = FeatureNotSupportedError("langchain", "streaming")
        assert "streaming" in str(error)
        assert "langchain" in str(error)


# ============================================================================
# Lazy Import Tests
# ============================================================================

class TestLazyImports:
    """Tests for lazy adapter imports."""

    def test_list_available_adapters(self):
        """Test listing available adapters."""
        available = list_available_adapters()
        assert isinstance(available, dict)
        assert "langchain" in available
        assert "llamaindex" in available
        assert "crewai" in available
        assert "autogen" in available
        assert "msaf" in available

    def test_get_adapter_class_unknown(self):
        """Test getting unknown adapter raises error."""
        with pytest.raises(AdapterNotFoundError):
            get_adapter_class("unknown_framework")


# ============================================================================
# LangChain Adapter Tests (Mocked)
# ============================================================================

class TestLangChainAdapterMocked:
    """Tests for LangChain adapter with mocked dependencies."""

    @pytest.fixture
    def mock_langchain(self):
        """Mock LangChain dependencies."""
        with patch.dict("sys.modules", {
            "langchain_core": MagicMock(),
            "langchain_core.language_models": MagicMock(),
            "langchain_core.messages": MagicMock(),
            "langchain_core.tools": MagicMock(),
            "langchain_core.prompts": MagicMock(),
            "langgraph": MagicMock(),
            "langgraph.prebuilt": MagicMock(),
            "langgraph.graph": MagicMock(),
        }):
            yield

    def test_langchain_adapter_available(self):
        """Test LangChain adapter availability check."""
        available = list_available_adapters()
        # Will be True if langchain is installed, False otherwise
        assert "langchain" in available

    @pytest.mark.asyncio
    async def test_langchain_version_info(self, mock_langchain):
        """Test version info retrieval."""
        try:
            from paracle_adapters.langchain_adapter import LangChainAdapter
            info = LangChainAdapter.get_version_info()
            assert "langchain_available" in info
        except ImportError:
            pytest.skip("LangChain not installed")


# ============================================================================
# LlamaIndex Adapter Tests (Mocked)
# ============================================================================

class TestLlamaIndexAdapterMocked:
    """Tests for LlamaIndex adapter with mocked dependencies."""

    def test_llamaindex_adapter_available(self):
        """Test LlamaIndex adapter availability check."""
        available = list_available_adapters()
        assert "llamaindex" in available


# ============================================================================
# CrewAI Adapter Tests (Mocked)
# ============================================================================

class TestCrewAIAdapterMocked:
    """Tests for CrewAI adapter with mocked dependencies."""

    def test_crewai_adapter_available(self):
        """Test CrewAI adapter availability check."""
        available = list_available_adapters()
        assert "crewai" in available


# ============================================================================
# AutoGen Adapter Tests (Mocked)
# ============================================================================

class TestAutoGenAdapterMocked:
    """Tests for AutoGen adapter with mocked dependencies."""

    def test_autogen_adapter_available(self):
        """Test AutoGen adapter availability check."""
        available = list_available_adapters()
        assert "autogen" in available


# ============================================================================
# MSAF Adapter Tests (Mocked)
# ============================================================================

class TestMSAFAdapterMocked:
    """Tests for MSAF adapter with mocked dependencies."""

    def test_msaf_adapter_available(self):
        """Test MSAF adapter availability check."""
        available = list_available_adapters()
        assert "msaf" in available


# ============================================================================
# Integration Tests with Real Adapters (when available)
# ============================================================================

class TestRealAdaptersWhenAvailable:
    """Integration tests that run only when adapters are installed."""

    @pytest.mark.asyncio
    async def test_langchain_adapter_if_available(self, sample_agent_spec):
        """Test LangChain adapter if installed."""
        available = list_available_adapters()
        if not available.get("langchain"):
            pytest.skip("LangChain not installed")

        from paracle_adapters.langchain_adapter import LangChainAdapter

        # Test without LLM (should work for creation)
        adapter = LangChainAdapter()
        assert adapter.framework_name == "langchain"
        assert "agents" in adapter.supported_features

        # Version info should work
        info = adapter.get_version_info()
        assert info["langchain_available"] is True

    @pytest.mark.asyncio
    async def test_llamaindex_adapter_if_available(self, sample_agent_spec):
        """Test LlamaIndex adapter if installed."""
        available = list_available_adapters()
        if not available.get("llamaindex"):
            pytest.skip("LlamaIndex not installed")

        from paracle_adapters.llamaindex_adapter import LlamaIndexAdapter

        adapter = LlamaIndexAdapter()
        assert adapter.framework_name == "llamaindex"
        assert "rag" in adapter.supported_features

    @pytest.mark.asyncio
    async def test_crewai_adapter_if_available(self, sample_agent_spec):
        """Test CrewAI adapter if installed."""
        available = list_available_adapters()
        if not available.get("crewai"):
            pytest.skip("CrewAI not installed")

        from paracle_adapters.crewai_adapter import CrewAIAdapter

        adapter = CrewAIAdapter()
        assert adapter.framework_name == "crewai"
        assert "crews" in adapter.supported_features

    @pytest.mark.asyncio
    async def test_autogen_adapter_if_available(self, sample_agent_spec):
        """Test AutoGen adapter if installed."""
        available = list_available_adapters()
        if not available.get("autogen"):
            pytest.skip("AutoGen not installed")

        from paracle_adapters.autogen_adapter import AutoGenAdapter

        adapter = AutoGenAdapter()
        assert adapter.framework_name == "autogen"
        assert "group_chat" in adapter.supported_features

    @pytest.mark.asyncio
    async def test_msaf_adapter_if_available(self, sample_agent_spec):
        """Test MSAF adapter if installed."""
        available = list_available_adapters()
        if not available.get("msaf"):
            pytest.skip("MSAF not installed")

        from paracle_adapters.msaf_adapter import MSAFAdapter

        # MSAF requires config, just test that class exists
        assert MSAFAdapter.__name__ == "MSAFAdapter"
