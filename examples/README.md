# Paracle Examples

This directory contains practical examples demonstrating how to use Paracle's features.

## ⭐ Featured Example: Agent Inheritance

**File**: [`real_world_inheritance.py`](real_world_inheritance.py)

Demonstrates Paracle's **unique agent inheritance feature** - not available in any other framework!

Build a hierarchy of specialized code reviewers:
- Base Reviewer → Python Specialist → FastAPI Expert → Security Auditor
- 4-level inheritance chain with tool/skill accumulation
- Property overrides and metadata merging

```bash
uv run python examples/real_world_inheritance.py
```

**Learn more**: [Agent Inheritance Documentation](../docs/agent-inheritance-example.md)

---

## Quick Start

All examples can be run using `uv`:

```bash
# From project root
uv run python examples/01_filesystem_tools.py
```

## Examples

### 1. Filesystem Tools (`01_filesystem_tools.py`)

Demonstrates file and directory operations:

- **read_file**: Read file contents with metadata
- **write_file**: Write content to files with auto-create directories
- **list_directory**: List directory contents (recursive option)
- **delete_file**: Delete files safely
- **Path restrictions**: Security through allowed paths

**Run**:
```bash
uv run python examples/01_filesystem_tools.py
```

**Key concepts**:
- Path-based security sandboxing
- Automatic parent directory creation
- File metadata (size, lines, encoding)
- Error handling patterns

---

### 2. HTTP Tools (`02_http_tools.py`)

Demonstrates HTTP client operations:

- **http_get**: GET requests with headers and params
- **http_post**: POST with JSON or form data
- **http_put**: PUT requests for updates
- **http_delete**: DELETE requests
- **Timeouts**: Custom timeout configuration

**Run**:
```bash
uv run python examples/02_http_tools.py
```

**Key concepts**:
- RESTful API interactions
- JSON auto-detection and parsing
- Query parameters and headers
- Timeout handling
- Real-world API examples (GitHub, JSONPlaceholder)

**Note**: Requires `httpx` package (already in project dependencies)

---

### 3. Shell Tools (`03_shell_tools.py`)

Demonstrates safe shell command execution:

- **run_command**: Execute shell commands safely
- **Security**: Blocked dangerous commands (rm, sudo, etc.)
- **Whitelists**: Command whitelisting for production
- **Timeouts**: Prevent hung processes
- **Stderr handling**: Capture both stdout and stderr

**Run**:
```bash
uv run python examples/03_shell_tools.py
```

**Key concepts**:
- Command blocklist (security)
- Command whitelist (production safety)
- Timeout enforcement
- Exit code handling
- Git and pytest integration

**Security notes**:
- Dangerous commands blocked by default
- Use whitelists in production
- Always validate command inputs

---

### 4. Agent with Tools (`04_agent_with_tools.py`)

Demonstrates building an agent that uses multiple tools together:

**Scenario**: Code analysis agent that:
1. Discovers Python files in a directory
2. Reads and analyzes source code
3. Runs test suite
4. Fetches external documentation
5. Generates comprehensive report

**Run**:
```bash
uv run python examples/04_agent_with_tools.py
```

**Key concepts**:
- Combining multiple tools in workflows
- Agent-based architecture
- Async/await patterns
- Report generation
- Real-world task automation

**Tools used**: list_directory, read_file, run_command, http_get, write_file

---

### 5. Tool Registry (`05_tool_registry.py`)

Advanced BuiltinToolRegistry usage:

- **Discovery**: List and inspect available tools
- **Categorization**: Tools organized by category
- **Security**: Configure permissions and restrictions
- **Dynamic selection**: Choose tools at runtime
- **Batch operations**: Execute multiple tools in parallel
- **Reconfiguration**: Update settings on the fly
- **Introspection**: Query tool metadata

**Run**:
```bash
uv run python examples/05_tool_registry.py
```

**Key concepts**:
- Centralized tool management
- Permission system
- Runtime configuration
- Tool metadata and introspection
- Error handling patterns
- Concurrent execution

---

### 6. Agent Skills (`06_agent_skills.py`)

Demonstrates the Agent Skills system (see existing example).

---

### 7. Human-in-the-Loop Approvals (`07_human_in_the_loop.py`)

Demonstrates Paracle's Human-in-the-Loop approval system for AI governance (ISO 42001):

