# Architecture Decision Records (ADR)

This document captures key architectural decisions made during Paracle development.

## Format

Each decision follows this structure:

- **Date**: When the decision was made
- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Context**: Why this decision was needed
- **Decision**: What was decided
- **Consequences**: Impact of the decision

---

## ADR-017: Strategic Direction - Developer Experience & Community Focus

**Date**: 2026-01-06
**Status**: Accepted
**Deciders**: PM Agent, Core Team

### Context

After completing Phase 5 (Execution Safety & Isolation), a comprehensive strategic assessment was conducted to evaluate Paracle's positioning and future direction. The assessment identified:

**Validated Strengths:**
- Meta approach (dogfooding - using Paracle to build Paracle)
- Strong governance & traceability (.parac/ as source of truth, ADRs)
- Production-ready architecture (hexagonal, modular monolith, 15+ packages)
- Unique features (agent inheritance, 14+ LLM providers, MCP native, sandbox execution)
- Quality metrics (771 tests, 97.2% pass, 87.5% coverage, ISO 42001 path)

**Critical Findings:**
1. **Complexity vs Accessibility** - Governance model is thorough but heavy for small projects
2. **Learning Curve** - Many concepts (agents, workflows, tools, inheritance, MCP), dense documentation
3. **Performance at Scale** - Focus on correctness (appropriate), need optimization plan
4. **Community & Ecosystem** - Early stage (v0.0.1), framework ready but community nascent

**Competitive Positioning:**
- vs LangChain: Smaller community BUT better governance, agent inheritance, production safety
- vs LlamaIndex: Different focus BUT multi-framework support, agent composition
- vs AutoGen: No Microsoft backing BUT simpler model, better isolation, YAML-first

**Key Insight:** Paracle has **strong potential** to become a leading multi-agent framework. Foundation is solid. **Challenge: Balance power with accessibility.**

### Decision

**Strategic Direction for v0.1.0-v1.0.0:** Focus on **Developer Experience (DX) + Community Growth + Performance**, maintaining production readiness and governance strengths.

**Three-Phase Roadmap:**

**Phase 6 (Weeks 21-24): Developer Experience**
- **Priority:** HIGH - Critical for adoption
- **Goal:** Reduce learning curve by ~50%
- **Deliverables:**
  1. Quick Start Mode (`paracle init --lite`) - Minimal .parac/ for prototyping
  2. Interactive Tutorial (`paracle tutorial`) - Built-in step-by-step guide
  3. Example Gallery - 10+ real-world, production-ready examples
  4. Project Templates - Small/Medium/Enterprise templates
  5. Video Guides - 4-5 screen recordings for visual learners

**Phase 7 (Weeks 25-28): Community & Growth**
- **Priority:** CRITICAL - Drives adoption
- **Goal:** Build vibrant ecosystem with network effects
- **Deliverables:**
  1. Community Templates Marketplace - User-contributed agents/workflows
  2. Plugin System - Extensibility SDK for community
  3. Discord Community - Real-time support (500+ members target)
  4. Monthly Webinars - Live demos, Q&A, community showcase
  5. Blog Series - 11 technical posts (Getting Started, Advanced, Case Studies)

**Phase 8 (Weeks 29-32): Performance & Scale**
- **Priority:** MEDIUM - Important for scale
- **Goal:** 2-3x performance improvement
- **Deliverables:**
  1. Response Caching - Redis/Valkey for LLM responses (30-50% cost reduction)
  2. Connection Pooling - HTTP and DB connection reuse
  3. Benchmarking Suite - Performance baselines, regression detection
  4. Performance Documentation - Tuning guide, optimization patterns

**Key Design Principles:**
1. **Progressive Disclosure** - Start simple, add governance as needed
2. **Lite Mode** - Minimal barrier to entry, graduate to full mode
3. **Community-Driven** - Enable ecosystem contributions
4. **Performance Without Compromise** - Optimize while maintaining safety

### Implementation

**Immediate (Post-Phase 5):**
- ✅ Document strategic feedback (.parac/memory/knowledge/strategic_feedback_jan2026.md)
- ✅ Create action plan (.parac/memory/knowledge/strategic_action_plan.md)
- ✅ Add strategic questions Q13-Q16 to open_questions.md
- ⏳ Update roadmap.yaml with Phase 6-8 details
- ⏳ Create Phase 6 detailed specifications
- ⏳ Prototype lite mode (`paracle init --lite`)

**Resource Requirements:**
- Personnel: ~36 developer-weeks over 12 weeks (1.5 FTE average)
- Budget: ~$115K (development + video + community tools)
- Timeline: 12 weeks (3 months) for Phases 6-8

**Success Metrics (6 Months):**
- Adoption: 1,000+ GitHub stars, 500+ weekly active users
- Community: 500+ Discord members, 20+ PRs/month
- Quality: >90% test coverage, <500ms p95 API latency, >70% tutorial completion
- Business: 20+ examples, 50+ community templates, 50+ production deployments

### Consequences

#### Positive

✅ **Clear Strategic Direction** - Phases 6-8 roadmap with concrete deliverables
✅ **Balanced Approach** - Maintains production readiness while improving accessibility
✅ **Differentiation Strategy** - Agent inheritance + BYO philosophy + production safety
✅ **Community Focus** - Network effects through templates, plugins, engagement
✅ **Resource Clarity** - Known costs, timeline, success metrics
✅ **Measurable** - Clear KPIs for adoption, quality, business success

#### Negative

⚠️ **Resource Commitment** - 36 developer-weeks, $115K over 3 months
⚠️ **Dual Focus** - Must maintain both power (enterprise) and simplicity (beginners)
⚠️ **Community Risk** - Hard to bootstrap, requires sustained engagement
⚠️ **Delayed Features** - Other features deferred to focus on DX/community

#### Mitigations

- **Lite Mode Exception** - Enterprise users keep full governance, beginners start lite
- **Phased Approach** - Phase 6 first (highest ROI), can adjust 7-8 based on feedback
- **Seed Community** - Core team creates initial examples/templates/content
- **Prioritization Framework** - Defer non-critical features to maintain focus

### Roadmap Integration

**Phase 6 (Developer Experience)** - Q13, Q14 from open_questions.md
- Week 21-22: Quick start mode + interactive tutorial
- Week 22-23: Example gallery (10 examples)
- Week 23-24: Project templates + video guides

**Phase 7 (Community & Growth)** - Q16 from open_questions.md
- Week 25-26: Templates marketplace + plugin system
- Week 26-27: Discord community + blog series
- Week 27-28: Monthly webinars

**Phase 8 (Performance & Scale)** - Q15 from open_questions.md
- Week 29-30: Response caching + connection pooling
- Week 30-31: Benchmarking suite
- Week 31-32: Performance documentation

### Related Decisions

- ADR-016: Pre-Flight Checklist - Ensures quality while reducing barrier
- ADR-013: API-First CLI - Supports programmatic access for community
- ADR-015: Persistence Strategy - Foundation for performance optimization

### References

- Strategic Assessment: .parac/memory/knowledge/strategic_feedback_jan2026.md
- Action Plan: .parac/memory/knowledge/strategic_action_plan.md
- Open Questions: Q13 (Complexity), Q14 (Learning), Q15 (Performance), Q16 (Community)
- Assessment Summary: .parac/memory/summaries/strategic_assessment_response_2026-01-06.md

---

## ADR-016: Mandatory Pre-Flight Checklist for AI Agents

**Date**: 2026-01-04
**Status**: Accepted
**Deciders**: Core Team

### Context

AI agents were implementing tasks without validating them against the roadmap, leading to:
- Off-track work not aligned with current phase priorities
- Scope creep without explicit decision-making
- No systematic check for task priority, phase alignment, or dependencies
- Wasted effort on features not planned for current phase

User feedback: "why the roadmap are not automatically checked when I ask you to implement task?"

### Decision

Implement **mandatory 9-step Pre-Flight Checklist** that ALL AI agents MUST complete before any implementation task:

1. Read GOVERNANCE.md (governance rules)
2. Check current_state.yaml (current phase & progress)
3. Consult roadmap.yaml (priorities & deliverables)
4. Check open_questions.md (blockers)
5. **VALIDATE with STOP conditions**:
   - Is task in roadmap? ❌ → Ask user to add/defer/justify
   - Is task in current phase? ❌ → Ask user to move/defer/justify
   - Is task priority P0/P1? 🟡 → Warn user if P2
   - Are dependencies complete? ❌ → Ask user to complete/proceed/block
6. Adopt agent persona from specs
7. Check policies (CODE_STYLE, TESTING, SECURITY)
8. Log action to agent_actions.log (after implementation)
9. Update current_state.yaml if milestone reached

**Critical enforcement**: If task NOT in roadmap, AI agent MUST **STOP and ask user** to either:
- a) Add to current phase roadmap
- b) Create ADR for decision/scope change
- c) Plan for future phase implementation
- d) Provide explicit justification to proceed

### Implementation

- Created `.parac/PRE_FLIGHT_CHECKLIST.md` (4-minute checklist)
- Updated UNIVERSAL_AI_INSTRUCTIONS.md with mandatory section
- Updated all IDE instructions:
  - .github/copilot-instructions.md
  - .cursorrules (Cursor)
  - .parac/integrations/ide/.clinerules (Cline)
  - .parac/integrations/ide/.windsurfrules (Windsurf)
  - .parac/integrations/ide/CLAUDE.md (Claude Code)
  - .parac/integrations/ide/copilot-instructions.md

### Consequences

**Positive:**
- ✅ Prevents off-roadmap work (saves hours of wasted effort)
- ✅ Forces explicit decision-making for scope changes
- ✅ Ensures task priority and phase alignment
- ✅ Creates audit trail for all implementation decisions
- ✅ Enforces governance rules systematically
- ✅ Prompts ADR creation for architectural changes
- ✅ 4-minute investment prevents 4-hour rework

**Negative:**
- ⚠️ Adds 4-minute overhead to each task (acceptable tradeoff)
- ⚠️ Requires AI agents to interrupt user flow with questions (by design)
- ⚠️ May slow down exploration/prototyping (exception cases documented)

**Mitigation:**
- Exception cases documented (emergency fixes, exploration, user override)
- Checklist optimized for speed (4 minutes target)
- Steps 1-4 can be parallelized by reading multiple files
- Benefits (prevent wrong work) far outweigh costs (4-minute validation)

### Related Decisions

- Related to ADR-013 (API-First CLI) - systematic enforcement pattern
- Related to roadmap governance rules in GOVERNANCE.md
- Supports dogfooding principle (Paracle develops Paracle using .parac/)

---

## ADR-001: Python as Primary Language

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Need to choose primary implementation language for Paracle framework. Considerations include:

- AI/ML ecosystem maturity
- Developer community size
- Library availability
- Performance requirements

### Decision

Use Python 3.10+ as primary language.

### Consequences

**Positive:**

- Rich AI/ML ecosystem (OpenAI, Anthropic, LangChain, etc.)
- Large developer community
- Rapid prototyping and iteration
- Excellent type hints support (Pydantic)

**Negative:**

- Performance limitations for CPU-intensive tasks
- GIL for multi-threading
- Requires async/await for concurrency

**Mitigation:**

- Use async/await extensively
- Optimize hot paths
- Consider Rust extensions for performance-critical parts in future

---

## ADR-002: Modular Monolith Architecture

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Need to balance between:

- Simplicity for early adopters (monolith)
- Flexibility for future scaling (microservices)
- Development velocity

### Decision

Implement as modular monolith with clear package boundaries (17 packages).

### Consequences

**Positive:**

- Single deployment unit (simple)
- Clear module boundaries
- Easy to develop and test
- Can evolve to microservices later

**Negative:**

- Single point of failure initially
- Requires discipline for module boundaries

**Migration Path:**
Each package can be extracted to microservice if needed.

---

## ADR-003: Agent Inheritance System

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

---

## ADR-010: API Middlewares Stack

**Date**: 2026-01-04
**Status**: Accepted
**Deciders**: Architect Agent
**Resolves**: Q10 (Open Questions)

### Context

Need to define complete middleware stack for FastAPI-based REST API. Requirements include:

- **Security**: Protection against common web vulnerabilities (OWASP Top 10)
- **Rate Limiting**: DoS/abuse prevention
- **Observability**: Request tracing and logging
- **Compliance**: ISO 42001 audit trail requirements
- **Performance**: Minimal overhead, support for async operations
- **Flexibility**: Easy to configure per environment (dev/staging/prod)

Current implementation already includes some middlewares but lacks formal documentation and standardization.

### Decision

Implement a **layered middleware stack** with the following components in strict order (first added = last executed on response):

#### 1. Security Headers Middleware (Outermost)
**Package**: `paracle_api.security.headers.SecurityHeadersMiddleware`
**Purpose**: OWASP security headers
**Headers**:
- `Strict-Transport-Security`: Force HTTPS (production only)
- `Content-Security-Policy`: Prevent XSS/injection attacks
- `X-Content-Type-Options: nosniff`: Prevent MIME sniffing
- `X-Frame-Options: DENY`: Prevent clickjacking
- `X-XSS-Protection`: Legacy XSS protection
- `Referrer-Policy`: Control referrer information
- `Permissions-Policy`: Restrict browser features

#### 2. CORS Middleware
**Package**: `fastapi.middleware.cors.CORSMiddleware`
**Purpose**: Cross-Origin Resource Sharing
**Configuration**:
- `allow_origins`: Configurable via `SecurityConfig.cors_allowed_origins`
- `allow_credentials`: Controlled per environment
- `allow_methods`: GET, POST, PUT, DELETE, PATCH, OPTIONS
- `allow_headers`: Standard + custom headers
- `expose_headers`: Rate limit headers

#### 3. Request Logging Middleware
**Package**: `paracle_core.logging.create_request_logging_middleware()`
**Purpose**: Observability and audit trail
**Features**:
- Correlation ID generation (X-Correlation-ID)
- Request/response logging with structured format
- Timing metrics (request duration)
- ISO 42001 compliance (audit trail)
- Error context capture

#### 4. Rate Limiting (Dependency Injection)
**Package**: `paracle_api.security.rate_limit`
**Purpose**: DoS/abuse prevention
**Implementation**: Dependency injection (not global middleware)
**Features**:
- Per-client IP tracking
- Sliding window algorithm
- Burst protection (20 req/window)
- Automatic blocking (5 min on abuse)
- Rate limit headers (X-RateLimit-*)

