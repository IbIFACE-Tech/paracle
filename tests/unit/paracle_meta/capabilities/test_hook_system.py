"""Unit tests for HookSystemCapability."""

import pytest
from typing import Any

from paracle_meta.capabilities.hook_system import (
    HookSystemCapability,
    HookSystemConfig,
    HookType,
    HookContext,
)


@pytest.fixture
def hook_system():
    """Create HookSystemCapability instance."""
    config = HookSystemConfig()
    return HookSystemCapability(config)


# Test callback functions
call_log = []


async def before_hook(context: HookContext) -> None:
    """Before hook callback."""
    call_log.append(("before", context.operation, context.args))


async def after_hook(context: HookContext) -> None:
    """After hook callback."""
    call_log.append(("after", context.operation, context.result))


async def error_hook(context: HookContext) -> None:
    """Error hook callback."""
    call_log.append(("error", context.operation, context.error))


async def finally_hook(context: HookContext) -> None:
    """Finally hook callback."""
    call_log.append(("finally", context.operation))


async def conditional_hook(context: HookContext) -> None:
    """Conditional hook."""
    call_log.append(("conditional", context.operation))


def should_run_hook(context: HookContext) -> bool:
    """Condition for conditional hook."""
    return context.args.get("run_hook", False) if context.args else False


@pytest.fixture(autouse=True)
def clear_call_log():
    """Clear call log before each test."""
    call_log.clear()
    yield
    call_log.clear()


@pytest.mark.asyncio
async def test_hook_system_initialization(hook_system):
    """Test HookSystemCapability initialization."""
    assert hook_system.name == "hook_system"
    assert len(hook_system._hooks) == 0


@pytest.mark.asyncio
async def test_register_before_hook(hook_system):
    """Test registering a before hook."""
    result = await hook_system.register(
        name="test_before",
        hook_type=HookType.BEFORE,
        operation="test_op",
        callback=before_hook
    )

    assert result.success is True
    assert "hook_name" in result.output
    assert result.output["hook_type"] == HookType.BEFORE


@pytest.mark.asyncio
async def test_register_after_hook(hook_system):
    """Test registering an after hook."""
    result = await hook_system.register(
        name="test_after",
        hook_type=HookType.AFTER,
        operation="test_op",
        callback=after_hook
    )

    assert result.success is True
    assert result.output["hook_type"] == HookType.AFTER


@pytest.mark.asyncio
async def test_register_error_hook(hook_system):
    """Test registering an error hook."""
    result = await hook_system.register(
        name="test_error",
        hook_type=HookType.ERROR,
        operation="test_op",
        callback=error_hook
    )

    assert result.success is True
    assert result.output["hook_type"] == HookType.ERROR


@pytest.mark.asyncio
async def test_register_finally_hook(hook_system):
    """Test registering a finally hook."""
    result = await hook_system.register(
        name="test_finally",
        hook_type=HookType.FINALLY,
        operation="test_op",
        callback=finally_hook
    )

    assert result.success is True
    assert result.output["hook_type"] == HookType.FINALLY


@pytest.mark.asyncio
async def test_execute_with_before_hook(hook_system):
    """Test executing operation with before hook."""
    await hook_system.register(
        name="test_before",
        hook_type=HookType.BEFORE,
        operation="test_op",
        callback=before_hook
    )

    async def test_operation(x: int) -> int:
        return x * 2

    result = await hook_system.execute_with_hooks(
        operation="test_op",
        callback=test_operation,
        args={"x": 5}
    )

    assert result.success is True
    assert result.output["result"] == 10
    assert len(call_log) == 1
    assert call_log[0][0] == "before"
    assert call_log[0][1] == "test_op"


@pytest.mark.asyncio
async def test_execute_with_after_hook(hook_system):
    """Test executing operation with after hook."""
    await hook_system.register(
        name="test_after",
        hook_type=HookType.AFTER,
        operation="test_op",
        callback=after_hook
    )

    async def test_operation(x: int) -> int:
        return x * 2

    result = await hook_system.execute_with_hooks(
        operation="test_op",
        callback=test_operation,
        args={"x": 5}
    )

    assert result.success is True
    assert len(call_log) == 1
    assert call_log[0][0] == "after"
    assert call_log[0][2] == 10  # Result


@pytest.mark.asyncio
async def test_execute_with_error_hook(hook_system):
    """Test executing operation that raises error."""
    await hook_system.register(
        name="test_error",
        hook_type=HookType.ERROR,
        operation="test_op",
        callback=error_hook
    )

    async def failing_operation() -> None:
        raise ValueError("Test error")

    result = await hook_system.execute_with_hooks(
        operation="test_op",
        callback=failing_operation
    )

    assert result.success is False
    assert len(call_log) == 1
    assert call_log[0][0] == "error"
    assert "Test error" in str(call_log[0][2])


@pytest.mark.asyncio
async def test_execute_with_finally_hook(hook_system):
    """Test finally hook is always executed."""
    await hook_system.register(
        name="test_finally",
        hook_type=HookType.FINALLY,
        operation="test_op",
        callback=finally_hook
    )

    async def test_operation() -> str:
        return "success"

    result = await hook_system.execute_with_hooks(
        operation="test_op",
        callback=test_operation
    )

    assert result.success is True
    assert len(call_log) == 1
    assert call_log[0][0] == "finally"


