"""Paracle Memory - Agent Memory System.

This package provides persistent memory for AI agents:
- Short-term memory (conversation context)
- Long-term memory (knowledge persistence)
- Episodic memory (interaction history)
- Working memory (task context)

Usage:
    from paracle_memory import MemoryManager, MemoryConfig

    # Initialize memory system
    memory = MemoryManager(
        config=MemoryConfig(
            backend="sqlite",  # or "vector" for semantic memory
            persist_dir=".paracle/memory"
        )
    )

    # Store memory
    await memory.store(
        agent_id="coder-agent",
        content="User prefers Python 3.12 features",
        memory_type="long_term",
        tags=["preferences", "python"]
    )

    # Retrieve relevant memories
    memories = await memory.retrieve(
        agent_id="coder-agent",
        query="What Python version does the user prefer?",
        top_k=5
    )

    # Clear agent memory
    await memory.clear(agent_id="coder-agent")
"""

from paracle_memory.config import MemoryBackend, MemoryConfig
from paracle_memory.manager import MemoryManager
from paracle_memory.models import (
    ConversationMemory,
    EpisodicMemory,
    Memory,
    MemoryType,
    SemanticMemory,
)
from paracle_memory.store import MemoryStore

__version__ = "1.0.1"

__all__ = [
    # Core
    "MemoryManager",
    "MemoryStore",
    "MemoryConfig",
    "MemoryBackend",
    # Models
    "Memory",
    "MemoryType",
    "ConversationMemory",
    "EpisodicMemory",
    "SemanticMemory",
]