**Why not global middleware?**
- Selective application (e.g., exempt health checks)
- Per-endpoint rate limits (different tiers)
- Better error handling
- Easier testing

#### 5. Authentication (Dependency Injection)
**Package**: `paracle_api.security.auth`
**Purpose**: JWT-based authentication
**Implementation**: OAuth2 with Password Bearer tokens
**Why not middleware?**
- Selective protection (public vs protected endpoints)
- Better integration with FastAPI dependency system
- Clear authorization boundaries

### Middleware Order Rationale

```python
# Order matters - first added = last executed on response
app.add_middleware(SecurityHeadersMiddleware)     # 1. Outermost (last)
app.add_middleware(CORSMiddleware)                # 2. Before logging
app.add_middleware(RequestLoggingMiddleware)      # 3. Innermost (first)

# Not middlewares (dependency injection)
# - Rate limiting: @router.get(..., dependencies=[Depends(check_rate_limit)])
# - Authentication: @router.get(..., dependencies=[Depends(get_current_user)])
```

**Request Flow** (inbound):
```
Client → CORS → Logging (start) → Rate Limit (DI) → Auth (DI) → Endpoint
```

**Response Flow** (outbound):
```
Endpoint → Auth (DI) → Rate Limit (DI) → Logging (end) → CORS → Security Headers → Client
```

### Configuration

All middleware settings centralized in `SecurityConfig`:

```python
class SecurityConfig:
    # CORS
    cors_allowed_origins: list[str]
    cors_allow_credentials: bool

    # Rate Limiting
    rate_limit_enabled: bool
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Security Headers
    hsts_enabled: bool (production only)
    csp_enabled: bool

    # Environment
    environment: Literal["development", "staging", "production"]
```

### Consequences

**Positive:**
- **Security**: Comprehensive protection against OWASP Top 10
- **Observability**: Full request tracing with correlation IDs
- **Compliance**: ISO 42001 audit trail ready
- **Performance**: Async-native, minimal overhead (<5ms per request)
- **Flexibility**: Environment-specific configuration
- **Maintainability**: Clear separation of concerns

**Negative:**
- **Complexity**: Multiple middleware layers increase cognitive load
- **Debugging**: Middleware order issues can be hard to diagnose
- **Testing**: Requires integration tests for full stack

**Mitigation:**
- Comprehensive documentation (this ADR)
- Middleware unit tests for each layer
- Integration tests for full stack
- Logging at each middleware layer for debugging

### Future Enhancements

**v0.5.0+:**
- Redis-based rate limiting for distributed deployments
- Request ID propagation to background tasks
- Compression middleware (gzip)
- Circuit breaker middleware
- OpenTelemetry tracing middleware

**v0.7.0+:**
- Advanced security: WAF integration
- Adaptive rate limiting (ML-based)
- Request signing/verification

### References

- OWASP Security Headers: https://owasp.org/www-project-secure-headers/
- FastAPI Middleware: https://fastapi.tiangolo.com/advanced/middleware/
- RFC 7807 Problem Details: https://tools.ietf.org/html/rfc7807
- ISO 42001:2023 AI Management System

---

## ADR-004: Tool Calling Interface - Hybrid Built-in + MCP

**Date**: 2026-01-04
**Status**: Accepted
**Deciders**: Architect Agent
**Resolves**: Q4 (Open Questions)

### Context

Agents need a flexible, secure, and extensible way to call tools. Requirements include:

- **Core Functionality**: Essential tools (filesystem, HTTP, shell) must work without external dependencies
- **Extensibility**: Support for custom/community tools via standard protocol
- **Security**: Sandboxing, permission model, input validation
- **Simplicity**: Easy to use for both end-users and developers
- **Standards Compliance**: Leverage emerging standards (MCP)
- **Performance**: Minimal overhead, async-native

Three main options considered:
1. **MCP-Only**: Pure Model Context Protocol implementation
2. **Built-in Only**: Custom tool system, no external protocol
3. **Hybrid**: Built-in tools + MCP integration

### Decision

Implement a **Hybrid Built-in + MCP architecture** with three tiers:

#### Tier 1: Built-in Tools (Core Package)
**Package**: `paracle_tools.builtin`
**Purpose**: Essential tools with zero external dependencies

**Tools Included** (9 total):
- Filesystem: `read_file`, `write_file`, `list_directory`, `delete_file`
- HTTP: `http_get`, `http_post`, `http_put`, `http_delete`
- Shell: `run_command` (with security controls)

**Architecture**:
```python
# Base protocol for all tools
class Tool(Protocol):
    name: str
    description: str
    parameters: dict[str, Any]

    async def execute(self, **kwargs) -> ToolResult

# Result type
class ToolResult(BaseModel):
    success: bool
    output: Any
    error: str | None
    metadata: dict[str, Any]
```

**Security Model**:
- **Filesystem tools**: Require explicit `allowed_paths` list (no defaults)
- **Shell tool**: Require explicit `allowed_commands` list (no defaults)
- **HTTP tools**: URL validation, timeout limits, size limits
- **Permission system**: Each tool declares required permissions
- **Sandboxing**: Factory functions create properly configured instances

**Example**:
```python
from paracle_tools import create_sandboxed_filesystem_tools

# Secure by default - requires explicit configuration
tools = create_sandboxed_filesystem_tools(
    allowed_paths=["/workspace/myproject"],
    readonly=False
)

# No default instances - all require configuration
```

#### Tier 2: MCP Integration (Protocol Adapter)
**Package**: `paracle_mcp`
**Purpose**: Discover and call Model Context Protocol tools

**Components**:
- `MCPClient`: HTTP client for MCP servers
- `MCPToolRegistry`: Discovery and caching of MCP tools
- Adapter pattern: Converts MCP tools to Paracle `Tool` protocol

**Features**:
- Auto-discovery of MCP servers
- Tool caching for performance
- Error handling and retries
- TLS verification for security
- Timeout management

**Example**:
```python
from paracle_mcp import MCPClient, MCPToolRegistry

# Connect to MCP server
client = MCPClient(server_url="https://mcp.example.com")
await client.connect()

# Discover tools
tools = await client.list_tools()

# Register MCP tools
registry = MCPToolRegistry()
await registry.register_server(client)

# Use MCP tool through standard interface
tool = registry.get_tool("mcp:custom_tool")
result = await tool.execute(param="value")
```

#### Tier 3: Custom Tools (User Extensions)
**Approach**: Implement `Tool` protocol
**Purpose**: Allow users to create custom tools

**Example**:
```python
from paracle_tools import BaseTool, ToolResult

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="Does something custom",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            }
        )

    async def _execute(self, input: str) -> Any:
        # Custom logic
        return {"result": input.upper()}

# Register with agent
agent.register_tool(MyCustomTool())
```

### Tool Registry Architecture

**Unified Tool Registry**:
```python
class ToolRegistry:
    """Central registry for all tools (built-in + MCP + custom)."""

    def register_builtin(self, tool: Tool) -> None: ...
    def register_mcp_server(self, client: MCPClient) -> None: ...
    def register_custom(self, tool: Tool) -> None: ...

    def get_tool(self, name: str) -> Tool | None: ...
    def list_tools(self, filter: str | None = None) -> list[Tool]: ...

    def execute_tool(self, name: str, **kwargs) -> ToolResult: ...
```

**Tool Naming Convention**:
- Built-in: `read_file`, `http_get` (no prefix)
- MCP: `mcp:server_name.tool_name` (prefix with `mcp:`)
- Custom: `custom:tool_name` (prefix with `custom:`)

### Security Considerations

**Built-in Tools**:
- ✅ No default instances (require explicit configuration)
- ✅ Sandboxing via `allowed_paths` / `allowed_commands`
- ✅ Input validation with Pydantic
- ✅ Permission system
- ✅ Audit logging

**MCP Tools**:
- ✅ TLS verification required (production)
- ✅ Server authentication (future: JWT/API keys)
- ✅ Request timeout limits
- ✅ Response size limits
- ✅ Audit trail for external calls

**Custom Tools**:
- ✅ Must implement security checks
- ✅ Inherit from `BaseTool` for standard protections
- ✅ Permission declaration required

### Integration with Agents

**Agent Specification**:
```yaml
# Agent can declare tools in spec
name: code-reviewer
model: gpt-4
tools:
  - read_file
  - write_file
  - mcp:github.create_pr
  - custom:static_analyzer
```

**Runtime Registration**:
```python
from paracle_domain import AgentSpec, AgentFactory
from paracle_tools import create_sandboxed_filesystem_tools

# Create agent with tools
spec = AgentSpec(
    name="code-reviewer",
    model="gpt-4",
    tools=["read_file", "write_file"]
)

# Register configured tools
agent = AgentFactory.create(spec)
filesystem_tools = create_sandboxed_filesystem_tools(
    allowed_paths=["/workspace"]
)
for tool in filesystem_tools:
    agent.register_tool(tool)
```

### Consequences

**Positive:**
- **Zero Dependencies**: Built-in tools work out of the box
- **Extensibility**: MCP support for community tools
- **Security**: Sandboxing and permissions by default
- **Standards**: MCP compliance for interoperability
- **Simplicity**: Single `Tool` protocol for all types
- **Performance**: Built-in tools are fast (no network calls)
- **Flexibility**: Users can choose built-in, MCP, or custom

**Negative:**
- **Complexity**: Multiple tool systems to maintain
- **Testing**: Need tests for built-in, MCP, and integration
- **Documentation**: More comprehensive docs needed
- **MCP Spec Changes**: Need to track MCP protocol evolution

**Mitigation:**
- Abstract common logic in `BaseTool`
- Comprehensive test suite for each tier
- Clear documentation with examples
- Version MCP protocol support

### Future Enhancements

**v0.5.0:**
- Tool marketplace (discover community tools)
- Tool versioning and updates
- Performance metrics per tool
- Tool usage analytics

**v0.7.0:**
- Advanced permissions model (RBAC for tools)
- Tool composition (chain tools together)
- Tool sandboxing with containers
- Tool rate limiting

**v0.9.0:**
- AI-powered tool discovery
- Automatic tool parameter inference
- Tool recommendation engine

### Migration Notes

**Breaking Change** (v0.0.1 → v0.1.0):
- Default tool instances removed for security
- Must use factory functions:
  ```python
  # OLD (insecure, REMOVED):
  from paracle_tools import read_file

  # NEW (secure, required):
  from paracle_tools import create_sandboxed_filesystem_tools
  tools = create_sandboxed_filesystem_tools(
      allowed_paths=["/workspace"]
  )
  ```

### References

- Model Context Protocol: https://modelcontextprotocol.io/
- Tool Security Audit: [security-audit-report.md](../docs/security-audit-report.md)
- Built-in Tools Guide: [builtin-tools.md](../docs/builtin-tools.md)
- OWASP API Security Top 10

---

## ADR-011: ISO 42001 Compliance Strategy

**Date**: 2026-01-04
**Status**: Accepted
**Deciders**: Architect Agent
**Resolves**: Q11 (Open Questions)

### Context

ISO 42001:2023 is the first international standard for AI Management Systems. Paracle must comply for enterprise adoption. Requirements include:

**ISO 42001 Core Requirements**:
- **6.1.3**: Risk treatment and audit trail
- **8.2**: Operational planning and control evidence
- **9.1**: Monitoring and measurement records
- **9.2**: Internal audit evidence
- **10.1**: Nonconformity and corrective action tracking
- **Annex A**: Comprehensive controls for AI systems

**Compliance Goals**:
- **Transparency**: All AI decisions traceable
- **Accountability**: Clear actor attribution
- **Auditability**: Comprehensive audit trail
- **Traceability**: End-to-end request tracking
- **Data Governance**: Data lifecycle management
- **Risk Management**: Continuous risk assessment

### Decision

Implement a **layered compliance architecture** with progressive enhancement across versions.

#### Phase 1: Foundation (v0.0.1 - CURRENT)

**Audit Logging System**
**Package**: `paracle_core.logging.audit`
**Status**: ✅ Implemented

**Features**:
- Immutable audit events (`AuditEvent` model)
- Structured logging with correlation IDs
- 10 audit categories (AI decisions, access, data, compliance)
- 5 severity levels (info → critical)
- File-based audit trail (append-only)
- JSON format for machine readability

**Audit Categories**:
```python
# AI System Events
AI_DECISION            # AI-made decisions
AI_OUTPUT             # AI-generated outputs
AI_TRAINING           # Model training events

# Agent Events
AGENT_CREATED/STARTED/COMPLETED/FAILED

# Workflow Events
WORKFLOW_STARTED/COMPLETED/FAILED/ROLLBACK

# Access Events
ACCESS_LOGIN/LOGOUT/DENIED/GRANTED

# Data Events
DATA_READ/WRITE/DELETE/EXPORT

# Configuration Events
CONFIG_CHANGED/POLICY_CHANGED/PERMISSION_CHANGED

# Compliance Events
APPROVAL_REQUESTED/GRANTED/DENIED
RISK_ASSESSED
INCIDENT_REPORTED

# System Events
SYSTEM_STARTUP/SHUTDOWN/ERROR
```

**Event Structure**:
```python
class AuditEvent(BaseModel):
    # Identification
    event_id: str                    # Unique ID
    timestamp: datetime              # UTC timestamp
    correlation_id: str | None       # Request tracing

    # Classification
    category: AuditCategory
    action: str
    outcome: AuditOutcome            # success, failure, denied
    severity: AuditSeverity          # info → critical

    # Actor (Who)
    actor: str                       # user, agent, system
    actor_type: str                  # user/agent/service/system
    actor_ip: str | None            # IP address

    # Resource (What)
    resource: str                    # Affected resource
    resource_type: str | None

    # Changes (How)
    old_value: Any | None           # Before
    new_value: Any | None           # After

    # Context (Why)
    reason: str | None
    evidence: dict | None           # Supporting data

    # Compliance
    policy_reference: str | None    # Applicable policy
    approval_reference: str | None  # Approval ID
```

**Request Tracing**
**Package**: `paracle_core.logging.context`
**Status**: ✅ Implemented

**Features**:
- Correlation ID generation (X-Correlation-ID)
- Context propagation across services
- Request/response logging with timing
- Error context capture
- Middleware integration

**Security Features**
**Package**: `paracle_api.security`
**Status**: ✅ Implemented

**Features**:
- JWT authentication with audit logging
- Rate limiting with abuse detection
- Security headers (OWASP compliance)
- Input validation (Pydantic)
- Permission-based access control

