"""Base Generator for Paracle Meta-Agent.

Provides common functionality for all artifact generators.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from paracle_core.logging import get_logger
from pydantic import BaseModel, Field

from paracle_meta.exceptions import GenerationError
from paracle_meta.providers import ProviderOrchestrator

logger = get_logger(__name__)


class GenerationRequest(BaseModel):
    """Request for artifact generation."""

    artifact_type: str = Field(..., description="Type: agent, workflow, skill, policy")
    name: str = Field(..., description="Artifact name")
    description: str = Field(..., description="Natural language description")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )
    auto_apply: bool = Field(default=False, description="Auto-apply without review")


class GenerationResult(BaseModel):
    """Result of artifact generation."""

    id: str = Field(..., description="Unique generation ID")
    artifact_type: str
    name: str
    content: str = Field(..., description="Generated artifact content")

    # Metadata
    provider: str = Field(..., description="LLM provider used")
    model: str = Field(..., description="Model used")
    quality_score: float = Field(
        default=0.0, ge=0, le=10, description="Quality score 0-10"
    )
    cost_usd: float = Field(default=0.0, ge=0, description="Cost in USD")

    tokens_input: int = Field(default=0, description="Input tokens")
    tokens_output: int = Field(default=0, description="Output tokens")

    reasoning: str = Field(default="", description="Meta-agent's reasoning")

    created_at: datetime = Field(default_factory=datetime.now)


class BaseGenerator(ABC):
    """Base class for artifact generators.

    Provides common functionality:
    - LLM provider interaction
    - Prompt construction
    - Response parsing
    - Error handling
    """

    # Override in subclasses
    ARTIFACT_TYPE: str = "base"
    SYSTEM_PROMPT: str = "You are a helpful assistant."

    def __init__(self, orchestrator: ProviderOrchestrator):
        """Initialize generator.

        Args:
            orchestrator: Provider orchestrator for LLM calls
        """
        self.orchestrator = orchestrator
        logger.debug(f"{self.__class__.__name__} initialized")

    async def generate(
        self,
        request: GenerationRequest,
        provider: str,
        model: str,
        best_practices: list[Any] | None = None,
    ) -> GenerationResult:
        """Generate an artifact.

        Args:
            request: Generation request
            provider: LLM provider to use
            model: Model to use
            best_practices: Best practices to include in prompt

        Returns:
            GenerationResult with generated content

        Raises:
            GenerationError: If generation fails
        """
        logger.info(
            f"Generating {request.artifact_type}: {request.name}",
            extra={"provider": provider, "model": model},
        )

        start_time = time.time()

        try:
            # Build prompt
            prompt = self._build_prompt(request, best_practices)

            # Call LLM
            response = await self._call_llm(provider, model, prompt)

            # Parse response
            content = self._parse_response(response)

            # Calculate cost
            tokens_in = response.get("tokens_input", 0)
            tokens_out = response.get("tokens_output", 0)
            cost = self._calculate_cost(provider, model, tokens_in, tokens_out)

            # Create result
            result = GenerationResult(
                id=f"gen_{int(datetime.now().timestamp() * 1000)}",
                artifact_type=request.artifact_type,
                name=request.name,
                content=content,
                provider=provider,
                model=model,
                cost_usd=cost,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                reasoning=response.get("reasoning", ""),
            )

            # Record performance
            latency_ms = (time.time() - start_time) * 1000
            self.orchestrator.record_request(
                provider=provider,
                model=model,
                tokens=tokens_in + tokens_out,
                cost=cost,
                quality_score=0,  # Will be updated later
                latency_ms=latency_ms,
                success=True,
            )

            logger.info(
                f"Generated {request.artifact_type}: {request.name}",
                extra={
                    "provider": provider,
                    "tokens": tokens_in + tokens_out,
                    "cost": cost,
                    "latency_ms": latency_ms,
                },
            )

            return result

        except Exception as e:
            logger.error(
                f"Generation failed: {e}",
                extra={"artifact_type": request.artifact_type, "name": request.name},
            )

            # Record failure
            self.orchestrator.record_request(
                provider=provider,
                model=model,
                tokens=0,
                cost=0,
                quality_score=0,
                latency_ms=(time.time() - start_time) * 1000,
                success=False,
            )

            raise GenerationError(
                artifact_type=request.artifact_type,
                name=request.name,
                reason=str(e),
                provider=provider,
            )

    @abstractmethod
    def _build_prompt(
        self,
        request: GenerationRequest,
        best_practices: list[Any] | None = None,
    ) -> str:
        """Build the prompt for LLM generation.

        Args:
            request: Generation request
            best_practices: Best practices to include

        Returns:
            Formatted prompt string
        """
        pass

    def _parse_response(self, response: dict[str, Any]) -> str:
        """Parse LLM response to extract content.

        Args:
            response: Raw LLM response

        Returns:
            Parsed content string
        """
        content = response.get("content", "")

        # Extract content from code blocks if present
        if "```yaml" in content:
            start = content.find("```yaml") + 7
            end = content.find("```", start)
            if end > start:
                content = content[start:end].strip()
        elif "```markdown" in content:
            start = content.find("```markdown") + 11
            end = content.find("```", start)
            if end > start:
                content = content[start:end].strip()
        elif "```" in content:
            # Generic code block
            start = content.find("```") + 3
            # Skip language identifier if present
            newline = content.find("\n", start)
            if newline > start:
                start = newline + 1
            end = content.find("```", start)
            if end > start:
                content = content[start:end].strip()

        return content

    async def _call_llm(
        self,
        provider: str,
        model: str,
        prompt: str,
    ) -> dict[str, Any]:
        """Call the LLM provider.

        Args:
            provider: Provider name
            model: Model name
            prompt: Prompt to send

        Returns:
            Dictionary with response content and metadata
        """
        # For now, return a mock response
        # In production, this would use paracle_providers
        try:
            from paracle_providers import get_provider

            llm_provider = get_provider(provider)
            response = await llm_provider.complete(
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                model=model,
                temperature=0.3,  # Low for deterministic output
            )

            return {
                "content": response.content,
                "tokens_input": response.usage.input_tokens if response.usage else 0,
                "tokens_output": response.usage.output_tokens if response.usage else 0,
                "reasoning": "",
            }

        except ImportError:
            # Fallback to mock for testing
            logger.warning("paracle_providers not available, using mock response")
            return self._mock_response(prompt)

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def _mock_response(self, prompt: str) -> dict[str, Any]:
        """Generate mock response for testing.

        Args:
            prompt: The prompt (used to determine response)

        Returns:
            Mock response dictionary
        """
        # Generate basic mock content based on artifact type
        mock_content = f"""# Generated {self.ARTIFACT_TYPE.title()}

