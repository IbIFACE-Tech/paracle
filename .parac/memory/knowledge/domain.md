# Paracle Domain Knowledge

## Overview

Paracle is a user-driven multi-agent framework designed for building AI-native applications with unique features like agent inheritance, multi-provider support, and API-first architecture.

## Core Concepts

### Agents

**Definition:** Autonomous AI entities that can execute tasks using LLMs, tools, and memory.

**Key Properties:**

- **Identity:** Unique ID, name, description
- **Spec:** Configuration (provider, model, temperature, prompts)
- **Status:** Runtime state (pending, running, succeeded, failed)
- **Inheritance:** Can extend other agents (unique feature)

**Agent Lifecycle:**

1. Definition (spec creation)
2. Resolution (inheritance chain)
3. Instantiation (runtime agent)
4. Execution (task processing)
5. Termination

### Agent Inheritance

**Concept:** Agents can inherit from parent agents, enabling reusability and specialization.

**Mechanics:**

- Child inherits parent's configuration
- Child can override specific properties
- Chain resolution (recursive)
- Validation of inheritance tree

**Example:**

```
base-agent (temperature: 0.7, model: gpt-4)
  ├── code-agent (system_prompt: "You are a coding expert")
  │   └── python-expert (tools: [pytest, pylint])
  └── review-agent (temperature: 0.3)
```

### Workflows

**Definition:** Directed Acyclic Graph (DAG) of agent tasks with dependencies.

**Components:**

- **Steps:** Individual tasks executed by agents
- **Dependencies:** Execution order constraints
- **Inputs:** Data passed between steps
- **Outputs:** Results aggregated

**Execution Model:**

- Topological sorting of steps
- Parallel execution where possible
- Context passing between steps
- Error handling and rollback

### Tools

**Definition:** Capabilities that agents can invoke to perform actions.

**Types:**

- **Internal:** Built into Paracle (file ops, API calls)
- **MCP:** Model Context Protocol tools
- **External:** Custom integrations

**Properties:**

- Name and description
- Input schema (JSON Schema)
- Output schema
- Permissions and security

### Memory

**Definition:** Context and state management for agents.

**Types:**

- **Short-term:** Conversation history (session)
- **Long-term:** Knowledge base (persistent)
- **Semantic:** Vector embeddings for search

**Operations:**

- Store context
- Retrieve relevant memories
- Update knowledge
- Garbage collection

## Domain Models

### Agent Model

```python
class Agent:
    id: str
    spec: AgentSpec
    status: AgentStatus
    created_at: datetime
    updated_at: datetime
```

### Workflow Model

```python
class Workflow:
    id: str
    spec: WorkflowSpec
    status: WorkflowStatus
    created_at: datetime
```

### Tool Model

```python
class Tool:
    id: str
    name: str
    description: str
    schema: ToolSchema
    handler: Callable
```

## Business Rules

### Agent Rules

1. Agent names must be unique within a project
2. Inheritance depth limited to 5 levels
3. Circular inheritance not allowed
4. Parent agent must exist before child can be created
5. Agent configuration must be valid for chosen provider

### Workflow Rules

1. Workflows must be DAGs (no cycles)
2. All step dependencies must exist
3. Steps must reference valid agents
4. Inputs must match expected schema
5. Workflows can be paused and resumed

### Tool Rules

1. Tools must have valid JSON schema
2. Tools require explicit permissions
3. Dangerous operations require confirmation
4. Tool execution timeout: 300s default
5. Tools can be disabled per-agent

## Terminology

### Agent-Related

- **Agent Spec:** Static configuration of an agent
- **Agent Instance:** Runtime instantiation
- **Agent Pool:** Collection of available agents
- **Agent Factory:** Creates agent instances

### Workflow-Related

- **Workflow Spec:** Workflow definition (DAG)
- **Workflow Execution:** Runtime workflow instance
- **Workflow Step:** Single task in workflow
- **Workflow Context:** Shared state during execution

### Provider-Related

- **Provider:** LLM service (OpenAI, Anthropic, etc.)
- **Model:** Specific LLM model (gpt-4, claude-3, etc.)
- **Adapter:** Interface between Paracle and provider

### Infrastructure

- **Orchestrator:** Coordinates workflow execution
- **Event Bus:** Asynchronous message system
- **Repository:** Data persistence abstraction
- **Registry:** Dynamic component discovery

## Key Patterns

### Hexagonal Architecture

- **Domain:** Pure business logic
- **Ports:** Interfaces to outside world
- **Adapters:** Implementations of ports

### Repository Pattern

- Abstract data access
- Decouples domain from storage
- Enables testing with mocks

### Event-Driven

- Events for state changes
- Asynchronous processing
- Audit trail

### Factory Pattern

- Agent instantiation
- Provider creation
- Tool registration

## Evolution

This document evolves as the domain understanding deepens. Major changes should be reflected in Architecture Decision Records.

**Last Updated:** 2025-12-24
**Version:** 1.0
