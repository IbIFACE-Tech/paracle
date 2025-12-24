"""Test configuration and fixtures."""

import pytest


@pytest.fixture
def sample_agent_spec() -> dict:
    """Sample agent specification for testing."""
    return {
        "name": "test-agent",
        "description": "Test agent",
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.7,
    }


@pytest.fixture
def sample_workflow_spec() -> dict:
    """Sample workflow specification for testing."""
    return {
        "name": "test-workflow",
        "description": "Test workflow",
        "steps": [
            {
                "id": "step1",
                "name": "First Step",
                "agent_id": "agent1",
                "prompt": "Do something",
                "dependencies": [],
            }
        ],
    }
