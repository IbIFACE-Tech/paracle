# Memory System Guide

This guide covers the `paracle_memory` package for agent memory persistence.

## Overview

The memory system provides:

- **Short-term memory** - Conversation context (auto-expires)
- **Long-term memory** - Persistent knowledge
- **Episodic memory** - Interaction history
- **Working memory** - Current task context
- **Semantic memory** - Knowledge with embeddings for search

## Quick Start

```python
from paracle_memory import MemoryManager, MemoryConfig, MemoryType

# Initialize memory system
manager = MemoryManager(
    config=MemoryConfig(
        backend="sqlite",
        persist_dir=".paracle/memory"
    )
)

# Store a memory
memory_id = await manager.store(
    agent_id="coder-agent",
    content="User prefers Python 3.12 features",
    memory_type=MemoryType.LONG_TERM,
    tags=["preferences", "python"],
    importance=0.8
)

# Retrieve memories
memories = await manager.retrieve(
    agent_id="coder-agent",
    query="What Python version does the user prefer?",
    top_k=5
)

# Get specific memory
memory = await manager.get(memory_id)

# Clear agent memories
await manager.clear(agent_id="coder-agent")

# Close manager
await manager.close()
```

## Memory Types

### Short-Term Memory

Temporary conversation context that auto-expires.

```python
await manager.store(
    agent_id="assistant",
    content="User asked about weather",
    memory_type=MemoryType.SHORT_TERM,
    # Auto-expires based on config (default: 24 hours)
)
```

### Long-Term Memory

Persistent knowledge that doesn't expire.

```python
await manager.store(
    agent_id="assistant",
    content="User's name is Alice",
    memory_type=MemoryType.LONG_TERM,
    importance=0.9,
    tags=["user-info", "name"]
)
```

### Episodic Memory

Records of specific interactions or events.

```python
from paracle_memory import EpisodicMemory

episode = EpisodicMemory(
    agent_id="coder",
    content="Completed code review for PR #123",
    episode_type="task",
    outcome="success",
    duration_seconds=120.5,
    context={"pr_number": 123, "files_reviewed": 5}
)
await manager._get_store().save(episode)
```

### Working Memory

Current task context (temporary).

```python
from paracle_memory import WorkingMemory

working = WorkingMemory(
    agent_id="coder",
    content="Currently implementing user authentication",
    task_id="task-123",
    priority=1,
    context_keys=["auth", "security"]
)
await manager._get_store().save(working)
```

### Semantic Memory

Knowledge with embeddings for semantic search.

```python
from paracle_memory import SemanticMemory

semantic = SemanticMemory(
    agent_id="knowledge-base",
    content="Python is a high-level programming language",
    source="documentation",
    confidence=0.95,
    embedding=[0.1, 0.2, ...]  # Generated embedding
)
await manager._get_store().save(semantic)
```

## Storage Backends

### In-Memory (Testing)

```python
config = MemoryConfig(backend="memory")
manager = MemoryManager(config=config)
```

Fast but not persistent - ideal for testing.

### SQLite (Default)

```python
config = MemoryConfig(
    backend="sqlite",
    persist_dir=".paracle/memory"
)
manager = MemoryManager(config=config)
```

Persistent local storage - ideal for development.

### Vector (Semantic Search)

```python
config = MemoryConfig(
    backend="vector",
    persist_dir=".paracle/memory",
    vector_store_type="chroma",
    embedding_provider="openai"
)
manager = MemoryManager(config=config)
```

Enables semantic search with embeddings.

### Hybrid (SQLite + Vector)

```python
config = MemoryConfig(
    backend="hybrid",
    persist_dir=".paracle/memory",
    enable_semantic_search=True,
    embedding_provider="mock"
)
manager = MemoryManager(config=config)
```

Best of both worlds - relational + semantic.

## Configuration Options

```python
from paracle_memory import MemoryConfig, MemoryBackend

config = MemoryConfig(
    # Backend selection
    backend=MemoryBackend.SQLITE,
    persist_dir=".paracle/memory",
    database_url=None,  # Custom DB URL

    # Vector settings
    vector_store_type="chroma",
    embedding_provider="mock",  # or "openai", "local"
    embedding_model="text-embedding-3-small",
    embedding_dimension=1536,

    # Memory limits
    max_short_term_memories=100,
    short_term_ttl_hours=24,

    # Cleanup
    cleanup_interval_hours=1,

    # Search settings
    enable_semantic_search=True,
    similarity_threshold=0.7
)
```

## Storing Memories

### Basic Storage

```python
memory_id = await manager.store(
    agent_id="my-agent",
    content="Important information"
)
```

### With Tags and Metadata

```python
memory_id = await manager.store(
    agent_id="my-agent",
    content="User prefers dark mode",
    tags=["preferences", "ui"],
    metadata={"source": "settings", "timestamp": "2024-01-01"}
)
```

### With Importance Score