name: generated_{self.ARTIFACT_TYPE}
description: Generated from natural language description

## Configuration

This is a mock response for testing.
In production, this would be generated by the LLM.

## Details

- Type: {self.ARTIFACT_TYPE}
- Generated: {datetime.now().isoformat()}
"""

        return {
            "content": mock_content,
            "tokens_input": len(prompt.split()) * 2,  # Rough estimate
            "tokens_output": len(mock_content.split()) * 2,
            "reasoning": "Mock generation for testing",
        }

    def _calculate_cost(
        self,
        provider: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
    ) -> float:
        """Calculate cost of generation.

        Args:
            provider: Provider name
            model: Model name
            tokens_in: Input tokens
            tokens_out: Output tokens

        Returns:
            Cost in USD
        """
        # Cost per 1K tokens (rough estimates)
        COSTS = {
            "anthropic": {
                "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
                "claude-opus-4-20250514": {"input": 0.015, "output": 0.075},
                "default": {"input": 0.003, "output": 0.015},
            },
            "openai": {
                "gpt-4o": {"input": 0.0025, "output": 0.01},
                "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
                "default": {"input": 0.003, "output": 0.01},
            },
            "google": {
                "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
                "default": {"input": 0.001, "output": 0.004},
            },
            "ollama": {
                "default": {"input": 0.0, "output": 0.0},  # Free local
            },
        }

        provider_costs = COSTS.get(
            provider, {"default": {"input": 0.002, "output": 0.008}}
        )
        model_costs = provider_costs.get(model, provider_costs.get("default", {}))

        input_cost = (tokens_in / 1000) * model_costs.get("input", 0.002)
        output_cost = (tokens_out / 1000) * model_costs.get("output", 0.008)

        return round(input_cost + output_cost, 6)

    def _format_best_practices(self, practices: list[Any] | None) -> str:
        """Format best practices for prompt inclusion.

        Args:
            practices: List of best practices

        Returns:
            Formatted string
        """
        if not practices:
            return ""

        lines = ["## Best Practices to Follow", ""]
        for p in practices:
            if hasattr(p, "title") and hasattr(p, "recommendation"):
                lines.append(f"- **{p.title}**: {p.recommendation}")
            elif isinstance(p, dict):
                lines.append(
                    f"- **{p.get('title', 'Practice')}**: {p.get('recommendation', '')}"
                )

        return "\n".join(lines)


__all__ = [
    "GenerationRequest",
    "GenerationResult",
    "BaseGenerator",
]
