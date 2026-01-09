"""Unit tests for paracle_meta.capabilities.memory module."""

import pytest
from pathlib import Path

from paracle_meta.capabilities.memory import (
    MemoryCapability,
    MemoryConfig,
    MemoryItem,
)


class TestMemoryConfig:
    """Tests for MemoryConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = MemoryConfig()
        assert config.storage_path is None
        assert config.max_short_term_items == 100
        assert config.max_context_tokens == 100000
        assert config.enable_persistence is True
        assert config.enable_embeddings is False
        assert config.ttl_hours == 24 * 7
        assert config.namespace == "default"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = MemoryConfig(
            storage_path="/tmp/memory.db",
            max_short_term_items=50,
            namespace="test",
            ttl_hours=48,
        )
        assert config.storage_path == "/tmp/memory.db"
        assert config.max_short_term_items == 50
        assert config.namespace == "test"
        assert config.ttl_hours == 48


class TestMemoryItem:
    """Tests for MemoryItem."""

    def test_create_item(self):
        """Test creating a memory item."""
        item = MemoryItem(
            key="test_key",
            value={"data": "value"},
            metadata={"source": "test"},
            ttl_hours=24,
        )

        assert item.key == "test_key"
        assert item.value == {"data": "value"}
        assert item.metadata == {"source": "test"}
        assert item.ttl_hours == 24
        assert item.access_count == 0

    def test_to_dict(self):
        """Test item conversion to dict."""
        item = MemoryItem(key="test", value="data")

        data = item.to_dict()

        assert data["key"] == "test"
        assert data["value"] == "data"
        assert "created_at" in data
        assert "accessed_at" in data

    def test_from_dict(self):
        """Test item creation from dict."""
        data = {
            "key": "test",
            "value": {"foo": "bar"},
            "metadata": {},
            "created_at": "2024-01-01T00:00:00+00:00",
            "accessed_at": "2024-01-01T00:00:00+00:00",
            "access_count": 5,
            "ttl_hours": 24,
        }

        item = MemoryItem.from_dict(data)

        assert item.key == "test"
        assert item.value == {"foo": "bar"}
        assert item.access_count == 5

    def test_is_expired(self):
        """Test expiration check."""
        from datetime import datetime, timezone, timedelta

        # Not expired
        item = MemoryItem(key="test", value="data", ttl_hours=24)
        assert item.is_expired() is False

        # Expired (manually set old created_at)
        item2 = MemoryItem(key="test2", value="data", ttl_hours=1)
        item2.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        assert item2.is_expired() is True

        # No TTL (never expires)
        item3 = MemoryItem(key="test3", value="data", ttl_hours=None)
        assert item3.is_expired() is False


class TestMemoryCapability:
    """Tests for MemoryCapability."""

    @pytest.fixture
    def memory_capability(self, tmp_path):
        """Create memory capability instance."""
        config = MemoryConfig(
            storage_path=str(tmp_path / "memory.db"),
            namespace="test",
            max_short_term_items=10,
        )
        return MemoryCapability(config=config)

    @pytest.fixture
    def memory_capability_no_persist(self, tmp_path):
        """Create memory capability without persistence."""
        config = MemoryConfig(
            enable_persistence=False,
            namespace="test",
        )
        return MemoryCapability(config=config)

    def test_initialization(self, memory_capability):
        """Test capability initialization."""
        assert memory_capability.name == "memory"
        assert "memory" in memory_capability.description.lower()

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, memory_capability):
        """Test initialize and shutdown lifecycle."""
        await memory_capability.initialize()
        assert memory_capability.is_initialized is True
        assert memory_capability._conn is not None

        await memory_capability.shutdown()
        assert memory_capability.is_initialized is False
        assert memory_capability._conn is None

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, memory_capability):
        """Test storing and retrieving data."""
        await memory_capability.initialize()

        # Store
        result = await memory_capability.store("user_pref", {"theme": "dark"})
        assert result.success is True
        assert result.output["stored"] is True

        # Retrieve
        result = await memory_capability.retrieve("user_pref")
        assert result.success is True
        assert result.output["value"] == {"theme": "dark"}
        assert result.output["source"] == "short_term"

        await memory_capability.shutdown()

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent(self, memory_capability):
        """Test retrieving nonexistent key."""
        await memory_capability.initialize()

        result = await memory_capability.retrieve("nonexistent")

        assert result.success is True
        assert result.output["value"] is None
        assert result.output.get("found") is False

        await memory_capability.shutdown()

    @pytest.mark.asyncio
    async def test_delete(self, memory_capability):
        """Test deleting data."""
        await memory_capability.initialize()

        # Store first
        await memory_capability.store("to_delete", "data")

        # Delete
        result = await memory_capability.execute(action="delete", key="to_delete")
        assert result.success is True
        assert result.output["deleted"] is True

        # Verify deleted
        result = await memory_capability.retrieve("to_delete")
        assert result.output["value"] is None

        await memory_capability.shutdown()

    @pytest.mark.asyncio
    async def test_list_keys(self, memory_capability):
        """Test listing keys."""
        await memory_capability.initialize()

        # Store some items
        await memory_capability.store("key1", "value1")
        await memory_capability.store("key2", "value2")
        await memory_capability.store("other", "value3")

        # List all
        result = await memory_capability.execute(action="list_keys")
        assert result.success is True
        assert "key1" in result.output["keys"]
        assert "key2" in result.output["keys"]
        assert result.output["count"] >= 3

        # List with pattern
        result = await memory_capability.execute(action="list_keys", pattern="key")
        assert result.success is True
        assert "key1" in result.output["keys"]
        assert "key2" in result.output["keys"]
        assert "other" not in result.output["keys"]

        await memory_capability.shutdown()

    @pytest.mark.asyncio
    async def test_search(self, memory_capability):
        """Test searching memory."""
        await memory_capability.initialize()

        # Store items
        await memory_capability.store("python_code", "def hello(): pass")
        await memory_capability.store("javascript_code", "function hello() {}")
        await memory_capability.store("config", {"language": "python"})

        # Search
        result = await memory_capability.search("python")
        assert result.success is True
        assert result.output["count"] >= 1

        # Check results contain python-related items
        keys = [r["key"] for r in result.output["results"]]
        assert "python_code" in keys or "config" in keys

        await memory_capability.shutdown()

    @pytest.mark.asyncio
    async def test_context_operations(self, memory_capability):
        """Test context history operations."""
        await memory_capability.initialize()

        # Add context
        result = await memory_capability.add_context("user", "Hello, how are you?")
        assert result.success is True
        assert result.output["added"] is True

        result = await memory_capability.add_context("assistant", "I'm doing well, thank you!")
        assert result.success is True

        # Get context
        result = await memory_capability.get_context(max_tokens=10000)
        assert result.success is True
        assert len(result.output["messages"]) == 2

        messages = result.output["messages"]
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

        await memory_capability.shutdown()

    @pytest.mark.asyncio
    async def test_clear_context(self, memory_capability):
        """Test clearing context."""
        await memory_capability.initialize()

        # Add context
        await memory_capability.add_context("user", "Test message")

        # Clear
        result = await memory_capability.execute(action="clear_context")
        assert result.success is True
        assert result.output["cleared"] is True
        assert result.output["items_removed"] >= 1

        # Verify cleared
        result = await memory_capability.get_context()
        assert result.output["message_count"] == 0

        await memory_capability.shutdown()

    @pytest.mark.asyncio
    async def test_consolidate(self, memory_capability):
        """Test memory consolidation."""
        await memory_capability.initialize()

        # Store items
        await memory_capability.store("item1", "data")
        await memory_capability.store("item2", "data")

        # Consolidate
        result = await memory_capability.execute(action="consolidate")
        assert result.success is True
        assert "expired_removed" in result.output

        await memory_capability.shutdown()

    @pytest.mark.asyncio
    async def test_stats(self, memory_capability):
        """Test getting memory stats."""
        await memory_capability.initialize()

        # Store some data
        await memory_capability.store("test", "data")
        await memory_capability.add_context("user", "message")

        # Get stats
        result = await memory_capability.execute(action="stats")
        assert result.success is True
        assert result.output["short_term_items"] >= 1
        assert result.output["context_items"] >= 1
        assert result.output["namespace"] == "test"

        await memory_capability.shutdown()

    @pytest.mark.asyncio
    async def test_export_import(self, memory_capability, tmp_path):
        """Test export and import."""
        await memory_capability.initialize()

        # Store data
        await memory_capability.store("export_test", {"value": 123})
        await memory_capability.add_context("user", "export message")

        # Export
        export_path = str(tmp_path / "export.json")
        result = await memory_capability.execute(action="export", path=export_path)
        assert result.success is True
        assert Path(export_path).exists()

        # Clear and reimport
        await memory_capability.execute(action="delete", key="export_test")

        result = await memory_capability.execute(action="import", path=export_path)
        assert result.success is True
        assert result.output["items_imported"] >= 1

        # Verify imported
        result = await memory_capability.retrieve("export_test")
        assert result.output["value"] == {"value": 123}

        await memory_capability.shutdown()

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, memory_capability):
        """Test execute with unknown action."""
        await memory_capability.initialize()

        result = await memory_capability.execute(action="unknown_action")

        assert result.success is False
        assert "Unknown action" in result.error

        await memory_capability.shutdown()

    @pytest.mark.asyncio
    async def test_short_term_limit(self, memory_capability):
        """Test short-term memory limit enforcement."""
        await memory_capability.initialize()

        # Store more than the limit (10)
        for i in range(15):
            await memory_capability.store(f"item_{i}", f"value_{i}")

        # Should only have max_short_term_items
        assert len(memory_capability._short_term) <= 10

        await memory_capability.shutdown()


class TestMemoryPersistence:
    """Tests for memory persistence."""

    @pytest.fixture
    def persistent_config(self, tmp_path):
        """Create config with persistence."""
        return MemoryConfig(
            storage_path=str(tmp_path / "persist.db"),
            namespace="persist_test",
            enable_persistence=True,
        )

    @pytest.mark.asyncio
    async def test_persist_and_reload(self, persistent_config, tmp_path):
        """Test data persists across sessions."""
        # First session - store data
        cap1 = MemoryCapability(config=persistent_config)
        await cap1.initialize()
        await cap1.store("persistent_key", {"important": "data"})
        await cap1.shutdown()

        # Second session - retrieve data
        cap2 = MemoryCapability(config=persistent_config)
        await cap2.initialize()
        result = await cap2.retrieve("persistent_key")

        assert result.success is True
        assert result.output["value"] == {"important": "data"}
        assert result.output["source"] == "persistent"

        await cap2.shutdown()

    @pytest.mark.asyncio
    async def test_no_persistence(self, tmp_path):
        """Test without persistence."""
        config = MemoryConfig(
            enable_persistence=False,
            namespace="no_persist",
        )

        cap = MemoryCapability(config=config)
        await cap.initialize()

        # Connection should be None
        assert cap._conn is None

        # Store and retrieve still works (short-term only)
        await cap.store("temp", "data")
        result = await cap.retrieve("temp")
        assert result.output["value"] == "data"
        assert result.output["source"] == "short_term"

        await cap.shutdown()


class TestMemoryNamespaces:
    """Tests for memory namespace isolation."""

    @pytest.mark.asyncio
    async def test_namespace_isolation(self, tmp_path):
        """Test that namespaces are isolated."""
        db_path = str(tmp_path / "shared.db")

        # Create two capabilities with different namespaces
        config1 = MemoryConfig(storage_path=db_path, namespace="ns1")
        config2 = MemoryConfig(storage_path=db_path, namespace="ns2")

        cap1 = MemoryCapability(config=config1)
        cap2 = MemoryCapability(config=config2)

        await cap1.initialize()
        await cap2.initialize()

        # Store in ns1
        await cap1.store("shared_key", "ns1_value")

        # Store in ns2
        await cap2.store("shared_key", "ns2_value")

        # Retrieve from each
        result1 = await cap1.retrieve("shared_key")
        result2 = await cap2.retrieve("shared_key")

        assert result1.output["value"] == "ns1_value"
        assert result2.output["value"] == "ns2_value"

        await cap1.shutdown()
        await cap2.shutdown()
