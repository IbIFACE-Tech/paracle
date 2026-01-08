# Agent Groups Guide

Agent Groups enable multi-agent collaboration in Paracle, allowing multiple agents to work together on complex tasks with structured communication.

## Overview

While individual agents excel at focused tasks, complex problems often benefit from multiple perspectives. Agent Groups provide:

- **Structured Collaboration**: Define how agents communicate and coordinate
- **Communication Patterns**: Peer-to-peer, broadcast, or coordinator-based
- **Session Management**: Track conversation history and shared context
- **Consensus Building**: Achieve agreement through FIPA-inspired performatives

## Concepts

### Agent Groups

An Agent Group is a team of agents configured to collaborate:

```python
from paracle_agent_comm.models import AgentGroup, CommunicationPattern

group = AgentGroup(
    name="Code Review Team",
    members=["architect", "coder", "reviewer"],
    communication_pattern=CommunicationPattern.PEER_TO_PEER,
    max_rounds=10,
    max_messages=100,
    timeout_seconds=300.0,
)
```

### Communication Patterns

**Peer-to-Peer**: Any agent can message any other agent directly.
- Best for: Open discussions, brainstorming
- Example: Design review where all perspectives are equal

**Broadcast**: All messages go to all agents.
- Best for: Information sharing, announcements
- Example: Status updates, shared context building

**Coordinator**: All communication flows through a designated coordinator.
- Best for: Structured workflows, task delegation
- Example: Project manager coordinating between specialists

```python
# Coordinator pattern example
group = AgentGroup(
    name="Development Team",
    members=["pm", "architect", "coder", "tester"],
    coordinator="pm",
    communication_pattern=CommunicationPattern.COORDINATOR,
)
```

### Message Types (Performatives)

Messages use FIPA-inspired performatives to express intent:

| Type | Purpose | Example |
|------|---------|---------|
| `INFORM` | Share information | "The API endpoint is /users" |
| `REQUEST` | Ask for action | "Please review this code" |
| `PROPOSE` | Suggest approach | "I propose we use async/await" |
| `ACCEPT` | Accept proposal | "I agree with this approach" |
| `REJECT` | Reject with reason | "I disagree because..." |
| `QUERY` | Ask question | "What is the expected input format?" |
| `DELEGATE` | Assign to another | "Coder, please implement this" |
| `CONFIRM` | Confirm understanding | "Understood, proceeding" |
| `CANCEL` | Cancel request | "Disregard previous request" |

### Sessions

Sessions track the full context of a collaboration:

```python
from paracle_agent_comm.models import GroupSession

session = GroupSession(
    group_id=group.id,
    goal="Design authentication system",
    shared_context={
        "requirements": ["OAuth 2.0", "JWT tokens"],
        "constraints": ["Must support SSO"],
    },
)
```

## Quick Start

### CLI Usage

```bash
# List groups
paracle groups list

# Create a group
paracle groups create "Review Team" -m coder,reviewer,tester

# Create with coordinator pattern
paracle groups create "Dev Team" -m pm,coder,tester -p coordinator -c pm

# View group details
paracle groups get "Review Team"

# List sessions
paracle groups sessions

# View session details
paracle groups session abc123 --messages

# Delete a group
paracle groups delete "Old Team"
```

### Python Usage

```python
import asyncio
from paracle_agent_comm.models import (
    AgentGroup,
    CommunicationPattern,
    GroupConfig,
)
from paracle_agent_comm.engine import GroupCollaborationEngine
from paracle_agent_comm.persistence import SQLiteSessionStore

async def run_collaboration():
    # Create a group
    group = AgentGroup(
        name="Architecture Team",
        members=["architect", "coder", "reviewer"],
        communication_pattern=CommunicationPattern.PEER_TO_PEER,
    )

    # Configure collaboration
    config = GroupConfig(
        require_consensus=True,
        max_cost_per_session=5.0,
        allow_human_injection=True,
    )

    # Create engine with your agent registry
    engine = GroupCollaborationEngine(
        group=group,
        agent_registry=my_registry,  # Your AgentRegistry implementation
        config=config,
    )

    # Run collaboration
    session = await engine.collaborate(
        goal="Design the authentication module",
        initial_context={
            "requirements": ["OAuth 2.0 support", "JWT tokens"],
        },
    )

    # Process results
    print(f"Status: {session.status}")
    print(f"Outcome: {session.outcome}")
    print(f"Rounds: {session.round_count}")

    # Access messages
    for msg in session.messages:
        print(f"{msg.sender}: {msg.get_text_content()}")

    # Save session
    store = SQLiteSessionStore("sessions.db")
    await store.save_session(session)

asyncio.run(run_collaboration())
```

## Architecture

### Package Structure

