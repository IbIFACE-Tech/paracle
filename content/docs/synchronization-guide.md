# Synchronization Guide

Patterns for synchronous and asynchronous operations in Paracle.

## Overview

Paracle uses async-first design for I/O-bound operations while providing synchronous wrappers for CLI and simple use cases.

## Async Architecture

### Core Pattern

```python
# Async by default for I/O operations
async def execute_agent(agent_id: str, task: str) -> AgentResult:
    agent = await agent_repository.get(agent_id)
    result = await llm_provider.complete(messages)
    await event_bus.publish(AgentExecutedEvent(...))
    return result
```

### Event Loop Management

```python
import asyncio

# In CLI context
def run_agent_sync(agent_id: str, task: str) -> AgentResult:
    """Synchronous wrapper for CLI usage."""
    return asyncio.run(execute_agent(agent_id, task))

# In API context (already async)
@app.post("/agents/{agent_id}/run")
async def run_agent_endpoint(agent_id: str, request: RunRequest):
    return await execute_agent(agent_id, request.task)
```

## Sync/Async Patterns

### 1. Repository Pattern

```python
from abc import ABC, abstractmethod

class AgentRepository(ABC):
    """Abstract repository interface."""

    @abstractmethod
    async def get(self, agent_id: str) -> Agent | None:
        pass

    @abstractmethod
    async def save(self, agent: Agent) -> None:
        pass

    @abstractmethod
    async def delete(self, agent_id: str) -> None:
        pass


class AsyncSQLiteRepository(AgentRepository):
    """Async SQLite implementation."""

    async def get(self, agent_id: str) -> Agent | None:
        async with self.session() as session:
            result = await session.execute(
                select(AgentModel).where(AgentModel.id == agent_id)
            )
            return result.scalar_one_or_none()
```

### 2. Provider Pattern

```python
class LLMProvider(Protocol):
    """LLM provider interface."""

    async def complete(
        self,
        messages: list[Message],
        model: str,
        temperature: float
    ) -> CompletionResult:
        ...

    async def stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float
    ) -> AsyncIterator[StreamChunk]:
        ...


class AnthropicProvider:
    """Anthropic Claude provider."""

    async def complete(self, messages, model, temperature):
        response = await self.client.messages.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return CompletionResult(content=response.content)

    async def stream(self, messages, model, temperature):
        async with self.client.messages.stream(
            model=model,
            messages=messages,
            temperature=temperature,
        ) as stream:
            async for chunk in stream:
                yield StreamChunk(content=chunk.delta.text)
```

### 3. Event Bus Pattern

```python
class EventBus:
    """Async event bus for domain events."""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(event.event_type, [])
        await asyncio.gather(*(h(event) for h in handlers))
```

## Concurrency Patterns

### 1. Parallel Agent Execution

```python
async def run_agent_group(agents: list[str], task: str) -> list[AgentResult]:
    """Run multiple agents concurrently."""
    tasks = [execute_agent(agent_id, task) for agent_id in agents]
    return await asyncio.gather(*tasks)
```

### 2. Workflow Step Parallelization

```python
async def execute_workflow(workflow: Workflow) -> WorkflowResult:
    """Execute workflow with parallel steps where possible."""
    completed = {}

    for step in workflow.topological_order():
        # Check dependencies
        deps_ready = all(d in completed for d in step.depends_on)

        if deps_ready:
            # Find parallel steps
            parallel_steps = workflow.get_parallel_steps(step)
            results = await asyncio.gather(
                *(execute_step(s, completed) for s in parallel_steps)
            )
            for s, r in zip(parallel_steps, results):
                completed[s.name] = r

    return WorkflowResult(steps=completed)
```

### 3. Streaming with Backpressure

```python
async def stream_agent_response(
    agent_id: str,
    task: str
) -> AsyncIterator[str]:
    """Stream response with backpressure control."""
    agent = await agent_repository.get(agent_id)
    provider = get_provider(agent.model)

    async for chunk in provider.stream(
        messages=[{"role": "user", "content": task}],
        model=agent.model,
        temperature=agent.temperature,
    ):
        yield chunk.content
        # Allow other tasks to run
        await asyncio.sleep(0)
```

## Connection Pooling

### Database Connections

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=20,           # Base pool size
    max_overflow=10,        # Additional connections
    pool_pre_ping=True,     # Verify connections
    pool_recycle=3600,      # Recycle after 1 hour
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session
```

### HTTP Client Pooling

```python
import httpx

