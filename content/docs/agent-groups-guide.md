# Agent Groups & Multi-Agent Communication Guide

**Version**: 1.1.0 | **Status**: v1.1.0 Feature | **Date**: 2026-01-10

Complete guide to multi-agent collaboration using Agent Groups in Paracle.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Communication Patterns](#communication-patterns)
5. [Creating Agent Groups](#creating-agent-groups)
6. [Running Collaborations](#running-collaborations)
7. [Session Management](#session-management)
8. [Message Types](#message-types)
9. [A2A Bridge](#a2a-bridge)
10. [CLI Commands](#cli-commands)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)
13. [FAQ](#faq)

---

## Overview

Agent Groups enable **multi-agent collaboration** in Paracle by orchestrating teams of specialized agents working together on complex tasks.

### Key Features

- ✅ **Communication Patterns** - Peer-to-peer, broadcast, coordinator
- ✅ **Session Management** - Stateful conversations with history
- ✅ **Message Types** - FIPA-inspired performatives (inform, request, propose, agree, etc.)
- ✅ **Multimodal Content** - Text, code, JSON, images, files
- ✅ **External Integration** - A2A bridge for external agents
- ✅ **Persistence** - SQLite session storage
- ✅ **CLI Integration** - Full command-line support

### Use Cases

| Use Case            | Agents Involved             | Pattern      |
| ------------------- | --------------------------- | ------------ |
| Feature Development | Architect, Coder, Tester    | Coordinator  |
| Code Review         | Reviewer, Security, Tester  | Broadcast    |
| Research Project    | Researcher, Analyst, Writer | Peer-to-peer |
| Bug Triage          | PM, Coder, DevOps           | Coordinator  |
| Design Sprint       | Designer, Architect, PM     | Broadcast    |

---

## Quick Start

### 1. Create an Agent Group

```python
from paracle_agent_comm import AgentGroup, CommunicationPattern

group = AgentGroup(
    id="feature-team",
    name="Feature Development Team",
    members=["architect", "coder", "tester"],
    coordinator="architect",
    communication_pattern=CommunicationPattern.COORDINATOR,
)
```

### 2. Run a Collaboration

```python
from paracle_agent_comm.engine import GroupCollaborationEngine

engine = GroupCollaborationEngine(
    group=group,
    agent_registry=agent_registry,  # Your AgentRegistry
    event_bus=event_bus,            # Optional EventBus
)

session = await engine.collaborate(
    goal="Design and implement user authentication system"
)

print(f"Session completed: {session.status}")
print(f"Messages exchanged: {len(session.messages)}")
print(f"Consensus: {session.consensus}")
```

### 3. CLI Usage

```bash
# Create a group
paracle groups create feature-team \
  --members architect,coder,tester \
  --coordinator architect \
  --pattern coordinator

# Run collaboration
paracle groups run feature-team \
  --goal "Design authentication system"

# List groups
paracle groups list

# View session history
paracle groups history feature-team
```

---

## Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────────────┐
│              Agent Groups Architecture                      │
│                                                            │
│  ┌────────────────┐  ┌─────────────────────────────────┐  │
│  │  AgentGroup    │  │  GroupCollaborationEngine       │  │
│  │  (Definition)  │→ │  (Orchestrates collaboration)   │  │
│  └────────────────┘  └──────────┬──────────────────────┘  │
│                                 │                          │
│  ┌─────────────────────────────▼──────────────────────┐   │
│  │          Communication Pattern                      │   │
│  │  ┌──────────┐ ┌───────────┐ ┌─────────────────┐   │   │
│  │  │ P2P      │ │ Broadcast │ │ Coordinator     │   │   │
│  │  └──────────┘ └───────────┘ └─────────────────┘   │   │
│  └─────────────────────────────┬──────────────────────┘   │
│                                 │                          │
│  ┌─────────────────────────────▼──────────────────────┐   │
│  │          GroupSession (Stateful)                    │   │
│  │  - Messages history                                 │   │
│  │  - Round counter                                    │   │
│  │  - Consensus tracking                               │   │
│  └─────────────────────────────┬──────────────────────┘   │
│                                 │                          │
│  ┌─────────────────────────────▼──────────────────────┐   │
│  │          Persistence Layer                          │   │
│  │  ┌───────────────┐  ┌───────────────────────────┐  │   │
│  │  │ SQLite Store  │  │ In-Memory Store           │  │   │
│  │  └───────────────┘  └───────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. User creates AgentGroup
   ↓
2. GroupCollaborationEngine initializes session
   ↓
3. Engine sends initial goal to coordinator (or all)
   ↓
4. Loop: Agents exchange messages via pattern
   ↓
5. Each message triggers agent execution
   ↓
6. Responses routed according to pattern
   ↓
7. Check for consensus or max rounds
   ↓
8. Session completed, results persisted
```

---

## Communication Patterns

### 1. Peer-to-Peer (P2P)

**Description**: Any agent can message any other agent directly.

**Use When**:
- Agents have equal authority
- Flexible, dynamic collaboration needed
- No clear leader

**Example**:
```python
group = AgentGroup(
    name="Research Team",
    members=["researcher", "analyst", "writer"],
    communication_pattern=CommunicationPattern.PEER_TO_PEER,
)
```

**Flow**:
```
Researcher ←→ Analyst
    ↕          ↕
  Writer  ←→ Writer
```

### 2. Broadcast

**Description**: Messages are sent to all group members.

**Use When**:
- Information needs to be shared with everyone
- Consensus-building
- Status updates

**Example**:
```python
group = AgentGroup(
    name="Review Team",
    members=["reviewer", "security", "tester"],
    communication_pattern=CommunicationPattern.BROADCAST,
)
```

**Flow**:
```
    Reviewer
      ↓  ↓  ↓
Security | Tester
```

### 3. Coordinator

**Description**: All messages go through a designated coordinator.

**Use When**:
- Clear leadership structure
- Coordinator needs to approve/route messages
- Structured workflow

**Example**:
```python
group = AgentGroup(
    name="Dev Team",
    members=["architect", "coder", "tester"],
    coordinator="architect",
    communication_pattern=CommunicationPattern.COORDINATOR,
)
```

**Flow**:
```
    Architect (Coordinator)
       ↓         ↓
     Coder    Tester
```

---

## Creating Agent Groups

### Basic Group

```python
from paracle_agent_comm import AgentGroup, CommunicationPattern

group = AgentGroup(
    id="basic-team",
    name="Basic Team",
    members=["agent1", "agent2", "agent3"],
    communication_pattern=CommunicationPattern.PEER_TO_PEER,
)
```

### With Coordinator

```python
group = AgentGroup(
    id="coordinated-team",
    name="Coordinated Team",
    members=["lead", "dev1", "dev2"],
    coordinator="lead",
    communication_pattern=CommunicationPattern.COORDINATOR,
)
```

### With Configuration

```python
group = AgentGroup(
    id="advanced-team",
    name="Advanced Team",
    members=["architect", "coder", "tester", "reviewer"],
    coordinator="architect",
    communication_pattern=CommunicationPattern.COORDINATOR,
    max_rounds=10,  # Maximum conversation rounds
    consensus_threshold=0.75,  # 75% agreement needed
    metadata={
        "project": "auth-system",
        "sprint": "2026-Q1",
    },
)
```

### CLI Creation

```bash
# Create with defaults
paracle groups create my-team --members agent1,agent2,agent3

# Create with coordinator
paracle groups create dev-team \
  --members architect,coder,tester \
  --coordinator architect \
  --pattern coordinator

# Create with full config
paracle groups create advanced-team \
  --members lead,dev1,dev2,qa \
  --coordinator lead \
  --pattern coordinator \
  --max-rounds 15 \
  --consensus 0.8
```

---

## Running Collaborations

### Programmatic Execution

```python
from paracle_agent_comm.engine import GroupCollaborationEngine
from paracle_core.registry import AgentRegistry
from paracle_events import EventBus

# Setup
agent_registry = AgentRegistry()
event_bus = EventBus()

engine = GroupCollaborationEngine(
    group=group,
    agent_registry=agent_registry,
    event_bus=event_bus,
)

# Run collaboration
session = await engine.collaborate(
    goal="Design authentication system with OAuth2 support"
)

# Access results
print(f"Status: {session.status}")
print(f"Rounds: {session.round}")
print(f"Messages: {len(session.messages)}")

if session.consensus:
    print(f"Consensus: {session.consensus}")
```

### CLI Execution

```bash
# Run collaboration
paracle groups run feature-team \
  --goal "Design and implement authentication" \
  --max-rounds 10

# Run with specific session
paracle groups run feature-team \
  --goal "Review code changes" \
  --session-id code-review-123

# Run and save output
paracle groups run feature-team \
  --goal "Research technologies" \
  --output research-results.json
```

### Async Streaming

```python
async def stream_collaboration():
    engine = GroupCollaborationEngine(group, agent_registry)

    async for event in engine.collaborate_stream(goal="Design API"):
        if event.type == "message":
            print(f"{event.sender}: {event.content}")
        elif event.type == "consensus":
            print(f"Consensus reached: {event.data}")

asyncio.run(stream_collaboration())
```

---

## Session Management

### Creating Sessions

```python
from paracle_agent_comm import GroupSession, GroupSessionStatus

session = GroupSession(
    id="session-123",
    group_id=group.id,
    goal="Design authentication system",
    status=GroupSessionStatus.ACTIVE,
    max_rounds=10,
)
```

### Adding Messages

```python
from paracle_agent_comm import GroupMessage, MessageType

msg = GroupMessage.create(
    group_id=group.id,
    session_id=session.id,
    sender="architect",
    recipient="coder",  # Optional, depends on pattern
    text="Let's use JWT tokens for authentication",
    message_type=MessageType.PROPOSE,
)

session.add_message(msg)
```

### Checking Consensus

```python
# Check if consensus reached
if session.has_consensus(threshold=0.75):
    print(f"Consensus: {session.consensus}")
else:
    print(f"No consensus yet ({len(session.messages)} messages)")

# Get agreement percentage
agreement = session.calculate_agreement()
print(f"Agreement: {agreement * 100:.1f}%")
```

### Persistence

```python
from paracle_agent_comm.persistence import SQLiteSessionStore

# Save session
store = SQLiteSessionStore(db_path=".parac/memory/data/agent_comm.db")
await store.save_session(session)

# Load session
loaded = await store.get_session(session.id)

# List all sessions
sessions = await store.list_sessions(group_id=group.id)

# Get session history
history = await store.get_session_history(group_id=group.id, limit=10)
```

---

## Message Types

### FIPA-Inspired Performatives

| Type       | Description          | Example                                |
| ---------- | -------------------- | -------------------------------------- |
| `INFORM`   | Share information    | "The API is ready"                     |
| `REQUEST`  | Ask for action       | "Please implement auth"                |
| `PROPOSE`  | Suggest solution     | "Let's use OAuth2"                     |
| `AGREE`    | Accept proposal      | "I agree with JWT approach"            |
| `DISAGREE` | Reject proposal      | "I prefer session tokens"              |
| `QUERY`    | Ask question         | "How should we handle refresh tokens?" |
| `CONFIRM`  | Verify understanding | "Confirmed: Using Redis"               |
| `REFUSE`   | Decline request      | "Cannot implement this week"           |

### Creating Messages

```python
# Informational message
msg_inform = GroupMessage.create(
    group_id=group.id,
    sender="architect",
    text="I've completed the system design",
    message_type=MessageType.INFORM,
)

# Request with code
msg_request = GroupMessage.create(
    group_id=group.id,
    sender="architect",
    recipient="coder",
    text="Please implement this authentication function",
    message_type=MessageType.REQUEST,
    parts=[
        MessagePart(
            content_type="code",
            content="def authenticate(username, password): ...",
            language="python",
        )
    ],
)

# Proposal with JSON data
msg_propose = GroupMessage.create(
    group_id=group.id,
    sender="architect",
    text="Here's the proposed API structure",
    message_type=MessageType.PROPOSE,
    parts=[
        MessagePart(
            content_type="json",
            content={"endpoints": ["/auth/login", "/auth/logout"]},
        )
    ],
)
```

---

## A2A Bridge

**A2A (Agent-to-Agent) Bridge** enables external agents to participate in Paracle agent groups.

### Setup

```python
from paracle_a2a import A2AClient, A2AServer
from paracle_agent_comm.bridges import A2ABridge

# Start A2A server
server = A2AServer(host="0.0.0.0", port=8080)
await server.start()

# Create bridge
bridge = A2ABridge(
    group_id=group.id,
    a2a_client=A2AClient(url="http://external-agent:8080"),
    agent_mapping={"external-coder": "coder"},
)

# Add bridge to engine
engine.add_bridge(bridge)
```

### External Agent Communication

```python
# External agent sends message to Paracle group
response = await a2a_client.send_message(
    group_id="feature-team",
    sender="external-coder",
    text="I've implemented the login endpoint",
    message_type="inform",
)

# Bridge forwards message to Paracle group
# Response flows back through bridge
```

---

## CLI Commands

### Group Management

```bash
# List all groups
paracle groups list

# Create group
paracle groups create GROUPID --members agent1,agent2,agent3

# Show group details
paracle groups show GROUPID

# Delete group
paracle groups delete GROUPID
```

### Collaboration

```bash
# Run collaboration
paracle groups run GROUPID --goal "Task description"

# Run with options
paracle groups run GROUPID \
  --goal "Design system" \
  --max-rounds 15 \
  --output results.json \
  --verbose

# Stream collaboration
paracle groups run GROUPID --goal "Research" --stream
```

### Session Management

```bash
# List sessions
paracle groups sessions GROUPID

# Show session details
paracle groups session SESSION_ID

# Export session
paracle groups session SESSION_ID --export session.json

# Delete session
paracle groups session SESSION_ID --delete
```

### A2A Integration

```bash
# Start A2A server
paracle a2a serve --port 8080

# List A2A connections
paracle a2a list

# Test A2A endpoint
paracle a2a test http://external-agent:8080
```

---

## Best Practices

### 1. Choose the Right Pattern

✅ **DO**:
- Use **Coordinator** for structured workflows (e.g., dev team with architect)
- Use **Broadcast** for consensus-building (e.g., code review)
- Use **Peer-to-Peer** for flexible research (e.g., analysis team)

❌ **DON'T**:
- Use P2P for highly structured tasks
- Use Coordinator without clear leadership
- Use Broadcast for 1:1 communications

### 2. Set Appropriate Limits

```python
group = AgentGroup(
    ...
    max_rounds=10,  # Prevent infinite loops
    consensus_threshold=0.75,  # 75% agreement needed
)
```

### 3. Structure Goals Clearly

```python
# ❌ Vague
goal = "Do something with auth"

# ✅ Clear
goal = """Design and implement OAuth2 authentication system:
- Support Google and GitHub providers
- JWT token-based sessions
- Refresh token rotation
- Role-based access control (RBAC)
"""
```

### 4. Monitor Sessions

```python
# Add logging
engine = GroupCollaborationEngine(group, agent_registry, event_bus)

event_bus.subscribe("group.message", lambda msg: print(f"📨 {msg}"))
event_bus.subscribe("group.consensus", lambda cons: print(f"✅ {cons}"))
event_bus.subscribe("group.round_complete", lambda r: print(f"🔄 Round {r}"))
```

### 5. Persist Important Sessions

```python
# Save to SQLite for audit trail
store = SQLiteSessionStore()
await store.save_session(session)

# Export for sharing
session_json = session.model_dump_json(indent=2)
with open("session-results.json", "w") as f:
    f.write(session_json)
```

---

## Troubleshooting

### Issue: Agents not responding

**Cause**: Agent not found in registry

**Solution**:
```python
# Check registry
agents = agent_registry.list_agents()
print(f"Available: {agents}")

# Ensure agents exist
for member in group.members:
    assert agent_registry.get_agent(member), f"Missing: {member}"
```

### Issue: Max rounds exceeded

**Cause**: No consensus reached

**Solution**:
```python
# Increase max_rounds
group.max_rounds = 20

# Or lower consensus threshold
group.consensus_threshold = 0.6  # 60% instead of 75%

# Or add explicit termination condition
if session.round > 15 and session.calculate_agreement() > 0.5:
    session.force_complete("Partial consensus")
```

### Issue: Messages not routing correctly

**Cause**: Wrong pattern or configuration

**Solution**:
```python
# Check pattern
print(f"Pattern: {group.communication_pattern}")

# Verify coordinator (if coordinator pattern)
if group.communication_pattern == CommunicationPattern.COORDINATOR:
    assert group.coordinator in group.members

# Test routing
pattern = engine.get_pattern()
recipients = pattern.route_message(test_message)
print(f"Message routed to: {recipients}")
```

---

## FAQ

### Q: Can I mix communication patterns?

**A**: Not in a single group, but you can create multiple groups with different patterns:

```python
# Coordinator group for implementation
dev_group = AgentGroup(..., pattern=CommunicationPattern.COORDINATOR)

# Broadcast group for review
review_group = AgentGroup(..., pattern=CommunicationPattern.BROADCAST)
```

### Q: How do I add dynamic members?

**A**: Update the group and restart the engine:

```python
group.members.append("new-agent")
await store.save_group(group)

# Restart engine with updated group
engine = GroupCollaborationEngine(group, agent_registry)
```

### Q: Can agents leave groups?

**A**: Yes, remove from members list:

```python
group.members.remove("departing-agent")
await store.save_group(group)
```

### Q: How do I handle agent failures?

**A**: Use resilience patterns:

```python
from paracle_resilience import CircuitBreaker

# Wrap agent execution
breaker = CircuitBreaker(max_failures=3)

@breaker.protected
async def execute_agent(agent_id, message):
    return await agent_registry.execute(agent_id, message)
```

### Q: Can I use agent groups in workflows?

**A**: Yes! Integrate with workflow steps:

```yaml
# workflow.yaml
steps:
  - id: group_collaboration
    type: agent_group
    config:
      group_id: feature-team
      goal: "Design authentication system"
      max_rounds: 10
```

---

## Related Documentation

- [ADR-025: Agent Groups Protocol](../../.parac/roadmap/decisions.md#adr-025) - Architecture decision
- [Agent Groups Example](../../content/examples/agents/23_agent_groups.py) - Complete example
- [A2A Protocol Guide](a2a-protocol-guide.md) - External agent integration
- [Workflow Guide](workflow-guide.md) - Multi-agent workflows

---

**Status**: v1.1.0 Feature | **Version**: 1.1.0 | **Date**: 2026-01-10

