"""Unit tests for TokenOptimizationCapability."""

import pytest

from paracle_meta.capabilities.token_optimization import (
    TokenOptimizationCapability,
    TokenOptimizationConfig,
    OptimizationLevel,
    ContentType,
)


@pytest.fixture
def token_optimizer():
    """Create TokenOptimizationCapability instance."""
    config = TokenOptimizationConfig(
        default_level=OptimizationLevel.MEDIUM,
    )
    return TokenOptimizationCapability(config)


@pytest.mark.asyncio
async def test_token_optimization_initialization(token_optimizer):
    """Test TokenOptimizationCapability initialization."""
    assert token_optimizer.name == "token_optimization"
    assert token_optimizer.config.default_level == OptimizationLevel.MEDIUM


@pytest.mark.asyncio
async def test_optimize_text_light(token_optimizer):
    """Test light optimization."""
    text = "This is a very, very long text with lots of repetition and redundant information."

    result = await token_optimizer.optimize(text=text, level=OptimizationLevel.LIGHT)

    assert result.success is True
    assert len(result.output["optimized_text"]) <= len(text)
    assert result.output["original_tokens"] > 0
    assert result.output["optimized_tokens"] > 0
    assert result.output["reduction_percent"] >= 0


@pytest.mark.asyncio
async def test_optimize_text_medium(token_optimizer):
    """Test medium optimization."""
    text = """
    This is a long document with many sentences.
    Some of these sentences contain redundant information.
    We want to compress this text significantly.
    The medium level should provide good compression.
    """

    result = await token_optimizer.optimize(text=text, level=OptimizationLevel.MEDIUM)

    assert result.success is True
    # Medium should compress more than light
    assert result.output["reduction_percent"] >= 10


@pytest.mark.asyncio
async def test_optimize_text_aggressive(token_optimizer):
    """Test aggressive optimization."""
    text = """
    This is a very long document with extensive content.
    We have multiple paragraphs here for testing purposes.
    The aggressive optimization level should compress this significantly.
    It should maintain core meaning while reducing tokens dramatically.
    Additional padding text to make it longer for testing.
    More text here to ensure significant compression opportunity.
    """

    result = await token_optimizer.optimize(
        text=text, level=OptimizationLevel.AGGRESSIVE
    )

    assert result.success is True
    # Aggressive should achieve significant compression
    assert result.output["reduction_percent"] >= 20


@pytest.mark.asyncio
async def test_optimize_code(token_optimizer):
    """Test optimizing code content."""
    code = """
def calculate_sum(numbers):
    # This function calculates the sum of numbers
    total = 0
    for number in numbers:
        total = total + number
    return total

# Test the function
result = calculate_sum([1, 2, 3, 4, 5])
print(f"The result is: {result}")
"""

    result = await token_optimizer.optimize(text=code, content_type=ContentType.CODE)

    assert result.success is True
    # Should preserve code structure
    assert "def calculate_sum" in result.output["optimized_text"]


@pytest.mark.asyncio
async def test_optimize_conversation(token_optimizer):
    """Test optimizing conversation history."""
    messages = [
        {"role": "user", "content": "Hello, how are you today?"},
        {
            "role": "assistant",
            "content": "I'm doing well, thank you! How can I help you?",
        },
        {"role": "user", "content": "I need help with Python programming"},
        {
            "role": "assistant",
            "content": "Of course! I'd be happy to help with Python. What specifically would you like to know?",
        },
        {"role": "user", "content": "How do I read a file?"},
        {
            "role": "assistant",
            "content": "You can read a file using open() function...",
        },
    ]

    result = await token_optimizer.optimize_conversation(
        messages=messages, preserve_recent=2  # Keep last 2 messages
    )

    assert result.success is True
    assert len(result.output["optimized_messages"]) >= 2
    assert result.output["original_tokens"] > result.output["optimized_tokens"]


@pytest.mark.asyncio
async def test_optimize_conversation_with_max_tokens(token_optimizer):
    """Test conversation optimization with token limit."""
    messages = [{"role": "user", "content": "Message " * 100} for _ in range(10)]

    result = await token_optimizer.optimize_conversation(
        messages=messages, max_tokens=200
    )

    assert result.success is True
    assert result.output["optimized_tokens"] <= 200


