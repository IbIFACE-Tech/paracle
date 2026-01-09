---
name: meta-capabilities
description: Advanced AI capabilities for paracle_meta including web search, code execution, MCP integration, and autonomous agent spawning. Use when you need enhanced AI functionality beyond basic generation.
license: Apache-2.0
compatibility: Python 3.10+, requires configured capabilities
metadata:
  author: paracle-team
  version: "1.0.0"
  category: integration
  level: expert
  display_name: "Meta Capabilities"
  tags:
    - capabilities
    - web
    - code-execution
    - mcp
    - spawning
  capabilities:
    - web-search
    - web-fetch
    - code-execution
    - mcp-tools
    - agent-spawning
    - filesystem
    - shell
allowed-tools: Read Write Bash WebSearch WebFetch
---

# Meta Capabilities Skill

## Overview

This skill provides access to the advanced capability system of paracle_meta, enabling web research, code execution, MCP tool integration, and autonomous agent spawning.

## Available Capabilities

| Capability | Description | Use Case |
|------------|-------------|----------|
| `WebCapability` | Web search and fetch | Research, documentation |
| `CodeExecutionCapability` | Safe code execution | Testing, validation |
| `MCPCapability` | Model Context Protocol tools | External integrations |
| `AgentSpawner` | Autonomous agent creation | Heavy workloads |
| `FileSystemCapability` | File operations | Code generation |
| `ShellCapability` | Shell command execution | Automation |
| `MemoryCapability` | Persistent context | Long conversations |

## Web Capabilities

### Web Search

```python
from paracle_meta import MetaAgent

async with MetaAgent() as meta:
    # Search the web
    results = await meta.web_search(
        "Python async best practices 2025",
        max_results=10
    )

    for result in results:
        print(f"{result.title}: {result.url}")
```

### Fetch Web Content

```python
# Fetch and parse a page
content = await meta.web_fetch(
    "https://docs.python.org/3/library/asyncio.html",
    extract_text=True
)

# Get specific content
code_examples = await meta.web_fetch(
    url,
    selector="pre.python"  # CSS selector
)
```

## Code Execution

### Safe Execution

```python
# Execute Python code safely
result = await meta.run_code(
    code="""
import math
result = math.factorial(10)
print(f"10! = {result}")
""",
    language="python",
    timeout=30  # seconds
)

print(result.stdout)  # "10! = 3628800"
print(result.exit_code)  # 0
```

### Sandboxed Execution

```python
from paracle_meta import CodeExecutionCapability, CodeExecutionConfig

config = CodeExecutionConfig(
    sandbox=True,
    max_memory_mb=512,
    max_cpu_seconds=30,
    allowed_imports=["math", "json", "datetime"]
)

capability = CodeExecutionCapability(config)
result = await capability.execute(code, "python")
```

## MCP Integration

### Using MCP Tools

```python
from paracle_meta import MCPCapability, MCPConfig

# Connect to MCP server
config = MCPConfig(
    server_url="http://localhost:3000",
    tools=["read_file", "write_file", "search"]
)

mcp = MCPCapability(config)
await mcp.initialize()

# Call a tool
result = await mcp.call_tool(
    "read_file",
    {"path": "/path/to/file.py"}
)
```

### Discovering Tools

```python
# List available tools
tools = await mcp.list_tools()
for tool in tools:
    print(f"{tool.name}: {tool.description}")
```

## Agent Spawning

### Spawn Specialized Agents

```python
from paracle_meta import AgentSpawner, SpawnConfig

spawner = AgentSpawner()

# Spawn a researcher agent
researcher = await spawner.spawn(
    SpawnConfig(
        name="Researcher",
        agent_type="researcher",
        task="Research Python testing frameworks",
        capabilities=["web_search", "web_fetch"]
    )
)

# Wait for results
result = await researcher.wait()
print(result.findings)
```

### Parallel Agents

```python
# Spawn multiple agents for parallel work
agents = await spawner.spawn_many([
    SpawnConfig(name="SecurityReviewer", task="Review for security issues"),
    SpawnConfig(name="PerformanceAnalyzer", task="Analyze performance"),
    SpawnConfig(name="DocumentationChecker", task="Check documentation"),
])

# Gather results
results = await asyncio.gather(*[a.wait() for a in agents])
```

## File System Operations

### Read/Write Files

```python
from paracle_meta import FileSystemCapability

fs = FileSystemCapability()

# Read a file
content = await fs.read("src/main.py")

# Write a file
await fs.write("output/report.md", report_content)

# Search files
matches = await fs.search(
    pattern="def test_",
    path="tests/",
    file_types=["*.py"]
)
```

### Git Operations

```python
# Git status
status = await fs.git_status()

# Git diff
diff = await fs.git_diff("HEAD~1")
```

## Shell Capability

### Execute Commands

```python
from paracle_meta import ShellCapability, ShellConfig

shell = ShellCapability(ShellConfig(
    allowed_commands=["ls", "cat", "grep", "find"],
    blocked_patterns=["rm -rf", "sudo"]
))

result = await shell.execute("ls -la src/")
print(result.stdout)
```

## Memory Capability

### Persistent Context

```python
from paracle_meta import MemoryCapability

memory = MemoryCapability()

# Store information
await memory.remember("api_key", "sk-...", ttl=3600)
await memory.remember("user_preferences", {"theme": "dark"})

# Recall information
api_key = await memory.recall("api_key")
prefs = await memory.recall("user_preferences")

# Search memory
results = await memory.search("api")
```

## Provider Chain

### Fallback Strategy

```python
from paracle_meta import ProviderChain, FallbackStrategy

chain = ProviderChain(
    providers=["anthropic", "openai", "ollama"],
    strategy=FallbackStrategy.SEQUENTIAL
)

# Automatically falls back on failure
result = await chain.complete(messages)
```

### Circuit Breaker

```python
from paracle_meta import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=60
)

# Prevents cascading failures
result = await breaker.call(provider.complete, messages)
```

## Configuration

### Environment Variables

```bash
# Web capabilities
PARACLE_WEB_TIMEOUT=30
PARACLE_WEB_MAX_RESULTS=10

# Code execution
PARACLE_CODE_SANDBOX=true
PARACLE_CODE_MAX_MEMORY=512

# MCP
PARACLE_MCP_SERVER_URL=http://localhost:3000

# Spawning
PARACLE_MAX_SPAWNED_AGENTS=10
```

## Security Considerations

1. **Code Execution**: Always use sandbox mode in production
2. **Shell Commands**: Whitelist allowed commands
3. **Web Access**: Respect rate limits and robots.txt
4. **Agent Spawning**: Limit concurrent agents
5. **Memory**: Don't store secrets in plain text

## Related Skills

- [meta-generation](../meta-generation/): Generate artifacts
- [meta-learning](../meta-learning/): Improve over time
- [tool-integration](../tool-integration/): Create custom tools
