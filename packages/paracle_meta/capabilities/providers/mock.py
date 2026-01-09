"""Mock provider for testing.

This provider returns predictable mock responses for testing purposes.
It does not require any API keys or external services.

Example:
    >>> from paracle_meta.capabilities.providers import MockProvider
    >>> from paracle_meta.capabilities.provider_protocol import LLMRequest
    >>>
    >>> provider = MockProvider()
    >>> await provider.initialize()
    >>>
    >>> request = LLMRequest(prompt="Hello")
    >>> response = await provider.complete(request)
    >>> assert response.provider == "mock"
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator
from typing import Any

from paracle_meta.capabilities.provider_protocol import (
    BaseProvider,
    LLMRequest,
    LLMResponse,
    LLMUsage,
    StreamChunk,
    ToolCallRequest,
)


class MockProvider(BaseProvider):
    """Mock LLM provider for testing.

    Returns predictable responses based on the request content.
    Useful for unit tests and development without API costs.

    Attributes:
        responses: Custom response mapping (pattern -> response).
        delay_ms: Simulated latency in milliseconds.
        fail_rate: Probability of simulated failures (0.0-1.0).
    """

    def __init__(
        self,
        responses: dict[str, str] | None = None,
        delay_ms: float = 0,
        fail_rate: float = 0.0,
        model: str = "mock-model",
    ):
        """Initialize mock provider.

        Args:
            responses: Custom pattern -> response mapping.
            delay_ms: Simulated response delay.
            fail_rate: Probability of simulated failure.
            model: Mock model name.
        """
        super().__init__(model=model)
        self._responses = responses or {}
        self._delay_ms = delay_ms
        self._fail_rate = fail_rate
        self._call_count = 0
        self._last_request: LLMRequest | None = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "mock"

    @property
    def call_count(self) -> int:
        """Number of calls made to this provider."""
        return self._call_count

    @property
    def last_request(self) -> LLMRequest | None:
        """Last request received."""
        return self._last_request

    async def initialize(self) -> None:
        """Initialize mock provider (always succeeds)."""
        self._set_available()

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate mock completion.

        Args:
            request: The LLM request.

        Returns:
            Mock response based on request content.
        """
        self._call_count += 1
        self._last_request = request

        if self._delay_ms > 0:
            await asyncio.sleep(self._delay_ms / 1000)

        # Check for simulated failure
        import random

        if random.random() < self._fail_rate:
            from paracle_meta.capabilities.provider_protocol import ProviderAPIError

            raise ProviderAPIError(self.name, "Simulated failure")

        content = self._generate_response(request)
        tool_calls = self._generate_tool_calls(request)

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=LLMUsage(
                input_tokens=len(str(request.prompt or "")) // 4,
                output_tokens=len(content) // 4,
            ),
            provider=self.name,
            model=self._model or "mock-model",
            stop_reason="end_turn",
            latency_ms=self._delay_ms,
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Stream mock completion.

        Args:
            request: The LLM request.

        Yields:
            Stream chunks with mock content.
        """
        self._call_count += 1
        self._last_request = request

        content = self._generate_response(request)
        words = content.split()

        for i, word in enumerate(words):
            if self._delay_ms > 0:
                await asyncio.sleep(self._delay_ms / 1000 / len(words))

            is_final = i == len(words) - 1
            yield StreamChunk(
                content=word + (" " if not is_final else ""),
                is_final=is_final,
                usage=(
                    LLMUsage(
                        input_tokens=len(str(request.prompt or "")) // 4,
                        output_tokens=len(content) // 4,
                    )
                    if is_final
                    else None
                ),
            )

    def _generate_response(self, request: LLMRequest) -> str:
        """Generate response based on request content."""
        prompt = request.prompt or ""
        if request.messages:
            # Get last user message
            for msg in reversed(request.messages):
                if msg.role == "user":
                    prompt = (
                        msg.content
                        if isinstance(msg.content, str)
                        else str(msg.content)
                    )
                    break

        prompt_lower = prompt.lower()

        # Check custom responses
        for pattern, response in self._responses.items():
            if re.search(pattern, prompt, re.IGNORECASE):
                return response

        # Default responses based on content
        if "code" in prompt_lower or "function" in prompt_lower:
            return self._code_response(prompt)
        if "test" in prompt_lower:
            return self._test_response(prompt)
        if "explain" in prompt_lower or "what" in prompt_lower:
            return self._explanation_response(prompt)
        if "refactor" in prompt_lower:
            return self._refactor_response(prompt)
        if "plan" in prompt_lower or "decompose" in prompt_lower:
            return self._plan_response(prompt)

        return f"Mock response for: {prompt[:100]}"

    def _code_response(self, prompt: str) -> str:
        """Generate mock code response."""
        return '''```python
def mock_function(x: int, y: int) -> int:
    """Mock function generated by MockProvider.

    Args:
        x: First parameter.
        y: Second parameter.

    Returns:
        Sum of x and y.
    """
    return x + y
```'''

    def _test_response(self, prompt: str) -> str:
        """Generate mock test response."""
        return '''```python
import pytest

def test_mock_function():
    """Test mock function."""
    assert mock_function(1, 2) == 3
    assert mock_function(0, 0) == 0
    assert mock_function(-1, 1) == 0
```'''

    def _explanation_response(self, prompt: str) -> str:
        """Generate mock explanation response."""
        return (
            "This is a mock explanation. In a real scenario, the LLM would provide "
            "a detailed explanation based on the context and question asked."
        )

    def _refactor_response(self, prompt: str) -> str:
        """Generate mock refactor response."""
        return '''```python
class RefactoredClass:
    """Refactored code by MockProvider."""

    def __init__(self, value: int):
        self._value = value

    @property
    def value(self) -> int:
        return self._value

    def process(self) -> int:
        return self._value * 2
```'''

    def _plan_response(self, prompt: str) -> str:
        """Generate mock plan response."""
        return """## Plan

