# A2A Protocol Integration Guide

**Version**: 1.1.0 | **Status**: Experimental | **Date**: 2026-01-10

Complete guide to integrating external agents with Paracle using the Agent-to-Agent (A2A) Protocol.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Protocol Specification](#protocol-specification)
4. [Server Setup](#server-setup)
5. [Client Integration](#client-integration)
6. [Agent Registration](#agent-registration)
7. [Message Exchange](#message-exchange)
8. [Security](#security)
9. [Examples](#examples)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The **A2A (Agent-to-Agent) Protocol** enables external agents (written in any language) to communicate with Paracle agents and participate in agent groups.

### Key Features

- ✅ **Language-Agnostic** - REST/WebSocket API, any language can integrate
- ✅ **Bidirectional** - External agents can send and receive messages
- ✅ **Group Participation** - Join Paracle agent groups
- ✅ **Message Types** - Full support for FIPA performatives
- ✅ **Multimodal** - Text, code, JSON, images, files
- ✅ **Secure** - API key authentication, TLS support

### Use Cases

| Use Case                      | External Agent Type | Integration Method |
| ----------------------------- | ------------------- | ------------------ |
| Integrate Python agent        | FastAPI service     | A2A Client         |
| Connect JavaScript agent      | Express.js          | HTTP REST API      |
| Human-in-the-loop             | Web UI              | WebSocket          |
| Legacy system integration     | SOAP service        | A2A Bridge         |
| Multi-framework orchestration | Mixed agents        | A2A Server         |

---

## Quick Start

### 1. Start A2A Server

```bash
# Start on default port 8080
paracle a2a serve

# Custom port and host
paracle a2a serve --host 0.0.0.0 --port 9000

# With TLS
paracle a2a serve --tls --cert server.crt --key server.key
```

### 2. Register External Agent

```bash
# Register via CLI
paracle a2a register external-coder \
  --url http://external-agent:8080 \
  --capabilities code,testing \
  --api-key secret-key-123
```

Or programmatically:

```python
from paracle_a2a import A2AClient, AgentInfo

client = A2AClient(base_url="http://localhost:8080")

agent_info = AgentInfo(
    id="external-coder",
    name="External Code Agent",
    url="http://external-agent:8080",
    capabilities=["code", "testing"],
    api_key="secret-key-123",
)

await client.register_agent(agent_info)
```

### 3. Send Messages

```python
# Send message to Paracle group
response = await client.send_message(
    group_id="feature-team",
    sender="external-coder",
    recipient="architect",  # Optional
    text="I've completed the login implementation",
    message_type="inform",
)

print(f"Response: {response.text}")
```

### 4. Receive Messages

```python
# Poll for messages
messages = await client.receive_messages(
    agent_id="external-coder",
    since=last_timestamp,
)

for msg in messages:
    print(f"From {msg.sender}: {msg.text}")

    # Process and respond
    response = await process_message(msg)
    await client.send_message(
        group_id=msg.group_id,
        sender="external-coder",
        text=response,
        in_reply_to=msg.id,
    )
```

---

## Protocol Specification

### HTTP REST API

Base URL: `http://localhost:8080/api/v1`

#### Authentication

```
Authorization: Bearer <API_KEY>
```

#### Endpoints

| Endpoint             | Method | Description            |
| -------------------- | ------ | ---------------------- |
| `/agents`            | GET    | List registered agents |
| `/agents`            | POST   | Register new agent     |
| `/agents/{id}`       | GET    | Get agent details      |
| `/agents/{id}`       | DELETE | Unregister agent       |
| `/messages`          | POST   | Send message           |
| `/messages`          | GET    | Receive messages       |
| `/groups/{id}/join`  | POST   | Join group             |
| `/groups/{id}/leave` | POST   | Leave group            |
| `/health`            | GET    | Health check           |

### WebSocket API

URL: `ws://localhost:8080/ws/{agent_id}`

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8080/ws/external-coder');

// Send message
ws.send(JSON.stringify({
  type: 'message',
  group_id: 'feature-team',
  text: 'Hello from external agent',
  message_type: 'inform',
}));

// Receive message
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(`From ${msg.sender}: ${msg.text}`);
};
```

### Message Format

```json
{
  "id": "msg-uuid-123",
  "group_id": "feature-team",
  "session_id": "session-456",
  "sender": "external-coder",
  "recipient": "architect",
  "text": "I've implemented the authentication",
  "message_type": "inform",
  "parts": [
    {
      "content_type": "code",
      "content": "def authenticate(user, password): ...",
      "language": "python"
    }
  ],
  "metadata": {
    "timestamp": "2026-01-10T10:30:00Z",
    "version": "1.1.0"
  }
}
```

---

## Server Setup

### Configuration

```yaml
# .parac/config/a2a.yaml
server:
  host: 0.0.0.0
  port: 8080
  tls:
    enabled: true
    cert: /path/to/server.crt
    key: /path/to/server.key

  cors:
    enabled: true
    origins:
      - "http://localhost:3000"
      - "https://app.example.com"

  rate_limiting:
    enabled: true
    requests_per_minute: 60

authentication:
  api_keys:
    - key: "secret-key-123"
      agent_id: "external-coder"
      capabilities: ["code", "testing"]
    - key: "secret-key-456"
      agent_id: "external-reviewer"
      capabilities: ["review"]

logging:
  level: INFO
  file: .parac/memory/logs/a2a.log
```

### Programmatic Setup

```python
from paracle_a2a.server import A2AServer, A2AConfig

config = A2AConfig(
    host="0.0.0.0",
    port=8080,
    tls_enabled=True,
    tls_cert="server.crt",
    tls_key="server.key",
    cors_origins=["http://localhost:3000"],
    rate_limit_rpm=60,
)

server = A2AServer(config)
await server.start()

print(f"A2A Server running on {config.host}:{config.port}")
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .
RUN pip install -e packages/paracle_a2a

EXPOSE 8080

CMD ["paracle", "a2a", "serve", "--host", "0.0.0.0", "--port", "8080"]
```

```yaml
# docker-compose.yml
services:
  a2a-server:
    build: .
    ports:
      - "8080:8080"
    environment:
      - A2A_API_KEY=secret-key-123
    volumes:
      - ./.parac:/app/.parac
```

---

## Client Integration

### Python Client

```python
from paracle_a2a import A2AClient, Message, MessageType

class ExternalCoderAgent:
    def __init__(self, a2a_url: str, api_key: str):
        self.client = A2AClient(
            base_url=a2a_url,
            api_key=api_key,
        )
        self.agent_id = "external-coder"

    async def start(self):
        # Register with A2A server
        await self.client.register_agent(
            id=self.agent_id,
            name="External Code Agent",
            capabilities=["python", "fastapi", "testing"],
        )

        # Start message loop
        await self.message_loop()

    async def message_loop(self):
        last_timestamp = None

        while True:
            # Poll for new messages
            messages = await self.client.receive_messages(
                agent_id=self.agent_id,
                since=last_timestamp,
            )

            for msg in messages:
                # Process message
                response = await self.handle_message(msg)

                # Send response
                await self.client.send_message(
                    group_id=msg.group_id,
                    sender=self.agent_id,
                    text=response,
                    message_type=MessageType.INFORM,
                    in_reply_to=msg.id,
                )

                last_timestamp = msg.timestamp

            await asyncio.sleep(1)  # Poll interval

    async def handle_message(self, msg: Message) -> str:
        if msg.message_type == MessageType.REQUEST:
            # Execute coding task
            result = await self.execute_code_task(msg.text)
            return f"Task completed: {result}"
        else:
            return "Acknowledged"

# Usage
agent = ExternalCoderAgent(
    a2a_url="http://localhost:8080",
    api_key="secret-key-123",
)
await agent.start()
```

### JavaScript Client

```javascript
// a2a-client.js
class A2AClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
    this.agentId = "external-coder";
  }

  async registerAgent(capabilities) {
    const response = await fetch(`${this.baseUrl}/api/v1/agents`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id: this.agentId,
        name: 'External Code Agent',
        capabilities: capabilities,
      }),
    });
    return response.json();
  }

  async sendMessage(groupId, text, messageType = 'inform') {
    const response = await fetch(`${this.baseUrl}/api/v1/messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        group_id: groupId,
        sender: this.agentId,
        text: text,
        message_type: messageType,
      }),
    });
    return response.json();
  }

  async receiveMessages(since = null) {
    const params = new URLSearchParams({
      agent_id: this.agentId,
      ...(since && { since: since }),
    });

    const response = await fetch(
      `${this.baseUrl}/api/v1/messages?${params}`,
      {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
        },
      }
    );
    return response.json();
  }
}

// Usage
const client = new A2AClient(
  'http://localhost:8080',
  'secret-key-123'
);

await client.registerAgent(['javascript', 'nodejs', 'testing']);

// Message loop
setInterval(async () => {
  const messages = await client.receiveMessages();
  for (const msg of messages) {
    console.log(`From ${msg.sender}: ${msg.text}`);

    // Process and respond
    const response = await handleMessage(msg);
    await client.sendMessage(msg.group_id, response);
  }
}, 1000);
```

---

## Agent Registration

### Registration Data

```python
from paracle_a2a.models import AgentInfo

agent_info = AgentInfo(
    id="external-coder",
    name="External Code Agent",
    description="Specialized Python coding agent",
    url="http://external-agent:8080",
    capabilities=[
        "python",
        "fastapi",
        "testing",
        "code-review",
    ],
    api_key="secret-key-123",
    metadata={
        "version": "1.0.0",
        "framework": "custom",
        "maintainer": "team@example.com",
    },
)

await client.register_agent(agent_info)
```

### Capability Negotiation

```python
# Query agent capabilities
agent = await client.get_agent("external-coder")
print(f"Capabilities: {agent.capabilities}")

# Check if agent has capability
if "python" in agent.capabilities:
    # Send Python coding task
    await client.send_message(
        group_id="dev-team",
        sender="architect",
        recipient="external-coder",
        text="Implement authentication function",
        message_type="request",
    )
```

---

## Message Exchange

### Request-Response Pattern

```python
# Architect sends request
request_msg = await client.send_message(
    group_id="feature-team",
    sender="architect",
    recipient="external-coder",
    text="Implement OAuth2 authentication",
    message_type="request",
)

# External coder responds
response_msg = await client.send_message(
    group_id="feature-team",
    sender="external-coder",
    recipient="architect",
    text="OAuth2 authentication implemented",
    message_type="inform",
    in_reply_to=request_msg.id,
    parts=[
        {
            "content_type": "code",
            "content": "def oauth2_authenticate(...): ...",
            "language": "python",
        }
    ],
)
```

### Broadcast Pattern

```python
# Send to all group members
broadcast_msg = await client.send_message(
    group_id="review-team",
    sender="reviewer",
    text="Code review starting in 5 minutes",
    message_type="inform",
    # No recipient = broadcast
)
```

### Multimodal Content

```python
# Message with code
msg_with_code = await client.send_message(
    group_id="dev-team",
    sender="external-coder",
    text="Here's the implementation",
    message_type="inform",
    parts=[
        {
            "content_type": "code",
            "content": "def authenticate(user, password): ...",
            "language": "python",
        }
    ],
)

# Message with JSON data
msg_with_json = await client.send_message(
    group_id="data-team",
    sender="external-analyst",
    text="Analysis results",
    message_type="inform",
    parts=[
        {
            "content_type": "json",
            "content": {
                "accuracy": 0.95,
                "precision": 0.92,
                "recall": 0.88,
            },
        }
    ],
)

# Message with file
msg_with_file = await client.send_message(
    group_id="docs-team",
    sender="external-writer",
    text="Updated documentation",
    message_type="inform",
    parts=[
        {
            "content_type": "file",
            "content": base64.b64encode(file_bytes).decode(),
            "filename": "api-docs.pdf",
            "mime_type": "application/pdf",
        }
    ],
)
```

---

## Security

### API Key Authentication

```python
# Server-side: Generate API keys
from paracle_a2a.security import generate_api_key

api_key = generate_api_key(
    agent_id="external-coder",
    capabilities=["code", "testing"],
    expires_days=90,
)

print(f"API Key: {api_key}")
```

```python
# Client-side: Use API key
client = A2AClient(
    base_url="http://localhost:8080",
    api_key="secret-key-123",
)
```

### TLS/SSL

```bash
# Generate self-signed cert (development)
openssl req -x509 -newkey rsa:4096 \
  -keyout server.key -out server.crt \
  -days 365 -nodes

# Start server with TLS
paracle a2a serve \
  --tls \
  --cert server.crt \
  --key server.key
```

```python
# Client with TLS verification
client = A2AClient(
    base_url="https://localhost:8080",
    api_key="secret-key-123",
    verify_ssl=True,
    ca_cert="ca-bundle.crt",
)
```

### Rate Limiting

```yaml
# .parac/config/a2a.yaml
rate_limiting:
  enabled: true
  requests_per_minute: 60
  burst: 10
```

### CORS Configuration

```yaml
# .parac/config/a2a.yaml
cors:
  enabled: true
  origins:
    - "http://localhost:3000"
    - "https://app.example.com"
  methods: ["GET", "POST", "PUT", "DELETE"]
  allow_credentials: true
```

---

## Examples

### Example 1: Python External Agent

```python
# external_coder_agent.py
import asyncio
from paracle_a2a import A2AClient, MessageType

class CoderAgent:
    def __init__(self):
        self.client = A2AClient(
            base_url="http://localhost:8080",
            api_key="secret-key-123",
        )
        self.agent_id = "external-coder"

    async def start(self):
        await self.client.register_agent(
            id=self.agent_id,
            name="External Coder",
            capabilities=["python", "testing"],
        )

        print(f"✅ Agent {self.agent_id} registered")

        await self.message_loop()

    async def message_loop(self):
        last_timestamp = None

        while True:
            messages = await self.client.receive_messages(
                agent_id=self.agent_id,
                since=last_timestamp,
            )

            for msg in messages:
                print(f"📨 From {msg.sender}: {msg.text}")

                if msg.message_type == MessageType.REQUEST:
                    # Execute coding task
                    code = self.generate_code(msg.text)

                    # Send response
                    await self.client.send_message(
                        group_id=msg.group_id,
                        sender=self.agent_id,
                        text="Code implementation complete",
                        message_type=MessageType.INFORM,
                        in_reply_to=msg.id,
                        parts=[{
                            "content_type": "code",
                            "content": code,
                            "language": "python",
                        }],
                    )

                    print(f"✅ Responded to {msg.sender}")

                last_timestamp = msg.timestamp

            await asyncio.sleep(1)

    def generate_code(self, task: str) -> str:
        # Implement code generation logic
        return f"# Implementation for: {task}\n..."

if __name__ == "__main__":
    agent = CoderAgent()
    asyncio.run(agent.start())
```

### Example 2: JavaScript WebSocket Client

```javascript
// external_reviewer.js
const WebSocket = require('ws');

class ReviewerAgent {
  constructor(wsUrl, apiKey) {
    this.wsUrl = wsUrl;
    this.apiKey = apiKey;
    this.agentId = 'external-reviewer';
  }

  async start() {
    // Connect WebSocket
    this.ws = new WebSocket(`${this.wsUrl}/ws/${this.agentId}`, {
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
      },
    });

    this.ws.on('open', () => {
      console.log(`✅ Agent ${this.agentId} connected`);
    });

    this.ws.on('message', async (data) => {
      const msg = JSON.parse(data);
      console.log(`📨 From ${msg.sender}: ${msg.text}`);

      if (msg.message_type === 'request') {
        // Perform code review
        const review = await this.reviewCode(msg.parts);

        // Send review response
        this.ws.send(JSON.stringify({
          type: 'message',
          group_id: msg.group_id,
          sender: this.agentId,
          text: 'Code review complete',
          message_type: 'inform',
          in_reply_to: msg.id,
          parts: [{
            content_type: 'json',
            content: review,
          }],
        }));

        console.log(`✅ Review sent to ${msg.sender}`);
      }
    });

    this.ws.on('error', (error) => {
      console.error('❌ WebSocket error:', error);
    });

    this.ws.on('close', () => {
      console.log('🔌 WebSocket closed');
      // Reconnect after delay
      setTimeout(() => this.start(), 5000);
    });
  }

  async reviewCode(parts) {
    // Implement code review logic
    return {
      approved: true,
      issues: [],
      suggestions: ['Consider adding more tests'],
    };
  }
}

const agent = new ReviewerAgent(
  'ws://localhost:8080',
  'secret-key-456'
);
agent.start();
```

---

## Troubleshooting

### Issue: Connection refused

**Cause**: A2A server not running

**Solution**:
```bash
# Check if server is running
curl http://localhost:8080/health

# Start server
paracle a2a serve
```

### Issue: Authentication failed

**Cause**: Invalid or missing API key

**Solution**:
```python
# Check API key configuration
from paracle_a2a.config import load_a2a_config

config = load_a2a_config()
print(f"API Keys: {config.api_keys}")

# Regenerate API key if needed
api_key = generate_api_key("external-coder")
```

### Issue: Messages not received

**Cause**: Agent not registered or polling too slowly

**Solution**:
```python
# Verify registration
agents = await client.list_agents()
assert "external-coder" in [a.id for a in agents]

# Increase polling frequency
await asyncio.sleep(0.5)  # Poll every 500ms instead of 1s

# Or use WebSocket for real-time
```

### Issue: Message delivery fails

**Cause**: Invalid group ID or recipient

**Solution**:
```python
# Verify group exists
groups = await client.list_groups()
assert "feature-team" in [g.id for g in groups]

# Verify recipient is group member
group = await client.get_group("feature-team")
assert "architect" in group.members
```

---

## Related Documentation

- [Agent Groups Guide](agent-groups-guide.md) - Multi-agent collaboration
- [ADR-025: Agent Groups Protocol](../.parac/roadmap/decisions.md#adr-025) - Architecture decision
- [Agent Groups Example](../content/examples/agents/23_agent_groups.py) - Complete example
- [Security Policy](../.parac/policies/SECURITY.md) - Security guidelines

---

**Status**: Experimental | **Version**: 1.1.0 | **Date**: 2026-01-10