class HTTPClientPool:
    """Pooled HTTP client for external APIs."""

    def __init__(self, max_connections: int = 100):
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=20,
        )
        self.client = httpx.AsyncClient(limits=limits)

    async def get(self, url: str) -> httpx.Response:
        return await self.client.get(url)

    async def close(self):
        await self.client.aclose()
```

## Rate Limiting

### Provider Rate Limits

```python
from asyncio import Semaphore
from datetime import datetime, timedelta

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate: int, period: timedelta):
        self.rate = rate
        self.period = period
        self.tokens = rate
        self.last_update = datetime.now()
        self.semaphore = Semaphore(rate)

    async def acquire(self) -> None:
        async with self.semaphore:
            now = datetime.now()
            elapsed = now - self.last_update

            # Refill tokens
            refill = int(elapsed / self.period * self.rate)
            self.tokens = min(self.rate, self.tokens + refill)
            self.last_update = now

            if self.tokens <= 0:
                # Wait for token
                await asyncio.sleep(self.period.total_seconds())
                self.tokens = 1

            self.tokens -= 1
```

### Usage

```python
# Create limiter for 100 requests per minute
limiter = RateLimiter(rate=100, period=timedelta(minutes=1))

async def call_api():
    await limiter.acquire()
    return await http_client.get(url)
```

## Timeout Handling

### Operation Timeouts

```python
async def execute_with_timeout(
    coro: Coroutine,
    timeout: float = 30.0
) -> Any:
    """Execute coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise OperationTimeoutError(
            f"Operation timed out after {timeout} seconds"
        )
```

### Graceful Cancellation

```python
async def cancellable_operation(task: str) -> str:
    """Operation that handles cancellation gracefully."""
    try:
        result = await long_running_operation(task)
        return result
    except asyncio.CancelledError:
        # Cleanup before propagating
        await cleanup_resources()
        raise
```

## Error Handling

### Retry with Backoff

```python
from paracle_resilience import retry_with_backoff, RetryConfig

config = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
)

async def reliable_api_call():
    return await retry_with_backoff(
        api_call,
        config=config,
        retryable_exceptions=(httpx.TimeoutException, httpx.NetworkError),
    )
```

### Circuit Breaker

```python
from paracle_resilience import CircuitBreaker

circuit = CircuitBreaker(
    failure_threshold=5,
    reset_timeout=60.0,
)

async def protected_call():
    async with circuit:
        return await external_api_call()
```

## Best Practices

### 1. Always Use Async for I/O

```python
# Good
async def fetch_data():
    return await http_client.get(url)

# Avoid blocking I/O in async context
def fetch_data_bad():
    return requests.get(url)  # Blocks event loop!
```

### 2. Use Structured Concurrency

```python
# Good - all tasks complete or cancel together
async with asyncio.TaskGroup() as tg:
    task1 = tg.create_task(operation1())
    task2 = tg.create_task(operation2())

# Results are available after the block
result1 = task1.result()
result2 = task2.result()
```

### 3. Handle Cancellation

```python
async def operation():
    try:
        await long_task()
    except asyncio.CancelledError:
        await cleanup()
        raise  # Always re-raise
```

### 4. Limit Concurrency

```python
# Limit concurrent operations
semaphore = asyncio.Semaphore(10)

async def limited_operation():
    async with semaphore:
        return await heavy_operation()

# Run many but limited concurrently
results = await asyncio.gather(
    *(limited_operation() for _ in range(100))
)
```

## CLI Synchronization

### Sync Wrappers

```python
import click
import asyncio

@click.command()
@click.argument("agent_id")
@click.option("--task", "-t", required=True)
def run_agent(agent_id: str, task: str):
    """Run agent synchronously from CLI."""
    result = asyncio.run(execute_agent(agent_id, task))
    click.echo(result)
```

### Streaming in CLI

```python
@click.command()
def stream_agent(agent_id: str, task: str):
    """Stream agent output to CLI."""
    async def _stream():
        async for chunk in stream_agent_response(agent_id, task):
            click.echo(chunk, nl=False)

    asyncio.run(_stream())
```

## Related Documentation

- [Architecture Overview](architecture.md) - System design
- [API-First CLI](api-first-cli.md) - CLI patterns
- [Built-in Tools](builtin-tools.md) - Tool implementations
