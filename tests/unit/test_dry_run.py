"""
Unit tests for Dry-Run Mode (DryRunExecutor).

Tests mocked LLM execution including:
- Different mock strategies (FIXED, RANDOM, FILE, ECHO)
- Configuration and initialization
- Mock response generation
- Step execution
- Response template creation
"""

import json
from pathlib import Path

import pytest
from paracle_domain.models import AgentSpec
from paracle_orchestration import (
    DryRunConfig,
    DryRunExecutor,
    MockResponse,
    MockStrategy,
    create_response_template,
)


@pytest.fixture
def test_agent() -> AgentSpec:
    """Test agent specification."""
    return AgentSpec(
        name="test-agent",
        description="Testing agent for dry-run tests",
        provider="openai",
        model="gpt-4",
    )


@pytest.fixture
def response_file(tmp_path: Path) -> Path:
    """Create temporary response file."""
    responses = {
        "responses": {
            "default": "Default mock response",
            "step_1": "Response for step 1",
            "step_2": "Response for step 2",
        },
        "metadata": {
            "version": "1.0",
            "description": "Test responses",
        },
    }

    file_path = tmp_path / "responses.json"
    with open(file_path, "w") as f:
        json.dump(responses, f)

    return file_path


# ============================================================================
# Configuration Tests
# ============================================================================


def test_dry_run_config_defaults():
    """Test DryRunConfig with default values."""
    config = DryRunConfig()

    assert config.strategy == MockStrategy.FIXED
    assert config.fixed_response is None
    assert config.response_file is None
    assert len(config.random_responses) == 3
    assert config.mock_tokens == 500
    assert config.mock_cost_per_token == 0.00001


def test_dry_run_config_custom():
    """Test DryRunConfig with custom values."""
    config = DryRunConfig(
        strategy=MockStrategy.RANDOM,
        random_responses=["Response A", "Response B"],
        mock_tokens=1000,
        mock_cost_per_token=0.00002,
    )

    assert config.strategy == MockStrategy.RANDOM
    assert config.random_responses == ["Response A", "Response B"]
    assert config.mock_tokens == 1000
    assert config.mock_cost_per_token == 0.00002


def test_dry_run_config_fixed_response():
    """Test DryRunConfig with fixed response."""
    config = DryRunConfig(
        strategy=MockStrategy.FIXED,
        fixed_response="This is a fixed response",
    )

    assert config.strategy == MockStrategy.FIXED
    assert config.fixed_response == "This is a fixed response"


def test_dry_run_config_file_strategy(response_file):
    """Test DryRunConfig with file strategy."""
    config = DryRunConfig(
        strategy=MockStrategy.FILE,
        response_file=response_file,
    )

    assert config.strategy == MockStrategy.FILE
    assert config.response_file == response_file


# ============================================================================
# Executor Initialization Tests
# ============================================================================


def test_executor_default_config():
    """Test DryRunExecutor with default configuration."""
    executor = DryRunExecutor()

    assert executor.config.strategy == MockStrategy.FIXED
    assert isinstance(executor._response_cache, dict)


def test_executor_custom_config():
    """Test DryRunExecutor with custom configuration."""
    config = DryRunConfig(
        strategy=MockStrategy.RANDOM,
        random_responses=["A", "B", "C"],
    )

    executor = DryRunExecutor(config)

    assert executor.config.strategy == MockStrategy.RANDOM
    assert executor.config.random_responses == ["A", "B", "C"]


def test_executor_loads_responses_from_file(response_file):
    """Test executor loads responses from file on init."""
    config = DryRunConfig(
        strategy=MockStrategy.FILE,
        response_file=response_file,
    )

    executor = DryRunExecutor(config)

    assert "default" in executor._response_cache
    assert "step_1" in executor._response_cache
    assert executor._response_cache["step_1"] == "Response for step 1"


def test_executor_file_missing_raises_error(tmp_path):
    """Test executor raises error if response file missing."""
    nonexistent = tmp_path / "nonexistent.json"

    config = DryRunConfig(
        strategy=MockStrategy.FILE,
        response_file=nonexistent,
    )

    with pytest.raises(FileNotFoundError):
        DryRunExecutor(config)


def test_executor_file_strategy_requires_file():
    """Test FILE strategy requires response_file."""
    config = DryRunConfig(strategy=MockStrategy.FILE)

    with pytest.raises(ValueError, match="response_file is required"):
        DryRunExecutor(config)


