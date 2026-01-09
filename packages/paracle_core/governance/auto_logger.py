"""Automatic Governance Logging - No Manual Logging Required.

This module provides decorators and context managers for automatic action logging.
All agent operations are logged automatically without manual intervention.

Key Features:
- @log_agent_action decorator for functions
- Automatic success/failure logging
- Context managers for sessions
- Integration with existing GovernanceLogger
- Zero manual logging required

Example:
    @log_agent_action("CoderAgent", "IMPLEMENTATION")
    async def implement_feature(spec: FeatureSpec) -> Implementation:
        # Implementation here
        # Automatically logged on success/failure!
        return result
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from typing import Any, ParamSpec, TypeVar

from paracle_core.governance.logger import get_governance_logger
from paracle_core.governance.types import GovernanceActionType, GovernanceAgentType

P = ParamSpec("P")
R = TypeVar("R")


def sanitize_args(args: tuple, kwargs: dict) -> dict[str, Any]:
    """Sanitize function arguments for logging.

    Removes sensitive data and limits size.

    Args:
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Sanitized argument dictionary
    """
    sanitized = {}

    # Sensitive keys to exclude
    sensitive_keys = {
        "password",
        "token",
        "api_key",
        "secret",
        "credentials",
        "auth",
        "authorization",
        "private_key",
        "access_token",
    }

    # Add kwargs (excluding sensitive)
    for key, value in kwargs.items():
        if key.lower() in sensitive_keys:
            sanitized[key] = "***REDACTED***"
        elif hasattr(value, "__dict__") and hasattr(value, "__class__"):
            # Object - just log class name
            sanitized[key] = f"<{value.__class__.__name__}>"
        else:
            # Try to serialize, truncate if too long
            try:
                str_value = str(value)
                if len(str_value) > 200:
                    sanitized[key] = str_value[:197] + "..."
                else:
                    sanitized[key] = str_value
            except Exception:
                sanitized[key] = f"<{type(value).__name__}>"

    # Add positional args
    if args:
        sanitized["_args"] = [
            f"<{arg.__class__.__name__}>" if hasattr(arg, "__class__") else str(arg)
            for arg in args[:5]  # Limit to first 5 args
        ]

    return sanitized


def log_agent_action(
    agent_type: str | GovernanceAgentType,
    action_type: str | GovernanceActionType | None = None,
    description: str | None = None,
    log_args: bool = True,
    log_result: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for automatic action logging.

    Automatically logs function execution with success/failure status.
    Works with both sync and async functions.

    Args:
        agent_type: Agent performing the action (e.g., "CoderAgent")
        action_type: Type of action (e.g., "IMPLEMENTATION"). If None, derived from function name
        description: Custom description. If None, uses function name and docstring
        log_args: Whether to log function arguments (default: True)
        log_result: Whether to log return value (default: False, can be large)

    Returns:
        Decorated function with automatic logging

    Example:
        @log_agent_action("CoderAgent", "IMPLEMENTATION")
        async def implement_feature(spec: FeatureSpec) -> Implementation:
            # ... implementation ...
            return result

        # Automatically logs:
        # [2026-01-07 10:30:00] [CoderAgent] [IMPLEMENTATION] implement_feature completed
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # Determine if async or sync
        is_async = inspect.iscoroutinefunction(func)

        # Determine action type from function name if not provided
        inferred_action = action_type or _infer_action_type(func.__name__)

        # Get description
        desc = description or _get_function_description(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                start_time = datetime.now()
                logger = get_governance_logger()

                try:
                    # Execute function
                    result = await func(*args, **kwargs)

                    # Log success
                    duration = (datetime.now() - start_time).total_seconds()
                    details = {"duration_seconds": duration}

                    if log_args:
                        details["arguments"] = sanitize_args(args, kwargs)

                    if log_result and result is not None:
                        try:
                            details["result"] = str(result)[:500]  # Limit size
                        except Exception:
                            details["result"] = f"<{type(result).__name__}>"

                    logger.log(
                        action=inferred_action,
                        description=f"{desc} completed",
                        agent=agent_type,
                        details=details,
                    )

                    return result

                except Exception as e:
                    # Log failure
                    duration = (datetime.now() - start_time).total_seconds()
                    logger.log(
                        action=GovernanceActionType.ERROR,
                        description=f"{desc} failed: {str(e)}",
                        agent=agent_type,
                        details={
                            "duration_seconds": duration,
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                        },
                    )
                    raise

            return async_wrapper  # type: ignore

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                start_time = datetime.now()
                logger = get_governance_logger()

                try:
                    # Execute function
                    result = func(*args, **kwargs)

                    # Log success
                    duration = (datetime.now() - start_time).total_seconds()
                    details = {"duration_seconds": duration}

                    if log_args:
                        details["arguments"] = sanitize_args(args, kwargs)

                    if log_result and result is not None:
                        try:
                            details["result"] = str(result)[:500]
                        except Exception:
                            details["result"] = f"<{type(result).__name__}>"

                    logger.log(
                        action=inferred_action,
                        description=f"{desc} completed",
                        agent=agent_type,
                        details=details,
                    )

                    return result

                except Exception as e:
                    # Log failure
                    duration = (datetime.now() - start_time).total_seconds()
                    logger.log(
                        action=GovernanceActionType.ERROR,
                        description=f"{desc} failed: {str(e)}",
                        agent=agent_type,
                        details={
                            "duration_seconds": duration,
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                        },
                    )
                    raise

            return sync_wrapper  # type: ignore

    return decorator


@contextmanager
def agent_operation(
    agent_type: str | GovernanceAgentType,
    operation: str,
    details: dict[str, Any] | None = None,
):
    """Context manager for automatic operation logging.

    Logs start and end of operation, including duration and any errors.

    Args:
        agent_type: Agent performing the operation
        operation: Description of operation
        details: Additional details to log

    Example:
        with agent_operation("CoderAgent", "Implementing authentication"):
            # ... do work ...
            pass

        # Automatically logs start and completion
    """
    logger = get_governance_logger()
    start_time = datetime.now()

    # Log start
    logger.log(
        action=GovernanceActionType.START,
        description=f"Started: {operation}",
        agent=agent_type,
        details=details,
    )

    try:
        yield

        # Log completion
        duration = (datetime.now() - start_time).total_seconds()
        logger.log(
            action=GovernanceActionType.COMPLETION,
            description=f"Completed: {operation}",
            agent=agent_type,
            details={
                **(details or {}),
                "duration_seconds": duration,
            },
        )

    except Exception as e:
        # Log error
        duration = (datetime.now() - start_time).total_seconds()
        logger.log(
            action=GovernanceActionType.ERROR,
            description=f"Failed: {operation} - {str(e)}",
            agent=agent_type,
            details={
                **(details or {}),
                "duration_seconds": duration,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        raise


@asynccontextmanager
async def async_agent_operation(
    agent_type: str | GovernanceAgentType,
    operation: str,
    details: dict[str, Any] | None = None,
):
    """Async context manager for automatic operation logging.

    Args:
        agent_type: Agent performing the operation
        operation: Description of operation
        details: Additional details to log

    Example:
        async with async_agent_operation("CoderAgent", "Implementing feature"):
            # ... async work ...
            pass
    """
    logger = get_governance_logger()
    start_time = datetime.now()

    # Log start
    logger.log(
        action=GovernanceActionType.START,
        description=f"Started: {operation}",
        agent=agent_type,
        details=details,
    )

    try:
        yield

        # Log completion
        duration = (datetime.now() - start_time).total_seconds()
        logger.log(
            action=GovernanceActionType.COMPLETION,
            description=f"Completed: {operation}",
            agent=agent_type,
            details={
                **(details or {}),
                "duration_seconds": duration,
            },
        )

    except Exception as e:
        # Log error
        duration = (datetime.now() - start_time).total_seconds()
        logger.log(
            action=GovernanceActionType.ERROR,
            description=f"Failed: {operation} - {str(e)}",
            agent=agent_type,
            details={
                **(details or {}),
                "duration_seconds": duration,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        raise


def _infer_action_type(function_name: str) -> GovernanceActionType:
    """Infer action type from function name.

    Args:
        function_name: Name of the function

    Returns:
        Inferred action type
    """
    name_lower = function_name.lower()

    # Implementation patterns
    if any(word in name_lower for word in ["implement", "create", "add", "build"]):
        return GovernanceActionType.IMPLEMENTATION

    # Testing patterns
    if any(word in name_lower for word in ["test", "validate", "verify", "check"]):
        return GovernanceActionType.TEST

    # Review patterns
    if any(word in name_lower for word in ["review", "audit", "inspect"]):
        return GovernanceActionType.REVIEW

    # Documentation patterns
    if any(word in name_lower for word in ["document", "write_docs", "generate_docs"]):
        return GovernanceActionType.DOCUMENTATION

    # Refactoring patterns
    if any(word in name_lower for word in ["refactor", "optimize", "improve"]):
        return GovernanceActionType.REFACTORING

    # Bug fix patterns
    if any(word in name_lower for word in ["fix", "repair", "correct", "bugfix"]):
        return GovernanceActionType.BUGFIX

    # Planning patterns
    if any(word in name_lower for word in ["plan", "design", "architect"]):
        return GovernanceActionType.PLANNING

    # Update patterns
    if any(word in name_lower for word in ["update", "modify", "change", "edit"]):
        return GovernanceActionType.UPDATE

    # Default to IMPLEMENTATION
    return GovernanceActionType.IMPLEMENTATION


def _get_function_description(func: Callable) -> str:
    """Get human-readable description from function.

    Args:
        func: Function to describe

    Returns:
        Description string
    """
    # Use function name as base
    name = func.__name__.replace("_", " ").title()

    # Add first line of docstring if available
    if func.__doc__:
        first_line = func.__doc__.strip().split("\n")[0]
        if first_line and len(first_line) < 100:
            return f"{name}: {first_line}"

    return name


# Convenience exports
__all__ = [
    "log_agent_action",
    "agent_operation",
    "async_agent_operation",
    "sanitize_args",
]
