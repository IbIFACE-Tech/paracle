"""
Example 20: Plugin Development

Demonstrates how to create custom plugins for Paracle:
- Provider Plugin: Custom LLM provider (Ollama)
- Tool Plugin: Custom tool (Database query)
- Observer Plugin: Monitoring (Metrics collector)

Requirements:
    pip install httpx sqlite3
    ollama serve  # If testing Ollama provider
"""

import asyncio
import logging
import sqlite3
from pathlib import Path

import httpx
from paracle_plugins import (
    ObserverPlugin,
    PluginCapability,
    PluginMetadata,
    PluginType,
    ProviderPlugin,
    ToolPlugin,
    get_plugin_registry,
)
from paracle_plugins.observer_plugin import ExecutionEvent
from paracle_plugins.provider_plugin import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message,
)
from paracle_plugins.tool_plugin import ToolExecutionContext, ToolParameter, ToolSchema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# 1. PROVIDER PLUGIN: Ollama Local LLM
# =============================================================================

class OllamaProvider(ProviderPlugin):
    """Ollama local LLM provider plugin.

    Enables using locally hosted Ollama models with Paracle.
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="ollama-provider",
            version="1.0.0",
            description="Ollama local LLM provider for Paracle",
            author="Community Example",
            homepage="https://github.com/community/paracle-ollama",
            license="MIT",
            plugin_type=PluginType.PROVIDER,
            capabilities=[
                PluginCapability.CHAT_COMPLETION,
                PluginCapability.STREAMING
            ],
            dependencies=["httpx>=0.24.0"],
            paracle_version=">=0.2.0",
            config_schema={
                "type": "object",
                "properties": {
                    "base_url": {
                        "type": "string",
                        "default": "http://localhost:11434"
                    },
                    "default_model": {
                        "type": "string",
                        "default": "llama2"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": 60
                    }
                },
                "required": ["base_url"]
            },
            tags=["llm", "local", "ollama", "provider"]
        )

    async def initialize(self, config: dict) -> None:
        """Initialize Ollama provider."""
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.default_model = config.get("default_model", "llama2")
        self.timeout = config.get("timeout", 60)

        self.client = httpx.AsyncClient(timeout=self.timeout)

        logger.info(
            f"Initialized Ollama provider: {self.base_url} "
            f"(model: {self.default_model})"
        )

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if hasattr(self, 'client'):
            await self.client.aclose()
        logger.info("Ollama provider cleaned up")

    def validate_config(self, config: dict) -> bool:
        """Validate configuration."""
        if "base_url" not in config:
            raise ValueError("base_url is required")
        return True

    async def health_check(self) -> dict:
        """Check Ollama server health."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])

            return {
                "status": "healthy",
                "details": {
                    "connected": True,
                    "models_available": len(models),
                    "base_url": self.base_url
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Execute chat completion."""
        model = request.model or self.default_model

        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": m.role, "content": m.content}
                    for m in request.messages
                ],
                "stream": False,
                "options": {
                    "temperature": request.temperature or 0.7,
                    "num_predict": request.max_tokens or 1000
                }
            }
        )
        response.raise_for_status()
        data = response.json()

        return ChatCompletionResponse(
            id=f"ollama-{model}-{hash(data['message']['content'])}",
            model=model,
            content=data["message"]["content"],
            role=data["message"]["role"],
            finish_reason="stop",
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("total_duration", 0)
            }
        )

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ):
        """Execute streaming chat completion."""
        model = request.model or self.default_model

        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": m.role, "content": m.content}
                    for m in request.messages
                ],
                "stream": True
            }
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    yield line

    async def list_models(self) -> list[str]:
        """List available Ollama models."""
        response = await self.client.get(f"{self.base_url}/api/tags")
        response.raise_for_status()
        data = response.json()
        return [model["name"] for model in data.get("models", [])]

    async def get_model_info(self, model_name: str) -> dict:
        """Get detailed model information."""
        response = await self.client.post(
            f"{self.base_url}/api/show",
            json={"name": model_name}
        )
        response.raise_for_status()
        return response.json()


# =============================================================================
# 2. TOOL PLUGIN: Database Query Tool
# =============================================================================

class DatabaseTool(ToolPlugin):
    """SQL database query tool plugin.

    Enables agents to query SQLite databases.
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="database-tool",
            version="1.0.0",
            description="Execute SQL queries on SQLite databases",
            author="Community Example",
            plugin_type=PluginType.TOOL,
            capabilities=[PluginCapability.DATABASE_ACCESS],
            paracle_version=">=0.2.0",
            config_schema={
                "type": "object",
                "properties": {
                    "database_path": {
                        "type": "string",
                        "description": "Path to SQLite database"
                    },
                    "read_only": {
                        "type": "boolean",
                        "default": True,
                        "description": "Allow only SELECT queries"
                    },
                    "max_rows": {
                        "type": "integer",
                        "default": 100
                    }
                },
                "required": ["database_path"]
            },
            tags=["database", "sql", "sqlite", "tool"]
        )

    async def initialize(self, config: dict) -> None:
        """Initialize database tool."""
        self.db_path = config["database_path"]
        self.read_only = config.get("read_only", True)
        self.max_rows = config.get("max_rows", 100)

        # Verify database exists
        if not Path(self.db_path).exists():
            raise FileNotFoundError(
                f"Database not found: {self.db_path}"
            )

        logger.info(
            f"Initialized database tool: {self.db_path} "
            f"(read_only={self.read_only})"
        )

    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Database tool cleaned up")

    def validate_config(self, config: dict) -> bool:
        """Validate configuration."""
        if "database_path" not in config:
            raise ValueError("database_path is required")
        return True

    async def health_check(self) -> dict:
        """Check database accessibility."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()

            return {
                "status": "healthy",
                "details": {
                    "database": self.db_path,
                    "accessible": True
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def get_tool_schema(self) -> ToolSchema:
        """Define tool schema for agents."""
        return ToolSchema(
            name="database_query",
            description=(
                "Execute SQL query on database. "
                "Returns columns and rows."
            ),
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="SQL query to execute",
                    required=True
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="Maximum rows to return",
                    required=False,
                    default=100
                )
            ]
        )

    async def execute(
        self, context: ToolExecutionContext, **kwargs
    ) -> dict:
        """Execute database query."""
        query = kwargs["query"]
        limit = min(kwargs.get("limit", self.max_rows), self.max_rows)

        # Validate read-only constraint
        if self.read_only:
            query_upper = query.strip().upper()
            if not query_upper.startswith("SELECT"):
                raise ValueError(
                    "Only SELECT queries allowed in read-only mode"
                )

        # Execute query
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query)

            # Fetch results
            rows = cursor.fetchmany(limit)
            columns = [desc[0] for desc in cursor.description]

            conn.close()

            return {
                "success": True,
                "columns": columns,
                "rows": [list(row) for row in rows],
                "row_count": len(rows),
                "truncated": len(rows) == limit
            }

        except sqlite3.Error as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }


# =============================================================================
# 3. OBSERVER PLUGIN: Simple Metrics Collector
# =============================================================================

class MetricsCollector(ObserverPlugin):
    """Simple metrics collection observer plugin.

    Tracks execution metrics in memory.
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="metrics-collector",
            version="1.0.0",
            description="Collect execution metrics and statistics",
            author="Community Example",
            plugin_type=PluginType.OBSERVER,
            capabilities=[PluginCapability.METRICS_COLLECTION],
            paracle_version=">=0.2.0",
            config_schema={
                "type": "object",
                "properties": {
                    "track_costs": {
                        "type": "boolean",
                        "default": True
                    }
                }
            },
            tags=["metrics", "monitoring", "observer"]
        )

    async def initialize(self, config: dict) -> None:
        """Initialize metrics collector."""
        self.track_costs = config.get("track_costs", True)

        # Metrics storage
        self.executions = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "by_agent": {}
        }
        self.llm_calls = {
            "total": 0,
            "by_provider": {},
            "by_model": {}
        }

        logger.info("Initialized metrics collector")

    async def cleanup(self) -> None:
        """Cleanup and report final metrics."""
        logger.info("Metrics Summary:")
        logger.info(f"  Executions: {self.executions}")
        logger.info(f"  LLM Calls: {self.llm_calls}")

    async def health_check(self) -> dict:
        """Return current metrics."""
        return {
            "status": "healthy",
            "details": {
                "executions": self.executions,
                "llm_calls": self.llm_calls
            }
        }

    async def on_execution_started(self, event: ExecutionEvent) -> None:
        """Track execution start."""
        self.executions["total"] += 1

        agent_id = event.agent_id or "unknown"
        if agent_id not in self.executions["by_agent"]:
            self.executions["by_agent"][agent_id] = {
                "total": 0,
                "successful": 0,
                "failed": 0
            }
        self.executions["by_agent"][agent_id]["total"] += 1

        logger.info(
            f"Execution started: {event.execution_id} "
            f"(agent: {agent_id})"
        )

    async def on_execution_completed(
        self, event: ExecutionEvent
    ) -> None:
        """Track successful execution."""
        self.executions["successful"] += 1

        agent_id = event.agent_id or "unknown"
        if agent_id in self.executions["by_agent"]:
            self.executions["by_agent"][agent_id]["successful"] += 1

        logger.info(f"Execution completed: {event.execution_id}")

    async def on_execution_failed(
        self, event: ExecutionEvent, error: Exception
    ) -> None:
        """Track failed execution."""
        self.executions["failed"] += 1

        agent_id = event.agent_id or "unknown"
        if agent_id in self.executions["by_agent"]:
            self.executions["by_agent"][agent_id]["failed"] += 1

        logger.error(
            f"Execution failed: {event.execution_id} - {error}"
        )

    async def on_llm_call(
        self, event: ExecutionEvent, provider: str, model: str
    ) -> None:
        """Track LLM call."""
        self.llm_calls["total"] += 1

        # Track by provider
        if provider not in self.llm_calls["by_provider"]:
            self.llm_calls["by_provider"][provider] = 0
        self.llm_calls["by_provider"][provider] += 1

        # Track by model
        model_key = f"{provider}/{model}"
        if model_key not in self.llm_calls["by_model"]:
            self.llm_calls["by_model"][model_key] = 0
        self.llm_calls["by_model"][model_key] += 1

        logger.debug(f"LLM call: {provider}/{model}")


