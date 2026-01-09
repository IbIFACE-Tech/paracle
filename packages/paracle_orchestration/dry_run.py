"""
Dry-Run Mode: Execute workflows with mocked LLM responses.

This module provides functionality to execute workflows in dry-run mode,
where LLM calls are mocked to enable cost-free testing and validation.
"""

import json
import random
from enum import Enum
from pathlib import Path
from typing import Any

from paracle_domain.models import AgentSpec
from pydantic import BaseModel, Field


class MockStrategy(str, Enum):
    """Strategy for generating mock responses."""

    FIXED = "fixed"  # Fixed response for all steps
    RANDOM = "random"  # Random response from predefined options
    FILE = "file"  # Load responses from file
    ECHO = "echo"  # Echo the prompt back as response


class MockResponse(BaseModel):
    """A mocked LLM response."""

    content: str = Field(description="Response content")
    model: str = Field(default="mock-model", description="Model identifier")
    tokens: int = Field(default=0, description="Tokens used (mocked)")
    cost: float = Field(default=0.0, description="Cost in USD (mocked)")


class DryRunConfig(BaseModel):
    """Configuration for dry-run execution."""

    strategy: MockStrategy = Field(
        default=MockStrategy.FIXED, description="Mock response strategy"
    )
    fixed_response: str | None = Field(
        default=None, description="Fixed response (for FIXED strategy)"
    )
    response_file: Path | None = Field(
        default=None, description="Response file path (for FILE strategy)"
    )
    random_responses: list[str] = Field(
        default_factory=lambda: [
            "Mock response: Task completed successfully.",
            "Mock response: Analysis complete. No issues found.",
            "Mock response: Data processed. Results available.",
        ],
        description="Response pool (for RANDOM strategy)",
    )
    mock_tokens: int = Field(
        default=500, description="Tokens to report for each response"
    )
    mock_cost_per_token: float = Field(
        default=0.00001, description="Cost per token (USD)"
    )


class DryRunExecutor:
    """
    Executes workflow steps with mocked LLM responses.

    This executor replaces actual LLM calls with mocked responses based on
    the configured strategy, enabling cost-free testing and validation.
    """

    def __init__(self, config: DryRunConfig | None = None):
        """
        Initialize dry-run executor.

        Args:
            config: Dry-run configuration
        """
        self.config = config or DryRunConfig()
        self._response_cache: dict[str, str] = {}

        # Load responses from file if FILE strategy
        if self.config.strategy == MockStrategy.FILE:
            self._load_responses_from_file()

    def _load_responses_from_file(self) -> None:
        """Load mocked responses from file."""
        if not self.config.response_file:
            raise ValueError("response_file is required for FILE strategy")

        if not self.config.response_file.exists():
            raise FileNotFoundError(
                f"Response file not found: {self.config.response_file}"
            )

        with open(self.config.response_file, encoding="utf-8") as f:
            data = json.load(f)
            self._response_cache = data.get("responses", {})

    def generate_mock_response(
        self,
        agent: AgentSpec,
        prompt: str,
        step_id: str,
    ) -> MockResponse:
        """
        Generate a mocked LLM response.

        Args:
            agent: Agent specification (for context)
            prompt: Input prompt
            step_id: Step identifier (for FILE strategy)

        Returns:
            MockResponse: Mocked LLM response
        """
        content = self._generate_content(step_id, prompt)
        tokens = self.config.mock_tokens
        cost = tokens * self.config.mock_cost_per_token

        return MockResponse(
            content=content,
            model=f"mock-{agent.provider or 'default'}",
            tokens=tokens,
            cost=cost,
        )

    def _generate_content(self, step_id: str, prompt: str) -> str:
        """
        Generate response content based on strategy.

        Args:
            step_id: Step identifier
            prompt: Input prompt

        Returns:
            str: Generated response content
        """
        if self.config.strategy == MockStrategy.FIXED:
            return self.config.fixed_response or "Mock response: Task completed."

        elif self.config.strategy == MockStrategy.RANDOM:
            return random.choice(self.config.random_responses)

        elif self.config.strategy == MockStrategy.FILE:
            # Try to find step-specific response
            if step_id in self._response_cache:
                return self._response_cache[step_id]
            # Fall back to default
            return self._response_cache.get(
                "default", "Mock response: No specific response configured."
            )

        elif self.config.strategy == MockStrategy.ECHO:
            return f"[DRY-RUN ECHO] Prompt: {prompt}"

        else:
            raise ValueError(f"Unknown mock strategy: {self.config.strategy}")

    async def execute_step(
        self,
        agent: AgentSpec,
        prompt: str,
        step_id: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a workflow step in dry-run mode.

        Args:
            agent: Agent specification
            prompt: Input prompt
            step_id: Step identifier
            context: Execution context

        Returns:
            Dict[str, Any]: Step execution result with mocked response
        """
        # Generate mock response
        mock_response = self.generate_mock_response(agent, prompt, step_id)

        # Return result in same format as actual execution
        return {
            "step_id": step_id,
            "agent_id": agent.name,
            "status": "completed",
            "output": mock_response.content,
            "metadata": {
                "dry_run": True,
                "mock_strategy": self.config.strategy.value,
                "model": mock_response.model,
                "tokens": mock_response.tokens,
                "cost_usd": mock_response.cost,
            },
        }


def create_response_template() -> dict[str, Any]:
    """
    Create a template for mock response files.

    Returns:
        Dict[str, Any]: Template structure

    Example:
        >>> template = create_response_template()
        >>> with open("responses.json", "w") as f:
        ...     json.dump(template, f, indent=2)
    """
    return {
        "responses": {
            "default": "Mock response: Task completed successfully.",
            "step_1": "Mock response for step 1: Analysis complete.",
            "step_2": "Mock response for step 2: Data processed.",
            "step_3": "Mock response for step 3: Report generated.",
        },
        "metadata": {
            "version": "1.0",
            "description": "Mock responses for dry-run workflow execution",
        },
    }


# Example usage:
"""
# 1. FIXED strategy (same response for all steps)
config = DryRunConfig(
    strategy=MockStrategy.FIXED,
    fixed_response="All tasks completed successfully."
)

# 2. RANDOM strategy (random from pool)
config = DryRunConfig(
    strategy=MockStrategy.RANDOM,
    random_responses=[
        "Response A: Success",
        "Response B: Complete",
        "Response C: Done",
    ]
)

# 3. FILE strategy (load from JSON)
config = DryRunConfig(
    strategy=MockStrategy.FILE,
    response_file=Path("responses.json")
)

# 4. ECHO strategy (echo prompt back)
config = DryRunConfig(strategy=MockStrategy.ECHO)

# Create executor
executor = DryRunExecutor(config)

# Execute step
result = await executor.execute_step(
    agent=my_agent,
    prompt="Analyze this data",
    step_id="step_1"
)
"""