# ============================================================================
# Mock Response Generation Tests
# ============================================================================


def test_generate_mock_response_fixed(test_agent):
    """Test mock response generation with FIXED strategy."""
    config = DryRunConfig(
        strategy=MockStrategy.FIXED,
        fixed_response="Fixed response content",
    )
    executor = DryRunExecutor(config)

    response = executor.generate_mock_response(
        agent=test_agent,
        prompt="Test prompt",
        step_id="step_1",
    )

    assert isinstance(response, MockResponse)
    assert response.content == "Fixed response content"
    assert response.model == "mock-openai"
    assert response.tokens == 500
    assert response.cost == 500 * 0.00001


def test_generate_mock_response_random(test_agent):
    """Test mock response generation with RANDOM strategy."""
    config = DryRunConfig(
        strategy=MockStrategy.RANDOM,
        random_responses=["Response A", "Response B", "Response C"],
    )
    executor = DryRunExecutor(config)

    response = executor.generate_mock_response(
        agent=test_agent,
        prompt="Test prompt",
        step_id="step_1",
    )

    assert isinstance(response, MockResponse)
    assert response.content in ["Response A", "Response B", "Response C"]
    assert response.model == "mock-openai"


def test_generate_mock_response_file(test_agent, response_file):
    """Test mock response generation with FILE strategy."""
    config = DryRunConfig(
        strategy=MockStrategy.FILE,
        response_file=response_file,
    )
    executor = DryRunExecutor(config)

    # Step with specific response
    response = executor.generate_mock_response(
        agent=test_agent,
        prompt="Test prompt",
        step_id="step_1",
    )

    assert response.content == "Response for step 1"

    # Step without specific response (falls back to default)
    response = executor.generate_mock_response(
        agent=test_agent,
        prompt="Test prompt",
        step_id="unknown_step",
    )

    assert response.content == "Default mock response"


def test_generate_mock_response_echo(test_agent):
    """Test mock response generation with ECHO strategy."""
    config = DryRunConfig(strategy=MockStrategy.ECHO)
    executor = DryRunExecutor(config)

    prompt = "This is the test prompt"
    response = executor.generate_mock_response(
        agent=test_agent,
        prompt=prompt,
        step_id="step_1",
    )

    assert isinstance(response, MockResponse)
    assert prompt in response.content
    assert "[DRY-RUN ECHO]" in response.content


def test_generate_mock_response_default_fixed(test_agent):
    """Test default FIXED strategy returns default message."""
    config = DryRunConfig(strategy=MockStrategy.FIXED)
    executor = DryRunExecutor(config)

    response = executor.generate_mock_response(
        agent=test_agent,
        prompt="Test prompt",
        step_id="step_1",
    )

    assert "Mock response" in response.content


def test_generate_mock_response_custom_tokens(test_agent):
    """Test mock response with custom token count."""
    config = DryRunConfig(
        strategy=MockStrategy.FIXED,
        fixed_response="Test",
        mock_tokens=1000,
        mock_cost_per_token=0.00002,
    )
    executor = DryRunExecutor(config)

    response = executor.generate_mock_response(
        agent=test_agent,
        prompt="Test prompt",
        step_id="step_1",
    )

    assert response.tokens == 1000
    assert response.cost == 1000 * 0.00002


# ============================================================================
# Step Execution Tests
# ============================================================================


@pytest.mark.asyncio
async def test_execute_step_fixed(test_agent):
    """Test step execution with FIXED strategy."""
    config = DryRunConfig(
        strategy=MockStrategy.FIXED,
        fixed_response="Step completed",
    )
    executor = DryRunExecutor(config)

    result = await executor.execute_step(
        agent=test_agent,
        prompt="Do something",
        step_id="step_1",
    )

    assert result["step_id"] == "step_1"
    assert result["agent_id"] == "test-agent"
    assert result["status"] == "completed"
    assert result["output"] == "Step completed"
    assert result["metadata"]["dry_run"] is True
    assert result["metadata"]["mock_strategy"] == "fixed"