1. **Step 1**: Analyze requirements
   - Review the current implementation
   - Identify areas for improvement

2. **Step 2**: Design solution
   - Create architecture diagram
   - Define interfaces

3. **Step 3**: Implement changes
   - Write code
   - Add tests

4. **Step 4**: Validate
   - Run tests
   - Review code"""

    def _generate_tool_calls(self, request: LLMRequest) -> list[ToolCallRequest] | None:
        """Generate mock tool calls if tools are provided."""
        if not request.tools:
            return None

        prompt = request.prompt or ""
        prompt_lower = prompt.lower()

        # Check if prompt suggests tool use
        if "search" in prompt_lower and any(t.name == "search" for t in request.tools):
            return [
                ToolCallRequest(
                    id="mock_call_1",
                    name="search",
                    input={"query": "mock search query"},
                )
            ]
        if "read" in prompt_lower and any(t.name == "read_file" for t in request.tools):
            return [
                ToolCallRequest(
                    id="mock_call_2",
                    name="read_file",
                    input={"path": "mock/path.txt"},
                )
            ]

        return None

    def add_response(self, pattern: str, response: str) -> None:
        """Add custom response pattern.

        Args:
            pattern: Regex pattern to match.
            response: Response to return when matched.
        """
        self._responses[pattern] = response

    def reset(self) -> None:
        """Reset call count and last request."""
        self._call_count = 0
        self._last_request = None


class RecordingMockProvider(MockProvider):
    """Mock provider that records all requests and responses.

    Useful for testing and debugging.
    """

    def __init__(self, **kwargs: Any):
        """Initialize recording mock provider."""
        super().__init__(**kwargs)
        self._history: list[tuple[LLMRequest, LLMResponse]] = []

    @property
    def history(self) -> list[tuple[LLMRequest, LLMResponse]]:
        """Request/response history."""
        return self._history

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Complete and record."""
        response = await super().complete(request)
        self._history.append((request, response))
        return response

    def clear_history(self) -> None:
        """Clear recorded history."""
        self._history.clear()


class FailingMockProvider(MockProvider):
    """Mock provider that always fails.

    Useful for testing error handling and fallback strategies.
    """

    def __init__(
        self,
        error_type: str = "api_error",
        error_message: str = "Simulated failure",
        **kwargs: Any,
    ):
        """Initialize failing provider.

        Args:
            error_type: Type of error to raise (api_error, rate_limit, auth).
            error_message: Error message.
        """
        super().__init__(**kwargs)
        self._error_type = error_type
        self._error_message = error_message

    @property
    def name(self) -> str:
        """Provider name."""
        return "failing_mock"

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Always fail."""
        self._call_count += 1
        self._last_request = request

        from paracle_meta.capabilities.provider_protocol import (
            ProviderAPIError,
            ProviderAuthenticationError,
            ProviderRateLimitError,
        )

        if self._error_type == "rate_limit":
            raise ProviderRateLimitError(self.name, retry_after=60)
        if self._error_type == "auth":
            raise ProviderAuthenticationError(self.name)

        raise ProviderAPIError(self.name, self._error_message)

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Always fail."""
        await self.complete(request)  # Will raise
        yield StreamChunk()  # Never reached
