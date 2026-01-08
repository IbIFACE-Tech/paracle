"""Unit tests for paracle_meta.registry module."""

import pytest

from paracle_meta.registry import (
    AsyncCapabilityProxy,
    CapabilityFacade,
    CapabilityInfo,
    CapabilityRegistry,
    CapabilityStatus,
    RegistryConfig,
)


class TestCapabilityStatus:
    """Tests for CapabilityStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert CapabilityStatus.NOT_LOADED.value == "not_loaded"
        assert CapabilityStatus.LOADING.value == "loading"
        assert CapabilityStatus.READY.value == "ready"
        assert CapabilityStatus.ERROR.value == "error"
        assert CapabilityStatus.SHUTDOWN.value == "shutdown"


class TestCapabilityInfo:
    """Tests for CapabilityInfo."""

    def test_create_info(self):
        """Test creating capability info."""
        info = CapabilityInfo(
            name="test",
            factory=lambda: None,
        )

        assert info.name == "test"
        assert info.status == CapabilityStatus.NOT_LOADED
        assert info.instance is None


class TestRegistryConfig:
    """Tests for RegistryConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RegistryConfig()

        assert config.auto_initialize is True
        assert config.parallel_init is True
        assert config.max_parallel == 5
        assert config.provider is None

    def test_custom_values(self):
        """Test custom configuration values."""
        config = RegistryConfig(
            auto_initialize=False,
            max_parallel=3,
        )

        assert config.auto_initialize is False
        assert config.max_parallel == 3


class TestCapabilityRegistry:
    """Tests for CapabilityRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a registry instance."""
        return CapabilityRegistry()

    @pytest.mark.asyncio
    async def test_initialize(self, registry):
        """Test registry initialization."""
        await registry.initialize()

        assert registry.is_initialized is True

    @pytest.mark.asyncio
    async def test_builtins_registered(self, registry):
        """Test built-in capabilities are registered."""
        await registry.initialize()

        assert registry.is_registered("filesystem")
        assert registry.is_registered("memory")
        assert registry.is_registered("shell")

    def test_list_capabilities(self, registry):
        """Test listing capabilities."""
        # Register before init to test
        registry.register("custom", lambda: None)

        caps = registry.list_capabilities()
        assert "custom" in caps

    @pytest.mark.asyncio
    async def test_get_status_not_loaded(self, registry):
        """Test status for not loaded capability."""
        await registry.initialize()

        status = registry.get_status("filesystem")
        assert status == CapabilityStatus.NOT_LOADED

    @pytest.mark.asyncio
    async def test_is_loaded_false(self, registry):
        """Test is_loaded returns false for unloaded capability."""
        await registry.initialize()

        assert registry.is_loaded("filesystem") is False

    @pytest.mark.asyncio
    async def test_contains(self, registry):
        """Test __contains__ method."""
        await registry.initialize()

        assert "filesystem" in registry
        assert "nonexistent" not in registry

    @pytest.mark.asyncio
    async def test_iter(self, registry):
        """Test __iter__ method."""
        await registry.initialize()

        caps = list(registry)
        assert len(caps) > 0
        assert "filesystem" in caps

    @pytest.mark.asyncio
    async def test_get_unregistered_raises_keyerror(self, registry):
        """Test get raises KeyError for unregistered capability."""
        await registry.initialize()

        with pytest.raises(KeyError, match="not registered"):
            await registry.get("nonexistent")

    @pytest.mark.asyncio
    async def test_get_optional_returns_none(self, registry):
        """Test get_optional returns None for missing capability."""
        await registry.initialize()

        result = await registry.get_optional("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_register_custom(self, registry):
        """Test registering custom capability."""

        class MockCapability:
            async def initialize(self):
                pass

            async def shutdown(self):
                pass

        registry.register("mock", MockCapability)
        await registry.initialize()

        assert registry.is_registered("mock")

    @pytest.mark.asyncio
    async def test_unregister(self, registry):
        """Test unregistering capability."""
        registry.register("temp", lambda: None)
        registry.unregister("temp")

        assert not registry.is_registered("temp")

    @pytest.mark.asyncio
    async def test_shutdown(self, registry):
        """Test registry shutdown."""
        await registry.initialize()
        await registry.shutdown()

        assert registry.is_initialized is False


class TestCapabilityFacade:
    """Tests for CapabilityFacade."""

    @pytest.fixture
    def registry(self):
        """Create registry."""
        return CapabilityRegistry()

    def test_create_facade(self, registry):
        """Test creating facade."""
        facade = CapabilityFacade(registry)
        assert facade._registry is registry

    def test_attribute_access_returns_proxy(self, registry):
        """Test attribute access returns proxy."""
        facade = CapabilityFacade(registry)

        proxy = facade.filesystem
        assert isinstance(proxy, AsyncCapabilityProxy)


class TestAsyncCapabilityProxy:
    """Tests for AsyncCapabilityProxy."""

    @pytest.fixture
    def registry(self):
        """Create registry."""
        return CapabilityRegistry()

    def test_create_proxy(self, registry):
        """Test creating proxy."""
        proxy = AsyncCapabilityProxy(registry, "filesystem")

        assert proxy._name == "filesystem"
