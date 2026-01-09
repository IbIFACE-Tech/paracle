"""Unit tests for paracle_meta.capabilities.base module."""

import pytest
from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class TestCapabilityConfig:
    """Tests for CapabilityConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CapabilityConfig()
        assert config.enabled is True
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_custom_values(self):
        """Test custom configuration values."""
        config = CapabilityConfig(
            enabled=False,
            timeout=60.0,
            max_retries=5,
        )
        assert config.enabled is False
        assert config.timeout == 60.0
        assert config.max_retries == 5

    def test_timeout_bounds(self):
        """Test timeout boundary validation."""
        # Valid bounds
        config = CapabilityConfig(timeout=1.0)
        assert config.timeout == 1.0

        config = CapabilityConfig(timeout=300.0)
        assert config.timeout == 300.0

        # Invalid bounds should raise
        with pytest.raises(ValueError):
            CapabilityConfig(timeout=0.5)

        with pytest.raises(ValueError):
            CapabilityConfig(timeout=400.0)


class TestCapabilityResult:
    """Tests for CapabilityResult."""

    def test_success_result(self):
        """Test creating a success result."""
        result = CapabilityResult.success_result(
            capability="test",
            output={"data": "value"},
            duration_ms=100.0,
            extra_key="extra_value",
        )

        assert result.capability == "test"
        assert result.success is True
        assert result.output == {"data": "value"}
        assert result.error is None
        assert result.duration_ms == 100.0
        assert result.metadata["extra_key"] == "extra_value"
        assert result.timestamp is not None

    def test_error_result(self):
        """Test creating an error result."""
        result = CapabilityResult.error_result(
            capability="test",
            error="Something went wrong",
            duration_ms=50.0,
        )

        assert result.capability == "test"
        assert result.success is False
        assert result.output is None
        assert result.error == "Something went wrong"
        assert result.duration_ms == 50.0

    def test_result_with_all_fields(self):
        """Test creating result with all fields."""
        result = CapabilityResult(
            capability="full_test",
            success=True,
            output=["item1", "item2"],
            error=None,
            duration_ms=250.5,
            metadata={"key": "value"},
        )

        assert result.capability == "full_test"
        assert result.success is True
        assert result.output == ["item1", "item2"]
        assert result.metadata["key"] == "value"


class ConcreteCapability(BaseCapability):
    """Concrete implementation for testing."""

    name = "test_capability"
    description = "A test capability"

    async def execute(self, **kwargs) -> CapabilityResult:
        if kwargs.get("fail"):
            return CapabilityResult.error_result(
                capability=self.name,
                error="Intentional failure",
            )
        return CapabilityResult.success_result(
            capability=self.name,
            output=kwargs,
        )


class TestBaseCapability:
    """Tests for BaseCapability."""

    @pytest.fixture
    def capability(self):
        """Create test capability instance."""
        return ConcreteCapability()

    def test_initialization(self, capability):
        """Test capability initialization."""
        assert capability.name == "test_capability"
        assert capability.description == "A test capability"
        assert capability.config.enabled is True
        assert capability.is_initialized is False

    def test_initialization_with_config(self):
        """Test capability with custom config."""
        config = CapabilityConfig(enabled=False, timeout=120.0)
        capability = ConcreteCapability(config=config)

        assert capability.config.enabled is False
        assert capability.config.timeout == 120.0
        assert capability.is_enabled is False

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, capability):
        """Test initialize and shutdown lifecycle."""
        assert capability.is_initialized is False

        await capability.initialize()
        assert capability.is_initialized is True

        await capability.shutdown()
        assert capability.is_initialized is False

    @pytest.mark.asyncio
    async def test_execute_success(self, capability):
        """Test successful execution."""
        await capability.initialize()

        result = await capability.execute(key="value")

        assert result.success is True
        assert result.capability == "test_capability"
        assert result.output["key"] == "value"

    @pytest.mark.asyncio
    async def test_execute_failure(self, capability):
        """Test failed execution."""
        await capability.initialize()

        result = await capability.execute(fail=True)

        assert result.success is False
        assert "Intentional failure" in result.error

    def test_repr(self, capability):
        """Test string representation."""
        repr_str = repr(capability)
        assert "ConcreteCapability" in repr_str
        assert "test_capability" in repr_str
        assert "enabled" in repr_str

    def test_disabled_capability(self):
        """Test disabled capability."""
        config = CapabilityConfig(enabled=False)
        capability = ConcreteCapability(config=config)

        assert capability.is_enabled is False
        repr_str = repr(capability)
        assert "disabled" in repr_str
