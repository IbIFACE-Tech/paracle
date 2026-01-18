"""Unit tests for SemanticMemoryCapability."""

import pytest
import tempfile
from pathlib import Path

from paracle_meta.capabilities.semantic_memory import (
    SemanticMemoryCapability,
    SemanticMemoryConfig,
)


@pytest.fixture
def temp_db():
    """Create temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def semantic_memory(temp_db):
    """Create SemanticMemoryCapability instance."""
    config = SemanticMemoryConfig(
        db_path=temp_db,
        enable_vector_search=False,  # Disable for unit tests
    )
    return SemanticMemoryCapability(config)


@pytest.mark.asyncio
async def test_semantic_memory_initialization(semantic_memory):
    """Test SemanticMemoryCapability initialization."""
    assert semantic_memory.name == "semantic_memory"
    assert semantic_memory.config.enable_vector_search is False


@pytest.mark.asyncio
async def test_store_memory(semantic_memory):
    """Test storing a memory."""
    result = await semantic_memory.store(
        content="This is a test memory",
        memory_type="conversation",
        agent_name="test-agent",
        metadata={"session": "test-session"},
    )

    assert result.success is True
    assert "memory_id" in result.output
    assert result.output["content"] == "This is a test memory"


@pytest.mark.asyncio
async def test_store_with_importance(semantic_memory):
    """Test storing memory with importance score."""
    result = await semantic_memory.store(
        content="Critical information", memory_type="knowledge", importance=0.9
    )

    assert result.success is True
    assert result.output["importance"] == 0.9


@pytest.mark.asyncio
async def test_search_memories_text(semantic_memory):
    """Test searching memories by text (without vector search)."""
    # Store memories
    await semantic_memory.store(
        content="Python is a programming language", memory_type="knowledge"
    )
    await semantic_memory.store(
        content="JavaScript is also a programming language", memory_type="knowledge"
    )
    await semantic_memory.store(content="Cats are animals", memory_type="knowledge")

    # Search
    result = await semantic_memory.search(query="programming language", top_k=10)

    assert result.success is True
    # Should find memories containing "programming"
    assert len(result.output["results"]) >= 1


@pytest.mark.asyncio
async def test_search_with_type_filter(semantic_memory):
    """Test searching with memory type filter."""
    # Store different types
    await semantic_memory.store(
        content="Conversation about Python", memory_type="conversation"
    )
    await semantic_memory.store(
        content="Python knowledge base", memory_type="knowledge"
    )

    # Search only knowledge
    result = await semantic_memory.search(query="Python", memory_type="knowledge")

    assert result.success is True
    for mem in result.output["results"]:
        assert mem["memory_type"] == "knowledge"


@pytest.mark.asyncio
async def test_get_memory_by_id(semantic_memory):
    """Test retrieving specific memory by ID."""
    # Store memory
    store_result = await semantic_memory.store(
        content="Test memory", memory_type="test"
    )
    memory_id = store_result.output["memory_id"]

    # Get by ID
    result = await semantic_memory.get(memory_id=memory_id)

    assert result.success is True
    assert result.output["memory_id"] == memory_id
    assert result.output["content"] == "Test memory"


@pytest.mark.asyncio
async def test_update_memory(semantic_memory):
    """Test updating a memory."""
    # Store memory
    store_result = await semantic_memory.store(
        content="Original content", memory_type="test"
    )
    memory_id = store_result.output["memory_id"]

    # Update
    result = await semantic_memory.update(
        memory_id=memory_id, content="Updated content", importance=0.8
    )

    assert result.success is True

    # Verify update
    get_result = await semantic_memory.get(memory_id=memory_id)
    assert get_result.output["content"] == "Updated content"
    assert get_result.output["importance"] == 0.8


@pytest.mark.asyncio
async def test_delete_memory(semantic_memory):
    """Test deleting a memory."""
    # Store memory
    store_result = await semantic_memory.store(
        content="To be deleted", memory_type="test"
    )
    memory_id = store_result.output["memory_id"]

    # Delete
    result = await semantic_memory.delete(memory_id=memory_id)
    assert result.success is True

    # Verify deletion
    get_result = await semantic_memory.get(memory_id=memory_id)
    assert get_result.success is False


@pytest.mark.asyncio
async def test_store_conversation_turn(semantic_memory):
    """Test storing a conversation turn."""
    result = await semantic_memory.store_conversation(
        agent_name="test-agent",
        user_message="What is Python?",
        assistant_message="Python is a programming language",
        metadata={"session": "test"},
    )

    assert result.success is True
    assert "conversation_id" in result.output


@pytest.mark.asyncio
async def test_get_conversation(semantic_memory):
    """Test retrieving conversation history."""
    # Store conversation
    store_result = await semantic_memory.store_conversation(
        agent_name="test-agent", user_message="Hello", assistant_message="Hi there!"
    )
    conv_id = store_result.output["conversation_id"]

    # Get conversation
    result = await semantic_memory.get_conversation(conversation_id=conv_id)

    assert result.success is True
    assert result.output["user_message"] == "Hello"
    assert result.output["assistant_message"] == "Hi there!"


@pytest.mark.asyncio
async def test_get_conversation_history(semantic_memory):
    """Test getting conversation history for agent."""
    # Store multiple turns
    for i in range(5):
        await semantic_memory.store_conversation(
            agent_name="test-agent",
            user_message=f"Question {i}",
            assistant_message=f"Answer {i}",
        )

    # Get history
    result = await semantic_memory.get_conversation_history(
        agent_name="test-agent", limit=3
    )

    assert result.success is True
    assert len(result.output["conversations"]) <= 3


@pytest.mark.asyncio
async def test_search_conversations(semantic_memory):
    """Test searching conversations."""
    # Store conversations
    await semantic_memory.store_conversation(
        agent_name="test-agent",
        user_message="Tell me about Python",
        assistant_message="Python is great",
    )
    await semantic_memory.store_conversation(
        agent_name="test-agent",
        user_message="What about JavaScript?",
        assistant_message="JavaScript is also good",
    )

    # Search
    result = await semantic_memory.search_conversations(
        query="Python", agent_name="test-agent"
    )

    assert result.success is True
    assert len(result.output["results"]) >= 1


@pytest.mark.asyncio
async def test_get_stats(semantic_memory):
    """Test getting memory statistics."""
    # Store various memories
    await semantic_memory.store(content="Memory 1", memory_type="knowledge")
    await semantic_memory.store(content="Memory 2", memory_type="conversation")

    result = await semantic_memory.get_stats()

    assert result.success is True
    assert "total_memories" in result.output
    assert result.output["total_memories"] >= 2


@pytest.mark.asyncio
async def test_cleanup_old_memories(semantic_memory):
    """Test cleaning up old memories."""
    # Store memory
    await semantic_memory.store(
        content="Old memory", memory_type="test", importance=0.1  # Low importance
    )

    # Cleanup (keep only important memories or recent ones)
    result = await semantic_memory.cleanup(keep_count=0, min_importance=0.5)

    assert result.success is True


@pytest.mark.asyncio
async def test_memory_with_metadata(semantic_memory):
    """Test storing and retrieving memory with metadata."""
    result = await semantic_memory.store(
        content="Test content",
        memory_type="test",
        metadata={"source": "unit_test", "tags": ["test", "demo"], "version": 1},
    )

    memory_id = result.output["memory_id"]

    # Get and verify metadata
    get_result = await semantic_memory.get(memory_id=memory_id)
    assert get_result.output["metadata"]["source"] == "unit_test"
    assert "test" in get_result.output["metadata"]["tags"]


@pytest.mark.asyncio
async def test_importance_filtering(semantic_memory):
    """Test filtering by importance."""
    # Store memories with different importance
    await semantic_memory.store(
        content="Very important", memory_type="test", importance=0.9
    )
    await semantic_memory.store(
        content="Less important", memory_type="test", importance=0.3
    )

    # Search with minimum importance
    result = await semantic_memory.search(query="important", min_importance=0.5)

    assert result.success is True
    # Should only return high importance memory
    for mem in result.output["results"]:
        assert mem["importance"] >= 0.5


@pytest.mark.asyncio
async def test_persistence(temp_db):
    """Test memory persistence across instances."""
    # First instance - store memory
    config1 = SemanticMemoryConfig(db_path=temp_db, enable_vector_search=False)
    cap1 = SemanticMemoryCapability(config1)

    store_result = await cap1.store(content="Persistent memory", memory_type="test")
    memory_id = store_result.output["memory_id"]

    # Second instance - should load existing memories
    config2 = SemanticMemoryConfig(db_path=temp_db, enable_vector_search=False)
    cap2 = SemanticMemoryCapability(config2)

    get_result = await cap2.get(memory_id=memory_id)
    assert get_result.success is True
    assert get_result.output["content"] == "Persistent memory"


@pytest.mark.asyncio
async def test_agent_name_filtering(semantic_memory):
    """Test filtering memories by agent name."""
    # Store memories for different agents
    await semantic_memory.store(
        content="Agent 1 memory", memory_type="test", agent_name="agent1"
    )
    await semantic_memory.store(
        content="Agent 2 memory", memory_type="test", agent_name="agent2"
    )

    # Search for agent1
    result = await semantic_memory.search(query="memory", agent_name="agent1")

    assert result.success is True
    # Should only return agent1 memories
    for mem in result.output["results"]:
        if mem.get("agent_name"):
            assert mem["agent_name"] == "agent1"
