# Core Concepts Overview

Paracle is built on four fundamental concepts that work together to create powerful multi-agent AI applications.

## The Four Pillars

### 1. 🤖 Agents

**Agents** are autonomous AI entities with specific roles and capabilities.

```yaml
name: code-reviewer
role: reviewer
description: Reviews code for quality and security
provider: openai
model: gpt-4
tools:
  - filesystem
  - python_analyzer
```

**Key Features:**
- Inheritance (like OOP classes)
- Configurable behavior
- Tool access
- Skill specialization

[Learn more about Agents →](agents.md)

### 2. 🔄 Workflows

**Workflows** orchestrate multiple agents to accomplish complex tasks.

```yaml
name: code-review-workflow
steps:
  - id: analyze
    agent: static-analyzer
  - id: review
    agent: code-reviewer
    depends_on: [analyze]
  - id: suggest
    agent: improvement-suggester
    depends_on: [review]
```

**Key Features:**
- DAG-based execution
- Parallel processing
- Conditional logic
- Error handling

[Learn more about Workflows →](../workflow-guide.md)

### 3. 🛠️ Tools

**Tools** give agents capabilities to interact with the world.

```python
from paracle_tools import Tool

@tool(name="file_reader", description="Read files")
def read_file(path: str) -> str:
    return Path(path).read_text()
```

**Built-in Tools:**
- Filesystem operations
- HTTP requests
- Shell commands
- Python execution
- Web search

[Learn more about Tools →](../builtin-tools.md)

### 4. 🧠 Providers

**Providers** connect to different LLM services.

**Supported:**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- Google (Gemini)
- xAI (Grok)
- DeepSeek
- Self-hosted (Ollama, LM Studio)

[Learn more about Providers →](../providers.md)

## How They Work Together

```
┌─────────────┐
│   Workflow  │ ← Orchestrates
└──────┬──────┘
       │
       ├──────→ Agent 1 ─→ Uses Tools ─→ Calls Provider ─→ GPT-4
       │
       ├──────→ Agent 2 ─→ Uses Tools ─→ Calls Provider ─→ Claude
       │
       └──────→ Agent 3 ─→ Uses Tools ─→ Calls Provider ─→ Ollama
```

## Quick Example

```python
from paracle_domain.models import AgentSpec, Agent
from paracle_orchestration import Workflow

# 1. Define an agent
agent_spec = AgentSpec(
    name="helper",
    provider="openai",
    model="gpt-4",
    tools=["filesystem", "http"]
)

agent = Agent(spec=agent_spec)

# 2. Create workflow
workflow = Workflow(
    name="assist",
    steps=[
        {"id": "help", "agent": "helper", "task": "{{ input.task }}"}
    ]
)

# 3. Execute
result = await workflow.run({"task": "Read README.md"})
```

## Next Steps

- [Create your first agent](../guides/creating-agents.md)
- [Build a workflow](../guides/creating-workflows.md)
- [Explore built-in tools](../builtin-tools.md)
- [Configure providers](../providers.md)