@pytest.mark.asyncio
async def test_preserve_recent_messages(token_optimizer):
    """Test preserving recent messages in conversation."""
    messages = [{"role": "user", "content": f"Message {i}"} for i in range(10)]

    result = await token_optimizer.optimize_conversation(
        messages=messages, preserve_recent=3
    )

    assert result.success is True
    # Last 3 messages should be preserved
    optimized = result.output["optimized_messages"]
    assert len(optimized) >= 3
    assert optimized[-1]["content"] == "Message 9"


@pytest.mark.asyncio
async def test_optimize_documentation(token_optimizer):
    """Test optimizing documentation content."""
    doc = """
# User Guide

## Introduction

This is a comprehensive user guide for our application.
It contains detailed instructions and examples.

## Installation

Follow these steps to install:
1. Download the package
2. Run the installer
3. Configure settings

## Usage

Here's how to use the application...
"""

    result = await token_optimizer.optimize(
        text=doc, content_type=ContentType.DOCUMENTATION
    )

    assert result.success is True
    # Should preserve structure
    assert "#" in result.output["optimized_text"]


@pytest.mark.asyncio
async def test_estimate_tokens(token_optimizer):
    """Test token estimation."""
    text = "This is a test sentence for token counting."

    result = await token_optimizer.estimate_tokens(text=text)

    assert result.success is True
    assert result.output["token_count"] > 0
    assert result.output["character_count"] == len(text)


@pytest.mark.asyncio
async def test_batch_optimize(token_optimizer):
    """Test batch optimization of multiple texts."""
    texts = [
        "First text to optimize",
        "Second text to optimize",
        "Third text to optimize",
    ]

    result = await token_optimizer.batch_optimize(
        texts=texts, level=OptimizationLevel.MEDIUM
    )

    assert result.success is True
    assert len(result.output["results"]) == 3
    assert result.output["total_reduction_percent"] >= 0


@pytest.mark.asyncio
async def test_optimize_preserves_meaning(token_optimizer):
    """Test that optimization preserves core meaning."""
    text = "Python is a high-level programming language known for its simplicity."

    result = await token_optimizer.optimize(text=text)

    assert result.success is True
    optimized = result.output["optimized_text"].lower()
    # Should preserve key concepts
    assert "python" in optimized
    assert "programming" in optimized or "language" in optimized


@pytest.mark.asyncio
async def test_empty_text(token_optimizer):
    """Test handling empty text."""
    result = await token_optimizer.optimize(text="")

    assert result.success is True
    assert result.output["optimized_text"] == ""
    assert result.output["reduction_percent"] == 0


@pytest.mark.asyncio
async def test_short_text_no_optimization(token_optimizer):
    """Test that very short text isn't over-optimized."""
    text = "Hi"

    result = await token_optimizer.optimize(text=text)

    assert result.success is True
    # Short text shouldn't be aggressively optimized
    assert len(result.output["optimized_text"]) >= 1


@pytest.mark.asyncio
async def test_get_optimization_stats(token_optimizer):
    """Test getting optimization statistics."""
    # Perform some optimizations
    await token_optimizer.optimize(text="Test text " * 50)
    await token_optimizer.optimize(text="Another test " * 30)

    result = await token_optimizer.get_stats()

    assert result.success is True
    assert "total_optimizations" in result.output
    assert "average_reduction_percent" in result.output


@pytest.mark.asyncio
async def test_different_content_types(token_optimizer):
    """Test optimization behavior for different content types."""
    content_samples = {
        ContentType.TEXT: "This is plain text content.",
        ContentType.CODE: "def foo(): return 42",
        ContentType.DOCUMENTATION: "# API Reference\n\nDetails here...",
        ContentType.CONVERSATION: "User: Hello\nAssistant: Hi there!",
    }

    for content_type, sample in content_samples.items():
        result = await token_optimizer.optimize(text=sample, content_type=content_type)

        assert result.success is True
        assert result.output["content_type"] == content_type


@pytest.mark.asyncio
async def test_optimize_with_custom_rules(token_optimizer):
    """Test optimization with custom preservation rules."""
    text = "IMPORTANT: Do not remove this critical information about PROJECT_NAME."

    result = await token_optimizer.optimize(
        text=text, preserve_patterns=["IMPORTANT", "PROJECT_NAME"]
    )

    assert result.success is True
    optimized = result.output["optimized_text"]
    # Should preserve marked terms
    assert "IMPORTANT" in optimized or "critical" in optimized.lower()
