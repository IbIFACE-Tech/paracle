"""Decorators for caching LLM calls."""

import functools
from collections.abc import Callable
from typing import Any

from paracle_cache.llm_cache import CacheKey, get_llm_cache


def cached_llm_call(ttl: int = 3600):
    """Decorator to cache LLM calls.

    Caches based on provider, model, messages, and parameters.

    Args:
        ttl: Time to live in seconds (default: 1 hour)

    Example:
        ```python
        @cached_llm_call(ttl=1800)  # 30 minutes
        async def call_llm(
            provider: str,
            model: str,
            messages: list[dict],
            temperature: float = 0.7,
        ) -> dict:
            # LLM call implementation
            ...
        ```
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(
            provider: str,
            model: str,
            messages: list[dict[str, str]],
            temperature: float = 0.7,
            max_tokens: int | None = None,
            **kwargs: Any,
        ) -> dict[str, Any]:
            cache = get_llm_cache(ttl=ttl)

            # Create cache key
            key = CacheKey(
                provider=provider,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Try cache first
            cached_response = cache.get(key)
            if cached_response is not None:
                return cached_response

            # Call LLM
            response = await func(
                provider=provider,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # Cache response
            cache.set(key, response, ttl=ttl)

            return response

        @functools.wraps(func)
        def sync_wrapper(
            provider: str,
            model: str,
            messages: list[dict[str, str]],
            temperature: float = 0.7,
            max_tokens: int | None = None,
            **kwargs: Any,
        ) -> dict[str, Any]:
            cache = get_llm_cache(ttl=ttl)

            # Create cache key
            key = CacheKey(
                provider=provider,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Try cache first
            cached_response = cache.get(key)
            if cached_response is not None:
                return cached_response

            # Call LLM
            response = func(
                provider=provider,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # Cache response
            cache.set(key, response, ttl=ttl)

            return response

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