@pytest.mark.asyncio
async def test_finally_hook_on_error(hook_system):
    """Test finally hook executes even on error."""
    await hook_system.register(
        name="test_finally",
        hook_type=HookType.FINALLY,
        operation="test_op",
        callback=finally_hook
    )

    async def failing_operation() -> None:
        raise ValueError("Test error")

    result = await hook_system.execute_with_hooks(
        operation="test_op",
        callback=failing_operation
    )

    assert result.success is False
    assert len(call_log) == 1
    assert call_log[0][0] == "finally"


@pytest.mark.asyncio
async def test_hook_priority_order(hook_system):
    """Test hooks execute in priority order."""
    priority_log = []

    async def high_priority_hook(context: HookContext) -> None:
        priority_log.append("high")

    async def low_priority_hook(context: HookContext) -> None:
        priority_log.append("low")

    # Register with different priorities
    await hook_system.register(
        name="low",
        hook_type=HookType.BEFORE,
        operation="test_op",
        callback=low_priority_hook,
        priority=10
    )

    await hook_system.register(
        name="high",
        hook_type=HookType.BEFORE,
        operation="test_op",
        callback=high_priority_hook,
        priority=90
    )

    async def test_operation() -> str:
        return "done"

    await hook_system.execute_with_hooks(
        operation="test_op",
        callback=test_operation
    )

    # High priority should execute first
    assert priority_log == ["high", "low"]


@pytest.mark.asyncio
async def test_conditional_hook(hook_system):
    """Test hook with condition."""
    await hook_system.register(
        name="conditional",
        hook_type=HookType.BEFORE,
        operation="test_op",
        callback=conditional_hook,
        condition=should_run_hook
    )

    async def test_operation() -> str:
        return "done"

    # Execute without condition being true
    await hook_system.execute_with_hooks(
        operation="test_op",
        callback=test_operation,
        args={"run_hook": False}
    )
    assert len(call_log) == 0

    # Execute with condition being true
    await hook_system.execute_with_hooks(
        operation="test_op",
        callback=test_operation,
        args={"run_hook": True}
    )
    assert len(call_log) == 1


@pytest.mark.asyncio
async def test_wildcard_operation(hook_system):
    """Test wildcard operation matching."""
    await hook_system.register(
        name="wildcard",
        hook_type=HookType.BEFORE,
        operation="test.*",
        callback=before_hook
    )

    async def test_operation() -> str:
        return "done"

    # Should match test.foo
    await hook_system.execute_with_hooks(
        operation="test.foo",
        callback=test_operation
    )
    assert len(call_log) == 1

    call_log.clear()

    # Should match test.bar
    await hook_system.execute_with_hooks(
        operation="test.bar",
        callback=test_operation
    )
    assert len(call_log) == 1


@pytest.mark.asyncio
async def test_unregister_hook(hook_system):
    """Test unregistering a hook."""
    # Register hook
    await hook_system.register(
        name="test_hook",
        hook_type=HookType.BEFORE,
        operation="test_op",
        callback=before_hook
    )

    # Unregister
    result = await hook_system.unregister(name="test_hook")
    assert result.success is True

    # Hook should not execute
    async def test_operation() -> str:
        return "done"

    await hook_system.execute_with_hooks(
        operation="test_op",
        callback=test_operation
    )
    assert len(call_log) == 0


@pytest.mark.asyncio
async def test_list_hooks(hook_system):
    """Test listing registered hooks."""
    # Register multiple hooks
    await hook_system.register(
        name="hook1",
        hook_type=HookType.BEFORE,
        operation="test_op",
        callback=before_hook
    )

    await hook_system.register(
        name="hook2",
        hook_type=HookType.AFTER,
        operation="test_op",
        callback=after_hook
    )

    result = await hook_system.list_hooks(operation="test_op")
    assert result.success is True
    assert len(result.output["hooks"]) == 2


@pytest.mark.asyncio
async def test_multiple_hooks_same_type(hook_system):
    """Test multiple hooks of same type execute."""
    hook_count = []

    async def hook1(context: HookContext) -> None:
        hook_count.append(1)

    async def hook2(context: HookContext) -> None:
        hook_count.append(2)

    await hook_system.register(
        name="hook1",
        hook_type=HookType.BEFORE,
        operation="test_op",
        callback=hook1
    )

    await hook_system.register(
        name="hook2",
        hook_type=HookType.BEFORE,
        operation="test_op",
        callback=hook2
    )

    async def test_operation() -> str:
        return "done"

    await hook_system.execute_with_hooks(
        operation="test_op",
        callback=test_operation
    )

    assert len(hook_count) == 2


@pytest.mark.asyncio
async def test_all_hook_types_together(hook_system):
    """Test all hook types execute in correct order."""
    execution_order = []

    async def before_test(context: HookContext) -> None:
        execution_order.append("before")

    async def after_test(context: HookContext) -> None:
        execution_order.append("after")

    async def finally_test(context: HookContext) -> None:
        execution_order.append("finally")

    await hook_system.register(
        name="before", hook_type=HookType.BEFORE,
        operation="test_op", callback=before_test
    )
    await hook_system.register(
        name="after", hook_type=HookType.AFTER,
        operation="test_op", callback=after_test
    )
    await hook_system.register(
        name="finally", hook_type=HookType.FINALLY,
        operation="test_op", callback=finally_test
    )

    async def test_operation() -> str:
        execution_order.append("operation")
        return "done"

    await hook_system.execute_with_hooks(
        operation="test_op",
        callback=test_operation
    )

    assert execution_order == ["before", "operation", "after", "finally"]