- **Approval Gates**: Steps that require human approval before proceeding
- **Approval Manager**: Create, approve, reject, cancel approval requests
- **Workflow Integration**: Automatic pause/resume based on approval status
- **REST API**: Full API endpoints for approval management
- **Priority Levels**: LOW, MEDIUM, HIGH, CRITICAL
- **Timeout Handling**: Auto-reject or manual handling on timeout

**Scenario**: CI/CD deployment pipeline where:

1. AI analyzes code changes (automatic)
2. AI performs security review (automatic)
3. Human reviews and approves deployment (REQUIRES APPROVAL)

**Run**:
```bash
uv run python examples/07_human_in_the_loop.py
```

**Key concepts**:

- `requires_approval=True` on WorkflowStep
- `approval_config` for timeout, priority, approvers
- ApprovalManager for approval lifecycle
- ExecutionStatus.AWAITING_APPROVAL state
- API endpoints: `/approvals/pending`, `/approvals/{id}/approve`

**ISO 42001 Compliance**:

- Human oversight for critical AI decisions
- Audit trail of all approvals/rejections
- Configurable approval policies

---

### 8. Multi-Provider Support (`07_multi_provider.py`)

Demonstrates using multiple LLM providers (see existing example).

---

### 9. Sandbox Execution (`09_sandbox_execution.py`)

**NEW - Phase 5**: Docker-based isolated execution with resource limits:

- **SandboxManager**: Create and orchestrate sandboxes
- **Resource Limits**: CPU, memory, disk, timeout constraints
- **SandboxMonitor**: Real-time resource monitoring
- **Automatic Cleanup**: Context managers for resource safety
- **Statistics**: CPU/memory usage, network I/O tracking

**Run**:
```bash
uv run python examples/09_sandbox_execution.py
```

**Key concepts**:
- Isolated Docker containers for safe execution
- Resource limit enforcement
- Real-time monitoring and alerts
- Automatic cleanup on exit

---

### 10. Network Isolation (`10_network_isolation.py`)

**NEW - Phase 5**: Network isolation and security policies:

- **NetworkIsolator**: Create isolated Docker networks
- **Network Policies**: Control internet/intra-network access
- **Container Attachment**: Connect containers to networks
- **Port Control**: Allow/block specific ports
- **IP Blocking**: Block dangerous IP ranges

**Run**:
```bash
uv run python examples/10_network_isolation.py
```

**Key concepts**:
- Docker network creation and management
- Policy-based network access control
- Inter-container communication
- External access restrictions

---

### 11. Rollback on Failure (`11_rollback_on_failure.py`)

**NEW - Phase 5**: Automatic snapshot-based recovery:

- **RollbackManager**: Snapshot and restore filesystem state
- **Automatic Rollback**: Policy-triggered recovery on errors
- **Snapshot Management**: Retention policies, cleanup
- **Manual Rollback**: Restore to specific checkpoints
- **Tarball Strategy**: Compressed snapshots

**Run**:
```bash
uv run python examples/11_rollback_on_failure.py
```

**Key concepts**:
- Filesystem snapshot creation
- Automatic recovery on failure
- Snapshot retention policies
- Manual checkpoint restoration

---

### 12. Artifact Review (`12_artifact_review.py`)

**NEW - Phase 5**: Human-in-the-loop artifact approval:

- **ReviewManager**: Create and manage artifact reviews
- **Risk Assessment**: Automatic pattern-based risk detection
- **Approval Workflow**: Multi-reviewer approval process
- **Auto-Approval**: Low-risk artifacts bypass review
- **Review Statistics**: Track approval metrics

**Run**:
```bash
uv run python examples/12_artifact_review.py
```

**Key concepts**:
- Pattern-based risk assessment
- Multi-approval workflow
- Auto-approval for low-risk changes
- Rejection and timeout handling

---

### 13. Phase 5 Integration (`13_phase5_integration.py`)

**NEW - Phase 5**: Complete safety stack integration:

- **Full Stack**: Sandbox + Network + Rollback + Review
- **Safety Pipeline**: Comprehensive execution protection
- **Error Recovery**: Automatic rollback on failures
- **Approval Gates**: Review workflow integration
- **Statistics**: End-to-end metrics

**Run**:
```bash
uv run python examples/13_phase5_integration.py
```

**Key concepts**:
- Complete Phase 5 feature integration
- Multi-layer security and safety
- Coordinated resource management
- Production-ready patterns

---

## Example Output

