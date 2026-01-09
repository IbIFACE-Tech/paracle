"""Tests for framework adapter base protocol."""

import pytest
from typing import Any

from paracle_adapters.base import FrameworkAdapter
from paracle_adapters.registry import AdapterRegistry
from paracle_adapters.exceptions import AdapterNotFoundError
from paracle_domain.models import AgentSpec, WorkflowSpec


class MockAdapter(FrameworkAdapter):
    """Mock adapter for testing."""

    async def create_agent(self, agent_spec: AgentSpec) -> Any:
        return {"agent": agent_spec.name, "framework": "mock"}

    async def execute_agent(
        self,
        agent_instance: Any,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        return {
            "response": "mock response",
            "metadata": {"framework": "mock"},
        }

    async def create_workflow(self, workflow_spec: WorkflowSpec) -> Any:
        return {"workflow": workflow_spec.name}

    async def execute_workflow(
        self,
        workflow_instance: Any,
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        return {"result": "workflow complete"}

    @property
    def framework_name(self) -> str:
        return "mock"

    @property
    def supported_features(self) -> list[str]:
        return ["agents", "workflows", "tools"]

    def validate_config(self, config: dict[str, Any]) -> bool:
        return True


class TestFrameworkAdapter:
    """Tests for FrameworkAdapter protocol."""

    def test_adapter_is_abstract(self):
        """Test that FrameworkAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            FrameworkAdapter()  # type: ignore

    def test_mock_adapter_creation(self):
        """Test creating a mock adapter."""
        adapter = MockAdapter()

        assert adapter.framework_name == "mock"
        assert "agents" in adapter.supported_features

    @pytest.mark.asyncio
    async def test_create_agent(self):
        """Test creating an agent."""
        adapter = MockAdapter()
        spec = AgentSpec(name="test-agent", provider="openai", model="gpt-4")

        agent_instance = await adapter.create_agent(spec)

        assert agent_instance["agent"] == "test-agent"
        assert agent_instance["framework"] == "mock"

    @pytest.mark.asyncio
    async def test_execute_agent(self):
        """Test executing an agent."""
        adapter = MockAdapter()
        spec = AgentSpec(name="test-agent", provider="openai", model="gpt-4")

        agent_instance = await adapter.create_agent(spec)
        result = await adapter.execute_agent(agent_instance, {"prompt": "Hello"})

        assert "response" in result
        assert result["response"] == "mock response"
        assert result["metadata"]["framework"] == "mock"

    def test_supports_feature(self):
        """Test feature support checking."""
        adapter = MockAdapter()

        assert adapter.supports_feature("agents")
        assert adapter.supports_feature("workflows")
        assert not adapter.supports_feature("streaming")

    def test_adapter_repr(self):
        """Test adapter string representation."""
        adapter = MockAdapter()
        repr_str = repr(adapter)

        assert "MockAdapter" in repr_str
        assert "mock" in repr_str


class TestAdapterRegistry:
    """Tests for AdapterRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        AdapterRegistry.clear()

    def test_register_adapter(self):
        """Test registering an adapter."""
        AdapterRegistry.register("mock", MockAdapter)

        assert AdapterRegistry.is_registered("mock")
        assert "mock" in AdapterRegistry.list_adapters()

    def test_register_invalid_adapter(self):
        """Test registering a non-adapter class raises TypeError."""

        class NotAnAdapter:
            pass

        with pytest.raises(TypeError):
            AdapterRegistry.register("invalid", NotAnAdapter)  # type: ignore

    def test_get_adapter_class(self):
        """Test retrieving an adapter class."""
        AdapterRegistry.register("mock", MockAdapter)

        adapter_class = AdapterRegistry.get_adapter_class("mock")
        assert adapter_class is MockAdapter

    def test_get_nonexistent_adapter(self):
        """Test retrieving a non-registered adapter raises error."""
        with pytest.raises(AdapterNotFoundError) as exc_info:
            AdapterRegistry.get_adapter_class("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_create_adapter(self):
        """Test creating an adapter instance."""
        AdapterRegistry.register("mock", MockAdapter)

        adapter = AdapterRegistry.create_adapter("mock", custom_param="value")

        assert isinstance(adapter, MockAdapter)
        assert adapter.config["custom_param"] == "value"

    def test_list_adapters(self):
        """Test listing all adapters."""
        AdapterRegistry.register("mock1", MockAdapter)
        AdapterRegistry.register("mock2", MockAdapter)

        adapters = AdapterRegistry.list_adapters()

        assert len(adapters) == 2
        assert "mock1" in adapters
        assert "mock2" in adapters

    def test_unregister_adapter(self):
        """Test unregistering an adapter."""
        AdapterRegistry.register("mock", MockAdapter)
        assert AdapterRegistry.is_registered("mock")

        AdapterRegistry.unregister("mock")

        assert not AdapterRegistry.is_registered("mock")

    def test_unregister_nonexistent_adapter(self):
        """Test unregistering a non-existent adapter raises error."""
        with pytest.raises(AdapterNotFoundError):
            AdapterRegistry.unregister("nonexistent")

    def test_clear_registry(self):
        """Test clearing all adapters."""
        AdapterRegistry.register("mock1", MockAdapter)
        AdapterRegistry.register("mock2", MockAdapter)

        assert len(AdapterRegistry.list_adapters()) == 2

        AdapterRegistry.clear()

        assert len(AdapterRegistry.list_adapters()) == 0
