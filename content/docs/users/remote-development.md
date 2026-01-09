# Remote Development Guide

> **Phase 8.1: Basic SSH Transport (v1.3.0)**

This guide shows how to run Paracle on remote servers while editing code locally in your IDE.

## Overview

Paracle remote support enables:
- **SSH-based remote execution** - Run Paracle on remote servers
- **Automatic tunnel management** - Port forwarding with auto-reconnect
- **WebSocket MCP transport** - Better remote MCP connections
- **Multi-host management** - Connect to multiple remote instances

## Quick Start

### 1. Add a Remote

```bash
# Add remote configuration
paracle remote add production user@prod-server.com /opt/paracle \
    --tunnel 8000:8000 \
    --set-default

# Test connection
paracle remote test production
```

### 2. Execute Commands Remotely

```bash
# List agents on remote server
paracle agents list --remote production

# Run workflow remotely
paracle workflows run code_review --remote production

# Get remote status
paracle status --remote production
```

### 3. Use as Default

```bash
# Set default remote (all commands use it)
paracle remote set-default production

# Now all commands execute remotely by default
paracle agents list
paracle workflows run bugfix
```

## Configuration

### Remote Configuration File

Remote configs are stored in `.parac/config/remotes.yaml`:

```yaml
remotes:
  production:
    type: ssh
    host: user@prod-server.com
    workspace: /opt/paracle
    port: 22
    identity_file: ~/.ssh/id_rsa
    tunnels:
      - local: 8000
        remote: 8000
        description: "API server"

  staging:
    type: ssh
    host: user@staging.example.com
    workspace: /opt/paracle
    port: 2222  # Custom SSH port
    tunnels:
      - local: 8001
        remote: 8000
        description: "API server"
      - local: 8002
        remote: 8001
        description: "MCP WebSocket"

default: production
```

### SSH Key Setup

Paracle requires SSH key authentication (no password support):

```bash
# Generate SSH key if needed
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy to remote server
ssh-copy-id user@remote-server.com

# Test connection
ssh user@remote-server.com
```

## CLI Commands

### Remote Management

```bash
# List configured remotes
paracle remote list

# Add new remote
paracle remote add <name> <host> <workspace> [options]

# Remove remote
paracle remote remove <name>

# Test connection
paracle remote test <name>

# Set default remote
paracle remote set-default <name>
```

### Remote Execution

All Paracle commands support `--remote` flag:

```bash
# Agents
paracle agents list --remote production
paracle agents run coder --task "Fix bug" --remote production

# Workflows
paracle workflows list --remote staging
paracle workflows run code_review --remote staging

# Status and info
paracle status --remote production
paracle runs list --remote production

# Configuration
paracle config show --remote production
```

## Python API

### Basic SSH Transport

```python
import asyncio
from paracle_transport import RemoteConfig, SSHTransport
from paracle_transport.remote_config import TunnelConfig

async def main():
    # Configure remote
    config = RemoteConfig(
        name="production",
        host="user@prod.com",
        workspace="/opt/paracle",
        tunnels=[
            TunnelConfig(local=8000, remote=8000)
        ]
    )

    # Connect and execute
    async with SSHTransport(config) as transport:
        result = await transport.execute("paracle agents list")
        print(result["stdout"])

asyncio.run(main())
```

### Tunnel Manager with Auto-Reconnect

```python
from paracle_transport import TunnelManager

async def main():
    config = RemoteConfig(
        name="production",
        host="user@prod.com",
        workspace="/opt/paracle",
        tunnels=[TunnelConfig(local=8000, remote=8000)]
    )

    # Tunnel manager monitors health and auto-reconnects
    async with TunnelManager(
        config,
        health_check_interval=10,  # Check every 10 seconds
        auto_reconnect=True
    ) as manager:
        # Execute commands
        result = await manager.execute("paracle agents list")
        print(result["stdout"])

        # Tunnels auto-reconnect if they die
        # Keep running...
        await asyncio.sleep(3600)  # 1 hour

asyncio.run(main())
```

