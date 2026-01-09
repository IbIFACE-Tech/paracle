"""Retry manager for workflow orchestration.

This module provides the RetryManager for handling retry logic
in workflow execution, including exponential backoff, error
classification, and context accumulation across attempts.

Usage:
    >>> from paracle_orchestration.retry import RetryManager
    >>> from paracle_domain.models.retry_policy import RetryPolicy, BackoffStrategy
    >>>
    >>> policy = RetryPolicy(
    ...     max_attempts=3,
    ...     backoff_strategy=BackoffStrategy.EXPONENTIAL,
    ...     initial_delay=1.0,
    ... )
    >>>
    >>> manager = RetryManager()
    >>> result = await manager.execute_with_retry(
    ...     step_name="api_call",
    ...     func=make_api_call,
    ...     policy=policy,
    ... )
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypeVar

from paracle_domain.models import (
    BackoffStrategy,
    ErrorCategory,
    RetryContext,
    RetryPolicy,
)

if TYPE_CHECKING:
    from paracle_events import EventBus

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryError(Exception):
    """Base exception for retry errors."""

    def __init__(self, message: str, *, code: str = "RETRY_ERROR") -> None:
        super().__init__(message)
        self.code = code


class MaxRetriesExceededError(RetryError):
    """Raised when maximum retry attempts are exceeded."""

    def __init__(self, step_name: str, attempts: int, last_error: Exception) -> None:
        super().__init__(
            f"Step '{step_name}' failed after {attempts} attempts: {last_error}",
            code="MAX_RETRIES_EXCEEDED",
        )
        self.step_name = step_name
        self.attempts = attempts
        self.last_error = last_error


def classify_error(error: Exception) -> ErrorCategory:
    """Classify an error into a category.

    This is a simple classification that can be extended with more
    sophisticated logic or learned from error patterns.

    Args:
        error: The exception to classify

    Returns:
        Error category
    """
    error_type = type(error).__name__
    error_message = str(error).lower()

    # Timeout errors
    if "timeout" in error_type.lower() or "timeout" in error_message:
        return ErrorCategory.TIMEOUT

    # Transient errors (network, rate limit, etc.)
    if any(
        keyword in error_message
        for keyword in [
            "rate limit",
            "too many requests",
            "temporarily unavailable",
            "service unavailable",
            "connection",
            "network",
            "502",
            "503",
            "504",
        ]
    ):
        return ErrorCategory.TRANSIENT

    # Validation errors
    if any(
        keyword in error_message
        for keyword in ["validation", "invalid", "bad request", "400"]
    ):
        return ErrorCategory.VALIDATION

    # Resource errors
    if any(
        keyword in error_message
        for keyword in [
            "out of memory",
            "quota",
            "limit exceeded",
            "insufficient",
            "resource",
        ]
    ):
        return ErrorCategory.RESOURCE

    # Permanent errors (auth, not found, etc.)
    if any(
        keyword in error_message
        for keyword in [
            "unauthorized",
            "forbidden",
            "not found",
            "401",
            "403",
            "404",
            "permission",
        ]
    ):
        return ErrorCategory.PERMANENT

    return ErrorCategory.UNKNOWN


class RetryManager:
    """Manages retry logic for workflow steps.

    The RetryManager handles:
    - Retry policy evaluation
    - Exponential backoff calculation
    - Error classification
    - Context accumulation across attempts
    - Event emission for observability

    Example:
        >>> manager = RetryManager(event_bus)
        >>>
        >>> policy = RetryPolicy(
        ...     max_attempts=3,
        ...     backoff_strategy=BackoffStrategy.EXPONENTIAL,
        ...     initial_delay=1.0,
        ... )
        >>>
        >>> result = await manager.execute_with_retry(
        ...     step_name="fetch_data",
        ...     func=fetch_from_api,
        ...     policy=policy,
        ...     workflow_id="wf_123",
        ...     execution_id="exec_456",
        ... )
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize the retry manager.

        Args:
            event_bus: Optional event bus for publishing retry events.
        """
        self._event_bus = event_bus
        self._retry_contexts: dict[str, RetryContext] = {}

    async def execute_with_retry(
        self,
        step_name: str,
        func: Callable[..., Any],
        policy: RetryPolicy,
        workflow_id: str = "",
        execution_id: str = "",
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a function with retry logic.

        Args:
            step_name: Name of the step being executed
            func: Function to execute (can be sync or async)
            policy: Retry policy to use
            workflow_id: ID of the workflow (for tracking)
            execution_id: ID of the execution (for tracking)
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function

        Raises:
            MaxRetriesExceededError: If all retry attempts fail
        """
        # Create retry context
        context_key = f"{workflow_id}:{execution_id}:{step_name}"
        retry_context = RetryContext(
            step_name=step_name,
            workflow_id=workflow_id,
            execution_id=execution_id,
            policy=policy,
        )
        self._retry_contexts[context_key] = retry_context

        attempt = 1
        last_error: Exception | None = None

        while attempt <= policy.max_attempts:
            try:
                # Calculate delay for this attempt (0 for first attempt)
                delay = policy.calculate_delay(attempt) if attempt > 1 else 0.0

                # Wait before retry (if not first attempt)
                if delay > 0:
                    logger.info(
                        f"Retry attempt {attempt}/{policy.max_attempts} for '{step_name}' "
                        f"after {delay:.1f}s delay"
                    )
                    await asyncio.sleep(delay)

                # Emit retry event
                if self._event_bus and attempt > 1:
                    await self._event_bus.publish(
                        event_type="workflow.step.retry",
                        data={
                            "step_name": step_name,
                            "workflow_id": workflow_id,
                            "execution_id": execution_id,
                            "attempt": attempt,
                            "max_attempts": policy.max_attempts,
                            "delay": delay,
                            "backoff_strategy": policy.backoff_strategy.value,
                        },
                    )

                # Execute the function
                started_at = datetime.utcnow()

                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Record successful attempt
                retry_context.add_attempt(
                    attempt_number=attempt,
                    started_at=started_at,
                    error=None,
                    delay_before=delay,
                    context={"result": "success"},
                )

                # Emit success event if there were retries
                if attempt > 1 and self._event_bus:
                    await self._event_bus.publish(
                        event_type="workflow.step.retry_succeeded",
                        data={
                            "step_name": step_name,
                            "workflow_id": workflow_id,
                            "execution_id": execution_id,
                            "total_attempts": attempt,
                            "total_retries": attempt - 1,
                        },
                    )

                return result

            except Exception as error:
                last_error = error
                error_category = classify_error(error)

                # Record failed attempt
                retry_context.add_attempt(
                    attempt_number=attempt,
                    started_at=datetime.utcnow(),
                    error=error,
                    error_category=error_category,
                    delay_before=delay if attempt > 1 else 0.0,
                    context={"error_type": type(error).__name__},
                )

                # Check if we should retry
                if not policy.should_retry(attempt, error, error_category):
                    logger.error(
                        f"Will not retry '{step_name}' after attempt {attempt}: "
                        f"{error_category.value} error - {error}"
                    )
                    break

                # Check if we've reached max attempts
                if attempt >= policy.max_attempts:
                    logger.error(
                        f"Max retries ({policy.max_attempts}) exceeded for '{step_name}'"
                    )
                    break

                # Log retry decision
                logger.warning(
                    f"Attempt {attempt}/{policy.max_attempts} failed for '{step_name}': "
                    f"{error_category.value} - {error}"
                )

                attempt += 1

        # All retries exhausted
        if self._event_bus:
            await self._event_bus.publish(
                event_type="workflow.step.retry_exhausted",
                data={
                    "step_name": step_name,
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "total_attempts": attempt - 1,
                    "last_error": str(last_error),
                },
            )

        raise MaxRetriesExceededError(
            step_name=step_name,
            attempts=attempt - 1,
            last_error=last_error or Exception("Unknown error"),
        )

    def get_retry_context(
        self, workflow_id: str, execution_id: str, step_name: str
    ) -> RetryContext | None:
        """Get retry context for a specific step.

        Args:
            workflow_id: Workflow ID
            execution_id: Execution ID
            step_name: Step name

        Returns:
            RetryContext if found, None otherwise
        """
        context_key = f"{workflow_id}:{execution_id}:{step_name}"
        return self._retry_contexts.get(context_key)

    def get_retry_stats(self) -> dict[str, Any]:
        """Get retry statistics across all executions.

        Returns:
            Statistics dictionary with counts and rates
        """
        total_contexts = len(self._retry_contexts)
        succeeded = sum(1 for ctx in self._retry_contexts.values() if ctx.succeeded)
        failed = total_contexts - succeeded

        total_attempts = sum(len(ctx.attempts) for ctx in self._retry_contexts.values())
        total_retries = sum(ctx.total_retries for ctx in self._retry_contexts.values())

        return {
            "total_contexts": total_contexts,
            "succeeded": succeeded,
            "failed": failed,
            "success_rate": succeeded / total_contexts if total_contexts > 0 else 0.0,
            "total_attempts": total_attempts,
            "total_retries": total_retries,
            "avg_retries_per_context": (
                total_retries / total_contexts if total_contexts > 0 else 0.0
            ),
        }

    def clear_context(self, workflow_id: str, execution_id: str) -> None:
        """Clear retry contexts for a specific execution.

        Args:
            workflow_id: Workflow ID
            execution_id: Execution ID
        """
        keys_to_remove = [
            key
            for key in self._retry_contexts
            if key.startswith(f"{workflow_id}:{execution_id}:")
        ]
        for key in keys_to_remove:
            del self._retry_contexts[key]


# Default retry policies for common scenarios

DEFAULT_RETRY_POLICY = RetryPolicy(
    enabled=True,
    max_attempts=3,
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    initial_delay=1.0,
    max_delay=60.0,
    backoff_factor=2.0,
)

AGGRESSIVE_RETRY_POLICY = RetryPolicy(
    enabled=True,
    max_attempts=5,
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    initial_delay=0.5,
    max_delay=30.0,
    backoff_factor=2.0,
)

CONSERVATIVE_RETRY_POLICY = RetryPolicy(
    enabled=True,
    max_attempts=2,
    backoff_strategy=BackoffStrategy.LINEAR,
    initial_delay=2.0,
    max_delay=10.0,
)

TRANSIENT_ONLY_POLICY = RetryPolicy(
    enabled=True,
    max_attempts=3,
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    initial_delay=1.0,
    max_delay=60.0,
    retry_condition={
        "error_categories": [ErrorCategory.TRANSIENT, ErrorCategory.TIMEOUT]
    },
)