### Filesystem Tools
```
==============================================================
Paracle Filesystem Tools Example
==============================================================

1. Writing files...
✓ Created file: /path/to/hello.txt
  Size: 32 bytes
  Lines: 2
✓ Created config: /path/to/config.yaml
✓ Created nested file: /path/to/data/output.json

2. Listing directory contents...
✓ Found 3 items in /path/to/temp_example
  📄 hello.txt (32 bytes)
  📄 config.yaml (98 bytes)
  📁 data
...
```

### HTTP Tools
```
==============================================================
Paracle HTTP Tools Example
==============================================================

1. GET request - Fetch user data from API...
✓ Status: 200
  URL: https://jsonplaceholder.typicode.com/users/1
  User: Leanne Graham
  Email: Sincere@april.biz
  City: Gwenborough
...
```

### Shell Tools
```
==============================================================
Paracle Shell Command Tool Example
==============================================================

1. Running simple commands...
✓ Command executed successfully
  Output: Hello from Paracle
  Return code: 0

6. Security - Blocked commands...
Attempting 'rm -rf /': success=False
  ✓ Blocked! Error: Command 'rm' is blocked for security
...
```

## Common Patterns

### Basic Tool Usage

```python
from paracle_tools import read_file

result = await read_file.execute(path="file.txt")

if result.success:
    print(result.output['content'])
else:
    print(f"Error: {result.error}")
```

### Using the Registry

```python
from paracle_tools import BuiltinToolRegistry

# Create registry with security config
registry = BuiltinToolRegistry(
    filesystem_paths=["./data"],
    allowed_commands=["git", "pytest"]
)

# Execute tool by name
result = await registry.execute_tool(
    "read_file",
    path="data/config.yaml"
)
```

### Error Handling

```python
result = await some_tool.execute(...)

if result.success:
    # Happy path
    data = result.output
else:
    # Error handling
    error_msg = result.error
    error_context = result.metadata
```

### Parallel Execution

```python
import asyncio

# Execute multiple tools concurrently
results = await asyncio.gather(
    read_file.execute(path="file1.txt"),
    read_file.execute(path="file2.txt"),
    http_get.execute(url="https://api.example.com")
)
```

## Security Best Practices

### 1. Filesystem Security

```python
# ✅ DO: Restrict filesystem access
tool = ReadFileTool(allowed_paths=["/app/data", "/tmp"])

# ❌ DON'T: Allow unrestricted access in production
tool = ReadFileTool()  # No restrictions
```

### 2. Command Security

```python
# ✅ DO: Use explicit whitelists
tool = RunCommandTool(allowed_commands=["git", "pytest"])

# ❌ DON'T: Rely only on blocklist
tool = RunCommandTool()  # Default blocklist only
```

### 3. Timeout Configuration

```python
# ✅ DO: Set appropriate timeouts
registry = BuiltinToolRegistry(
    http_timeout=10.0,
    command_timeout=30.0
)

# ❌ DON'T: Use very long timeouts
registry = BuiltinToolRegistry(
    http_timeout=3600.0  # 1 hour - too long!
)
```

### 4. Input Validation

```python
# ✅ DO: Validate inputs before executing
def safe_read_file(user_input: str):
    path = Path(user_input).resolve()
    if not path.is_file():
        raise ValueError("Not a file")
    return await read_file.execute(path=str(path))

# ❌ DON'T: Pass user input directly
result = await read_file.execute(path=user_input)
```

## Next Steps

- **Read the docs**: See [docs/builtin-tools.md](../docs/builtin-tools.md) for full API reference
- **Build an agent**: Combine tools to create your own agents
- **Explore MCP tools**: Check out Model Context Protocol integration
- **Run tests**: See how tools are tested in `tests/unit/test_builtin_tools_*.py`

## Troubleshooting

### httpx not installed

```
Error: httpx is not installed. Install with: pip install httpx
```

**Fix**:
```bash
uv add httpx
```

### Permission denied

```
Error: Access denied: /etc/passwd is not in allowed paths
```

**Fix**: Check your allowed_paths configuration or use a different path

### Command not allowed

```
Error: Command 'python' is not in allowed commands
```

**Fix**: Add the command to allowed_commands list or use a different command

### Timeout

```
Error: Command timed out after 30.0 seconds
```

**Fix**: Increase timeout or optimize the command

## Contributing

To add a new example:

1. Create `examples/0X_example_name.py`
2. Follow existing structure (imports, main function, docstring)
3. Add clear comments and error handling
4. Update this README
5. Test the example: `uv run python examples/0X_example_name.py`

## License

See [LICENSE](../LICENSE) file in the project root.