## WebSocket MCP (Remote Connections)

### Start WebSocket MCP Server

On remote server:

```bash
# Start WebSocket MCP server
paracle mcp serve --websocket --host 0.0.0.0 --port 8001

# With JWT authentication (recommended)
paracle mcp serve --websocket --host 0.0.0.0 --port 8001 --auth jwt
```

### Connect from Local Machine

```python
from paracle_mcp.transports import WebSocketTransport

async def main():
    # Connect to remote MCP server
    transport = WebSocketTransport(
        url="ws://remote-server.com:8001/mcp",
        auth_token="your-jwt-token"  # If using JWT auth
    )

    async with transport:
        # Send MCP request
        response = await transport.send_request({
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        })
        print(response)

asyncio.run(main())
```

### Configure IDE for Remote MCP

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "paracle-remote": {
      "command": "paracle",
      "args": ["mcp", "connect", "--remote", "production"],
      "env": {
        "PARACLE_AUTO_RECONNECT": "true"
      }
    }
  }
}
```

## Troubleshooting

### Connection Issues

```bash
# Test SSH connection manually
ssh user@remote-server.com

# Verify remote workspace
ssh user@remote-server.com "ls -la /opt/paracle/.parac"

# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa

# Verbose SSH debugging
ssh -vvv user@remote-server.com
```

### Tunnel Issues

```bash
# Check if port is already in use
netstat -an | grep 8000  # Windows
lsof -i :8000           # Linux/macOS

# Kill process using port
# Windows: taskkill /PID <pid> /F
# Linux/macOS: kill -9 <pid>
```

### Remote Execution Issues

```bash
# Check remote Paracle installation
ssh user@remote-server.com "paracle --version"

# Check remote workspace
ssh user@remote-server.com "cd /opt/paracle && paracle status"

# Check logs
ssh user@remote-server.com "tail -f /opt/paracle/.parac/memory/logs/agent_actions.log"
```

## Security Best Practices

1. **Use SSH Keys Only**
   - Never use password authentication
   - Use strong key algorithms (ed25519, rsa 4096+)
   - Protect private keys with passphrases

2. **Restrict SSH Access**
   ```bash
   # In ~/.ssh/authorized_keys on remote server
   from="192.168.1.100" ssh-ed25519 AAAAC3...
   ```

3. **Use JWT for WebSocket MCP**
   ```bash
   # Generate JWT token
   paracle auth generate-token --expires 24h
   ```

4. **Firewall Configuration**
   - Only open SSH port (22) - all traffic tunneled
   - No need to expose API ports (8000, 8001, etc.)
   - Use corporate VPN if required

5. **Monitor Access**
   ```bash
   # View remote access logs
   paracle logs show --type access --remote production
   ```

## Performance Considerations

- **Latency**: SSH adds ~50ms overhead vs local
- **Compression**: Enable SSH compression for better performance
  ```bash
  # In ~/.ssh/config
  Host prod-server.com
      Compression yes
      CompressionLevel 6
  ```
- **Connection Pooling**: Reuse SSH connections
  ```bash
  # In ~/.ssh/config
  Host *
      ControlMaster auto
      ControlPath ~/.ssh/sockets/%r@%h-%p
      ControlPersist 600
  ```

## Examples

See [examples/25_remote_development.py](../examples/25_remote_development.py) for complete examples.

## Next Steps

- **Phase 8.2**: Multi-host coordination and load balancing
- **Phase 8.3**: Browser-based remote IDE integration
- **Phase 8.4**: Kubernetes and cloud marketplace support

## Related Documentation

- [ADR-019: Remote SSH Support](../.parac/roadmap/adr/ADR-019-Remote-SSH-Support.md)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [SSH Configuration Best Practices](https://www.ssh.com/academy/ssh/config)

---

**Status**: Phase 8.1 Implemented (v1.3.0)
**Last Updated**: 2026-01-08
