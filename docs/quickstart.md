# Quick Start Guide

Get up and running with Paracle in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- pip package manager
- (Optional) Docker for sandbox features

## Installation

### 1. Install Paracle

=== "Minimal"

    ```bash
    pip install paracle
    ```

=== "With API Server"

    ```bash
    pip install "paracle[api]"
    ```

=== "Full Installation"

    ```bash
    pip install "paracle[all]"
    ```

### 2. Verify Installation

```bash
paracle --version
# Output: paracle version 0.0.1
```

## Your First Agent

### 1. Create Agent Directory

```bash
mkdir my-first-agent
cd my-first-agent
```

### 2. Create Agent Spec

Create `agent.yaml`:

```yaml
name: hello-agent
role: assistant
description: A friendly AI assistant
provider: openai
model: gpt-4
temperature: 0.7
system_prompt: |
  You are a helpful AI assistant.
  Be friendly and concise.
tools:
  - echo
  - datetime
```

### 3. Set API Key

```bash
# Linux/macOS
export OPENAI_API_KEY="sk-your-key-here"

# Windows PowerShell
$env:OPENAI_API_KEY = "sk-your-key-here"
```

See [API Keys Guide](api-keys.md) for all providers.

### 4. Initialize Paracle Workspace

```bash
paracle init
```

### 5. Run an Agent

```bash
# List available agents
paracle agents list

# Run an agent with a task
paracle agents run coder --task "Create a hello world script"
```

Example output:

```
🛡️ Running Agent: CODER

Task: Create a hello world script
Mode: SAFE

✅ Execution Complete

Outputs:
  • result: Created hello.py with print("Hello, World!")
```

## Next Steps

### Create a Multi-Agent Workflow

Create `workflow.yaml`:

```yaml
name: research-workflow
description: Multi-agent research workflow

agents:
  - name: researcher
    role: research
    provider: openai
    model: gpt-4
    system_prompt: You are a research specialist.

  - name: summarizer
    role: summarization
    provider: anthropic
    model: claude-3-sonnet
    system_prompt: You are a summarization expert.

steps:
  - id: research
    agent: researcher
    input: "Research the topic: {topic}"
    depends_on: []

  - id: summarize
    agent: summarizer
    input: "Summarize this research: {research.output}"
    depends_on: [research]
```

Run the workflow:

```bash
paracle workflow run workflow.yaml --input '{"topic": "AI frameworks"}'
```

### Use the API Server

Start the API server:

```bash
paracle server start
```

API available at: `http://localhost:8000`

Test the API:

```bash
curl http://localhost:8000/health
# Output: {"status": "healthy"}

# Create agent
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d @agent.yaml

# Execute agent
curl -X POST http://localhost:8000/agents/hello-agent/execute \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello!"}'
```

See [API Reference](api-reference.md) for all endpoints.

### Add Custom Tools

Create `custom_tool.py`:

```python
from paracle_tools import tool, ToolSchema

@tool(
    name="custom_calculator",
    description="Perform calculations",
    schema=ToolSchema(
        parameters={
            "expression": {
                "type": "string",
                "description": "Math expression to evaluate"
            }
        },
        required=["expression"]
    )
)
async def custom_calculator(expression: str) -> float:
    """Evaluate a mathematical expression safely."""
    # Implementation
    return eval(expression)  # Note: Use safe eval in production!

# Register tool
from paracle_tools import ToolRegistry
registry = ToolRegistry()
registry.register(custom_calculator)
```

Use in agent:

```yaml
name: calculator-agent
tools:
  - custom_calculator
```

### Enable Sandbox Features

Install Docker dependencies:

```bash
pip install "paracle[sandbox]"
```

Run agent in sandbox mode:

```bash
paracle agents run tester --task "Run security tests" --mode sandbox
```

Features:

- ✅ Docker isolation
- ✅ Resource limits
- ✅ Automatic rollback on failure
- ✅ Artifact review

## Common Patterns

### Pattern 1: Research Assistant

```python
from paracle_domain import AgentSpec

research_agent = AgentSpec(
    name="research-assistant",
    role="research",
    provider="openai",
    model="gpt-4",
    tools=["web_search", "file_read", "file_write"],
    system_prompt="""
    You are a research assistant. When given a topic:
    1. Search for relevant information
    2. Analyze and synthesize findings
    3. Save a comprehensive report
    """
)
```

### Pattern 2: Code Review Bot

```python
code_reviewer = AgentSpec(
    name="code-reviewer",
    role="review",
    provider="anthropic",
    model="claude-3-opus",
    tools=["git_diff", "static_analysis", "comment"],
    system_prompt="""
    You are an expert code reviewer. For each PR:
    1. Analyze code changes
    2. Check for bugs and security issues
    3. Suggest improvements
    4. Add review comments
    """
)
```

### Pattern 3: Data Pipeline

```python
from paracle_domain import WorkflowSpec, WorkflowStep

data_pipeline = WorkflowSpec(
    name="data-pipeline",
    steps=[
        WorkflowStep(
            id="extract",
            agent="data-extractor",
            depends_on=[]
        ),
        WorkflowStep(
            id="transform",
            agent="data-transformer",
            depends_on=["extract"]
        ),
        WorkflowStep(
            id="load",
            agent="data-loader",
            depends_on=["transform"]
        )
    ]
)
```

## Troubleshooting

### API Key Not Found

```bash
# Check if set
echo $OPENAI_API_KEY  # Linux/macOS
echo $env:OPENAI_API_KEY  # Windows

# Set in .env file
echo "OPENAI_API_KEY=sk-..." > .env
```

### Port Already in Use

```bash
# Use different port
paracle server start --port 8001
```

### Module Not Found

```bash
# Reinstall with all dependencies
pip install --force-reinstall "paracle[all]"
```

## Next Steps

- 📖 [User Guide](user-guide/agents.md) - Learn core concepts
- 🛠️ [Built-in Tools](builtin-tools.md) - Available tools
- 🌐 [Providers](providers.md) - LLM provider setup
- 🔧 [Advanced Topics](agent-skills.md) - Agent skills, MCP integration
- 🚀 [Execution Modes](execution-modes.md) - Safe, YOLO, sandbox, review modes

## Getting Help

- 💬 [GitHub Discussions](https://github.com/IbIFACE-Tech/paracle-lite/discussions)
- 🐛 [Issue Tracker](https://github.com/IbIFACE-Tech/paracle-lite/issues)
- 📧 Email: team@ibiface-tech.com

---

**Ready to dive deeper?** [Continue to User Guide →](user-guide/agents.md)