**Tool Security**
**Package**: `paracle_tools.builtin`
**Status**: ✅ Implemented

**Features**:
- Sandboxed filesystem operations
- Command whitelisting for shell tools
- Audit logging of all tool executions
- Permission checks before execution

#### Phase 2: Enhanced Governance (v0.5.0 - Q2 2026)

**Deliverables**:

1. **Policy Engine**
   - Package: `paracle_governance` (new)
   - Define approval workflows
   - Automated policy enforcement
   - Policy violation detection
   - Compliance reporting

2. **Risk Assessment Engine**
   - Package: `paracle_risk` (new)
   - Automated risk scoring for agents
   - Risk-based approval thresholds
   - Risk mitigation tracking
   - Continuous risk monitoring

3. **Data Governance**
   - Data classification (public, internal, confidential, restricted)
   - Data lineage tracking
   - PII detection and handling
   - Data retention policies
   - GDPR/CCPA compliance

4. **Enhanced Audit Storage**
   - SQLite-based audit database
   - Full-text search capabilities
   - Audit log retention policies
   - Automated compliance reports
   - Tamper-evident logging (hash chains)

#### Phase 3: Advanced Compliance (v0.7.0 - Q4 2026)

**Deliverables**:

1. **Automated Compliance Testing**
   - Continuous compliance validation
   - Automated policy testing
   - Compliance dashboard
   - Alert system for violations

2. **AI Explainability**
   - Decision explanation generation
   - Feature importance tracking
   - Model interpretability tools
   - Audit trail for AI decisions

3. **Bias Detection & Mitigation**
   - Fairness metrics
   - Bias testing framework
   - Mitigation strategies
   - Ongoing monitoring

4. **External Audit Support**
   - Compliance report generation
   - Evidence collection automation
   - Audit trail export (SIEM integration)
   - Third-party auditor access

#### Phase 4: Enterprise Compliance (v0.9.0 - Q2 2027)

**Deliverables**:

1. **Multi-Tenant Compliance**
   - Tenant-specific policies
   - Isolated audit trails
   - Cross-tenant compliance reporting

2. **Regulatory Compliance Packs**
   - GDPR compliance pack
   - HIPAA compliance pack
   - SOC 2 compliance pack
   - Industry-specific packs

3. **Advanced Risk Management**
   - ML-powered risk prediction
   - Automated incident response
   - Risk quantification
   - Board-level reporting

### Implementation Roadmap

| Version | Focus      | Delivery | ISO 42001 Coverage                    |
| ------- | ---------- | -------- | ------------------------------------- |
| v0.0.1  | Foundation | ✅ Done   | ~40% (Audit trail, logging)           |
| v0.5.0  | Governance | Q2 2026  | ~65% (Policies, risk assessment)      |
| v0.7.0  | Advanced   | Q4 2026  | ~85% (Explainability, bias detection) |
| v0.9.0  | Enterprise | Q2 2027  | ~95% (Full compliance, certifiable)   |

### Audit Trail Design

**Storage Strategy**:

**v0.0.1**: File-based (NDJSON)
- Location: `.parac/logs/audit.log`
- Format: Newline-delimited JSON
- Rotation: Daily (7-day retention)
- Backup: Manual export

**v0.5.0**: SQLite database
- Location: `.parac/audit/audit.db`
- Schema: Normalized tables
- Retention: Configurable (default: 90 days)
- Query: Full-text search
- Export: JSON, CSV, SIEM formats

**v0.9.0**: Distributed (optional)
- PostgreSQL/MongoDB for scale
- Real-time streaming to SIEM
- Long-term archival (S3/Azure Blob)
- Encryption at rest

**Retention Policy**:
```yaml
audit_retention:
  critical_events: 7_years    # ISO 42001 requirement
  high_severity: 3_years
  medium_severity: 1_year
  low_severity: 90_days
  info_events: 30_days
```

### Compliance Checkpoints

**Every Release**:
- [ ] Audit log review (no gaps)
- [ ] Security scan (OWASP Top 10)
- [ ] Permission model review
- [ ] Documentation updates

**Quarterly (v0.5.0+)**:
- [ ] Internal compliance audit
- [ ] Risk assessment review
- [ ] Policy effectiveness review
- [ ] Training data review

**Annually (v0.9.0+)**:
- [ ] External audit preparation
- [ ] ISO 42001 self-assessment
- [ ] Certification readiness review
- [ ] Compliance report publication

### Consequences

**Positive:**
- ✅ **Foundation Built**: Audit system ready for v0.0.1
- ✅ **Progressive Enhancement**: Incremental compliance approach
- ✅ **Clear Roadmap**: Phased implementation over 18 months
- ✅ **Standards-Based**: ISO 42001 compliance from start
- ✅ **Enterprise-Ready**: Path to full certification (v0.9.0)
- ✅ **Competitive Advantage**: Few AI frameworks have this

**Negative:**
- ⚠️ **Complexity**: Compliance adds engineering overhead
- ⚠️ **Performance**: Audit logging has minimal overhead (~2-5ms)
- ⚠️ **Storage**: Audit trails require disk space
- ⚠️ **Maintenance**: Requires ongoing compliance monitoring

**Mitigation:**
- Async audit logging (non-blocking)
- Configurable verbosity levels
- Automated log rotation and archival
- Compliance automation tools (v0.5.0+)

### Monitoring & Metrics

**v0.0.1 Metrics** (Already Tracked):
- Audit events per hour
- Failed access attempts
- Tool execution audit coverage
- Correlation ID propagation rate

**v0.5.0 Metrics** (Planned):
- Policy violation rate
- Risk score distribution
- Approval processing time
- Compliance score per agent

**v0.9.0 Metrics** (Future):
- ISO 42001 compliance percentage
- Audit readiness score
- Incident response time
- Training effectiveness

### Documentation Requirements

**User-Facing**:
- [ ] Compliance overview guide
- [ ] Audit log interpretation
- [ ] Policy configuration examples
- [ ] Risk assessment guide

**Internal**:
- [ ] Compliance architecture doc
- [ ] Audit system design doc
- [ ] Testing procedures
- [ ] Incident response playbook

### References

- ISO/IEC 42001:2023 AI Management System
- NIST AI Risk Management Framework
- EU AI Act (High-Risk AI Systems)
- OWASP Top 10 for LLM Applications
- SOC 2 Trust Services Criteria
- GDPR Article 22 (Automated Decision-Making)

### Success Criteria

**v0.0.1** (Current):
- ✅ 100% of API calls have correlation IDs
- ✅ All agent executions logged to audit trail
- ✅ All tool executions logged with actor
- ✅ Authentication events audited

**v0.5.0** (Q2 2026):
- [ ] 100% of policy violations detected
- [ ] Risk assessment for all agent creations
- [ ] Automated compliance reports generated
- [ ] Zero audit log gaps

**v0.9.0** (Q2 2027):
- [ ] Pass external ISO 42001 audit
- [ ] 95%+ compliance score
- [ ] Certification-ready
- [ ] Industry benchmark compliance

---

## ADR-003: Agent Inheritance System (continued)

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Agents often share common configurations (prompts, tools, models). Need mechanism for reusability without duplication.

### Decision

Implement functional inheritance system for agents:

- Agents can extend other agents
- Child agents inherit parent's config
- Override mechanism for specialization
- Validation of inheritance chain

### Consequences

**Positive:**

- DRY principle for agent configuration
- Easy specialization of agents
- Reduced configuration duplication
- Unique feature vs other frameworks

**Negative:**

- Added complexity in agent resolution
- Potential for deep inheritance chains

**Mitigation:**

- Limit inheritance depth (max 5 levels)
- Clear documentation and validation

---

## ADR-004: API-First Design

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Framework must be accessible via multiple interfaces (CLI, SDK, API, UI).

### Decision

Design API-first with FastAPI, then build CLI/SDK/UI on top of API.

### Consequences

**Positive:**

- Clear contract (OpenAPI)
- Easy integration
- Multiple client options
- Testable via HTTP

**Negative:**

- Additional layer of abstraction
- Network overhead for local usage

**Mitigation:**

- Provide SDK that can bypass API for local use
- Optimize API performance

---

## ADR-005: Multi-Provider Abstraction

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Users want freedom to choose LLM providers (OpenAI, Anthropic, Google, Local).

### Decision

Create provider abstraction layer with:

- Common interface for all providers
- Provider registry
- Runtime provider selection
- Bring Your Own Key (BYO)

### Consequences

**Positive:**

- Provider flexibility
- No vendor lock-in
- Easy to add new providers
- Cost optimization for users

**Negative:**

- Maintenance burden (multiple SDKs)
- Feature parity challenges

**Mitigation:**

- Focus on common features first
- Clear provider capability matrix

---

## ADR-006: Event-Driven Architecture

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Need audit trail, observability, and async processing.

### Decision

Implement event bus with:

- Append-only event log (NDJSON)
- Async event handlers
- Event replay capability
- Rollback support via snapshots

### Consequences

**Positive:**

- Complete audit trail
- Debugging and replay
- Async processing
- Rollback capability

**Negative:**

- Added complexity
- Storage requirements

**Mitigation:**

- Event retention policies
- Optional event storage

---

## ADR-007: MCP (Model Context Protocol) Support

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Tool ecosystem fragmentation. Need standard protocol for tool integration.

### Decision

Support MCP as primary tool protocol, alongside internal tools.

### Consequences

**Positive:**

- Interoperability with MCP ecosystem
- Standard tool interface
- Community tools
- Future-proof

**Negative:**

- Additional protocol to maintain
- MCP ecosystem still emerging

**Mitigation:**

- Also support internal tools
- Hybrid approach

---

## ADR-008: .parac Workspace Structure

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Projects need:

- Configuration management
- Memory and context
- Run history and rollback
- Policy enforcement

### Decision

Create `.parac/` workspace structure as local project configuration and state.

### Consequences

**Positive:**

- Clear project structure
- Version-controlled configuration (optional)
- Local state management
- Policy-first approach

**Negative:**

- Learning curve for structure
- Additional files to manage

**Mitigation:**

- Excellent documentation
- CLI commands to manage .parac
- Templates and examples

---

## ADR-009: .parac/ Governance in Framework

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

The `.parac/` workspace needs to stay synchronized with project reality. Initial implementation used manual Python scripts in `.parac/hooks/`, but this approach has limitations:

- Scripts must be called manually
- Logic duplicated for each project
- No integration with framework lifecycle
- Users must maintain their own sync logic

### Decision

Move `.parac/` governance logic into the framework (`packages/`):

1. **`paracle_core/parac/`** - Core governance logic:
   - State synchronization
   - Validation
   - YAML parsing and updates

2. **`paracle_cli/commands/parac.py`** - CLI commands:
   - `paracle parac status` - Show current state
   - `paracle parac sync` - Synchronize with project
   - `paracle parac validate` - Validate consistency
   - `paracle parac session start` - Start work session
   - `paracle parac session end` - End session with updates

3. **Git hooks** (optional, installed via `paracle init`):
   - pre-commit: validate .parac/
   - post-commit: sync state

4. **User hooks** - Custom hooks in `.parac/hooks/` called by framework

### Consequences

**Positive:**

- Single implementation, reusable across all projects
- Integrated with CLI and framework lifecycle
- Automatic synchronization options
- Consistent behavior for all users
- Framework can evolve governance logic

**Negative:**

- More code in framework to maintain
- Users depend on framework for governance

**Migration:**

- Existing `.parac/hooks/` scripts remain as prototypes
- Framework commands replace manual script calls
- User custom hooks still supported via config

### Implementation Order

1. `paracle_core/parac/` - Core logic (Phase 1)
2. `paracle_cli/commands/parac.py` - CLI commands (Phase 1)
3. Git hooks integration (Phase 2)
4. `paracle_governance/` - Full governance package (v0.7.0)

---

## Future Decisions

### Under Consideration

- [ ] TypeScript SDK for web integration
- [ ] gRPC API alongside REST
- [ ] Plugin system architecture
- [ ] Multi-tenancy support
- [ ] Distributed tracing (OpenTelemetry)

### Deferred to Later Versions

- Microservices architecture (post v1.0)
- Kubernetes operators (post v1.0)
- Enterprise features (SSO, RBAC) (post v0.5)
- UI/Dashboard (post v0.3)

---

## ADR-008: Agent Discovery System for IDE/AI Assistant Integration

**Date**: 2025-12-25
**Status**: Proposed
**Deciders**: Architect Agent, PM Agent
**Consulted**: Coder Agent

### Context

Currently, integrating PARACLE agents with IDEs/AI assistants requires manual configuration for each tool:
- **Copilot**: Duplicate agent specs in `.github/copilot-instructions.md`
- **Cursor**: Custom `.cursorrules` file with embedded specs
- **Claude**: Separate `.claude-instructions.md` with specs
- **Cline, Windsurf**: Similar duplication pattern

**Problems**:
1. **Duplication**: Agent specs must be copied to each IDE configuration
2. **Maintenance**: Updating one agent requires updating 5+ files
3. **No Discovery**: IDEs cannot auto-discover agents from `.parac/`
4. **Not Scalable**: Adding new IDEs requires more duplication
5. **Framework Limitation**: This should be solved at framework level, not user level

### Decision

Implement a **standardized agent discovery system** in the PARACLE framework with 3 components:

#### 1. Agent Manifest (`.parac/manifest.yaml`)

Auto-generated metadata file that IDEs can read:

```yaml
schema_version: "1.0"
workspace:
  name: "paracle-lite"
  version: "0.0.1"
  parac_version: "0.0.1"

agents:
  - id: "pm"
    name: "PM Agent"
    role: "Project Manager"
    spec_file: ".parac/agents/specs/pm.md"
    capabilities: ["planning", "tracking", "coordination"]

  - id: "architect"
    name: "Architect Agent"
    role: "System Architect"
    spec_file: ".parac/agents/specs/architect.md"
    capabilities: ["design", "decisions", "documentation"]

  - id: "coder"
    name: "Coder Agent"
    role: "Developer"
    spec_file: ".parac/agents/specs/coder.md"
    capabilities: ["implementation", "refactoring", "bugfix"]
```

#### 2. CLI Introspection Commands

```bash
# List all agents
paracle agents list
paracle agents list --format=json

# Get specific agent spec
paracle agents get pm
paracle agents get coder --format=markdown

# Export all agents
paracle agents export --format=json > agents.json
```

#### 3. IDE Instructions Generator

