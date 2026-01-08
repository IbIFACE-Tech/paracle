# Phase 7 Integration Guide: Community & Ecosystem

## Overview

Phase 7 introduces three major technical features to enable community growth and ecosystem expansion:

1. **MCP Server**: Expose Paracle as Model Context Protocol server
2. **Plugin System SDK**: Extensibility framework for community contributions
3. **Git Workflow Manager**: Branch-per-execution isolation for safe operations

This guide covers setup, usage, and best practices for all three systems.

---

## 1. MCP Server

### What is MCP?

The Model Context Protocol (MCP) allows AI assistants like Claude Desktop to access tools, resources, and prompts from external servers. Paracle's MCP server exposes agents, workflows, and tools.

### Quick Start

**1. Start MCP Server**

```bash
# HTTP mode (default port 8765)
paracle mcp serve --host 0.0.0.0 --port 8765

# Stdio mode (for Claude Desktop)
paracle mcp serve --stdio
```

**2. Configure Claude Desktop**

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "paracle": {
      "command": "python",
      "args": ["-m", "paracle_cli.main", "mcp", "serve", "--stdio"],
      "env": {
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

**3. Test Integration**

In Claude Desktop:
```
/mcp paracle tools list
/mcp paracle agents list
/mcp paracle workflow run bugfix --bug_description "Memory leak in auth"
```

### MCP Features

**Tools Exposed**:
- `paracle_list_agents` - List all available agents
- `paracle_run_agent` - Execute a single agent
- `paracle_list_workflows` - List all workflows
- `paracle_run_workflow` - Execute a workflow
- `paracle_list_tools` - List available tools

**Resources Exposed**:
- `agent://<agent_id>` - Agent specifications
- `workflow://<workflow_id>` - Workflow definitions
- `state://current` - Current project state

**Prompts Exposed**:
- `code_review` - Code review assistant
- `feature_development` - Feature implementation guide
- `bug_diagnosis` - Bug analysis helper

### Configuration

Create `.parac/config/mcp.yaml`:

```yaml
mcp_server:
  host: "0.0.0.0"
  port: 8765
  transport: http  # or "stdio"

  # Tool exposure settings
  expose_agents: true
  expose_workflows: true
  expose_tools: true
  expose_resources: true
  expose_prompts: true

  # Security
  require_auth: false  # Set true for production
  api_key: "${MCP_API_KEY}"  # If require_auth=true

  # Rate limiting
  rate_limit:
    enabled: true
    requests_per_minute: 60

  # Logging
  log_level: INFO
  log_file: ".parac/memory/logs/mcp_server.log"
```

### Advanced Usage

**Custom Tool Registration**:

```python
from paracle_mcp import MCPServer

server = MCPServer()

@server.register_tool(
    name="custom_analyzer",
    description="Custom code analysis tool"
)
async def analyze_code(code: str) -> dict:
    """Analyze code and return insights."""
    return {"complexity": 5, "issues": []}

server.serve(transport="http", port=8765)
```

**Custom Resource Provider**:

```python
@server.register_resource(
    uri_pattern="metrics://{metric_name}",
    description="Project metrics"
)
async def get_metric(metric_name: str) -> str:
    """Retrieve project metric."""
    return f"Value for {metric_name}"
```

### Troubleshooting

**Issue**: Claude Desktop can't connect

**Solution**: Check stdio mode is configured correctly:
```bash
# Test stdio mode manually
echo '{"jsonrpc":"2.0","method":"initialize","id":1}' | \
  python -m paracle_cli.main mcp serve --stdio
```

**Issue**: Workflow execution times out

**Solution**: Increase timeout in `mcp.yaml`:
```yaml
mcp_server:
  execution_timeout: 600  # 10 minutes
```

---

## 2. Plugin System SDK

### Overview

The Plugin System enables community contributions of:
- **Providers**: Custom LLM providers (Ollama, local models, APIs)
- **Tools**: Custom agent tools (database, API, specialized)
- **Adapters**: Framework integrations (LangChain, LlamaIndex, CrewAI)
- **Observers**: Monitoring and metrics (Prometheus, Sentry, cost tracking)
- **Memory**: Custom memory backends (Redis, PostgreSQL, vector DBs)

### Plugin Architecture

```
BasePlugin (ABC)
├── ProviderPlugin (LLM providers)
├── ToolPlugin (Agent tools)
├── AdapterPlugin (Framework integrations)
├── ObserverPlugin (Monitoring)
└── MemoryPlugin (Memory backends) [Future]
```

### Creating a Provider Plugin

**Example: Ollama Provider**

```python
# .parac/plugins/ollama_provider.py
from paracle_plugins import ProviderPlugin, PluginMetadata, PluginType
from paracle_plugins.provider_plugin import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message
)
import httpx

class OllamaProvider(ProviderPlugin):
    """Ollama local LLM provider."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="ollama-provider",
            version="1.0.0",
            description="Ollama local LLM provider",
            author="Community",
            homepage="https://github.com/community/paracle-ollama",
            license="MIT",
            plugin_type=PluginType.PROVIDER,
            capabilities=["chat_completion", "streaming"],
            dependencies=["httpx>=0.24.0"],
            paracle_version=">=0.2.0",
            config_schema={
                "type": "object",
                "properties": {
                    "base_url": {
                        "type": "string",
                        "default": "http://localhost:11434"
                    },
                    "model": {"type": "string", "default": "llama2"}
                },
                "required": ["base_url", "model"]
            },
            tags=["llm", "local", "ollama"]
        )

    async def initialize(self, config: dict) -> None:
        """Initialize provider with config."""
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model = config.get("model", "llama2")
        self.client = httpx.AsyncClient()

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.client.aclose()

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Execute chat completion."""
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": request.model or self.model,
                "messages": [m.dict() for m in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens
            }
        )
        data = response.json()

        return ChatCompletionResponse(
            id=data["id"],
            model=request.model or self.model,
            content=data["message"]["content"],
            role=data["message"]["role"],
            finish_reason="stop",
            usage={
                "prompt_tokens": data.get("prompt_tokens", 0),
                "completion_tokens": data.get("completion_tokens", 0),
                "total_tokens": data.get("total_tokens", 0)
            }
        )

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ):
        """Execute streaming chat completion."""
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={
                "model": request.model or self.model,
                "messages": [m.dict() for m in request.messages],
                "stream": True
            }
        ) as response:
            async for chunk in response.aiter_bytes():
                yield chunk

    async def list_models(self) -> list[str]:
        """List available models."""
        response = await self.client.get(f"{self.base_url}/api/tags")
        data = response.json()
        return [model["name"] for model in data["models"]]

    async def get_model_info(self, model_name: str) -> dict:
        """Get model information."""
        response = await self.client.post(
            f"{self.base_url}/api/show",
            json={"name": model_name}
        )
        return response.json()
```

**Usage**:

```python
from paracle_plugins import get_plugin_registry

# Plugin auto-loads from .parac/plugins/
registry = get_plugin_registry()

# Use plugin
ollama = registry.get_plugin("ollama-provider")
response = await ollama.chat_completion(request)
```

### Creating a Tool Plugin

**Example: Database Query Tool**

```python
# .parac/plugins/database_tool.py
from paracle_plugins import ToolPlugin, PluginMetadata, PluginType
from paracle_plugins.tool_plugin import (
    ToolSchema,
    ToolParameter,
    ToolExecutionContext
)
import sqlite3

class DatabaseTool(ToolPlugin):
    """SQL database query tool."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="database-tool",
            version="1.0.0",
            description="Execute SQL queries on databases",
            author="Community",
            plugin_type=PluginType.TOOL,
            capabilities=["database_access"],
            config_schema={
                "type": "object",
                "properties": {
                    "database_path": {"type": "string"},
                    "read_only": {"type": "boolean", "default": True}
                },
                "required": ["database_path"]
            }
        )

    async def initialize(self, config: dict) -> None:
        self.db_path = config["database_path"]
        self.read_only = config.get("read_only", True)

    def get_tool_schema(self) -> ToolSchema:
        """Define tool schema."""
        return ToolSchema(
            name="database_query",
            description="Execute SQL query on database",
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
                    description="Max rows to return",
                    required=False,
                    default=100
                )
            ]
        )

    async def execute(
        self, context: ToolExecutionContext, **kwargs
    ) -> dict:
        """Execute tool."""
        query = kwargs["query"]
        limit = kwargs.get("limit", 100)

        # Validate read-only
        if self.read_only and not query.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries allowed in read-only mode")

        # Execute query
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchmany(limit)
        columns = [desc[0] for desc in cursor.description]
        conn.close()

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows)
        }
```

### Creating an Observer Plugin

**Example: Prometheus Metrics**

```python
# .parac/plugins/prometheus_observer.py
from paracle_plugins import ObserverPlugin, PluginMetadata, PluginType
from paracle_plugins.observer_plugin import ExecutionEvent
from prometheus_client import Counter, Histogram, start_http_server

class PrometheusObserver(ObserverPlugin):
    """Prometheus metrics observer."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="prometheus-observer",
            version="1.0.0",
            description="Export metrics to Prometheus",
            author="Community",
            plugin_type=PluginType.OBSERVER,
            capabilities=["metrics_collection"],
            dependencies=["prometheus-client>=0.17.0"],
            config_schema={
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "default": 9090}
                }
            }
        )

    async def initialize(self, config: dict) -> None:
        port = config.get("port", 9090)
        start_http_server(port)

        # Define metrics
        self.executions_total = Counter(
            'paracle_executions_total',
            'Total number of executions',
            ['agent_id', 'status']
        )
        self.execution_duration = Histogram(
            'paracle_execution_duration_seconds',
            'Execution duration in seconds',
            ['agent_id']
        )
        self.llm_calls_total = Counter(
            'paracle_llm_calls_total',
            'Total LLM calls',
            ['provider', 'model']
        )

    async def on_execution_started(self, event: ExecutionEvent) -> None:
        """Track execution start."""
        # Store start time for duration calculation
        pass

    async def on_execution_completed(self, event: ExecutionEvent) -> None:
        """Track successful execution."""
        self.executions_total.labels(
            agent_id=event.agent_id or "unknown",
            status="success"
        ).inc()

    async def on_execution_failed(
        self, event: ExecutionEvent, error: Exception
    ) -> None:
        """Track failed execution."""
        self.executions_total.labels(
            agent_id=event.agent_id or "unknown",
            status="failed"
        ).inc()

    async def on_llm_call(
        self, event: ExecutionEvent, provider: str, model: str
    ) -> None:
        """Track LLM call."""
        self.llm_calls_total.labels(
            provider=provider,
            model=model
        ).inc()
```

### Plugin Discovery

Plugins are auto-discovered from three sources:

**1. Directory** (`.parac/plugins/`):
```
.parac/plugins/
├── ollama_provider.py
├── database_tool.py
└── prometheus_observer.py
```

**2. Configuration** (`.parac/config/plugins.yaml`):
```yaml
plugins:
  - name: ollama-provider
    enabled: true
    config:
      base_url: "http://localhost:11434"
      model: "llama2"

  - name: database-tool
    enabled: true
    config:
      database_path: ".parac/memory/data/metrics.db"
      read_only: true

  - name: prometheus-observer
    enabled: true
    config:
      port: 9090
```

**3. Entry Points** (`pyproject.toml`):
```toml
[project.entry-points."paracle.plugins"]
ollama-provider = "paracle_community.ollama:OllamaProvider"
database-tool = "paracle_community.database:DatabaseTool"
```

### Plugin Management CLI

```bash
# List all loaded plugins
paracle plugin list

# Show plugin details
paracle plugin show ollama-provider

# Check plugin health
paracle plugin health

# Load plugins from all sources
paracle plugin load --source all

# Reload specific plugin
paracle plugin reload ollama-provider

# Plugin statistics
paracle plugin stats
```

### Plugin Best Practices

**1. Versioning**:
- Use semantic versioning (1.0.0, 1.1.0, 2.0.0)
- Specify `paracle_version` compatibility (e.g., ">=0.2.0,<1.0.0")
- List all dependencies with versions

**2. Error Handling**:
```python
async def execute(self, context, **kwargs):
    try:
        # Plugin logic
        return result
    except SomeError as e:
        # Log and re-raise with context
        logger.error(f"Plugin error: {e}")
        raise RuntimeError(f"Plugin failed: {e}") from e
```

**3. Configuration Validation**:
```python
def validate_config(self, config: dict) -> bool:
    """Validate configuration."""
    required = ["database_path"]
    if not all(k in config for k in required):
        raise ValueError(f"Missing required config: {required}")
    return True
```

**4. Health Checks**:
```python
async def health_check(self) -> dict:
    """Check plugin health."""
    try:
        # Test connection/functionality
        await self.client.get("/health")
        return {
            "status": "healthy",
            "latency_ms": 50,
            "details": {"connected": True}
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

**5. Testing**:
```python
# tests/test_ollama_plugin.py
import pytest
from paracle_plugins import get_plugin_registry

@pytest.mark.asyncio
async def test_ollama_provider():
    registry = get_plugin_registry()
    ollama = registry.get_plugin("ollama-provider")

    await ollama.initialize({"base_url": "http://localhost:11434"})

    models = await ollama.list_models()
    assert len(models) > 0

    await ollama.cleanup()
```

---

## 3. Git Workflow Manager

### Overview

The Git Workflow Manager provides branch-per-execution isolation, enabling:
- Safe parallel execution
- Easy rollback on failure
- Clean audit trail
- Pull request automation

### Architecture

```
ExecutionManager (high-level)
    ↓ uses
BranchManager (low-level git ops)
    ↓ uses
subprocess (git commands)
```

### Quick Start

**1. Initialize Git Workflows**:

```bash
paracle git init-workflow
```

**2. Start Execution with Branching**:

```python
from paracle_git_workflows import ExecutionManager, ExecutionConfig

config = ExecutionConfig(
    enable_branching=True,
    auto_commit=True,
    auto_merge=True,
    auto_cleanup=True,
    base_branch="main"
)

manager = ExecutionManager(config=config, repo_path=".")

# Start execution (creates branch: exec/abc123/20260107_143022)
info = manager.start_execution("abc123")
print(f"Created branch: {info['branch_name']}")

# Work happens...
manager.commit_changes("abc123", "feat: Add auth", ["src/auth.py"])

# Complete execution (merges and cleans up)
manager.complete_execution("abc123", success=True)
```

**3. Manage Branches via CLI**:

```bash
# List execution branches
paracle git branches

# Merge execution branch
paracle git merge exec/abc123/20260107_143022 --target main

# Create PR for execution
paracle git pr-create abc123 "Add authentication feature" \
  --body "Implements JWT authentication"

# Cleanup merged branches
paracle git cleanup --target main
```

### Branch Naming Convention

Format: `exec/{execution_id}/{timestamp}`

Examples:
- `exec/abc123/20260107_143022`
- `exec/feature-auth-456/20260107_150530`
- `exec/workflow-bugfix-789/20260107_162045`

### ExecutionManager API

**Configuration**:

```python
from paracle_git_workflows import ExecutionConfig

config = ExecutionConfig(
    enable_branching=True,       # Create branches per execution
    auto_commit=True,            # Auto-commit changes
    auto_merge=True,             # Merge on successful completion
    auto_cleanup=True,           # Delete branch after merge
    base_branch="main"           # Base branch for new executions
)
```

**Lifecycle Methods**:

```python
manager = ExecutionManager(config=config, repo_path=".")

# 1. Start execution
info = manager.start_execution("exec-001")
# Returns: {"execution_id": "exec-001", "branch_name": "exec/exec-001/..."}

# 2. Commit changes during execution
manager.commit_changes(
    execution_id="exec-001",
    message="feat: Implement feature X",
    files=["src/feature.py", "tests/test_feature.py"]
)

# 3. Complete execution
manager.complete_execution(
    execution_id="exec-001",
    success=True  # Merges and cleans up if True
)

# 4. List active executions
active = manager.list_active_executions()
# Returns: {"exec-001": BranchInfo(...), ...}

# 5. Cleanup old branches
count = manager.cleanup_old_branches(days=7)
print(f"Cleaned up {count} old branches")
```

### BranchManager API

**Low-level operations**:

```python
from paracle_git_workflows import BranchManager
from pathlib import Path

manager = BranchManager(Path("."))

# Create execution branch
branch = manager.create_execution_branch(
    execution_id="exec-001",
    base_branch="main"
)
print(f"Created: {branch.name}")

# List execution branches
branches = manager.list_execution_branches()
for branch in branches:
    print(f"{branch.name}: {branch.commit_count} commits")

# Merge branch
manager.merge_execution_branch(
    branch_name="exec/exec-001/20260107_143022",
    target_branch="main"
)

# Delete branch
manager.delete_execution_branch(
    branch_name="exec/exec-001/20260107_143022",
    force=False  # Use -d (safe) vs -D (force)
)

# Cleanup merged branches
count = manager.cleanup_merged_branches(target_branch="main")
print(f"Removed {count} merged branches")

# Get current branch
current = manager.get_current_branch()
print(f"On branch: {current}")

# Switch branch
manager.switch_branch("exec/exec-002/20260107_150000")
```

### Workflow Integration

**Agent Execution with Git Isolation**:

```python
from paracle_orchestration import Orchestrator
from paracle_git_workflows import ExecutionManager, ExecutionConfig

# Configure git workflows
git_config = ExecutionConfig(enable_branching=True, auto_commit=True)
git_manager = ExecutionManager(config=git_config, repo_path=".")

# Start agent execution
execution_id = "agent-run-001"
git_manager.start_execution(execution_id)

try:
    # Run agent
    orchestrator = Orchestrator()
    result = await orchestrator.execute_agent(
        agent_id="coder",
        task="Implement authentication"
    )

    # Commit changes
    git_manager.commit_changes(
        execution_id=execution_id,
        message=f"feat: {result.summary}",
        files=result.modified_files
    )

    # Complete successfully
    git_manager.complete_execution(execution_id, success=True)

except Exception as e:
    # Failed - don't merge, keep branch for debugging
    git_manager.complete_execution(execution_id, success=False)
    raise
```

**Workflow Execution with Git Isolation**:

```python
from paracle_orchestration import WorkflowEngine
from paracle_git_workflows import ExecutionManager

git_manager = ExecutionManager(...)

# Start workflow
execution_id = "workflow-feature-dev-001"
git_manager.start_execution(execution_id)

workflow_engine = WorkflowEngine()
result = await workflow_engine.execute_workflow(
    workflow_id="feature_development",
    context={"feature_name": "authentication"}
)

# Commit after each step
for step_result in result.step_results:
    if step_result.modified_files:
        git_manager.commit_changes(
            execution_id=execution_id,
            message=f"{step_result.step_name}: {step_result.summary}",
            files=step_result.modified_files
        )

# Complete
git_manager.complete_execution(execution_id, success=result.success)
```

### CLI Commands

```bash
# Initialize git workflows
paracle git init-workflow --repo .

# List execution branches
paracle git branches --repo .

# Merge execution branch
paracle git merge exec/abc123/20260107_143022 --target main --repo .

# Create pull request (shows GitHub CLI command)
paracle git pr-create abc123 "Feature: Authentication" \
  --body "Implements JWT authentication with refresh tokens"

# Cleanup merged branches
paracle git cleanup --target main --repo .
```

### Best Practices

**1. Always Use Config**:
```python
# Don't: Manual branch management
branch = "exec/temp/20260107_143022"
os.system(f"git checkout -b {branch}")

# Do: Use ExecutionManager
manager = ExecutionManager(config=ExecutionConfig(...))
manager.start_execution("temp")
```

**2. Commit Frequently**:
```python
# Commit after each significant change
manager.commit_changes(
    execution_id="exec-001",
    message="feat: Add user model",
    files=["src/models/user.py"]
)
# ... more work ...
manager.commit_changes(
    execution_id="exec-001",
    message="feat: Add user endpoints",
    files=["src/api/users.py"]
)
```

**3. Handle Failures Gracefully**:
```python
try:
    # Execution logic
    result = execute_agent(...)
    manager.complete_execution(execution_id, success=True)
except Exception as e:
    # Keep branch for debugging
    manager.complete_execution(execution_id, success=False)
    logger.error(f"Execution failed: {e}")
    # Branch remains: exec/exec-001/... for investigation
```

**4. Cleanup Regularly**:
```bash
# Weekly cron job
0 0 * * 0 paracle git cleanup --target main

# Or programmatically
manager.cleanup_old_branches(days=7)
```

**5. Use Conventional Commits**:
```python
# Follow conventional commits format
manager.commit_changes(
    execution_id="exec-001",
    message="feat(auth): Add JWT authentication\n\n- Implements JWT tokens\n- Adds refresh token support",
    files=[...]
)
```

### Troubleshooting

**Issue**: Branch already exists

**Solution**: Use unique execution IDs or cleanup old branches
```bash
paracle git cleanup --target main
```

**Issue**: Merge conflicts

**Solution**: Branches are isolated, but conflicts can occur on merge. Resolve manually:
```bash
git checkout exec/abc123/20260107_143022
git merge main  # Resolve conflicts
paracle git merge exec/abc123/20260107_143022 --target main
```

**Issue**: Failed execution leaves orphaned branch

**Solution**: Set `auto_cleanup=False` to keep failed branches for debugging, then manually cleanup:
```bash
paracle git branches  # List all branches
git branch -D exec/failed-001/20260107_143022  # Force delete if needed
```

---

## Examples

### Example 1: End-to-End Plugin Development

See [examples/20_plugin_development.py](../examples/20_plugin_development.py)

### Example 2: Git Workflow Integration

See [examples/21_git_workflows.py](../examples/21_git_workflows.py)

### Example 3: MCP Server with Claude

See [examples/22_mcp_integration.py](../examples/22_mcp_integration.py)

---

## Community Resources

### Templates Marketplace (USER TODO)

User will create a GitHub-based marketplace for:
- Agent templates
- Workflow templates
- Plugin templates
- Integration templates

**Features**:
- Search and discovery
- Ratings and reviews
- One-command installation
- CLI: `paracle template search/install/publish`

### Discord Community (USER TODO)

User will setup Discord server with:
- #general - Community chat
- #support - Help and questions
- #showcase - Share projects
- #dev - Development discussions
- #announcements - Updates

**Target**: 500+ members in 6 months

### Webinars (USER TODO)

User will organize monthly webinars:
1. **Paracle Overview** - Getting started
2. **Agent Inheritance** - Advanced patterns
3. **Production Deployment** - Best practices
4. **MCP Integration** - Claude Desktop workflows
5. **Community Showcase** - User projects

**Target**: 50+ live attendees per session

### Blog Series (USER TODO)

User will write 11 blog posts:

**Getting Started** (3 posts):
- Installing and first agent
- Basic workflows
- Tools and integrations

**Advanced Topics** (5 posts):
- Agent inheritance patterns
- MCP server setup
- Plugin development guide
- Git workflows
- Production deployment

**Case Studies** (3 posts):
- Building a support bot
- DevOps agent
- Research assistant

**Target**: 20K+ total views

---

## Next Steps

1. **Technical (DONE)**:
   - ✅ MCP Server implemented
   - ✅ Plugin System SDK complete
   - ✅ Git Workflow Manager complete

2. **Documentation (YOU ARE HERE)**:
   - ✅ Phase 7 Integration Guide
   - ⏳ Example files (next)
   - ⏳ API reference updates

3. **Community (USER TODO)**:
   - 🧑 Templates Marketplace
   - 🧑 Discord Community
   - 🧑 Webinars
   - 🧑 Blog Series

---

## Support

- **Documentation**: [docs/](../docs/)
- **Examples**: [examples/](../examples/)
- **Issues**: [GitHub Issues](https://github.com/IbIFACE-Tech/paracle-lite/issues)
- **Discord** (coming soon): User will setup

---

**Version**: 1.0
**Last Updated**: 2026-01-07
**Phase**: 7 - Community & Ecosystem
**Status**: Technical features complete, community features in progress