# =============================================================================
# MAIN: Plugin Usage Examples
# =============================================================================

async def example_ollama_provider():
    """Example: Using Ollama provider plugin."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Ollama Provider Plugin")
    print("=" * 60)

    # Create and register plugin
    ollama = OllamaProvider()
    await ollama.initialize({
        "base_url": "http://localhost:11434",
        "default_model": "llama2"
    })

    registry = get_plugin_registry()
    registry.register("ollama-provider", ollama, {})

    # Check health
    health = await ollama.health_check()
    print(f"\nHealth: {health['status']}")
    if health["status"] == "healthy":
        print(f"Models available: {health['details']['models_available']}")

        # List models
        models = await ollama.list_models()
        print(f"Models: {models[:3]}...")  # Show first 3

        # Test chat completion
        request = ChatCompletionRequest(
            model="llama2",
            messages=[
                Message(role="user", content="Say hello in 5 words")
            ],
            temperature=0.7
        )

        response = await ollama.chat_completion(request)
        print(f"\nResponse: {response.content}")
        print(f"Tokens: {response.usage}")

    await ollama.cleanup()
    print("\n✓ Ollama provider example complete")


async def example_database_tool():
    """Example: Using database tool plugin."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Database Tool Plugin")
    print("=" * 60)

    # Create test database
    db_path = "test_plugin.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT
        )
    """)
    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES (1, 'Alice', 'alice@example.com')"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES (2, 'Bob', 'bob@example.com')"
    )
    conn.commit()
    conn.close()

    # Create and register plugin
    db_tool = DatabaseTool()
    await db_tool.initialize({
        "database_path": db_path,
        "read_only": True
    })

    registry = get_plugin_registry()
    registry.register("database-tool", db_tool, {})

    # Check health
    health = await db_tool.health_check()
    print(f"\nHealth: {health['status']}")

    # Get tool schema
    schema = db_tool.get_tool_schema()
    print(f"Tool: {schema.name}")
    print(f"Parameters: {[p.name for p in schema.parameters]}")

    # Execute query
    context = ToolExecutionContext(
        execution_id="test-001",
        agent_id="test-agent"
    )

    result = await db_tool.execute(
        context,
        query="SELECT * FROM users",
        limit=10
    )

    print("\nQuery result:")
    print(f"  Columns: {result['columns']}")
    print(f"  Rows: {result['row_count']}")
    for row in result['rows']:
        print(f"    {row}")

    await db_tool.cleanup()

    # Cleanup test database
    Path(db_path).unlink(missing_ok=True)

    print("\n✓ Database tool example complete")


async def example_metrics_collector():
    """Example: Using metrics collector plugin."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Metrics Collector Plugin")
    print("=" * 60)

    # Create and register plugin
    metrics = MetricsCollector()
    await metrics.initialize({"track_costs": True})

    registry = get_plugin_registry()
    registry.register("metrics-collector", metrics, {})

    # Simulate execution events
    event1 = ExecutionEvent(
        event_type="execution_started",
        timestamp="2026-01-07T14:30:00Z",
        agent_id="coder",
        execution_id="exec-001"
    )
    await metrics.on_execution_started(event1)

    event2 = ExecutionEvent(
        event_type="llm_call",
        timestamp="2026-01-07T14:30:05Z",
        agent_id="coder",
        execution_id="exec-001"
    )
    await metrics.on_llm_call(event2, provider="openai", model="gpt-4")

    event3 = ExecutionEvent(
        event_type="execution_completed",
        timestamp="2026-01-07T14:30:10Z",
        agent_id="coder",
        execution_id="exec-001"
    )
    await metrics.on_execution_completed(event3)

    # Check metrics
    health = await metrics.health_check()
    print("\nMetrics collected:")
    print(f"  Executions: {health['details']['executions']}")
    print(f"  LLM Calls: {health['details']['llm_calls']}")

    await metrics.cleanup()
    print("\n✓ Metrics collector example complete")


async def main():
    """Run all plugin examples."""
    print("\n" + "=" * 60)
    print("PLUGIN DEVELOPMENT EXAMPLES")
    print("=" * 60)

    # Example 1: Ollama Provider (requires Ollama running)
    try:
        await example_ollama_provider()
    except Exception as e:
        print(f"\n⚠ Ollama example skipped: {e}")
        print("  (Start Ollama with: ollama serve)")

    # Example 2: Database Tool
    await example_database_tool()

    # Example 3: Metrics Collector
    await example_metrics_collector()

    print("\n" + "=" * 60)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Copy plugins to .parac/plugins/")
    print("2. Configure in .parac/config/plugins.yaml")
    print("3. Load with: paracle plugin load")
    print("4. List with: paracle plugin list")


if __name__ == "__main__":
    asyncio.run(main())
