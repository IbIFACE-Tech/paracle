"""Ollama provider implementation.

This provider uses the Ollama API to interact with local models.

Example:
    >>> from paracle_meta.capabilities.providers import OllamaProvider
    >>> from paracle_meta.capabilities.provider_protocol import LLMRequest
    >>>
    >>> provider = OllamaProvider(model="llama3.2")
    >>> await provider.initialize()
    >>>
    >>> request = LLMRequest(prompt="Explain Python decorators")
    >>> response = await provider.complete(request)
    >>> print(response.content)
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import Any

from paracle_meta.capabilities.provider_protocol import (
    BaseProvider,
    LLMRequest,
    LLMResponse,
    LLMUsage,
    ProviderAPIError,
    ProviderUnavailableError,
    StreamChunk,
)


class OllamaModels:
    """Common Ollama model identifiers."""

    # Llama models
    LLAMA_32 = "llama3.2"
    LLAMA_31 = "llama3.1"
    LLAMA_3 = "llama3"

    # Code models
    CODELLAMA = "codellama"
    DEEPSEEK_CODER = "deepseek-coder"
    QWEN_CODER = "qwen2.5-coder"

    # Other models
    MISTRAL = "mistral"
    MIXTRAL = "mixtral"
    PHI = "phi"
    GEMMA = "gemma"

    # Default
    DEFAULT = LLAMA_32


class OllamaProvider(BaseProvider):
    """Ollama provider for local models.

    Uses the Ollama HTTP API to interact with locally running models.
    Supports completion and streaming.

    Note: Tool use support in Ollama is limited and model-dependent.

    Attributes:
        model: Model name to use.
        host: Ollama server host.
        port: Ollama server port.
    """

    def __init__(
        self,
        model: str = OllamaModels.DEFAULT,
        host: str = "localhost",
        port: int = 11434,
        timeout: float = 120.0,
    ):
        """Initialize Ollama provider.

        Args:
            model: Model name to use.
            host: Ollama server host.
            port: Ollama server port.
            timeout: Request timeout in seconds.
        """
        super().__init__(model=model)
        self._host = host
        self._port = port
        self._timeout = timeout
        self._base_url = f"http://{host}:{port}"
        self._session: Any = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "ollama"

    async def initialize(self) -> None:
        """Initialize and check Ollama connection."""
        try:
            import aiohttp

            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout)
            )

            # Check if Ollama is running
            async with self._session.get(f"{self._base_url}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m["name"] for m in data.get("models", [])]

                    # Check if requested model is available
                    if self._model and not any(self._model in m for m in models):
                        self._set_error(
                            f"Model '{self._model}' not found. "
                            f"Available: {', '.join(models[:5])}"
                        )
                        return

                    self._set_available()
                else:
                    self._set_error(f"Ollama returned status {resp.status}")

        except ImportError:
            self._set_error("aiohttp package not installed")
        except Exception as e:
            self._set_error(f"Cannot connect to Ollama: {e}")

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate completion using Ollama.

        Args:
            request: The LLM request.

        Returns:
            LLM response with content and metadata.

        Raises:
            ProviderError: If completion fails.
        """
        if not self._session:
            raise ProviderUnavailableError(self.name, "Not initialized")

        start_time = time.time()

        try:
            params = self._build_params(request)

            async with self._session.post(
                f"{self._base_url}/api/chat",
                json=params,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise ProviderAPIError(self.name, error_text, resp.status)

                data = await resp.json()
                return self._parse_response(data, start_time)

        except ProviderAPIError:
            raise
        except Exception as e:
            raise ProviderAPIError(self.name, str(e)) from e

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Stream completion from Ollama.

        Args:
            request: The LLM request.

        Yields:
            Stream chunks with partial content.
        """
        if not self._session:
            raise ProviderUnavailableError(self.name, "Not initialized")

        try:
            params = self._build_params(request, stream=True)

            async with self._session.post(
                f"{self._base_url}/api/chat",
                json=params,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise ProviderAPIError(self.name, error_text, resp.status)

                total_tokens = 0
                async for line in resp.content:
                    if not line:
                        continue

                    import json

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    message = data.get("message", {})
                    content = message.get("content", "")

                    if data.get("done"):
                        # Final chunk
                        eval_count = data.get("eval_count", 0)
                        prompt_eval_count = data.get("prompt_eval_count", 0)
                        yield StreamChunk(
                            content=content,
                            is_final=True,
                            usage=LLMUsage(
                                input_tokens=prompt_eval_count,
                                output_tokens=eval_count,
                            ),
                        )
                    else:
                        yield StreamChunk(content=content)

        except ProviderAPIError:
            raise
        except Exception as e:
            raise ProviderAPIError(self.name, str(e)) from e

    def _build_params(
        self, request: LLMRequest, stream: bool = False
    ) -> dict[str, Any]:
        """Build API request parameters."""
        messages: list[dict[str, str]] = []

        # Add system prompt
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        # Add conversation messages
        for msg in request.get_messages():
            if msg.role == "system":
                continue

            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            messages.append({"role": msg.role, "content": content})

        params: dict[str, Any] = {
            "model": self._model or OllamaModels.DEFAULT,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        # Add optional parameters
        if request.top_p is not None:
            params["options"]["top_p"] = request.top_p
        if request.top_k is not None:
            params["options"]["top_k"] = request.top_k
        if request.stop_sequences:
            params["options"]["stop"] = request.stop_sequences

        return params

    def _parse_response(self, data: dict[str, Any], start_time: float) -> LLMResponse:
        """Parse Ollama API response."""
        message = data.get("message", {})
        content = message.get("content", "")

        return LLMResponse(
            content=content,
            usage=LLMUsage(
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
            ),
            provider=self.name,
            model=data.get("model", self._model or ""),
            stop_reason=data.get("done_reason", "stop"),
            latency_ms=(time.time() - start_time) * 1000,
        )

    async def shutdown(self) -> None:
        """Shutdown the provider."""
        if self._session:
            await self._session.close()
            self._session = None
        await super().shutdown()

    async def list_models(self) -> list[str]:
        """List available models.

        Returns:
            List of available model names.
        """
        if not self._session:
            raise ProviderUnavailableError(self.name, "Not initialized")

        async with self._session.get(f"{self._base_url}/api/tags") as resp:
            if resp.status == 200:
                data = await resp.json()
                return [m["name"] for m in data.get("models", [])]
            return []

    async def pull_model(self, model: str) -> bool:
        """Pull a model from the Ollama library.

        Args:
            model: Model name to pull.

        Returns:
            True if successful.
        """
        if not self._session:
            raise ProviderUnavailableError(self.name, "Not initialized")

        async with self._session.post(
            f"{self._base_url}/api/pull",
            json={"name": model},
        ) as resp:
            return resp.status == 200