```bash
# Generate instructions for specific IDE
paracle generate instructions --ide=copilot
paracle generate instructions --ide=cursor --output=.cursorrules
paracle generate instructions --ide=claude

# Generate for all supported IDEs
paracle generate instructions --all

# Regenerate when agents change
paracle generate instructions --ide=copilot --force
```

**Generated files**:
- `.github/copilot-instructions.md` (GitHub Copilot)
- `.cursorrules` (Cursor AI)
- `.claude-instructions.md` (Claude Projects)
- `.clinerules` (Cline)
- `.windsurfrules` (Windsurf)

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                 PARACLE FRAMEWORK                   │
│                   (packages/)                       │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │  paracle_core/parac/                     │     │
│  │    • agent_discovery.py                  │     │
│  │    • manifest_generator.py               │     │
│  │    • instruction_generator.py            │     │
│  └──────────────────────────────────────────┘     │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │  paracle_cli/commands/                   │     │
│  │    • agents.py (list, get, export)       │     │
│  │    • generate.py (instructions)          │     │
│  └──────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
                      ↓ generates
┌─────────────────────────────────────────────────────┐
│                .parac/ WORKSPACE                    │
│                                                     │
│  • manifest.yaml (auto-generated)                  │
│  • agents/specs/*.md (user-defined)                │
└─────────────────────────────────────────────────────┘
                      ↓ reads
┌─────────────────────────────────────────────────────┐
│            IDE INSTRUCTION FILES                    │
│            (auto-generated)                         │
│                                                     │
│  • .github/copilot-instructions.md                 │
│  • .cursorrules                                     │
│  • .claude-instructions.md                          │
│  • etc.                                             │
└─────────────────────────────────────────────────────┘
```

### Implementation Plan

#### Phase 1: Core Discovery System

**Files to create**:
- `packages/paracle_core/parac/agent_discovery.py`
- `packages/paracle_core/parac/manifest_generator.py`
- `packages/paracle_cli/commands/agents.py`

**Functionality**:
- Scan `.parac/agents/specs/` directory
- Parse agent markdown files
- Generate `manifest.yaml`
- Expose via CLI: `paracle agents list/get/export`

#### Phase 2: Instructions Generator

**Files to create**:
- `packages/paracle_core/parac/instruction_generator.py`
- `packages/paracle_cli/commands/generate.py`
- `templates/ide-instructions/*.jinja2` (templates for each IDE)

**Functionality**:
- Read manifest and agent specs
- Use Jinja2 templates for each IDE
- Generate IDE-specific instruction files
- Support: Copilot, Cursor, Claude, Cline, Windsurf

#### Phase 3: Auto-Sync

**Functionality**:
- Watch `.parac/agents/specs/` for changes
- Auto-regenerate `manifest.yaml`
- Optional: Auto-regenerate IDE instructions
- Integrate with `paracle parac sync`

### Consequences

#### Positive

✅ **Single Source of Truth**: Agents defined once in `.parac/agents/specs/`
✅ **Zero Duplication**: IDE files auto-generated from specs
✅ **Easy Maintenance**: Update one agent → regenerate all IDE files
✅ **IDE Agnostic**: Add new IDEs with just a template
✅ **Framework-Level**: Solved at the right abstraction level
✅ **Discoverable**: `manifest.yaml` is machine-readable
✅ **Extensible**: New IDEs just need a Jinja2 template

#### Negative

⚠️ **Build Step**: Users must run `paracle generate instructions` after agent changes
⚠️ **Template Maintenance**: Each IDE needs its own template
⚠️ **Complexity**: Adds new framework components

#### Mitigations

- Auto-generate on `paracle parac sync`
- Provide git pre-commit hook
- Clear error messages if files out of sync
- Well-documented templates for community contributions

### Alternatives Considered

#### Alternative 1: MCP (Model Context Protocol) Server

**Pros**: Real-time, no file generation, IDE-agnostic protocol
**Cons**: Only supported by some IDEs, requires running server
**Decision**: Keep as future enhancement, not MVP

#### Alternative 2: HTTP API

**Pros**: RESTful, language-agnostic
**Cons**: Requires running service, overkill for local files
**Decision**: Not needed, CLI is sufficient

#### Alternative 3: Keep Manual Configuration

**Pros**: No framework changes
**Cons**: Doesn't scale, high maintenance, defeats PARAC purpose
**Decision**: Rejected - this is the problem we're solving

### References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [GitHub Copilot Instructions](https://docs.github.com/en/copilot)
- [Cursor AI Rules](https://cursor.sh/docs)
- PARACLE Agent Specifications (`.parac/agents/specs/`)

### Related ADRs

- ADR-001: Python as Primary Language
- ADR-002: Hexagonal Architecture
- ADR-009: API First Architecture (Supersedes partial implementation)

---

## ADR-009: API First Architecture for Agent Discovery

**Date**: 2025-12-25
**Status**: Accepted
**Deciders**: Architect Agent

### Context

After implementing ADR-008 (Agent Discovery System), we discovered that the CLI commands (`paracle agents`) were directly calling `AgentDiscovery` and `ManifestGenerator` services, bypassing the API layer. This violated the project's "API First" principle stated in the architecture.

**Problem**: CLI should consume the REST API, not call services directly.

**Principle**: PARACLE is API First - every feature must be exposed via REST API before being consumed by clients (CLI, Web, IDE plugins).

### Decision

Refactor agent discovery to follow API First architecture:

1. **Create REST API endpoints** in `packages/paracle_api/routers/agents.py`:
   - `GET /agents` - List all agents
   - `GET /agents/{agent_id}` - Get agent metadata
   - `GET /agents/{agent_id}/spec` - Get agent specification
   - `GET /agents/manifest` - Get manifest as JSON
   - `POST /agents/manifest` - Generate and write manifest.yaml

2. **Create Pydantic schemas** in `packages/paracle_api/schemas/agents.py`:
   - `AgentMetadataResponse`
   - `AgentListResponse`
   - `AgentSpecResponse`
   - `ManifestResponse`
   - `ManifestWriteResponse`

3. **Refactor CLI** in `packages/paracle_cli/commands/agents.py`:
   - Replace direct service calls with HTTP requests via `httpx`
   - Add proper error handling for API connectivity
   - Keep Rich formatting for beautiful terminal output

4. **Add httpx dependency** to runtime dependencies (moved from dev-only)

5. **Create comprehensive tests** in `tests/unit/test_api_agents.py`

6. **Update documentation** in `docs/agent-discovery.md` with API usage

### Architecture

```
┌─────────────────────┐
│   REST API          │
│  (FastAPI)          │
│                     │
│  GET /agents        │  ← Single source of truth
│  GET /agents/{id}   │  ← All clients consume this
│  POST /manifest     │
└─────────┬───────────┘
          │
  ┌───────┼───────┐
  │       │       │
┌─▼──┐ ┌─▼──┐ ┌─▼──┐
│CLI │ │Web │ │IDE │
└────┘ └────┘ └────┘
```

**Benefits**:
- ✅ Consistency: One implementation shared by all clients
- ✅ Testability: API tested independently
- ✅ Extensibility: Easy to add new clients (web app, IDE plugins)
- ✅ Documentation: OpenAPI/Swagger automatic
- ✅ Separation: Clear boundaries between layers

### Consequences

#### Positive

✅ **Architectural Correctness**: Respects API First principle
✅ **Multi-Client Support**: Web, CLI, IDE plugins all use same API
✅ **Better Testing**: API can be tested independently
✅ **Auto-Documentation**: FastAPI generates OpenAPI/Swagger docs
✅ **Future-Proof**: Easy to add GraphQL, gRPC, WebSocket layers

#### Negative

⚠️ **Runtime Dependency**: CLI requires API to be running
⚠️ **Network Overhead**: HTTP calls add latency vs direct calls
⚠️ **Complexity**: More components (API server + CLI client)

#### Mitigations

- **For local use**: API can run embedded in CLI (future enhancement)
- **For development**: `uvicorn --reload` makes API startup instant
- **For production**: API runs as service, CLI is thin client
- **Error handling**: Clear messages when API is unreachable

### Implementation Details

**Files Created**:
- `packages/paracle_api/schemas/agents.py` (80 lines)
- `packages/paracle_api/routers/agents.py` (230 lines)
- `tests/unit/test_api_agents.py` (250 lines)

**Files Modified**:
- `packages/paracle_api/main.py` - Register agents router
- `packages/paracle_api/routers/__init__.py` - Export agents_router
- `packages/paracle_cli/commands/agents.py` - Refactored to use httpx
- `pyproject.toml` - Added httpx to runtime dependencies
- `docs/agent-discovery.md` - Added API documentation section

**Test Coverage**:
- ✅ GET /agents (list all)
- ✅ GET /agents/{id} (get one)
- ✅ GET /agents/{id}/spec (get spec content)
- ✅ GET /agents/manifest (manifest as JSON)
- ✅ POST /agents/manifest (write manifest.yaml)
- ✅ Error handling (404, 409, 500)

### Alternatives Considered

#### Alternative 1: Keep Direct Service Calls

**Pros**: Simpler, no API needed, faster
**Cons**: Violates API First principle, no web/IDE support, duplicates logic
**Decision**: Rejected - goes against core architectural principle

#### Alternative 2: Dual Mode (Direct + API)

**Pros**: Flexibility, works offline
**Cons**: Two code paths to maintain, inconsistency risk
**Decision**: Rejected - adds complexity without clear benefit

#### Alternative 3: Embedded API Mode

**Pros**: Best of both worlds, CLI can run API internally
**Cons**: Complex, requires process management
**Decision**: Consider for future enhancement (Phase 2)

### Migration Path

**For existing users**:
1. Start API server: `uvicorn paracle_api.main:app --reload`
2. Use CLI as before: `paracle agents list`

**For new users**:
- Quick start guide shows API + CLI setup
- Docker Compose file includes both services

### Success Metrics

✅ All CLI commands work via API
✅ API endpoints have 100% test coverage
✅ Documentation includes API usage examples
✅ OpenAPI docs accessible at `/docs`

### References

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [API First Design](https://swagger.io/resources/articles/adopting-an-api-first-approach/)
- [RESTful API Design](https://restfulapi.net/)
- ADR-008: Agent Discovery System

### Related ADRs

- ADR-002: Hexagonal Architecture
- ADR-008: Agent Discovery System

---

## ADR-010: CLI Simplification - Remove `parac` Sub-command

**Date**: 2025-12-25
**Status**: Accepted
**Deciders**: Core Team

### Context

The CLI had a nested command structure where governance commands were under a `parac` sub-group:

```bash
# Old structure (verbose)
paracle parac status
paracle parac sync --manifest
paracle parac validate
paracle parac session start
```

This structure was redundant since:
1. `paracle` is the Paracle framework CLI
2. `.parac/` governance is a core feature, not a separate module
3. Users should interact with the framework naturally without extra nesting

### Decision

Promote governance commands to the root level:

```bash
# New structure (clean)
paracle status        # Show current project state
paracle sync          # Synchronize with project reality
paracle validate      # Validate workspace consistency
paracle session start # Start work session
paracle init          # Initialize new .parac/ workspace
```

**Backward Compatibility**: Keep the `parac` sub-group as hidden (deprecated) for existing scripts:

```bash
# Still works (deprecated, hidden from help)
paracle parac status  # → redirects to paracle status
```

### Implementation

1. **Commands promoted to root level**:
   - `status` - Show project state
   - `sync` - Synchronize with reality
   - `validate` - Validate consistency
   - `session` - Session management group
   - `init` - Initialize workspace (new)

2. **New command added**:
   - `paracle init [path]` - Creates `.parac/` structure

3. **Legacy support**:
   - `parac` group kept but hidden (`hidden=True`)
   - Same commands accessible via old path

4. **Hooks updated**:
   - All hooks now use `paracle sync` instead of `paracle parac sync`

### Consequences

#### Positive

✅ **Cleaner UX**: Less typing, more intuitive
✅ **Framework Identity**: Commands feel native to Paracle
✅ **Discoverability**: Root commands visible in `--help`
✅ **Backward Compatible**: Old scripts still work

#### Negative

⚠️ **Migration**: Users must update scripts (optional, old syntax works)
⚠️ **Documentation**: Must update all docs

#### Files Modified

- `packages/paracle_cli/commands/parac.py` - Restructured as standalone commands
- `packages/paracle_cli/main.py` - Register commands at root level
- `tests/unit/test_parac_cli.py` - Updated tests for new API + legacy tests
- `.git/hooks/pre-commit.ps1` - Use new command syntax
- `.parac/hooks/install-hooks.ps1` - Use new command syntax
- `.parac/hooks/install-hooks.sh` - Use new command syntax
- `.parac/hooks/pre-commit` - Use new command syntax
- `.parac/hooks/README.md` - Use new command syntax

### CLI Reference

| Old Command                   | New Command             | Description          |
| ----------------------------- | ----------------------- | -------------------- |
| `paracle parac status`        | `paracle status`        | Show project state   |
| `paracle parac sync`          | `paracle sync`          | Sync with reality    |
| `paracle parac validate`      | `paracle validate`      | Validate workspace   |
| `paracle parac session start` | `paracle session start` | Start session        |
| `paracle parac session end`   | `paracle session end`   | End session          |
| (none)                        | `paracle init`          | Initialize workspace |

### Related ADRs

- ADR-009: .parac/ Governance in Framework

---

## ADR-011: LLM Provider Package Naming Convention

**Date**: 2025-12-31
**Status**: Accepted
**Deciders**: Core Team
**Phase**: Phase 2 - Multi-Provider & Multi-Framework

### Context

During Phase 2 implementation, we needed to decide on package naming for:
1. LLM provider abstractions (OpenAI, Anthropic, Google, Ollama)
2. Framework adapters (MSAF, LangChain, LlamaIndex)

**Conflicting Documentation:**
- `.roadmap/PHASE2_MULTI_PROVIDER.md` proposed: `paracle_llm/` and `paracle_frameworks/`
- `docs/architecture.md` (line 103) specified: `paracle_providers/` and `paracle_adapters/`
- Existing empty packages: `paracle_providers/` and `paracle_adapters/` already created

### Decision

**Use `paracle_providers` and `paracle_adapters`** (as per architecture.md).

**Rationale:**
1. **Consistency**: Aligns with existing architecture documentation
2. **Semantic Clarity**:
   - `providers` → LLM API providers (external services)
   - `adapters` → Framework adapters (hexagonal architecture pattern)
3. **Avoid Confusion**: Prevents potential conflict with future `paracle_llm` package for LLM-specific utilities
4. **Existing Structure**: Packages already exist in codebase

### Implementation

**Package Structure:**

```
packages/
├── paracle_providers/          # LLM Provider Abstraction
│   ├── base.py                 # LLMProvider protocol
│   ├── registry.py             # Provider registry
│   ├── exceptions.py           # Provider exceptions
│   ├── auto_register.py        # Auto-registration
│   ├── openai_provider.py      # OpenAI (GPT-4, GPT-3.5)
│   ├── anthropic_provider.py   # Anthropic (Claude 3.5, 3)
│   ├── google_provider.py      # Google (Gemini Pro)
│   └── ollama_provider.py      # Ollama (Local models)
│
└── paracle_adapters/           # Framework Adapters
    ├── base.py                 # FrameworkAdapter protocol
    ├── msaf_adapter.py         # Microsoft Agent Framework
    ├── langchain_adapter.py    # LangChain
    └── llamaindex_adapter.py   # LlamaIndex (optional)
```

**Provider Interface:**
- Protocol-based (`typing.Protocol`) for maximum flexibility
- Async-first design (all operations async)
- Streaming support as first-class citizen
- Graceful degradation (optional dependencies)

**Auto-Registration:**
- Providers register on import via `auto_register.py`
- Missing dependencies don't break imports
- Registry pattern for discovery

### Consequences

**Positive:**
- ✅ Clear separation: providers (external APIs) vs adapters (frameworks)
- ✅ Follows hexagonal architecture principles
- ✅ Consistent with existing documentation
- ✅ Extensible via Protocol (users can add providers)
- ✅ Graceful handling of missing dependencies

**Negative:**
- ⚠️ Requires updating `.roadmap/PHASE2_MULTI_PROVIDER.md` documentation
- ⚠️ Different from initial Phase 2 spec (but better aligned with architecture)

**Neutral:**
- Package naming is internal implementation detail
- Users interact via public API, not package names

### Metrics (Implementation)

**Phase 2 Progress (as of 2025-12-31):**
- ✅ Base protocol implemented (ChatMessage, LLMConfig, LLMResponse, StreamChunk)
- ✅ Provider registry with auto-registration
- ✅ 4 providers implemented (OpenAI, Anthropic, Google, Ollama)
- ✅ 30 unit tests (100% passing)
- ✅ UTC-aware datetime (no deprecation warnings)
- 📊 Test count: 255 total (+30 from Phase 1)

**Files Created:**
- `paracle_providers/base.py` (203 lines)
- `paracle_providers/registry.py` (115 lines)
- `paracle_providers/exceptions.py` (68 lines)
- `paracle_providers/auto_register.py` (49 lines)
- `paracle_providers/openai_provider.py` (289 lines)
- `paracle_providers/anthropic_provider.py` (242 lines)
- `paracle_providers/google_provider.py` (183 lines)
- `paracle_providers/ollama_provider.py` (248 lines)
- `tests/unit/test_provider_base.py` (154 lines)
- `tests/unit/test_provider_registry.py` (147 lines)

### Related ADRs

- ADR-002: Modular Monolith Architecture
- ADR-005: Hexagonal Architecture (Ports & Adapters)

### Next Steps

1. ✅ Implement framework adapters in `paracle_adapters/`
2. ✅ Implement MCP support in `paracle_tools/`
3. ✅ Update AgentFactory to use providers
4. ✅ Update Phase 2 documentation
5. ✅ Add integration tests with mocked API calls

---

## ADR-012: Agent Factory with Provider Integration

**Date**: 2025-12-31
**Status**: Accepted
**Deciders**: Core Team

### Context

Phase 2 requires integrating the provider registry with agent creation. Need to design how agents are instantiated with:
- Inheritance resolution (from Phase 1)
- Provider selection and instantiation (from Phase 2)
- Clean separation of concerns
- Flexibility for different use cases

Key requirements:
1. Agent creation should resolve inheritance before provider selection
2. Provider instantiation should be optional (for testing, dry-run, etc.)
3. Factory should provide utilities (validation, preview, chain inspection)
4. Temperature inheritance should handle default values correctly

### Decision

**Implement AgentFactory in `paracle_domain/factory.py`** with two creation modes:

1. **`create(spec)`**: Creates agent with resolved inheritance (no provider)
2. **`create_with_provider(spec, config)`**: Creates agent + provider instance

**Temperature Inheritance Fix:**
- Modified `_merge_specs()` in `inheritance.py` to detect default values
- Child temperature only overrides parent if != 0.7 (default)
- Same logic applied to all scalar fields with defaults

**Factory Features:**
- `validate_spec()`: Check inheritance without creating agent
- `get_inheritance_chain()`: Inspect inheritance chain
- `preview_resolved_spec()`: See final merged spec
- Metadata attachment: `_inheritance_chain`, `_inheritance_depth`, `_inheritance_warnings`

### Implementation

**Factory Constructor:**
```python
AgentFactory(
    spec_provider: Callable[[str], AgentSpec | None],  # Get parent specs
    provider_registry: Any | None = None,              # Optional provider registry
    max_inheritance_depth: int = 5,
    warn_depth: int = 3,
)
```

**Basic Usage:**
```python
# Without provider (testing, validation)
factory = AgentFactory(repository.get_spec)
agent = factory.create(spec)

# With provider (production)
factory = AgentFactory(repository.get_spec, ProviderRegistry)
agent, provider = factory.create_with_provider(spec, {"api_key": "..."})
```

**Temperature Inheritance Logic:**
```python
# Before (incorrect):
temperature = leaf.temperature  # Always uses child's default (0.7)

# After (correct):
merged_temperature = base.temperature
for child in specs[1:]:
    if child.temperature != 0.7:  # Not default
        merged_temperature = child.temperature
```

**Error Handling:**
- `InheritanceError`: Circular dependency, max depth, missing parent
- `ProviderNotAvailableError`: Provider not in registry
- `ValueError`: Provider registry not configured

### Consequences

**Positive:**
- ✅ Clean separation: inheritance resolution vs provider instantiation
- ✅ Flexible: can create agents without providers (testing)
- ✅ Utilities: validation, preview, chain inspection
- ✅ Correct inheritance: default values don't override parent values
- ✅ Well-tested: 16 unit tests covering all scenarios
- ✅ Type-safe: Full type hints with Protocol support

**Negative:**
- ⚠️ Complexity: Default value detection hardcoded for temperature (0.7)
- ⚠️ Coupling: Factory depends on ProviderRegistry (mitigated by Protocol)

**Neutral:**
- Factory follows existing patterns (Repository, Registry)
- Metadata attachment uses private attributes (future: proper metadata field)

### Metrics (Implementation)

**Files Created:**
- `paracle_domain/factory.py` (218 lines)
- `tests/unit/test_agent_factory.py` (413 lines)

**Files Modified:**
- `paracle_domain/__init__.py` (added exports)
- `paracle_domain/inheritance.py` (temperature inheritance fix)

**Test Coverage:**
- 16 new tests (100% passing)
- Scenarios covered:
  - Simple agent creation
  - Single-level inheritance
  - Multi-level inheritance (grandparent → parent → child)
  - Tools/metadata merging
  - Circular inheritance detection
  - Max depth enforcement
  - Missing parent detection
  - Provider selection and instantiation
  - Error conditions (provider unavailable, no registry)

**Phase 2 Completion:**
- Test count: 304 total (+79 from providers, adapters, MCP, factory)
- Python files: 67 (+3)
- Test files: 20 (+1)
- Code coverage: 87.5%
- **Phase 2: 100% COMPLETE** ✅

### Trade-offs

**Default Value Detection:**
- **Chosen**: Hardcode check `temperature != 0.7`
- **Alternative 1**: Store original Pydantic defaults in spec metadata
  - Pro: More robust
  - Con: Adds complexity, increases memory
- **Alternative 2**: Require explicit `temperature=None` to inherit
  - Pro: Explicit is better than implicit
  - Con: Breaking change, less ergonomic

**Rationale**: Pragmatic solution for v0.0.1. Can enhance with metadata in future.

### Related ADRs

- ADR-003: Agent Inheritance System
- ADR-011: LLM Provider Package Naming

### Next Steps

1. ✅ Phase 2 Complete
2. 📋 Begin Phase 3: Orchestration Engine
3. 📋 Consider enhancing inheritance with explicit field metadata (post-v0.0.1)

---

## ADR-013: State Management and Rollback System

**Date**: 2026-01-02
**Status**: Accepted
**Deciders**: Core Team
**Phase**: Phase 3 Enhancement - State Management

### Context

Paracle needed robust state management and rollback capabilities for:
1. **Workflow Recovery**: Resume failed workflows from checkpoints
2. **State Versioning**: Track entity changes over time
3. **Event Sourcing**: Enable replay-based state reconstruction
4. **Transaction Semantics**: Provide compensation for failed multi-step operations

**Existing Foundation:**
- In-memory `EventStore` in `paracle_events/bus.py` with replay capability
- Immutable events with `ConfigDict(frozen=True)`
- `ExecutionContext` tracking workflow state
- Repository pattern with thread-safe operations

**Missing:**
- Persistent event storage (events lost on restart)
- State snapshots for aggregates
- Rollback mechanism for workflows
- Compensating transactions for failed steps

### Decision

Implement a comprehensive state management and rollback system with 4 components:

#### 1. Persistent Event Store (`paracle_events/persistent_store.py`)

SQLite-backed durable event storage with:
- Ordered event sequences
- Event querying by type, source, time range
- Checkpoint support for snapshots
- Replay from any sequence number
- NDJSON export/import

```python
store = PersistentEventStore("events.db")
store.append(event)
store.replay(handler, from_sequence=100)
store.save_checkpoint("chk_1", aggregate_id, state)
```

#### 2. State Snapshot System (`paracle_store/snapshot.py`)

Point-in-time snapshots of aggregate state:
- Immutable `StateSnapshot` model with version tracking
- `InMemorySnapshotStore` (extensible to SQLite)
- `Snapshottable` mixin for entities
- Rollback to any previous version

```python
snapshot_store = InMemorySnapshotStore()
snapshottable = Snapshottable(snapshot_store, "Agent")
snapshottable.create_snapshot(entity, entity_id)
entity = snapshottable.rollback(entity_id, to_version=5)
```

#### 3. Workflow Rollback Manager (`paracle_orchestration/rollback.py`)

Checkpoint-based workflow recovery:
- `StepCheckpoint`: Captures state after each step
- `CheckpointManager`: Creates and retrieves checkpoints
- `CompensatingAction`: Defines rollback behavior per step
- `WorkflowRollbackManager`: Orchestrates rollback

```python
manager = WorkflowRollbackManager()
manager.create_checkpoint(execution_id, step_name, result, context)
manager.register_compensation(step_name, CompensatingAction(...))
result = await manager.rollback(execution_id, to_step_index=2)
```

#### 4. Transaction-like Wrapper (`WorkflowTransaction`)

Provides begin/commit/rollback semantics:
- Auto-rollback on exception
- Manual rollback support
- Context manager syntax

```python
async with WorkflowTransaction(manager, execution_id) as tx:
    result = await execute_step()
    tx.checkpoint("step_1", result, context)
    # Auto-commit on success, auto-rollback on exception
```

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   PARACLE FRAMEWORK                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  paracle_events/                                      │  │
│  │    bus.py (existing EventBus, in-memory EventStore)  │  │
│  │    persistent_store.py (NEW: SQLite-backed storage)  │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓ stores events                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  paracle_store/                                       │  │
│  │    repository.py (existing Repository pattern)       │  │
│  │    snapshot.py (NEW: State snapshots + versioning)   │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓ uses snapshots                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  paracle_orchestration/                               │  │
│  │    engine.py (existing WorkflowOrchestrator)         │  │
│  │    context.py (existing ExecutionContext)            │  │
│  │    rollback.py (NEW: Checkpoints + Rollback)         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

**Files Created:**
- `packages/paracle_events/persistent_store.py` (350+ lines)
- `packages/paracle_store/snapshot.py` (300+ lines)
- `packages/paracle_orchestration/rollback.py` (450+ lines)
- `tests/unit/test_rollback.py` (25 tests)

**Files Modified:**
- `packages/paracle_events/__init__.py` (export PersistentEventStore)

**Test Coverage:**
- 25 new tests covering all rollback functionality
- 100% test pass rate
- Scenarios: snapshots, persistent events, checkpoints, rollback, transactions

### Consequences

#### Positive

✅ **Durability**: Events persist across restarts (SQLite)
✅ **Recovery**: Failed workflows can resume from checkpoints
✅ **Versioning**: Full history of entity state changes
✅ **Rollback**: Undo completed steps with compensation
✅ **Transaction Semantics**: Auto-rollback on exceptions
✅ **Event Sourcing Ready**: Foundation for full event sourcing
✅ **Audit Trail**: Complete history for compliance (ISO 42001)
✅ **Extensible**: Protocol-based handlers for custom compensation

#### Negative

⚠️ **Storage Requirements**: Events accumulate over time
⚠️ **Complexity**: More moving parts to maintain
⚠️ **Performance**: SQLite writes add latency

#### Mitigations

- Event pruning policies (configurable retention)
- Checkpoint pruning (keep N most recent)
- Optional persistent storage (in-memory for testing)
- Async operations where possible

### Usage Examples

**1. Persistent Event Storage:**
```python
from paracle_events import PersistentEventStore, agent_created

store = PersistentEventStore("events.db")
store.append(agent_created("agent_123", "spec"))

# Later: replay events
store.replay(handler, from_sequence=0)
```

**2. State Snapshots:**
```python
from paracle_store.snapshot import InMemorySnapshotStore, Snapshottable

store = InMemorySnapshotStore()
snapshottable = Snapshottable(store, "Agent", deserializer=Agent.model_validate)

# Create snapshot on state change
snapshottable.create_snapshot(agent, agent.id, reason="Updated status")

# Rollback to previous version
agent = snapshottable.rollback(agent.id, to_version=1)
```

**3. Workflow Rollback:**
```python
from paracle_orchestration.rollback import (
    WorkflowRollbackManager,
    CompensatingAction,
    WorkflowTransaction,
)

manager = WorkflowRollbackManager()

# Register compensating actions
manager.register_compensation("send_email", CompensatingAction(
    step_name="send_email",
    action_type="cancel_email",
    parameters={"action": "mark_as_cancelled"},
))

# Use transaction semantics
async with WorkflowTransaction(manager, execution_id) as tx:
    result1 = await process_order()
    tx.checkpoint("process_order", result1, context)

    result2 = await send_email()  # This might fail
    tx.checkpoint("send_email", result2, context)
    # If send_email fails, process_order is compensated
```

### Roadmap Integration

This ADR adds state management to the Phase 3 deliverables:

**Phase 3 (Updated):**
- ✅ Workflow orchestrator
- ✅ REST API (FastAPI)
- ✅ WebSocket support (planned)
- ✅ Authentication (JWT)
- **✅ State management & rollback (NEW)**

**v0.5.0 (Future):**
- Memory management (builds on snapshots)
- Knowledge engine (uses event sourcing)

**v0.7.0 (Future):**
- Full ISO 42001 audit trail (uses persistent events)
- Policy enforcement (uses checkpoints)

### Related ADRs

- ADR-006: Event-Driven Architecture (foundation)
- ADR-002: Modular Monolith Architecture (package structure)

### References

- [Event Sourcing Pattern](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Saga Pattern](https://microservices.io/patterns/data/saga.html)
- [SQLite JSON1 Extension](https://www.sqlite.org/json1.html)

---

## ADR-015: Hybrid Persistence Strategy

**Date**: 2026-01-04
**Status**: Accepted
**Deciders**: Core Team
**Phase**: Phase 4 - Persistence & Production Scale

### Context

Paracle needed a persistence strategy that:
1. Keeps configurations human-readable and git-friendly
2. Provides reliable runtime data storage
3. Supports AI-native features (RAG, embeddings, memory)
4. Scales from development to production
5. Works with zero external dependencies for simple cases

**Existing State:**
- `.parac/` workspace with YAML/Markdown files (working)
- In-memory repositories (data lost on restart)
- `PersistentEventStore` with SQLite (basic event storage)

**Requirements:**
- ACID transactions for runtime data
- Query capabilities for history and analytics
- Vector storage for future RAG/memory features
- Progressive complexity (simple → production)

### Decision

Implement a **Hybrid Three-Layer Persistence Architecture**:

#### Layer 1: YAML/Markdown Files (Source of Truth for Definitions)

**Location**: `.parac/`
**Scope**: Configuration and definitions
**Status**: ✅ Implemented

**Contents:**
- Agent specifications (`.parac/agents/specs/`)
- Workflow definitions (`.parac/workflows/`)
- Tool configurations
- Governance state (roadmap, decisions)
- Project configuration

**Benefits:**
- Human-readable and editable
- Git-friendly (version control)
- Declarative configuration
- Zero external dependencies

#### Layer 2: SQLite → PostgreSQL (Runtime Data)

**Package**: `paracle_store`
**Scope**: Transactional runtime data
**Status**: 🔄 Implementing (Phase 4)

**Tables:**
```sql
-- Agent runtime instances
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    spec_hash TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- Workflow executions
CREATE TABLE executions (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSON,
    error TEXT,
    context JSON
);

-- Event log
CREATE TABLE events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    source TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data JSON
);

-- Audit trail (ISO 42001)
CREATE TABLE audit (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    resource TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    outcome TEXT,
    severity TEXT,
    data JSON
);

-- Sessions
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    state JSON,
    summary TEXT
);
```

**Migration Path:**
- v0.0.1: SQLite (file-based, zero config)
- v0.7.0+: PostgreSQL option (connection string)

#### Layer 3: ChromaDB → pgvector (AI-Native Storage)

**Package**: `paracle_knowledge` (v0.5.0)
**Scope**: Embeddings, RAG, semantic search
**Status**: 📋 Planned

**Contents:**
- Document embeddings for RAG
- Agent memory vectors
- Semantic code search indexes
- Conversation history embeddings

**Migration Path:**
- v0.5.0: ChromaDB (embedded, simple)
- v1.0.0: pgvector (unified with PostgreSQL)

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     STORAGE CONFIGURATION                        │
│                                                                  │
│  StorageConfig:                                                  │
│    workspace_path: Path = ".parac"                              │
│    database_url: str | None = "sqlite:///paracle.db"           │
│    vector_store: Literal["none", "chroma", "pgvector"] = "none"│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    REPOSITORY PATTERN                            │
│                                                                  │
│  Repository[T] (Abstract)                                        │
│    ├── InMemoryRepository[T]  (testing, ephemeral)              │
│    └── SQLiteRepository[T]    (persistent, production)          │
│                                                                  │
│  AgentRepository                                                 │
│    ├── InMemoryAgentRepository                                  │
│    └── SQLiteAgentRepository                                    │
│                                                                  │
│  WorkflowRepository, ExecutionRepository, EventRepository...   │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

**Files to Create:**

```
packages/paracle_store/
├── database.py           # Database connection management
├── models.py             # SQLAlchemy models
├── sqlite_repository.py  # SQLite implementations
└── migrations/
    ├── env.py            # Alembic config
    └── versions/
        └── 001_initial.py
```

**Storage Configuration:**

```python
# packages/paracle_core/storage.py

from pydantic import BaseModel
from pathlib import Path
from typing import Literal

class StorageConfig(BaseModel):
    """Multi-layer storage configuration."""

    # Layer 1: File-based (always available)
    workspace_path: Path = Path(".parac")

    # Layer 2: Relational (optional, progressive)
    database_url: str | None = None  # sqlite:/// or postgresql://

    # Layer 3: Vector (optional, for RAG)
    vector_store: Literal["none", "chroma", "pgvector"] = "none"
    vector_store_path: str | None = None

    @property
    def is_persistent(self) -> bool:
        return self.database_url is not None

    @property
    def default_sqlite_path(self) -> Path:
        return self.workspace_path / "data" / "paracle.db"
```

### Consequences

#### Positive

✅ **Zero-Config Start**: Works with just YAML files (no database setup)
✅ **Progressive Complexity**: Add SQLite when persistence needed
✅ **Human-Readable Configs**: Agent specs stay in YAML
✅ **Git-Friendly**: Definitions version-controlled
✅ **Production-Ready Path**: Clear migration to PostgreSQL
✅ **AI-Native Future**: Vector storage for RAG/memory
✅ **ACID Transactions**: Reliable runtime data
✅ **Queryable History**: SQL for analytics
✅ **ISO 42001 Compliant**: Proper audit trail

#### Negative

⚠️ **Complexity**: Multiple storage systems to maintain
⚠️ **Synchronization**: Must keep YAML and DB in sync
⚠️ **Dependencies**: SQLAlchemy, Alembic for full features

#### Mitigations

- Clear separation: YAML for definitions, DB for runtime
- Sync utilities in CLI (`paracle sync`)
- Optional dependencies (SQLite is stdlib)
- Comprehensive documentation

### Migration Path

| Version | Storage             | Description                        |
| ------- | ------------------- | ---------------------------------- |
| v0.0.1  | YAML + SQLite       | Config in files, runtime in SQLite |
| v0.1.0  | + Event persistence | Persistent event store             |
| v0.5.0  | + ChromaDB          | RAG and embeddings                 |
| v0.7.0  | + PostgreSQL option | Production scaling                 |
| v1.0.0  | + pgvector          | Unified relational + vector        |

### Success Criteria

- [ ] SQLite persistence for agents, workflows, executions
- [ ] Event persistence survives restart
- [ ] Audit trail for all operations
- [ ] Session data persistence
- [ ] Migration tooling (Alembic)
- [ ] Repository pattern with both in-memory and SQLite

### References

- SQLAlchemy 2.0 Documentation
- Alembic Migration Tool
- ChromaDB Documentation
- pgvector Extension

### Related ADRs

- ADR-006: Event-Driven Architecture
- ADR-013: State Management and Rollback
- ADR-011: ISO 42001 Compliance Strategy

---

## ADR-014: CLI Commands Enhancement Roadmap

**Date**: 2026-01-02
**Status**: Accepted
**Deciders**: Core Team
**Phase**: Cross-Phase Enhancement

### Context

Analysis of the Paracle CLI revealed significant gaps compared to industry-standard AI frameworks (LangChain, CrewAI, AutoGen). The current CLI has 10 implemented commands focused on workspace governance, but lacks essential runtime and developer experience commands.

**Current State (10 commands):**
- Workspace: `init`, `status`, `sync`, `validate`
- Session: `session start`, `session end`
- Agents: `agents list`, `agents get`, `agents export`
- Utility: `hello`

**Industry Comparison:**

| Feature        | LangChain | CrewAI | AutoGen | Paracle   |
| -------------- | --------- | ------ | ------- | --------- |
| `serve`        | ✅         | ✅      | ❌       | ❌         |
| `run agent`    | ✅         | ✅      | ✅       | ❌         |
| `create agent` | ✅         | ✅      | ❌       | ❌         |
| `list tools`   | ✅         | ✅      | ❌       | ❌         |
| `new project`  | ✅         | ✅      | ❌       | ⚠️ Partial |
| `config`       | ✅         | ✅      | ❌       | ❌         |

### Decision

Implement 35 additional CLI commands across phases, prioritized by user impact:

#### Priority 0 - Essential (Blocking Usage)

These commands are required for Paracle to be usable as a framework:

```bash
# Phase 3
paracle serve                    # Start API server
paracle serve --port 8000        # Custom port
paracle serve --reload           # Dev mode

# Phase 5
paracle agents create <name>     # Create from template
paracle agents run <name>        # Run interactively
```

#### Priority 1 - Core Features

```bash
# Workflow Management (Phase 3)
paracle workflow list            # List workflows
paracle workflow run <name>      # Execute workflow
paracle workflow status <id>     # Check execution
paracle workflow cancel <id>     # Cancel running
paracle workflow history         # Execution history

# Provider Management (Phase 2)
paracle providers list           # List providers
paracle providers add <name>     # Add provider
paracle providers test <name>    # Test connection
paracle providers default <name> # Set default

# Tool Management (Phase 2)
paracle tools list               # List tools
paracle tools info <name>        # Tool details
paracle tools register <path>    # Register custom
paracle tools test <name>        # Test execution
```

#### Priority 2 - Developer Experience

```bash
# Development (Phase 4)
paracle dev                      # Start dev environment
paracle logs                     # Stream logs
paracle logs --tail 100          # Last N logs

# Events (Phase 4)
paracle events list              # Recent events
paracle events replay <id>       # Replay from event

# Configuration (Phase 4)
paracle config show              # Show config
paracle config set <key> <val>   # Set value
paracle config get <key>         # Get value
paracle config env               # Environment vars

# Monitoring (Phase 4)
paracle health                   # Health check
paracle metrics                  # Show metrics
```

#### Priority 3 - Polish & Onboarding

```bash
# Project Creation (Phase 5)
paracle new <name>               # Full project scaffold
paracle new --template api       # From template
paracle new --template chatbot   # Different archetypes

# Agent Lifecycle (Phase 5)
paracle agents test <name>       # Test with samples
paracle agents delete <name>     # Remove agent
paracle agents validate <name>   # Validate spec

# Maintenance (Phase 5)
paracle doctor                   # Diagnose issues
paracle upgrade                  # Upgrade version
```

### Implementation Plan

| Phase   | Commands | Priority | Total     |
| ------- | -------- | -------- | --------- |
| Phase 1 | 10       | -        | 10 (done) |
| Phase 2 | +8       | P1       | 18        |
| Phase 3 | +5       | P0/P1    | 23        |
| Phase 4 | +12      | P2       | 35        |
| Phase 5 | +10      | P0/P3    | 45        |

### Architecture

All commands follow the established pattern:

```
packages/paracle_cli/
├── main.py              # Entry point, Click groups
├── commands/
│   ├── parac.py         # Workspace commands (existing)
│   ├── agents.py        # Agent commands (existing)
│   ├── workflow.py      # Workflow commands (new)
│   ├── providers.py     # Provider commands (new)
│   ├── tools.py         # Tool commands (new)
│   ├── config.py        # Config commands (new)
│   ├── server.py        # Serve command (new)
│   └── dev.py           # Dev commands (new)
└── utils/
    └── api_client.py    # API client (existing)
```

### Command Design Principles

1. **Consistency**: All commands follow `paracle <noun> <verb>` pattern
2. **Output Formats**: Support `--format=table|json|yaml` where applicable
3. **API-First**: Commands connect to API when server is running
4. **Offline Mode**: Core commands work without server
5. **Progressive Disclosure**: Simple by default, options for power users

### Consequences

#### Positive

✅ **Usability**: Framework becomes actually usable
✅ **Parity**: Competitive with LangChain/CrewAI CLIs
✅ **Developer Experience**: Smooth onboarding and debugging
✅ **Discoverability**: Commands self-document features

#### Negative

⚠️ **Implementation Effort**: 35 commands to implement
⚠️ **Testing Surface**: Each command needs tests
⚠️ **Documentation**: CLI reference docs needed

#### Mitigations

- Phased rollout by priority
- Reuse existing API endpoints
- Generate docs from Click metadata
- Template-based command generation

### Related ADRs

- ADR-002: Modular Monolith Architecture
- ADR-013: State Management and Rollback

### References

- [Click Documentation](https://click.palletsprojects.com/)
- [LangChain CLI](https://python.langchain.com/docs/langchain-cli/)
- [CrewAI CLI](https://docs.crewai.com/)

---

## ADR-017: Comprehensive Multi-Provider Support

**Date**: 2026-01-04
**Status**: Accepted
**Deciders**: Core Team

### Context

Current provider support is limited to OpenAI, Anthropic, Google, and Ollama. The AI landscape has expanded significantly with new providers offering performance advantages (Groq), cost benefits (DeepSeek), and extended capabilities (xAI). Users need flexibility to choose providers based on cost, performance, and features.

### Decision

Expand provider support with:
1. New Providers: xAI (Grok), DeepSeek, Groq, OpenAI-compatible wrapper
2. Model Capabilities System: ModelCapability enum, ModelInfo, ProviderInfo, ModelCatalog
3. Enhanced Documentation: Comprehensive provider guide (docs/providers.md)

### Implementation

**New Files**:
- packages/paracle_providers/capabilities.py - Capabilities tracking
- packages/paracle_providers/xai_provider.py - xAI implementation
- packages/paracle_providers/deepseek_provider.py - DeepSeek implementation
- packages/paracle_providers/groq_provider.py - Groq implementation
- packages/paracle_providers/openai_compatible.py - Generic wrapper
- docs/providers.md - Comprehensive guide
- examples/07_multi_provider.py - Multi-provider examples

### Consequences

**Positive**:
✅ Provider choice based on cost, performance, features
✅ Cost optimization with DeepSeek (0.14/M) and Groq (0.05/M)
✅ Ultra-fast inference with Groq (500+ tokens/sec)
✅ Self-hosted options with OpenAI-compatible APIs

**Negative**:
⚠️ More providers to maintain and test
⚠️ API variations between providers

### References
- Vercel AI SDK: https://ai-sdk.dev/docs/foundations/providers-and-models
- xAI, DeepSeek, Groq API documentation


---

## ADR-018: Complete Provider Ecosystem Coverage

**Date**: 2026-01-04
**Status**: Accepted
**Deciders**: Core Team

### Context

Following ADR-017's successful addition of xAI, DeepSeek, Groq, and OpenAI-compatible providers, users requested comprehensive coverage of ALL major commercial and self-hosted providers. The goal is to make Paracle the most complete multi-provider framework available.

### Decision

Add complete provider ecosystem:

**6 New Commercial Providers**:
1. Mistral - Open-weight models with function calling
2. Cohere - Specialized in embeddings, reranking, RAG
3. Together.ai - 100+ open-source models with fast inference
4. Perplexity - Search-enhanced AI with real-time web access
5. OpenRouter - Unified gateway to 200+ models
6. Fireworks.ai - Production-grade inference

**8 Self-Hosted Solutions** (via factory functions):
1. vLLM - Production GPU inference
2. llama.cpp - CPU-optimized inference
3. text-generation-webui - Feature-rich UI
4. LocalAI - OpenAI-compatible Docker solution
5. Jan - Privacy-focused desktop app
6. Anyscale - Ray-based endpoints
7. Cloudflare Workers AI - Edge deployment
8. (LM Studio, Together, Perplexity already had factories)

### Implementation

**New Files Created**:
- packages/paracle_providers/mistral_provider.py (270 lines)
- packages/paracle_providers/cohere_provider.py (250 lines)
- packages/paracle_providers/together_provider.py (220 lines)
- packages/paracle_providers/perplexity_provider.py (230 lines)
- packages/paracle_providers/openrouter_provider.py (210 lines)
- packages/paracle_providers/fireworks_provider.py (210 lines)
- examples/08_self_hosted_providers.py (300 lines)

**Files Modified**:
- packages/paracle_providers/openai_compatible.py - Added 8 factory functions
- packages/paracle_providers/auto_register.py - Registered 6 new providers
- packages/paracle_providers/__init__.py - Exported factory functions
- docs/providers.md - Extended with 300+ lines of documentation

### Provider Statistics

**Total Providers**: 14+ (8 commercial + 6 self-hosted)
**Total Models**: 50+ models across all providers
**Context Windows**: 4k to 2M tokens
**Pricing**: Free (self-hosted) to \/M tokens
**Features**: Chat, vision, search, reasoning, tool calling, embeddings

### Cost Comparison (per 1M tokens)

**Ultra-Budget** (< \.50):
- DeepSeek: \.14/M (cheapest)
- Groq Mixtral: \.05/M (input)

**Budget** (\.50-\.00):
- Groq Llama: \.79/M
- Together 70B: \.88/M
- Fireworks 70B: \.90/M
- Perplexity Small: \.20/M

**Moderate** (\-\):
- Mistral Large: \.00/M (input)
- Cohere R+: \.50/M (input)
- Together 405B: \.50/M
- Fireworks 405B: \.00/M

### Use Case Mapping

**Speed Critical**: Groq, Fireworks
**Cost Optimization**: DeepSeek, Groq, Together
**Search + AI**: Perplexity (citations)
**Multi-Provider**: OpenRouter (200+ models)
**Privacy/Self-Hosted**: vLLM, llama.cpp, LocalAI, Jan
**Easy Local Setup**: LM Studio, Jan, Ollama
**Production GPU**: vLLM, Fireworks
**Production CPU**: llama.cpp
**Enterprise**: Mistral, Anthropic, OpenAI

### Consequences

**Positive**:
✅ Most comprehensive provider support in any framework
✅ True provider flexibility and vendor independence
✅ Self-hosted options for privacy/cost control
✅ Complete cost spectrum from free to premium
✅ Specialized providers for every use case
✅ Easy migration between providers
✅ Unified API for all providers

**Negative**:
⚠️ More providers to maintain and test
⚠️ API variations require careful handling
⚠️ Documentation must stay current

**Neutral**:
ℹ️ Users can choose based on requirements
ℹ️ Graceful degradation if packages not installed

### Metrics

- **Code Added**: ~2,700 lines (1,390 provider code + 300 examples + 1,000 docs)
- **Providers**: 14+ (up from 8)
- **Models**: 50+ (up from 30+)
- **Self-Hosted Options**: 8 factory functions
- **Documentation**: Comprehensive guides for all
- **Time to Complete**: ~2 hours

### References

- Mistral: https://docs.mistral.ai
- Cohere: https://docs.cohere.com
- Together: https://docs.together.ai
- Perplexity: https://docs.perplexity.ai
- OpenRouter: https://openrouter.ai/docs
- Fireworks: https://docs.fireworks.ai
- vLLM: https://vllm.ai
- llama.cpp: https://github.com/ggerganov/llama.cpp


---

## ADR-019: Enterprise Log Management System

**Date**: 2026-01-04
**Status**: Accepted
**Deciders**: Core Team, Security Team

### Context

As Paracle grows, log management becomes critical for:
- **Troubleshooting**: Fast root cause analysis
- **Security**: Threat detection and incident response
- **Compliance**: Audit trails for ISO 42001, ISO 27001, GDPR
- **Performance**: System health monitoring
- **Cost Optimization**: LLM API cost tracking

Current logging was functional but lacked:
- Centralized aggregation across all components
- Automated retention and cleanup
- Fast search and analysis tools
- Anomaly detection
- Compliance reporting

**Inspiration**: CrowdStrike's log management best practices provided framework for enterprise-grade solution.

### Decision

Implement **three-tier enterprise log management architecture**:

#### 1. Framework Logs (~/.paracle/logs/)
- **Purpose**: Paracle framework operations
- **Retention**: 90 days
- **Format**: JSON structured
- **Versioned**: No
- **Content**: Core framework, providers, orchestration, errors

#### 2. Governance Logs (.parac/memory/logs/)
- **Purpose**: Development decisions and agent actions
- **Retention**: Permanent (version controlled)
- **Format**: JSON structured
- **Versioned**: Yes (Git)
- **Content**: Agent actions, decisions, sessions

#### 3. Runtime Logs (.parac/memory/logs/runtime/)
- **Purpose**: Agent/workflow execution
- **Retention**: 30 days (security: 365 days)
- **Format**: JSON structured
- **Versioned**: No (high volume)
- **Content**: Agents, workflows, errors, security

### Implementation

**New Files Created**:
1. .parac/policies/LOG_MANAGEMENT.md (800+ lines)
   - Complete policy document
   - CrowdStrike best practices implementation
   - Retention policies, security, compliance

2. .parac/memory/logs/runtime/config.yaml (450+ lines)
   - Comprehensive runtime log configuration
   - Centralized aggregation settings
   - Monitoring, alerting, performance tuning

3. packages/paracle_core/logging/management.py (650+ lines)
   - LogManager class for log operations
   - Search, aggregation, analysis tools
   - Anomaly detection algorithms
   - Compliance reporting

**Files Modified**:
- .parac/project.yaml - Enhanced logging section (70+ lines)

### Architecture

\\\
┌──────────────────────────────────────────────────────────┐
│                    LOG SOURCES                           │
├──────────────────────────────────────────────────────────┤
│  Framework  │  Agents  │  Workflows  │  API  │  Security │
└─────┬────────────┬────────────┬─────────┬───────────┬────┘
      │            │            │         │           │
      ▼            ▼            ▼         ▼           ▼
┌──────────────────────────────────────────────────────────┐
│              STRUCTURED LOGGING (JSON)                   │
│  • Correlation IDs    • Context enrichment               │
│  • Timestamps (ISO)   • PII redaction                    │
└─────┬────────────────────────────────────────────────┬───┘
      │                                                │
      ▼                                                ▼
┌────────────────────────┐            ┌────────────────────┐
│   LOCAL STORAGE        │            │  EXTERNAL AGGR.    │
│   .parac/logs/         │            │  (Optional)        │
│   ~/.paracle/logs/     │            │  • Elasticsearch   │
│                        │            │  • Splunk          │
│   • Daily rotation     │            │  • Datadog         │
│   • Compression (7d)   │            │  • CloudWatch      │
│   • Auto-cleanup       │            └────────────────────┘
└───────┬────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│                  SQLITE INDEX                            │
│  • Fast search (indexed fields)                          │
│  • Full-text search (FTS5)                               │
│  • Aggregation queries                                   │
└───────┬──────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│                 ANALYSIS TOOLS                           │
│  • Search & Filter     • Anomaly Detection               │
│  • Aggregation         • Compliance Reports              │
│  • Statistics          • Cost Tracking                   │
└──────────────────────────────────────────────────────────┘
\\\

### Features

#### Centralized Aggregation ✅
- Single access point for all logs
- Support for local + external aggregators
- Elasticsearch, Splunk, Datadog, CloudWatch

#### Automation ⚙️
- Automatic daily rotation (midnight UTC)
- Compression after 7 days (gzip, 70-90% reduction)
- Retention policy enforcement
- Disk space monitoring

#### Retention Policies 📅

| Category   | Retention | Compression | Rationale              |
| ---------- | --------- | ----------- | ---------------------- |
| Framework  | 90 days   | After 7d    | Troubleshooting window |
| Governance | Permanent | No (Git)    | Audit trail            |
| Runtime    | 30 days   | After 7d    | Active debugging       |
| Security   | 365 days  | After 30d   | Compliance (ISO 27001) |
| Errors     | 90 days   | After 7d    | Root cause analysis    |
| API Access | 180 days  | After 30d   | Security audits        |

#### Monitoring & Alerting 🚨
- Error rate thresholds (>5% triggers alert)
- Disk usage warnings (80% warning, 90% critical)
- Log volume anomaly detection
- Real-time alerting (email, Slack, PagerDuty)

#### Security 🔒
- PII redaction (emails, API keys, credit cards)
- Access control per log category
- Encryption at rest (future)
- TLS for log forwarding
- Audit trail for log access

#### Search & Analysis 🔍
- Fast indexed search (<100ms)
- Full-text search with FTS5
- Aggregation by agent, workflow, user
- Correlation ID tracing
- Time range queries

#### Compliance ✅
- **ISO 42001**: Immutable audit trail, model decisions
- **ISO 27001**: Security events, 365-day retention
- **GDPR**: PII protection, right to erasure
- **SOC 2**: Access logging, change management

### Statistics

- **Policy Document**: 800+ lines (LOG_MANAGEMENT.md)
- **Configuration**: 450+ lines (runtime/config.yaml)
- **Management Tools**: 650+ lines (management.py)
- **Total Added**: ~2,000 lines of documentation + code

### Implementation Details

**LogManager API**:
\\\python
from paracle_core.logging.management import LogManager

manager = LogManager()

# Search
errors = manager.search(level="ERROR", since="1h ago", limit=100)

# Aggregate
stats = manager.aggregate(group_by="agent_id", metric="count")

# Detect anomalies
anomalies = manager.detect_anomalies(metric="error_rate", threshold=2.0)

# Compliance report
report = manager.compliance_report(standard="ISO42001")

# Cleanup
deleted = manager.cleanup(dry_run=False)
\\\

**CLI Commands** (planned):
\\\ash
paracle logs search --since "2h ago" --level ERROR
paracle logs stats --since "24h ago"
paracle logs anomalies --metric error_rate
paracle logs compliance-report --standard ISO42001
paracle logs cleanup --dry-run
paracle logs health
\\\

### Performance Targets

- **Write Latency**: <1 ms (async logging)
- **Search Latency**: <100 ms (indexed fields)
- **Full-Text Search**: <1 second
- **Indexing Rate**: 10,000+ entries/second
- **Storage**: Compression reduces size by 70-90%

### Consequences

**Positive**:
✅ Enterprise-grade observability
✅ Fast troubleshooting (indexed search)
✅ Proactive monitoring (anomaly detection)
✅ Compliance ready (ISO, GDPR, SOC 2)
✅ Cost tracking (LLM API usage)
✅ Security hardening (PII redaction, access control)
✅ Scalable architecture (supports external aggregators)

**Negative**:
⚠️ Increased complexity (3-tier architecture)
⚠️ Storage requirements (~100 MB/day typical)
⚠️ Learning curve (new tools and APIs)
⚠️ Maintenance overhead (retention cleanup)

**Neutral**:
⚡ Optional external aggregators (Elasticsearch, Splunk)
⚡ Configurable retention policies
⚡ Can disable features if not needed

### Metrics

**Log Volumes** (estimated):
- Small deployment: 1-10 GB/day
- Medium deployment: 10-100 GB/day
- Large deployment: 100+ GB/day

**Compression Ratio**: 70-90% size reduction

**Index Size**: ~10% of raw log size

**Retention Savings**:
- 30-day runtime logs: ~90% deletion
- 90-day framework logs: ~70% deletion
- Compression: Additional 80% space savings

### Compliance Mapping

| Standard      | Requirements Met                                          |
| ------------- | --------------------------------------------------------- |
| **ISO 42001** | Audit trail, tamper-proof, user actions, model decisions  |
| **ISO 27001** | Security events (365d), access control, incident response |
| **GDPR**      | PII protection, right to erasure, data breach logging     |
| **SOC 2**     | Access logging, change management, monitoring             |

### Future Enhancements (Phase 5+)

1. **ML-Based Anomaly Detection**
   - Isolation Forest algorithm
   - Adaptive thresholds
   - Predictive alerting

2. **Distributed Tracing**
   - OpenTelemetry integration
   - Cross-service correlation
   - Performance profiling

3. **Real-Time Streaming**
   - WebSocket log streaming
   - Live dashboards
   - Real-time alerting

4. **Advanced Visualization**
   - Grafana dashboards
   - Kibana integration
   - Custom charts

### References

**Standards**:
- [ISO 42001](https://www.iso.org/standard/81230.html) - AI Management
- [ISO 27001](https://www.iso.org/standard/27001) - Information Security
- [GDPR](https://gdpr.eu/) - Data Protection
- [NIST 800-92](https://csrc.nist.gov/publications/detail/sp/800-92/final) - Log Management

**Best Practices**:
- [CrowdStrike Log Management](https://www.crowdstrike.com/en-us/cybersecurity-101/next-gen-siem/log-management/)
- [12-Factor App: Logs](https://12factor.net/logs)
- [OpenTelemetry Logging](https://opentelemetry.io/docs/specs/otel/logs/)

**Internal**:
- .parac/policies/LOG_MANAGEMENT.md
- .parac/memory/logs/README.md
- packages/paracle_core/logging/

### Approval

- **Proposed By**: AI Agent (CoderAgent)
- **Reviewed By**: Security Team, DevOps Team
- **Approved By**: CTO
- **Date**: 2026-01-04
- **Next Review**: 2026-04-04


---

## ADR-020: Vibe Kanban-Inspired Features for Total AI Project Management

**Date**: 2026-01-05
**Status**: Accepted
**Context**: Roadmap expansion for community edition

### Context

After analyzing [Vibe Kanban](https://github.com/BloopAI/vibe-kanban), a visual orchestration platform for AI coding agents, we identified key features that would transform Paracle from a **framework for building agents** into a **complete platform for managing AI project lifecycles**.

**Key Difference**:
- **Paracle**: Framework for building AI agent applications (programmatic)
- **Vibe Kanban**: Visual project management tool for AI coding agents (UI-based)

### Decision

Add 6 new phases (Phase 5-10) to roadmap, incorporating Vibe Kanban's best practices for **Community Edition** (CLI/API only, no UI):

#### **Phase 5: Execution Safety & Isolation** (3 weeks)
- Docker-based sandboxing for agent execution
- Resource limits (CPU, memory, timeout)
- Filesystem isolation per execution
- Automatic rollback on failure
- Artifact review and approval workflow (API)

**Rationale**: Production safety - agents should run in isolated environments, especially for code generation.

#### **Phase 6: Iterative Execution & Agent Profiles** (3 weeks)
- Follow-up execution with feedback loop
- Agent configuration profiles (variants)
- Human-in-the-loop workflows (pause/review/continue)
- Conditional retry based on validation
- Context accumulation across attempts
- Model switching per task type

**Rationale**: AI rarely succeeds on first attempt. Iteration is essential for reliability.

#### **Phase 7: Git Integration & Change Tracking** (3 weeks)
- Branch per execution for isolation
- Automatic commits of agent changes
- GitHub/GitLab MR/PR generation
- Conflict resolution for concurrent executions
- Audit trail via git history

**Rationale**: Version control is critical for code-generating agents and compliance.

#### **Phase 8: Real-time Monitoring & Templates** (2 weeks)
- WebSocket API for live execution streaming
- Pause/resume/cancel workflow controls
- Progress indicators and resource monitoring
- Pre-built workflow templates (RAG, multi-agent, code review)
- Quick-start wizards for common patterns
- Execution versioning and comparison

**Rationale**: Long-running workflows need visibility. Templates reduce time-to-value.

#### **Phase 9: Notifications & Advanced Features** (2 weeks)
- Multi-channel notifications (email, Slack, webhook)
- Smart alerts (anomaly detection, cost thresholds)
- Agent escalation on errors
- Time travel debugging (replay executions)
- A/B testing for agent configurations
- Comprehensive cost tracking and reporting

**Rationale**: Async workflows need proactive notifications. Cost tracking is critical for production.

#### **Phase 10: Polish & v0.1.0 Release** (2 weeks)
- Comprehensive documentation
- Migration guides
- Security audit
- Performance benchmarks
- v0.1.0 release

### Architecture

**Community Edition** (CLI + API):
```
Paracle Framework (Community)
├── Core Domain (Phases 0-4) ✅
├── Execution Safety (Phase 5)
│   ├── packages/paracle_sandbox/
│   └── Docker isolation
├── Iterative Execution (Phase 6)
│   ├── packages/paracle_execution/
│   └── Agent profiles
├── Git Integration (Phase 7)
│   └── packages/paracle_git/
├── Real-time Monitoring (Phase 8)
│   ├── WebSocket API
│   └── Templates
└── Notifications (Phase 9)
    └── packages/paracle_notifications/
```

**Enterprise Edition** (Future, v1.0+):
- Community Edition + Web UI
- Visual workflow builder
- Kanban board interface
- Graphical code review
- Team collaboration features

### Implementation

**Timeline Extended**: 17 weeks → 32 weeks
**CLI Commands**: 45 → 75 commands
**New Packages**: 5 packages (sandbox, execution, git, notifications, templates)

**New CLI Commands**:
```bash
# Phase 5 - Safety
paracle sandbox create/list/cleanup
paracle review list/approve/reject

# Phase 6 - Iteration
paracle workflow retry/continue
paracle profiles list/create
paracle agents switch-model

# Phase 7 - Git
paracle git init/branches/merge/pr-create/cleanup

# Phase 8 - Monitoring
paracle stream/pause/resume
paracle init --template
paracle templates list
paracle history compare

# Phase 9 - Notifications
paracle notify configure
paracle alerts list
paracle replay
paracle cost report
```

### Consequences

**Positive**:
- ✅ **Complete platform** - Not just a framework, but full project management
- ✅ **Production-ready** - Safety, isolation, monitoring built-in
- ✅ **Enterprise-grade** - Git integration, audit trail, cost tracking
- ✅ **Developer-friendly** - Templates, quick-start, CLI power
- ✅ **Community focus** - No UI barrier, programmatic control

**Negative**:
- ⚠️ **Timeline extended** - 17 weeks → 32 weeks
- ⚠️ **Increased complexity** - More packages to maintain
- ⚠️ **Docker dependency** - Requires container runtime

**Neutral**:
- 🔵 **Enterprise edition** - Reserved for future (v1.0+)
- 🔵 **UI excluded** - Community stays CLI/API-focused

### Metrics

**v0.1.0 Targets**:
- Execution isolation: 100% of workflows in sandboxes
- Iteration success rate: >80% after 3 attempts
- Git integration: 100% of code-gen workflows tracked
- Template usage: <5min time-to-first-workflow
- Cost tracking: 100% of LLM calls tracked

### Alternatives Considered

1. **Build UI first** - Rejected: Community users prefer CLI/API
2. **Incremental approach** - Rejected: Features are interdependent
3. **Fork Vibe Kanban** - Rejected: Different architecture, licensing

### References

- [Vibe Kanban Repository](https://github.com/BloopAI/vibe-kanban)
- [Vibe Kanban Documentation](https://vibekanban.com/docs)
- ADR-015: Persistence Strategy
- ADR-019: Enterprise Log Management

---

## ADR-021: Kanban Task Management System

**Date**: 2026-01-05
**Status**: Accepted
**Context**: User request for Kanban-style task status tracking

### Context

Paracle currently uses simple linear status models (`PENDING → RUNNING → COMPLETED/FAILED`). Users requested Kanban-style task management with stages like:
- **To Do** - Tasks queued for execution
- **In Progress** - Currently executing
- **In Review** - Awaiting human review/approval
- **Done** - Successfully completed
- **Cancelled** - Manually cancelled

This aligns with common project management workflows and integrates with the Human-in-the-Loop approval system (ADR-013, ISO 42001).

### Decision

Add **Kanban task management** as a **core domain feature** (not just Enterprise UI):

#### 1. New TaskStatus Enum

```python
# packages/paracle_domain/models.py
class TaskStatus(str, Enum):
    """Kanban-style task status."""

    BACKLOG = "backlog"           # In backlog, not scheduled
    TODO = "todo"                 # Scheduled, ready to start
    IN_PROGRESS = "in_progress"   # Currently executing
    IN_REVIEW = "in_review"       # Awaiting human review
    BLOCKED = "blocked"           # Blocked by dependency/issue
    DONE = "done"                 # Successfully completed
    CANCELLED = "cancelled"       # Manually cancelled
```

#### 2. Task Model

```python
class Task(BaseModel):
    """Kanban task for tracking work items."""

    id: str
    title: str
    description: str | None
    status: TaskStatus = TaskStatus.BACKLOG
    priority: TaskPriority  # P0, P1, P2, P3
    assignee: str | None    # Agent ID or human
    workflow_id: str | None # Associated workflow
    step_id: str | None     # Associated workflow step
    labels: list[str]       # Tags/categories
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime

    # Kanban metadata
    column_order: int       # Order within column
    swimlane: str | None    # Agent, priority, etc.
```

#### 3. CLI Commands (Phase 6)

```bash
# Task management
paracle task list [--status STATUS] [--assignee AGENT]
paracle task create "Title" [--priority P1] [--assignee coder]
paracle task move TASK_ID STATUS
paracle task assign TASK_ID AGENT_ID
paracle task view TASK_ID

# Board view (text-based)
paracle board show [--swimlane agent|priority]
paracle board stats
```

#### 4. API Endpoints

```
GET    /tasks                    # List tasks
POST   /tasks                    # Create task
GET    /tasks/{id}               # Get task
PUT    /tasks/{id}               # Update task
DELETE /tasks/{id}               # Delete task
POST   /tasks/{id}/move          # Move to status
POST   /tasks/{id}/assign        # Assign to agent

GET    /board                    # Get board view
GET    /board/stats              # Board statistics
```

#### 5. Integration with Workflows

```python
# Workflow steps can create/update tasks
WorkflowStep(
    id="review",
    agent="reviewer",
    creates_task=True,           # Auto-create task
    task_status="in_review",     # Initial status
    requires_approval=True,      # Human approval gate
)

# Task completion triggers workflow continuation
task.complete() → workflow.resume()
```

### Implementation Plan

**Phase 6** (Iterative Execution & Agent Profiles):
- Add `TaskStatus` enum to `paracle_domain/models.py`
- Add `Task` model to `paracle_domain/models.py`
- Add `TaskRepository` to `paracle_store/`
- Add CLI commands (`paracle task`, `paracle board`)
- Add API endpoints (`/tasks`, `/board`)
- Integrate with workflow execution

**Phase 8** (Real-time Monitoring):
- WebSocket updates for task status changes
- Real-time board synchronization

### Consequences

**Positive**:
- ✅ **Familiar workflow** - Developers know Kanban
- ✅ **Visual progress** - Even in CLI with `paracle board show`
- ✅ **Human integration** - IN_REVIEW maps to approval gates
- ✅ **Prioritization** - Tasks can be prioritized and ordered
- ✅ **Multi-agent coordination** - Swimlanes by agent
- ✅ **Enterprise-ready** - Foundation for UI board in v1.0+

**Negative**:
- ⚠️ **Complexity** - New domain model to maintain
- ⚠️ **State management** - Tasks + workflows need synchronization

### Alternatives Considered

1. **Keep simple statuses** - Rejected: User explicitly requested Kanban
2. **Enterprise-only feature** - Rejected: Core domain value, CLI-friendly
3. **External tool integration** - Rejected: Tight workflow integration needed

### Related Decisions

- ADR-013: State Management and Rollback System
- ADR-015: Hybrid Persistence Strategy
- ADR-020: Vibe Kanban-Inspired Features


---

## ADR-022: Execution Modes Architecture

**Date**: 2026-01-05
**Status**: Accepted
**Deciders**: Core Team

### Context

Paracle workflows can execute in various modes depending on requirements:
- **Development**: Interactive debugging, step-by-step execution
- **Testing**: Dry-run without real API calls, cost-free validation
- **CI/CD**: Automated execution without human approvals (YOLO mode)
- **Production**: Full execution with proper approvals
- **Planning**: Preview execution plan without running

Users requested two high-value modes after reviewing execution-modes.md analysis:
1. **Plan Mode**: Analyze and preview workflow execution before running
2. **Dry-Run Mode**: Execute workflow with mocked LLM responses for testing

This ADR documents the architecture for execution modes and implements Plan and Dry-Run modes.

### Decision

Implement **execution modes as orchestration-level parameters** (not agent capabilities):

#### Architecture Principles

1. **Modes are Orchestration Parameters**: Controlled at workflow execution level
2. **Not Agent Capabilities**: Agents don't need mode awareness
3. **Composable**: Modes can combine (e.g., `--dry-run --yolo`)
4. **Graceful Degradation**: Modes fail gracefully if not supported

#### Currently Implemented Modes

| Mode            | Parameter                | Description                     | Phase |
| --------------- | ------------------------ | ------------------------------- | ----- |
| **Async**       | (default)                | Background execution            | 3     |
| **Sync**        | `sync=True`              | Blocking execution              | 3     |
| **Watch**       | `watch=True`             | Live streaming of execution     | 3     |
| **YOLO**        | `auto_approve=True`      | Auto-approve all approval gates | 4     |
| **Interactive** | (default with approvals) | Human-in-the-loop approvals     | 3     |
| **Sandbox**     | (filesystem tools)       | Restricted filesystem access    | 2     |

#### New Modes (This ADR)

**7. Plan Mode** (⭐⭐⭐ High Value):
- **Purpose**: Preview execution plan without running
- **Implementation**: Analyzes workflow DAG, estimates costs/time
- **CLI**: `paracle workflow plan <name>`
- **API**: `POST /workflows/plan`
- **Output**:
  - Topological execution order
  - Parallel execution groups
  - Approval gates identified
  - Cost estimation (tokens × price)
  - Time estimation (parallel groups)
- **Phase**: 4 (API Server & CLI Enhancement)

**8. Dry-Run Mode** (⭐⭐ Medium Value):
- **Purpose**: Execute with mocked LLM responses
- **Implementation**: Intercepts LLM calls, returns fixed/random responses
- **CLI**: `paracle workflow run <name> --dry-run`
- **API**: `POST /workflows/execute {"dry_run": true}`
- **Benefits**:
  - Cost-free testing
  - Predictable responses
  - No external dependencies
- **Phase**: 4 (API Server & CLI Enhancement)

### Consequences

#### Positive

✅ **Plan Mode**: Preview before execution, cost estimation, identify parallelization
✅ **Dry-Run Mode**: Cost-free testing, predictable behavior, no external deps
✅ **Architecture**: Clean separation (modes ≠ agent capabilities), composable, extensible

#### Negative

⚠️ **Plan Mode**: Estimates may be inaccurate, doesn't account for dynamic branching
⚠️ **Dry-Run Mode**: Mock responses may not match real behavior

### Roadmap Integration

**Phase 4** (API Server & CLI Enhancement):
- ✅ plan_mode # IMPLEMENTED
- ✅ dry_run_mode # IMPLEMENTED

### References

- ADR-020: Vibe Kanban Features
- docs/execution-modes.md
- examples/08_yolo_mode.py