```python
memory_id = await manager.store(
    agent_id="my-agent",
    content="Critical security requirement",
    importance=0.95  # 0.0 to 1.0
)
```

### With Time-to-Live

```python
memory_id = await manager.store(
    agent_id="my-agent",
    content="Temporary context",
    ttl_hours=2  # Expires in 2 hours
)
```

### Without Embedding

```python
memory_id = await manager.store(
    agent_id="my-agent",
    content="No embedding needed",
    generate_embedding=False
)
```

## Retrieving Memories

### Recent Memories

```python
memories = await manager.retrieve(
    agent_id="my-agent",
    top_k=10
)
```

### Semantic Search

```python
memories = await manager.retrieve(
    agent_id="my-agent",
    query="What are the user's preferences?",
    top_k=5,
    min_score=0.7
)
```

### Filter by Type

```python
memories = await manager.retrieve(
    agent_id="my-agent",
    memory_type=MemoryType.LONG_TERM,
    top_k=20
)
```

### Filter by Tags

```python
memories = await manager.retrieve(
    agent_id="my-agent",
    tags=["preferences", "important"]
)
```

## Memory Management

### Get Specific Memory

```python
memory = await manager.get(memory_id)
if memory:
    print(f"Content: {memory.content}")
    print(f"Importance: {memory.importance}")
    print(f"Access count: {memory.access_count}")
```

### Delete Memory

```python
deleted = await manager.delete(memory_id)
```

### Clear Agent Memories

```python
# Clear all memories
count = await manager.clear(agent_id="my-agent")

# Clear specific type
count = await manager.clear(
    agent_id="my-agent",
    memory_type=MemoryType.SHORT_TERM
)
```

### Get Summary

```python
summary = await manager.get_summary("my-agent")
print(f"Total memories: {summary.total_memories}")
print(f"By type: {summary.by_type}")
print(f"Access count: {summary.total_access_count}")
```

## Cleanup and Maintenance

### Manual Cleanup

```python
# Remove expired memories
removed = await manager.cleanup()
print(f"Removed {removed} expired memories")
```

### Background Cleanup

```python
# Start background cleanup task
await manager.start_cleanup_task()

# Stop when done
await manager.stop_cleanup_task()
```

### Retention Policy

```python
from paracle_memory import MemoryRetentionPolicy

policy = MemoryRetentionPolicy(
    max_age_days=30,       # Remove memories older than 30 days
    max_memories=1000,     # Max memories per agent
    min_importance=0.1,    # Keep only important memories
    min_access_count=1,    # Keep accessed memories
    keep_recent=50         # Always keep 50 most recent
)

await manager.cleanup(policy=policy)
```

## Best Practices

### 1. Use Appropriate Memory Types

```python
# User preferences → Long-term
await manager.store(
    agent_id="assistant",
    content="User prefers concise responses",
    memory_type=MemoryType.LONG_TERM
)

# Current conversation → Short-term
await manager.store(
    agent_id="assistant",
    content="User asked about Python",
    memory_type=MemoryType.SHORT_TERM
)

# Completed tasks → Episodic
await manager.store(
    agent_id="coder",
    content="Fixed bug in auth module",
    memory_type=MemoryType.EPISODIC
)
```

### 2. Set Importance Scores

```python
# Critical information
await manager.store(..., importance=0.9)

# Nice to have
await manager.store(..., importance=0.3)
```

### 3. Use Tags for Organization

```python
await manager.store(
    content="...",
    tags=["user-preferences", "ui", "theme"]
)

# Later: retrieve by tags
memories = await manager.retrieve(tags=["user-preferences"])
```

### 4. Close Resources

```python
try:
    # Use manager
    await manager.store(...)
finally:
    await manager.close()
```

### 5. Handle Errors

```python
from paracle_memory.store import MemoryStoreError

try:
    memories = await manager.retrieve(agent_id="unknown")
except MemoryStoreError as e:
    print(f"Memory error: {e}")
```

## API Reference

### Memory

| Field | Type | Description |
|-------|------|-------------|
| id | str | Unique identifier |
| agent_id | str | Agent this belongs to |
| content | str | Memory content |
| memory_type | MemoryType | Type of memory |
| tags | list[str] | Categorization tags |
| metadata | dict | Additional data |
| importance | float | Score 0-1 |
| access_count | int | Times accessed |
| created_at | datetime | Creation time |
| last_accessed | datetime | Last access time |
| expires_at | datetime | Optional | Expiration |
| embedding | list[float] | Optional | Vector |

### MemorySummary

| Field | Type | Description |
|-------|------|-------------|
| agent_id | str | Agent identifier |
| total_memories | int | Total count |
| by_type | dict | Count by type |
| oldest_memory | datetime | Oldest timestamp |
| newest_memory | datetime | Newest timestamp |
| total_access_count | int | Sum of accesses |

## Installation

```bash
# Basic memory system
pip install paracle

# With semantic search
pip install paracle[memory]

# With vector storage
pip install paracle[vector]
```
