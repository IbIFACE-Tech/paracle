"""Ollama provider for local LLM models with retry support."""

from collections.abc import AsyncIterator
from typing import Any

try:
    import httpx
except ImportError:
    raise ImportError(
        "httpx package is required for Ollama provider. "
        "Install it with: pip install httpx"
    )

from paracle_providers.base import (
    ChatMessage,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    StreamChunk,
    TokenUsage,
)
from paracle_providers.exceptions import (
    LLMProviderError,
    ProviderConnectionError,
    ProviderTimeoutError,
)
from paracle_providers.retry import RetryableProvider, RetryConfig


class OllamaProvider(LLMProvider, RetryableProvider):
    """
    Ollama LLM provider for local models with automatic retry support.

    Supports Llama, Mistral, CodeLlama, and other models via Ollama.
    Includes exponential backoff with jitter for transient failures.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        retry_config: RetryConfig | None = None,
        **kwargs,
    ):
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            retry_config: Configuration for retry behavior (optional)
            **kwargs: Additional configuration
        """
        super().__init__(api_key=None, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)

        # Initialize retry configuration
        if retry_config:
            self.configure_retry(retry_config)

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate a chat completion using Ollama with automatic retry.

        Uses exponential backoff with jitter for transient failures.

        Args:
            messages: List of chat messages
            config: LLM configuration
            model: Model name (e.g., "llama2", "mistral")
            **kwargs: Additional Ollama-specific parameters

        Returns:
            LLMResponse with generated content

        Raises:
            LLMProviderError: On Ollama API errors after retries exhausted
            ProviderTimeoutError: On timeout after retries
        """

        async def _make_request() -> LLMResponse:
            return await self._raw_chat_completion(messages, config, model, **kwargs)

        operation_name = f"ollama.chat_completion({model})"
        return await self.with_retry(_make_request, operation_name)

    async def _raw_chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> LLMResponse:
        """Raw chat completion without retry wrapper."""
        try:
            # Convert messages to Ollama format
            ollama_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            # Build request payload
            payload = {
                "model": model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": config.temperature,
                },
            }

            if config.max_tokens:
                payload["options"]["num_predict"] = config.max_tokens
            if config.top_p:
                payload["options"]["top_p"] = config.top_p
            if config.stop_sequences:
                payload["options"]["stop"] = config.stop_sequences

            payload.update(kwargs)

            # Make API call
            response = await self.client.post(
                "/api/chat",
                json=payload,
                timeout=config.timeout,
            )
            response.raise_for_status()

            data = response.json()

            # Extract response
            message = data.get("message", {})
            content = message.get("content", "")

            return LLMResponse(
                content=content,
                finish_reason=data.get("done_reason", "stop"),
                usage=TokenUsage(
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                    total_tokens=data.get("prompt_eval_count", 0)
                    + data.get("eval_count", 0),
                ),
                model=data.get("model", model),
                metadata={
                    "total_duration": data.get("total_duration"),
                    "load_duration": data.get("load_duration"),
                    "eval_duration": data.get("eval_duration"),
                },
            )

        except httpx.TimeoutException as e:
            raise ProviderTimeoutError(
                str(e), provider="ollama", timeout=config.timeout
            ) from e
        except httpx.ConnectError as e:
            raise ProviderConnectionError(str(e), provider="ollama") from e
        except httpx.HTTPError as e:
            raise LLMProviderError(
                str(e), provider="ollama", model=model, original_error=e
            ) from e

    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a chat completion using Ollama.

        Args:
            messages: List of chat messages
            config: LLM configuration
            model: Model name
            **kwargs: Additional Ollama-specific parameters

        Yields:
            StreamChunk objects with incremental content

        Raises:
            LLMProviderError: On Ollama API errors
        """
        try:
            ollama_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            payload = {
                "model": model,
                "messages": ollama_messages,
                "stream": True,
                "options": {
                    "temperature": config.temperature,
                },
            }

            if config.max_tokens:
                payload["options"]["num_predict"] = config.max_tokens
            if config.top_p:
                payload["options"]["top_p"] = config.top_p

            payload.update(kwargs)

            # Stream response
            async with self.client.stream(
                "POST",
                "/api/chat",
                json=payload,
                timeout=config.timeout,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip():
                        import json

                        data = json.loads(line)

                        message = data.get("message", {})
                        content = message.get("content", "")

                        yield StreamChunk(
                            content=content,
                            finish_reason="stop" if data.get("done") else None,
                            metadata={"model": data.get("model", model)},
                        )

        except httpx.HTTPError as e:
            raise LLMProviderError(
                str(e), provider="ollama", model=model, original_error=e
            ) from e

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate Ollama-specific configuration."""
        if "model" in config and not isinstance(config["model"], str):
            raise ValueError("model must be a string")

        if "temperature" in config:
            temp = config["temperature"]
            if not isinstance(temp, int | float) or not 0 <= temp <= 2:
                raise ValueError("temperature must be between 0 and 2")

        return True

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "ollama"

    @property
    def supported_models(self) -> list[str]:
        """
        Return list of commonly supported models.

        Note: Actual available models depend on what's installed locally.
        """
        return [
            "llama2",
            "llama2:13b",
            "llama2:70b",
            "mistral",
            "mixtral",
            "codellama",
            "phi",
            "neural-chat",
            "starling-lm",
        ]

    async def list_local_models(self) -> list[str]:
        """
        List models installed locally in Ollama.

        Returns:
            List of available model names

        Raises:
            LLMProviderError: On API errors
        """
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])

            return [model["name"] for model in models]

        except httpx.HTTPError as e:
            raise LLMProviderError(str(e), provider="ollama", original_error=e) from e

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
