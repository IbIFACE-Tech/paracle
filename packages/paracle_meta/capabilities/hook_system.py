"""Hook system capability for MetaAgent.

Provides pre/post operation hooks for extensibility:
- Before/after operation hooks
- Async hook execution
- Hook chaining
- Conditional hooks
- Error handling hooks
- Performance monitoring hooks

Inspired by middleware patterns and lifecycle hooks.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class HookType(str, Enum):
    """Type of hook."""

    BEFORE = "before"  # Before operation
    AFTER = "after"  # After successful operation
    ERROR = "error"  # On error
    FINALLY = "finally"  # Always execute


class HookPriority(int, Enum):
    """Hook execution priority."""

    HIGHEST = 0
    HIGH = 10
    NORMAL = 50
    LOW = 90
    LOWEST = 100


@dataclass
class HookContext:
    """Context passed to hooks."""

    operation: str
    args: dict[str, Any]
    result: Any | None = None
    error: Exception | None = None
    start_time: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "args": self.args,
            "result": self.result,
            "error": str(self.error) if self.error else None,
            "elapsed_ms": (time.time() - self.start_time) * 1000,
            "metadata": self.metadata,
        }


@dataclass
class Hook:
    """A registered hook."""

    id: str
    name: str
    hook_type: HookType
    operation: str  # Operation pattern (supports wildcards)
    callback: Callable[[HookContext], Coroutine[Any, Any, None]]
    priority: HookPriority = HookPriority.NORMAL
    enabled: bool = True
    condition: Callable[[HookContext], bool] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_count: int = 0
    last_executed: datetime | None = None
    total_duration_ms: float = 0.0

    def matches_operation(self, operation: str) -> bool:
        """Check if hook matches operation.

        Args:
            operation: Operation name

        Returns:
            True if hook should be triggered
        """
        # Support wildcards
        if self.operation == "*":
            return True

        if self.operation.endswith("*"):
            prefix = self.operation[:-1]
            return operation.startswith(prefix)

        return self.operation == operation

    def should_execute(self, context: HookContext) -> bool:
        """Check if hook should execute.

        Args:
            context: Hook context

        Returns:
            True if hook should execute
        """
        if not self.enabled:
            return False

        if not self.matches_operation(context.operation):
            return False

        if self.condition and not self.condition(context):
            return False

        return True


class HookSystemConfig(CapabilityConfig):
    """Configuration for hook system capability."""

    max_hooks: int = Field(
        default=1000,
        description="Maximum hooks to register",
    )
    hook_timeout: float = Field(
        default=5.0,
        description="Default hook timeout in seconds",
    )
    stop_on_error: bool = Field(
        default=False,
        description="Stop hook chain on first error",
    )
    enable_metrics: bool = Field(
        default=True,
        description="Track hook performance metrics",
    )


class HookSystemCapability(BaseCapability):
    """Hook system for operation lifecycle management.

    Provides extensibility through pre/post operation hooks:
    - Before hooks: Execute before operation starts
    - After hooks: Execute after successful operation
    - Error hooks: Execute on operation failure
    - Finally hooks: Always execute regardless of outcome

    Example:
        >>> hooks = HookSystemCapability()
        >>> await hooks.initialize()

        >>> # Define a logging hook
        >>> async def log_operation(ctx: HookContext):
        ...     print(f"Operation: {ctx.operation}, Args: {ctx.args}")

        >>> # Register before hook
        >>> await hooks.register(
        ...     name="logger",
        ...     hook_type="before",
        ...     operation="*",  # All operations
        ...     callback=log_operation
        ... )

        >>> # Execute operation with hooks
        >>> result = await hooks.execute_with_hooks(
        ...     operation="compute",
        ...     callback=lambda ctx: {"sum": ctx.args["a"] + ctx.args["b"]},
        ...     args={"a": 5, "b": 3}
        ... )

        >>> # Register conditional hook
        >>> await hooks.register(
        ...     name="error_notifier",
        ...     hook_type="error",
        ...     operation="*",
        ...     callback=send_error_notification,
        ...     condition=lambda ctx: ctx.error is not None
        ... )
    """

    name = "hook_system"
    description = "Pre/post operation hooks for extensibility"

    def __init__(self, config: HookSystemConfig | None = None):
        """Initialize hook system capability."""
        super().__init__(config or HookSystemConfig())
        self.config: HookSystemConfig = self.config
        self._hooks: dict[str, Hook] = {}
        self._hook_counter = 0

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute hook system operation.

        Args:
            action: Operation (register, unregister, list, clear, execute_with_hooks)
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "list")
        start_time = time.time()

        try:
            if action == "register":
                result = await self._register_hook(**kwargs)
            elif action == "unregister":
                result = self._unregister_hook(**kwargs)
            elif action == "enable":
                result = self._enable_hook(**kwargs)
            elif action == "disable":
                result = self._disable_hook(**kwargs)
            elif action == "list":
                result = self._list_hooks(**kwargs)
            elif action == "clear":
                result = self._clear_hooks(**kwargs)
            elif action == "execute_with_hooks":
                result = await self._execute_with_hooks(**kwargs)
            elif action == "stats":
                result = self._get_stats(**kwargs)
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result,
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    async def _register_hook(
        self,
        name: str,
        hook_type: str,
        operation: str,
        callback: Callable[[HookContext], Coroutine[Any, Any, None]],
        priority: int = HookPriority.NORMAL,
        condition: Callable[[HookContext], bool] | None = None,
        metadata: dict | None = None,
        **extra,
    ) -> dict[str, Any]:
        """Register a new hook.

        Args:
            name: Hook name
            hook_type: Hook type (before, after, error, finally)
            operation: Operation pattern (supports wildcards: "compute", "compute*", "*")
            callback: Async function to call
            priority: Execution priority (0=highest, 100=lowest)
            condition: Optional condition function
            metadata: Additional metadata

        Returns:
            Hook registration info
        """
        if len(self._hooks) >= self.config.max_hooks:
            raise ValueError(f"Maximum hooks limit reached: {self.config.max_hooks}")

        hook_type_enum = HookType(hook_type)

        # Generate ID
        self._hook_counter += 1
        hook_id = f"hook-{self._hook_counter}"

        hook = Hook(
            id=hook_id,
            name=name,
            hook_type=hook_type_enum,
            operation=operation,
            callback=callback,
            priority=HookPriority(priority) if isinstance(priority, int) else priority,
            condition=condition,
            metadata=metadata or {},
        )

        self._hooks[hook_id] = hook

        return {
            "hook_id": hook_id,
            "name": name,
            "hook_type": hook_type,
            "operation": operation,
            "priority": priority,
        }

    def _unregister_hook(self, hook_id: str, **kwargs) -> dict[str, Any]:
        """Unregister a hook.

        Args:
            hook_id: Hook ID to remove

        Returns:
            Unregistration result
        """
        if hook_id not in self._hooks:
            raise ValueError(f"Hook not found: {hook_id}")

        hook = self._hooks.pop(hook_id)

        return {
            "hook_id": hook_id,
            "name": hook.name,
            "removed": True,
        }

    def _enable_hook(self, hook_id: str, **kwargs) -> dict[str, Any]:
        """Enable a hook.

        Args:
            hook_id: Hook ID

        Returns:
            Enable result
        """
        if hook_id not in self._hooks:
            raise ValueError(f"Hook not found: {hook_id}")

        self._hooks[hook_id].enabled = True

        return {
            "hook_id": hook_id,
            "enabled": True,
        }

    def _disable_hook(self, hook_id: str, **kwargs) -> dict[str, Any]:
        """Disable a hook.

        Args:
            hook_id: Hook ID

        Returns:
            Disable result
        """
        if hook_id not in self._hooks:
            raise ValueError(f"Hook not found: {hook_id}")

        self._hooks[hook_id].enabled = False

        return {
            "hook_id": hook_id,
            "enabled": False,
        }

    def _list_hooks(
        self,
        hook_type: str | None = None,
        operation: str | None = None,
        enabled: bool | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """List registered hooks.

        Args:
            hook_type: Filter by hook type
            operation: Filter by operation
            enabled: Filter by enabled status

        Returns:
            Hooks list
        """
        hooks = list(self._hooks.values())

        # Apply filters
        if hook_type:
            hook_type_enum = HookType(hook_type)
            hooks = [h for h in hooks if h.hook_type == hook_type_enum]

        if operation:
            hooks = [h for h in hooks if h.matches_operation(operation)]

        if enabled is not None:
            hooks = [h for h in hooks if h.enabled == enabled]

        # Sort by priority
        hooks.sort(key=lambda h: h.priority.value)

        return {
            "hooks": [
                {
                    "id": h.id,
                    "name": h.name,
                    "hook_type": h.hook_type.value,
                    "operation": h.operation,
                    "priority": h.priority.value,
                    "enabled": h.enabled,
                    "execution_count": h.execution_count,
                    "avg_duration_ms": (
                        h.total_duration_ms / h.execution_count
                        if h.execution_count > 0
                        else 0
                    ),
                }
                for h in hooks
            ],
            "count": len(hooks),
        }

    def _clear_hooks(
        self,
        hook_type: str | None = None,
        operation: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Clear hooks.

        Args:
            hook_type: Clear only hooks of this type
            operation: Clear only hooks for this operation

        Returns:
            Clear result
        """
        if hook_type is None and operation is None:
            # Clear all
            count = len(self._hooks)
            self._hooks.clear()
        else:
            # Selective clear
            to_remove = []
            for hook_id, hook in self._hooks.items():
                if hook_type and hook.hook_type.value != hook_type:
                    continue
                if operation and not hook.matches_operation(operation):
                    continue
                to_remove.append(hook_id)

            for hook_id in to_remove:
                del self._hooks[hook_id]

            count = len(to_remove)

        return {
            "cleared": True,
            "count": count,
        }

    async def _execute_with_hooks(
        self,
        operation: str,
        callback: Callable[[HookContext], Coroutine[Any, Any, Any]],
        args: dict | None = None,
        **extra,
    ) -> dict[str, Any]:
        """Execute operation with hooks.

        Args:
            operation: Operation name
            callback: Async function to execute
            args: Arguments for callback

        Returns:
            Operation result with hook execution info
        """
        args = args or {}
        context = HookContext(operation=operation, args=args)

        hook_results = {
            "before": [],
            "after": [],
            "error": [],
            "finally": [],
        }

        try:
            # Execute BEFORE hooks
            await self._execute_hooks(HookType.BEFORE, context, hook_results)

            # Execute main operation
            context.result = await callback(context)

            # Execute AFTER hooks
            await self._execute_hooks(HookType.AFTER, context, hook_results)

        except Exception as e:
            context.error = e

            # Execute ERROR hooks
            await self._execute_hooks(HookType.ERROR, context, hook_results)

            # Re-raise if no error hook handled it
            raise

        finally:
            # Execute FINALLY hooks
            await self._execute_hooks(HookType.FINALLY, context, hook_results)

        return {
            "operation": operation,
            "result": context.result,
            "hooks_executed": sum(len(v) for v in hook_results.values()),
            "hook_results": hook_results,
            "elapsed_ms": (time.time() - context.start_time) * 1000,
        }

    async def _execute_hooks(
        self,
        hook_type: HookType,
        context: HookContext,
        results: dict[str, list],
    ) -> None:
        """Execute all hooks of a given type.

        Args:
            hook_type: Type of hooks to execute
            context: Hook context
            results: Results accumulator
        """
        # Get matching hooks
        hooks = [
            h
            for h in self._hooks.values()
            if h.hook_type == hook_type and h.should_execute(context)
        ]

        # Sort by priority
        hooks.sort(key=lambda h: h.priority.value)

        # Execute hooks
        for hook in hooks:
            try:
                hook_start = time.time()

                # Execute with timeout
                await asyncio.wait_for(
                    hook.callback(context),
                    timeout=self.config.hook_timeout,
                )

                # Update metrics
                if self.config.enable_metrics:
                    hook.execution_count += 1
                    hook.last_executed = datetime.utcnow()
                    duration_ms = (time.time() - hook_start) * 1000
                    hook.total_duration_ms += duration_ms

                results[hook_type.value].append(
                    {
                        "hook_id": hook.id,
                        "hook_name": hook.name,
                        "success": True,
                        "duration_ms": (
                            duration_ms if self.config.enable_metrics else None
                        ),
                    }
                )

            except asyncio.TimeoutError:
                results[hook_type.value].append(
                    {
                        "hook_id": hook.id,
                        "hook_name": hook.name,
                        "success": False,
                        "error": f"Timeout after {self.config.hook_timeout}s",
                    }
                )
                if self.config.stop_on_error:
                    break

            except Exception as e:
                results[hook_type.value].append(
                    {
                        "hook_id": hook.id,
                        "hook_name": hook.name,
                        "success": False,
                        "error": str(e),
                    }
                )
                if self.config.stop_on_error:
                    break

    def _get_stats(self, **kwargs) -> dict[str, Any]:
        """Get hook system statistics.

        Returns:
            Statistics
        """
        total_hooks = len(self._hooks)
        enabled_hooks = len([h for h in self._hooks.values() if h.enabled])

        # Group by type
        by_type = {}
        for hook in self._hooks.values():
            hook_type = hook.hook_type.value
            if hook_type not in by_type:
                by_type[hook_type] = 0
            by_type[hook_type] += 1

        # Most executed
        most_executed = sorted(
            self._hooks.values(),
            key=lambda h: h.execution_count,
            reverse=True,
        )[:5]

        # Slowest hooks
        slowest = sorted(
            [h for h in self._hooks.values() if h.execution_count > 0],
            key=lambda h: h.total_duration_ms / h.execution_count,
            reverse=True,
        )[:5]

        return {
            "total_hooks": total_hooks,
            "enabled_hooks": enabled_hooks,
            "disabled_hooks": total_hooks - enabled_hooks,
            "by_type": by_type,
            "most_executed": [
                {
                    "id": h.id,
                    "name": h.name,
                    "execution_count": h.execution_count,
                }
                for h in most_executed
            ],
            "slowest_hooks": [
                {
                    "id": h.id,
                    "name": h.name,
                    "avg_duration_ms": h.total_duration_ms / h.execution_count,
                }
                for h in slowest
            ],
        }

    # Convenience methods
    async def register(
        self,
        name: str,
        hook_type: str,
        operation: str,
        callback: Callable[[HookContext], Coroutine[Any, Any, None]],
        **kwargs,
    ) -> CapabilityResult:
        """Register a hook."""
        return await self.execute(
            action="register",
            name=name,
            hook_type=hook_type,
            operation=operation,
            callback=callback,
            **kwargs,
        )

    async def unregister(self, hook_id: str) -> CapabilityResult:
        """Unregister a hook."""
        return await self.execute(action="unregister", hook_id=hook_id)

    async def execute_with_hooks(
        self,
        operation: str,
        callback: Callable[[HookContext], Coroutine[Any, Any, Any]],
        args: dict | None = None,
    ) -> CapabilityResult:
        """Execute operation with hooks."""
        return await self.execute(
            action="execute_with_hooks",
            operation=operation,
            callback=callback,
            args=args,
        )

    async def list_hooks(self, **kwargs) -> CapabilityResult:
        """List registered hooks."""
        return await self.execute(action="list", **kwargs)

    async def get_stats(self) -> CapabilityResult:
        """Get hook system statistics."""
        return await self.execute(action="stats")