@pytest.mark.asyncio
async def test_execute_step_with_context(test_agent):
    """Test step execution with execution context."""
    config = DryRunConfig(strategy=MockStrategy.FIXED)
    executor = DryRunExecutor(config)

    context = {"previous_output": "Some data"}

    result = await executor.execute_step(
        agent=test_agent,
        prompt="Use previous output",
        step_id="step_2",
        context=context,
    )

    assert result["status"] == "completed"
    assert "metadata" in result
    assert result["metadata"]["dry_run"] is True


@pytest.mark.asyncio
async def test_execute_step_metadata(test_agent):
    """Test step execution includes all metadata."""
    config = DryRunConfig(
        strategy=MockStrategy.FIXED,
        mock_tokens=750,
        mock_cost_per_token=0.00001,
    )
    executor = DryRunExecutor(config)

    result = await executor.execute_step(
        agent=test_agent,
        prompt="Test",
        step_id="step_1",
    )

    metadata = result["metadata"]
    assert metadata["dry_run"] is True
    assert metadata["mock_strategy"] == "fixed"
    assert metadata["model"] == "mock-openai"
    assert metadata["tokens"] == 750
    assert metadata["cost_usd"] == 750 * 0.00001


@pytest.mark.asyncio
async def test_execute_step_random_varies(test_agent):
    """Test RANDOM strategy produces different responses."""
    config = DryRunConfig(
        strategy=MockStrategy.RANDOM,
        random_responses=["A", "B", "C"],
    )
    executor = DryRunExecutor(config)

    # Execute multiple times
    outputs = set()
    for i in range(10):
        result = await executor.execute_step(
            agent=test_agent,
            prompt="Test",
            step_id=f"step_{i}",
        )
        outputs.add(result["output"])

    # Should get more than one unique response (statistically likely)
    assert len(outputs) > 1


# ============================================================================
# Response Template Tests
# ============================================================================


def test_create_response_template():
    """Test creating response template."""
    template = create_response_template()

    assert isinstance(template, dict)
    assert "responses" in template
    assert "metadata" in template

    responses = template["responses"]
    assert "default" in responses
    assert "step_1" in responses
    assert "step_2" in responses
    assert "step_3" in responses

    metadata = template["metadata"]
    assert "version" in metadata
    assert "description" in metadata


def test_response_template_structure():
    """Test response template has correct structure."""
    template = create_response_template()

    # Verify all step responses are strings
    for key, value in template["responses"].items():
        assert isinstance(key, str)
        assert isinstance(value, str)


# ============================================================================
# MockResponse Model Tests
# ============================================================================


def test_mock_response_model():
    """Test MockResponse model."""
    response = MockResponse(
        content="Test content",
        model="mock-model",
        tokens=100,
        cost=0.001,
    )

    assert response.content == "Test content"
    assert response.model == "mock-model"
    assert response.tokens == 100
    assert response.cost == 0.001


def test_mock_response_defaults():
    """Test MockResponse with default values."""
    response = MockResponse(content="Test")

    assert response.content == "Test"
    assert response.model == "mock-model"
    assert response.tokens == 0
    assert response.cost == 0.0


def test_mock_response_serialization():
    """Test MockResponse can be serialized."""
    response = MockResponse(
        content="Test",
        model="mock-openai",
        tokens=500,
        cost=0.005,
    )

    response_dict = response.model_dump()

    assert isinstance(response_dict, dict)
    assert response_dict["content"] == "Test"
    assert response_dict["tokens"] == 500


# ============================================================================
# MockStrategy Enum Tests
# ============================================================================


def test_mock_strategy_values():
    """Test MockStrategy enum values."""
    assert MockStrategy.FIXED == "fixed"
    assert MockStrategy.RANDOM == "random"
    assert MockStrategy.FILE == "file"
    assert MockStrategy.ECHO == "echo"


def test_mock_strategy_from_string():
    """Test creating MockStrategy from string."""
    assert MockStrategy("fixed") == MockStrategy.FIXED
    assert MockStrategy("random") == MockStrategy.RANDOM
    assert MockStrategy("file") == MockStrategy.FILE
    assert MockStrategy("echo") == MockStrategy.ECHO


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_dry_run_workflow(test_agent, response_file):
    """Test complete dry-run workflow execution."""
    # Setup
    config = DryRunConfig(
        strategy=MockStrategy.FILE,
        response_file=response_file,
        mock_tokens=500,
        mock_cost_per_token=0.00001,
    )
    executor = DryRunExecutor(config)

    # Execute multiple steps
    results = []
    for i in range(1, 4):
        result = await executor.execute_step(
            agent=test_agent,
            prompt=f"Step {i} prompt",
            step_id=f"step_{i}",
        )
        results.append(result)

    # Verify all steps completed
    assert len(results) == 3
    assert all(r["status"] == "completed" for r in results)

    # Verify different responses for step_1 and step_2
    assert results[0]["output"] == "Response for step 1"
    assert results[1]["output"] == "Response for step 2"
    # step_3 not in file
    assert results[2]["output"] == "Default mock response"