```
packages/paracle_agent_comm/
├── __init__.py           # Package exports
├── models.py             # Data models (AgentGroup, GroupMessage, etc.)
├── engine.py             # GroupCollaborationEngine
├── exceptions.py         # Custom exceptions
├── patterns/             # Communication pattern implementations
│   ├── peer_to_peer.py
│   ├── broadcast.py
│   └── coordinator.py
├── bridges/              # External integration
│   └── a2a_bridge.py     # Google A2A protocol bridge
└── persistence/          # Storage backends
    ├── session_store.py  # Abstract interface
    └── sqlite_store.py   # SQLite implementation
```

### Protocol Support

Agent Groups support two interoperability protocols:

**A2A (Agent-to-Agent)**: Google's protocol for external agent communication
- Used for cross-system agent interoperability
- JSON-RPC 2.0 based with Agent Cards

**ACP-Inspired Sessions**: Internal session management
- Rich multimodal messaging (text, code, JSON, files)
- Session-based state tracking
- Cost and token tracking

## Advanced Usage

### Custom Termination

Define when collaboration should end:

```python
def should_terminate(session):
    # End when consensus is reached
    if session.has_consensus():
        return True

    # End after 5 rounds minimum if we have a proposal
    proposals = session.get_messages_by_type(MessageType.PROPOSE)
    if session.round_count >= 5 and proposals:
        return True

    return False

session = await engine.collaborate(
    goal="Design API",
    termination_fn=should_terminate,
)
```

### Human-in-the-Loop

Inject human messages during collaboration:

```python
# During an active session
message = await engine.inject_human_message(
    session,
    text="Consider using GraphQL instead of REST",
    message_type=MessageType.PROPOSE,
)
```

### Event Handling

Subscribe to collaboration events:

```python
class MyEventBus:
    async def publish(self, event):
        if event["type"] == "group.session.started":
            print(f"Session started: {event['session_id']}")
        elif event["type"] == "group.agent.responded":
            print(f"Agent {event['agent_id']} responded")

engine = GroupCollaborationEngine(
    group=group,
    agent_registry=registry,
    event_bus=MyEventBus(),
)
```

### External Agents (A2A)

Integrate external A2A-compatible agents:

```python
from paracle_agent_comm.bridges import A2ABridge

# Create bridge to external agent
bridge = A2ABridge(
    agent_url="https://external-agent.example.com",
    agent_card=agent_card,  # A2A Agent Card
)

# Use in group (as member)
group.external_members = [
    {"url": "https://external-agent.example.com", "card": card_json}
]
```

## Best Practices

### Group Design

1. **Keep groups focused**: 3-5 agents per group works best
2. **Choose appropriate patterns**: Use coordinator for structured tasks
3. **Set reasonable limits**: Prevent runaway costs with max_rounds/max_messages
4. **Define clear goals**: Specific goals lead to better outcomes

### Communication

1. **Use appropriate performatives**: `REQUEST` for actions, `QUERY` for questions
2. **Build consensus gradually**: PROPOSE → ACCEPT/REJECT cycle
3. **Share context early**: Use initial_context for shared knowledge
4. **Target messages when possible**: Use recipients for directed communication

### Cost Control

```python
config = GroupConfig(
    max_tokens_per_round=10000,
    max_cost_per_session=10.0,  # USD
)
```

### Persistence

```python
# Use SQLite for durable storage
from paracle_agent_comm.persistence import SQLiteSessionStore

store = SQLiteSessionStore(".parac/memory/data/agent_comm.db")

# Save sessions
await store.save_session(session)

# Query sessions
recent = await store.list_sessions(
    group_id=group.id,
    status=GroupSessionStatus.COMPLETED,
    limit=10,
)
```

## Troubleshooting

### Common Issues

**"CoordinatorRequiredError"**
- Coordinator pattern requires a coordinator to be set
- Solution: Set `coordinator="agent_id"` when creating group

**"MaxMessagesExceededError"**
- Session hit message limit
- Solution: Increase `max_messages` or use termination function

**"SessionTimeoutError"**
- Session exceeded timeout
- Solution: Increase `timeout_seconds` or optimize agent responses

### Debugging

Enable verbose logging:

```python
import logging
logging.getLogger("paracle_agent_comm").setLevel(logging.DEBUG)
```

Check session state:

```python
# View recent messages
for msg in session.get_recent_messages(10):
    print(f"{msg.sender} ({msg.message_type.value}): {msg.get_text_content()}")

# Check for consensus
print(f"Has consensus: {session.has_consensus()}")

# View shared context
print(f"Context: {session.shared_context}")
```

## API Reference

See the full API documentation for:
- [Models Reference](api/agent-comm-models.md)
- [Engine Reference](api/agent-comm-engine.md)
- [Patterns Reference](api/agent-comm-patterns.md)
- [CLI Reference](cli-reference.md#groups)
