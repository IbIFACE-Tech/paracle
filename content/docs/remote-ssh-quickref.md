# Remote SSH Native Support - Implementation Status

**Version**: v1.3.0 | **Status**: COMPLETE ✅ | **Date**: 2026-01-10

Quick reference for the implemented Remote SSH Native Support in Paracle.

---

## Implementation Status

### ✅ COMPLETE - All Components Implemented

| Component            | Status | Location                                             |
| -------------------- | ------ | ---------------------------------------------------- |
| SSH Transport Layer  | ✅ DONE | `packages/paracle_transport/ssh.py`                  |
| Remote Configuration | ✅ DONE | `packages/paracle_transport/remote_config.py`        |
| Tunnel Manager       | ✅ DONE | `packages/paracle_transport/tunnel_manager.py`       |
| Base Transport       | ✅ DONE | `packages/paracle_transport/base.py`                 |
| CLI Commands         | ✅ DONE | `packages/paracle_cli/commands/remote.py`            |
| Unit Tests           | ✅ DONE | `tests/test_transport.py`                            |
| Documentation        | ✅ DONE | `content/docs/users/remote-development.md`           |
| Examples             | ✅ DONE | `content/examples/advanced/25_remote_development.py` |
| Dependencies         | ✅ DONE | `pyproject.toml` (asyncssh, websockets)              |

---

## Quick Start

### 1. Install Transport Dependencies

```bash
pip install -e ".[transport]"
```

This installs:
- `asyncssh>=2.14.0` - SSH transport
- `websockets>=12.0` - WebSocket MCP transport

### 2. Add a Remote Server

```bash
# Add remote configuration
paracle remote add production user@prod-server.com /opt/paracle \
    --tunnel 8000:8000 \
    --set-default

# Test connection
paracle remote test production
```

### 3. Execute Commands Remotely

```bash
# List agents on remote server
paracle agents list --remote production

# Run workflow remotely
paracle workflows run code_review --remote production

# Get remote status
paracle status --remote production
```

---

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
```

---

## Configuration

Remotes are stored in `.parac/config/remotes.yaml`:

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

---

## Python API

### Basic SSH Transport

```python
import asyncio
from paracle_transport import RemoteConfig, SSHTransport
from paracle_transport.remote_config import TunnelConfig

async def main():
    # Configure remote connection
    config = RemoteConfig(
        name="production",
        host="user@prod-server.com",
        workspace="/opt/paracle",
        port=22,
        identity_file="~/.ssh/id_rsa",
        tunnels=[
            TunnelConfig(
                local=8000,
                remote=8000,
                description="API server",
            )
        ],
    )

    # Connect and execute commands
    async with SSHTransport(config) as transport:
        print(f"✓ Connected to {config.host}")

        # List agents
        result = await transport.execute("paracle agents list")
        print(result["stdout"])

        # Get project status
        result = await transport.execute("paracle status")
        print(result["stdout"])

asyncio.run(main())
```

### Tunnel Manager

```python
from paracle_transport import TunnelManager

async def with_tunnel_manager():
    config = RemoteConfig(...)

    async with TunnelManager(config) as manager:
        # Auto-connect SSH and establish tunnels
        print(f"✓ Tunnels established")

        # Get tunnel status
        status = await manager.status()
        print(f"Active tunnels: {len(status['tunnels'])}")

        # Reconnect if needed
        if not status['connected']:
            await manager.reconnect()
```

---

## Architecture

### Transport Layer Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Transport Layer                           │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │    Base      │  │     SSH      │  │     Tunnel     │   │
│  │  Transport   │→ │   Transport  │→ │    Manager     │   │
│  └──────────────┘  └──────────────┘  └────────────────┘   │
│         ↑                 ↑                   ↑             │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │   Remote     │  │ Connection   │  │Port Forwarding │   │
│  │   Config     │  │   Pool       │  │  Management    │   │
│  └──────────────┘  └──────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Features

- ✅ **SSH Key Authentication** - No password support (security)
- ✅ **Automatic Reconnection** - Resilient connection handling
- ✅ **Tunnel Management** - Port forwarding with health checks
- ✅ **Multi-host Support** - Connect to multiple remote instances
- ✅ **WebSocket Transport** - Better remote MCP connections
- ✅ **Connection Pooling** - Reuse SSH connections

---

## Workarounds (Before v1.3.0)

For users not ready to use native SSH support, these workarounds are documented:

### Method 1: VS Code Remote-SSH (Recommended)

```bash
# Install VS Code Remote-SSH extension
code --install-extension ms-vscode-remote.remote-ssh

# Connect to remote
# Ctrl+Shift+P → "Remote-SSH: Connect to Host"
```

### Method 2: Manual SSH Tunneling

```bash
# Start SSH tunnel
ssh -L 8000:localhost:8000 user@remote-server.com

# In another terminal, start Paracle API
paracle api serve

# Connect from local machine
export PARACLE_API_URL=http://localhost:8000
paracle agents list
```

### Method 3: Docker Deployment

```bash
# Build and deploy Docker container
docker build -t paracle-server .
docker run -d -p 8000:8000 paracle-server
```

---

## Testing

### Run Transport Tests

```bash
# All transport tests
pytest tests/test_transport.py -v

# Specific test classes
pytest tests/test_transport.py::TestRemoteConfig -v
pytest tests/test_transport.py::TestSSHTransport -v
pytest tests/test_transport.py::TestTunnelManager -v
```

### Manual Testing

```bash
# Test SSH connection
paracle remote test production

# Check tunnel status
paracle remote status production

# List all remotes
paracle remote list
```

---

## Dependencies

Required in `pyproject.toml`:

```toml
[project.optional-dependencies]
transport = [
    "asyncssh>=2.14.0",  # SSH transport for remote connections
    "websockets>=12.0",   # WebSocket MCP transport
]
```

Install with:

```bash
pip install -e ".[transport]"
```

---

## Known Limitations

1. **SSH Key Only** - No password authentication (by design for security)
2. **asyncssh Required** - Must install `transport` extra
3. **Connection Latency** - ~50ms overhead vs local execution
4. **No Multi-hop** - Direct SSH only (no proxy/bastion support yet)

---

## Roadmap (Future Phases)

- **Phase 8.2**: Multi-host coordination and load balancing
- **Phase 8.3**: Browser-based remote IDE integration
- **Phase 8.4**: Kubernetes and cloud marketplace support
- **Phase 9**: SSH ProxyJump and bastion host support

---

## Related Documentation

- [Full Remote Development Guide](../content/docs/users/remote-development.md) - Complete guide (371 lines)
- [Remote Development Example](../content/examples/advanced/25_remote_development.py) - Code examples (182 lines)
- [ADR-019: Remote SSH Support](../.parac/roadmap/adr/ADR-019-Remote-SSH-Support.md) - Architecture decision
- [SSH Best Practices](https://www.ssh.com/academy/ssh/config) - SSH configuration guide

---

## Summary

✅ **Remote SSH Native Support is COMPLETE in v1.3.0**

- 5 packages implemented (`ssh.py`, `remote_config.py`, `tunnel_manager.py`, `base.py`, `__init__.py`)
- CLI commands implemented (`paracle remote add/list/test/remove/set-default`)
- Full documentation (371 lines guide + 182 lines example)
- Unit tests (test_transport.py)
- Dependencies configured (`asyncssh`, `websockets`)

**No additional work needed** - Feature is production-ready! 🎉

---

**Status**: COMPLETE ✅ | **Version**: v1.3.0 | **Date**: 2026-01-10