@pytest.mark.asyncio
async def test_cost_tracking_across_steps(test_agent):
    """Test cost tracking across multiple steps."""
    config = DryRunConfig(
        strategy=MockStrategy.FIXED,
        mock_tokens=500,
        mock_cost_per_token=0.00001,
    )
    executor = DryRunExecutor(config)

    # Execute 5 steps
    total_cost = 0.0
    for i in range(5):
        result = await executor.execute_step(
            agent=test_agent,
            prompt=f"Step {i}",
            step_id=f"step_{i}",
        )
        total_cost += result["metadata"]["cost_usd"]

    # Verify total cost
    expected_cost = 5 * 500 * 0.00001
    assert abs(total_cost - expected_cost) < 0.000001


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_invalid_strategy_raises_error(test_agent):
    """Test that invalid strategy raises error."""
    config = DryRunConfig(strategy=MockStrategy.FIXED)
    executor = DryRunExecutor(config)

    # Manually set invalid strategy (shouldn't happen normally)
    executor.config.strategy = "invalid"  # type: ignore

    with pytest.raises(ValueError, match="Unknown mock strategy"):
        executor.generate_mock_response(
            agent=test_agent,
            prompt="Test",
            step_id="step_1",
        )


def test_malformed_response_file(tmp_path):
    """Test executor handles malformed response file."""
    bad_file = tmp_path / "bad.json"
    with open(bad_file, "w") as f:
        f.write("{ invalid json")

    config = DryRunConfig(
        strategy=MockStrategy.FILE,
        response_file=bad_file,
    )

    with pytest.raises(json.JSONDecodeError):
        DryRunExecutor(config)


def test_response_file_missing_responses_key(tmp_path):
    """Test response file without 'responses' key."""
    bad_file = tmp_path / "bad.json"
    with open(bad_file, "w") as f:
        json.dump({"metadata": {}}, f)  # Missing 'responses'

    config = DryRunConfig(
        strategy=MockStrategy.FILE,
        response_file=bad_file,
    )

    executor = DryRunExecutor(config)

    # Should create empty cache
    assert executor._response_cache == {}


# ============================================================================
# Edge Cases
# ============================================================================


@pytest.mark.asyncio
async def test_execute_step_agent_without_provider(test_agent):
    """Test execution with agent that has minimal fields (should still work)."""
    agent_minimal = AgentSpec(
        name="minimal-agent",
        provider="mock",
        model="mock-model",
    )

    config = DryRunConfig(strategy=MockStrategy.FIXED)
    executor = DryRunExecutor(config)

    result = await executor.execute_step(
        agent=agent_minimal,
        prompt="Test prompt",
        step_id="step_1",
    )

    # Should work with minimal agent fields
    assert result["status"] == "completed"
    assert result["metadata"]["dry_run"] is True


@pytest.mark.asyncio
async def test_execute_step_empty_prompt(test_agent):
    """Test execution with empty prompt."""
    config = DryRunConfig(strategy=MockStrategy.ECHO)
    executor = DryRunExecutor(config)

    result = await executor.execute_step(
        agent=test_agent,
        prompt="",
        step_id="step_1",
    )

    assert result["status"] == "completed"
    assert "[DRY-RUN ECHO]" in result["output"]


def test_random_responses_empty_list():
    """Test RANDOM strategy with empty response list."""
    config = DryRunConfig(
        strategy=MockStrategy.RANDOM,
        random_responses=[],
    )

    executor = DryRunExecutor(config)

    # Should raise error when trying to choose from empty list
    with pytest.raises(IndexError):
        executor.generate_mock_response(
            agent=AgentSpec(name="test", provider="mock", model="mock-model"),
            prompt="Test",
            step_id="step_1",
        )
